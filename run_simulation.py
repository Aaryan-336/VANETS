import os
import sys
from simulation.engine import SimulationEngine

if __name__ == "__main__":
    # Use the Vile Parle config as requested
    config = os.path.abspath("sumo_config/vile_parle/vile_parle.sumocfg")
    
    if not os.path.exists(config):
        # Fallback to generated config if Vile Parle is missing
        config = os.path.abspath("assets/sumo/city.sumocfg")
        
    if not os.path.exists(config):
        print(f"Error: Simulation config not found.")
        sys.exit(1)
        
    print(f"Starting simulation with config: {config}")
    engine = SimulationEngine(config)
    engine.run()
