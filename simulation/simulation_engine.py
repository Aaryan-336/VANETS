"""
Main simulation engine integrating SUMO with protocol testing
"""
import traci
import random
import numpy as np
from typing import Dict, List
from .protocols import create_protocols, Protocol
from .vehicle import VehicleManager
from .metrics_collector import MetricsCollector


class VANETSimulation:
    """Main VANET simulation engine"""
    
    def __init__(self, sumo_config_file: str, scenario_type: str = "urban"):
        self.sumo_config = sumo_config_file
        self.scenario_type = scenario_type
        self.protocols = create_protocols()
        self.vehicle_manager = VehicleManager()
        self.metrics = MetricsCollector()
        self.simulation_time = 0
        self.step_size = 0.1  # 100ms steps
        self.message_interval = 1.0  # Send messages every 1 second
        self.last_message_time = 0
        
    def start_sumo(self, gui: bool = False):
        """Start SUMO simulation"""
        sumo_binary = "sumo-gui" if gui else "sumo"
        sumo_cmd = [sumo_binary, "-c", self.sumo_config, 
                   "--step-length", str(self.step_size),
                   "--collision.action", "warn",
                   "--no-warnings", "true"]
        
        traci.start(sumo_cmd)
        print(f"SUMO started with config: {self.sumo_config}")
    
    def update_vehicles_from_sumo(self):
        """Update vehicle positions from SUMO"""
        # Get all vehicle IDs from SUMO
        vehicle_ids = traci.vehicle.getIDList()
        
        # Update or add vehicles
        for veh_id in vehicle_ids:
            position = traci.vehicle.getPosition(veh_id)
            speed = traci.vehicle.getSpeed(veh_id)
            angle = traci.vehicle.getAngle(veh_id)
            
            self.vehicle_manager.update_vehicle(veh_id, position, speed, angle)
        
        # Remove vehicles that left the simulation
        current_vehicles = set(self.vehicle_manager.vehicles.keys())
        sumo_vehicles = set(vehicle_ids)
        for veh_id in current_vehicles - sumo_vehicles:
            self.vehicle_manager.remove_vehicle(veh_id)
    
    def simulate_v2v_communication(self):
        """Simulate V2V communication between vehicles"""
        vehicles = self.vehicle_manager.get_all_vehicles()
        
        if len(vehicles) < 2:
            return
        
        # Select random pairs for communication
        num_communications = min(len(vehicles) // 2, 20)  # Limit to 20 simultaneous comms
        
        for _ in range(num_communications):
            # Random sender and receiver
            sender = random.choice(vehicles)
            receiver = random.choice(vehicles)
            
            if sender.id == receiver.id:
                continue
            
            distance = sender.distance_to(receiver)
            message = sender.generate_message("BSM")
            
            # Get current conditions
            vehicle_count = len(vehicles)
            avg_speed = self.vehicle_manager.get_average_speed() * 3.6  # Convert to km/h
            
            # Test each protocol
            for protocol_name, protocol in self.protocols.items():
                success, latency = protocol.attempt_transmission(
                    distance=distance,
                    packet_size=message['size'],
                    vehicle_density=vehicle_count,
                    speed=avg_speed
                )
                
                if success:
                    receiver.receive_message(message)
    
    def run_distance_test(self):
        """Test protocols at various distances"""
        print("\nRunning distance-based tests...")
        
        distances = range(50, 1100, 50)  # 50m to 1100m
        
        for protocol_name, protocol in self.protocols.items():
            protocol.reset_metrics()
            
            for distance in distances:
                # Simulate 10 transmissions at each distance
                successes = 0
                total_latency = 0
                
                for _ in range(10):
                    success, latency = protocol.attempt_transmission(
                        distance=distance,
                        packet_size=300,
                        vehicle_density=30,
                        speed=50
                    )
                    
                    if success:
                        successes += 1
                        total_latency += latency
                
                avg_latency = total_latency / successes if successes > 0 else 0
                self.metrics.record_distance_test(
                    protocol_name, distance, 
                    successes > 5, avg_latency
                )
    
    def run_density_test(self):
        """Test protocols at various vehicle densities"""
        print("\nRunning density-based tests...")
        
        densities = range(10, 210, 20)  # 10 to 200 vehicles
        
        for protocol_name, protocol in self.protocols.items():
            for density in densities:
                protocol.reset_metrics()
                
                # Simulate 50 transmissions at this density
                for _ in range(50):
                    distance = random.uniform(50, 300)
                    protocol.attempt_transmission(
                        distance=distance,
                        packet_size=300,
                        vehicle_density=density,
                        speed=50
                    )
                
                self.metrics.record_density_test(
                    protocol_name, density,
                    protocol.get_pdr(),
                    protocol.get_average_latency()
                )
    
    def run_speed_test(self):
        """Test protocols at various vehicle speeds"""
        print("\nRunning speed-based tests...")
        
        speeds = range(20, 140, 20)  # 20 to 140 km/h
        
        for protocol_name, protocol in self.protocols.items():
            for speed in speeds:
                protocol.reset_metrics()
                
                # Simulate 50 transmissions at this speed
                for _ in range(50):
                    distance = random.uniform(50, 300)
                    protocol.attempt_transmission(
                        distance=distance,
                        packet_size=300,
                        vehicle_density=50,
                        speed=speed
                    )
                
                self.metrics.record_speed_test(
                    protocol_name, speed,
                    protocol.get_pdr(),
                    protocol.get_average_latency()
                )
    
    def run_simulation(self, duration: int = 300, gui: bool = False):
        """
        Run the full simulation
        duration: simulation duration in seconds
        """
        print(f"\n{'='*70}")
        print(f"Starting VANET Simulation - {self.scenario_type.upper()} Scenario")
        print(f"{'='*70}\n")
        
        self.start_sumo(gui)
        
        steps = int(duration / self.step_size)
        
        try:
            for step in range(steps):
                # Advance SUMO simulation
                traci.simulationStep()
                self.simulation_time = step * self.step_size
                
                # Update vehicle positions
                self.update_vehicles_from_sumo()
                
                # Simulate communications at regular intervals
                if self.simulation_time - self.last_message_time >= self.message_interval:
                    self.simulate_v2v_communication()
                    self.last_message_time = self.simulation_time
                
                # Record metrics every 10 seconds
                if step % int(10 / self.step_size) == 0:
                    self.metrics.record_time_series(self.simulation_time, self.protocols)
                    
                    # Progress indicator
                    vehicle_count = self.vehicle_manager.get_vehicle_count()
                    progress = (step / steps) * 100
                    print(f"\rProgress: {progress:.1f}% | Time: {self.simulation_time:.1f}s | Vehicles: {vehicle_count}", end='')
            
            print("\n\nSUMO simulation completed!")
            
            # Run additional tests
            self.run_distance_test()
            self.run_density_test()
            self.run_speed_test()
            
            # Calculate final statistics
            self.metrics.calculate_summary_statistics(self.protocols)
            
            # Print report
            print(self.metrics.get_comparison_report())
            
        except Exception as e:
            print(f"\nError during simulation: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            traci.close()
            print("\nSUMO connection closed")
    
    def export_results(self, filename: str = None):
        """Export simulation results"""
        if filename is None:
            filename = f"results/{self.scenario_type}_results.json"
        
        self.metrics.export_to_json(filename)
        return self.metrics.get_data_for_dashboard()