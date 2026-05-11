"""
Protocol implementations for DSRC, C-V2X, and 5G-V2X
"""
import numpy as np
from dataclasses import dataclass
from typing import Tuple
import random


@dataclass
class ProtocolSpecs:
    """Specifications for V2X protocols"""
    name: str
    max_range: float  # meters
    base_latency: float  # milliseconds
    bandwidth: float  # Mbps
    frequency: float  # GHz
    reliability: float  # 0-1


class Protocol:
    """Base class for V2X protocols"""
    
    def __init__(self, specs: ProtocolSpecs):
        self.specs = specs
        self.transmitted_packets = 0
        self.received_packets = 0
        self.total_latency = 0
        self.failed_transmissions = 0
        
    def calculate_signal_strength(self, distance: float, obstacles: int = 0) -> float:
        """Calculate signal strength based on distance and obstacles"""
        if distance > self.specs.max_range:
            return 0.0
        
        # Path loss model
        path_loss = 20 * np.log10(distance) + 20 * np.log10(self.specs.frequency) + 32.4
        obstacle_loss = obstacles * 10  # 10dB per obstacle
        total_loss = path_loss + obstacle_loss
        
        # Normalize to 0-1 range
        signal_strength = max(0, 1 - (total_loss / 150))
        return signal_strength
    
    def calculate_latency(self, distance: float, signal_strength: float) -> float:
        """Calculate end-to-end latency"""
        # Base latency + propagation delay + processing delay
        propagation_delay = (distance / 3e8) * 1000  # Convert to ms
        processing_delay = self.specs.base_latency
        
        # Add interference-based delay
        interference_delay = (1 - signal_strength) * 5  # Up to 5ms additional
        
        total_latency = propagation_delay + processing_delay + interference_delay
        return total_latency
    
    def attempt_transmission(self, distance: float, packet_size: int, 
                           vehicle_density: int, speed: float) -> Tuple[bool, float]:
        """
        Attempt to transmit a packet
        Returns: (success, latency)
        """
        self.transmitted_packets += 1
        
        # Calculate obstacles based on urban density
        obstacles = max(0, int(vehicle_density / 20))
        
        # Calculate signal strength
        signal_strength = self.calculate_signal_strength(distance, obstacles)
        
        # Calculate success probability
        success_prob = self._calculate_success_probability(
            signal_strength, vehicle_density, speed, packet_size
        )
        
        # Determine if transmission succeeds
        success = random.random() < success_prob
        
        if success:
            self.received_packets += 1
            latency = self.calculate_latency(distance, signal_strength)
            self.total_latency += latency
            return True, latency
        else:
            self.failed_transmissions += 1
            return False, 0
    
    def _calculate_success_probability(self, signal_strength: float, 
                                      density: int, speed: float, 
                                      packet_size: int) -> float:
        """Calculate probability of successful transmission"""
        # Base probability from signal strength
        base_prob = signal_strength * self.specs.reliability
        
        # Adjust for vehicle density (more vehicles = more interference)
        density_factor = max(0.5, 1 - (density / 200))
        
        # Adjust for speed (higher speed = more doppler effect)
        speed_factor = max(0.7, 1 - (speed / 150))
        
        # Adjust for packet size
        size_factor = max(0.8, 1 - (packet_size / 2000))
        
        return base_prob * density_factor * speed_factor * size_factor
    
    def get_pdr(self) -> float:
        """Get Packet Delivery Ratio"""
        if self.transmitted_packets == 0:
            return 0
        return self.received_packets / self.transmitted_packets
    
    def get_average_latency(self) -> float:
        """Get average latency"""
        if self.received_packets == 0:
            return 0
        return self.total_latency / self.received_packets
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.transmitted_packets = 0
        self.received_packets = 0
        self.total_latency = 0
        self.failed_transmissions = 0


class DSRC(Protocol):
    """DSRC (IEEE 802.11p) Protocol"""
    
    def __init__(self):
        specs = ProtocolSpecs(
            name="DSRC",
            max_range=300,  # meters
            base_latency=4,  # ms
            bandwidth=27,  # Mbps
            frequency=5.9,  # GHz
            reliability=0.85
        )
        super().__init__(specs)


class CV2X(Protocol):
    """C-V2X (LTE-based) Protocol"""
    
    def __init__(self):
        specs = ProtocolSpecs(
            name="C-V2X",
            max_range=500,  # meters
            base_latency=20,  # ms (higher due to network processing)
            bandwidth=100,  # Mbps
            frequency=5.9,  # GHz
            reliability=0.92
        )
        super().__init__(specs)
    
    def _calculate_success_probability(self, signal_strength: float, 
                                      density: int, speed: float, 
                                      packet_size: int) -> float:
        """C-V2X has better performance in high density"""
        base_prob = super()._calculate_success_probability(
            signal_strength, density, speed, packet_size
        )
        # C-V2X handles density better
        density_bonus = min(0.15, density / 1000)
        return min(1.0, base_prob + density_bonus)


class FiveGV2X(Protocol):
    """5G-V2X (5G NR-based) Protocol"""
    
    def __init__(self):
        specs = ProtocolSpecs(
            name="5G-V2X",
            max_range=1000,  # meters
            base_latency=1,  # ms (ultra-low latency)
            bandwidth=1000,  # Mbps
            frequency=28,  # GHz (mmWave)
            reliability=0.99
        )
        super().__init__(specs)
    
    def calculate_signal_strength(self, distance: float, obstacles: int = 0) -> float:
        """5G has better signal processing but mmWave is more sensitive to obstacles"""
        base_strength = super().calculate_signal_strength(distance, obstacles * 1.5)
        
        # 5G beamforming advantage
        if distance < 500:
            beamforming_gain = 0.2
        else:
            beamforming_gain = 0.1
            
        return min(1.0, base_strength + beamforming_gain)
    
    def _calculate_success_probability(self, signal_strength: float, 
                                      density: int, speed: float, 
                                      packet_size: int) -> float:
        """5G-V2X excels in all conditions"""
        base_prob = super()._calculate_success_probability(
            signal_strength, density, speed, packet_size
        )
        
        # 5G advantages
        density_bonus = min(0.1, density / 1500)
        speed_bonus = min(0.05, speed / 200)
        
        return min(1.0, base_prob + density_bonus + speed_bonus)


def create_protocols():
    """Factory function to create all protocols"""
    return {
        'DSRC': DSRC(),
        'C-V2X': CV2X(),
        '5G-V2X': FiveGV2X()
    }