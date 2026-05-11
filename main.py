
import sys
import os
import json
from simulation.simulation_engine import VANETSimulation
from flask import Flask, jsonify, send_file
from flask_cors import CORS

# Create results directory if it doesn't exist
os.makedirs('results', exist_ok=True)

def run_urban_simulation(gui=False):
    
    print("\n" + "="*70)
    print("RUNNING URBAN SCENARIO")
    print("="*70)
    
    sim = VANETSimulation(
        sumo_config_file='sumo_config/urban.sumocfg',
        scenario_type='urban'
    )
    
    sim.run_simulation(duration=300, gui=gui)
    results = sim.export_results('results/urban_results.json')
    
    return results

def run_mixed_simulation(gui=False):
    
    print("\n" + "="*70)
    print("RUNNING MIXED SCENARIO")
    print("="*70)
    
    sim = VANETSimulation(
        sumo_config_file='sumo_config/mixed.sumocfg',
        scenario_type='mixed'
    )
    
    sim.run_simulation(duration=300, gui=gui)
    results = sim.export_results('results/mixed_results.json')
    
    return results

def run_vile_parle_simulation(gui=False):
    
    print("\n" + "="*70)
    print("RUNNING VILE PARLE, MUMBAI SCENARIO")
    print("Real-world map from OpenStreetMap")
    print("="*70)
    
    sim = VANETSimulation(
        sumo_config_file='sumo_config/vile_parle/vile_parle.sumocfg',
        scenario_type='vile_parle'
    )
    
    sim.run_simulation(duration=300, gui=gui)
    results = sim.export_results('results/vile_parle_results.json')
    
    return results

def start_dashboard_server():
    
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    @app.route('/')
    def index():
        return send_file('dashboard.html')
    
    @app.route('/api/results/<scenario>', methods=['GET', 'OPTIONS'])
    def get_results(scenario):
        if request.method == 'OPTIONS':
            return '', 204
            
        try:
            filename = f'results/{scenario}_results.json'
            if not os.path.exists(filename):
                return jsonify({'error': f'Results not found for {scenario}. Run simulation first.'}), 404
                
            with open(filename, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/run/<scenario>', methods=['GET', 'OPTIONS'])
    def run_simulation(scenario):
        if request.method == 'OPTIONS':
            return '', 204
            
        try:
            print(f"\n{'='*70}")
            print(f"API Request: Running {scenario} simulation")
            print(f"{'='*70}\n")
            
            if scenario == 'urban':
                results = run_urban_simulation(gui=False)
            elif scenario == 'mixed':
                results = run_mixed_simulation(gui=False)
            elif scenario == 'vile_parle':
                results = run_vile_parle_simulation(gui=False)
            else:
                return jsonify({'error': f'Invalid scenario: {scenario}. Valid options: urban, mixed, vile_parle'}), 400
            
            return jsonify({
                'status': 'success', 
                'message': f'{scenario.replace("_", " ").title()} simulation completed successfully'
            })
        except Exception as e:
            print(f"\nERROR: {str(e)}\n")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'running',
            'message': 'VANET Dashboard API is running',
            'available_scenarios': ['urban', 'mixed', 'vile_parle']
        })
    
    print("\n" + "="*70)
    print("VANET DASHBOARD SERVER STARTED")
    print("="*70)
    print("\nServer Information:")
    print(f"  URL: http://localhost:8000")
    print(f"  API Base: http://localhost:8000/api")
    print(f"  Health Check: http://localhost:8000/api/health")
    print("\nAvailable Scenarios:")
    print("  - urban")
    print("  - mixed")
    print("  - vile_parle")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    # Run with threaded mode for better concurrency
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)

def main():
    """Main function"""
    print("\n" + "="*70)
    print("VANET SIMULATION - PROTOCOL COMPARISON")
    print("DSRC vs C-V2X vs 5G-V2X")
    print("="*70)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python main.py urban [--gui]       - Run urban scenario")
        print("  python main.py mixed [--gui]       - Run mixed scenario")
        print("  python main.py vile_parle [--gui]  - Run Vile Parle (Mumbai) scenario")
        print("  python main.py all [--gui]         - Run all scenarios")
        print("  python main.py dashboard           - Start web dashboard server")
        print("\nOptions:")
        print("  --gui                              - Show SUMO GUI during simulation")
        print("\nExamples:")
        print("  python main.py dashboard           - Start the web dashboard")
        print("  python main.py urban --gui         - Run urban scenario with GUI")
        print("  python main.py all                 - Run all scenarios without GUI")
        return
    
    command = sys.argv[1]
    show_gui = '--gui' in sys.argv
    
    if command == 'urban':
        run_urban_simulation(gui=show_gui)
        print("\n✅ Urban simulation completed!")
    
    elif command == 'mixed':
        run_mixed_simulation(gui=show_gui)
        print("\n✅ Mixed simulation completed!")
    
    elif command == 'vile_parle':
        run_vile_parle_simulation(gui=show_gui)
        print("\n✅ Vile Parle simulation completed!")
    
    elif command == 'all':
        run_urban_simulation(gui=show_gui)
        run_mixed_simulation(gui=show_gui)
        run_vile_parle_simulation(gui=show_gui)
        print("\n✅ All simulations completed!")
    
    elif command == 'dashboard':
        start_dashboard_server()
    
    else:
        print(f"\n❌ Unknown command: {command}")
        print("Use 'python main.py' without arguments to see usage")

if __name__ == "__main__":
    main()