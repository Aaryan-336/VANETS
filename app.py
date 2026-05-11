from flask import Flask, render_template, jsonify, request
import subprocess
import os

app = Flask(__name__)

# Constants
SIM_SCRIPT = "run_simulation.py"

# Global store for real-time stats (all protocols)
all_sim_stats = {
    "5G": {"vehicle_count": 0, "pdr": 0, "packets_sent": 0, "packets_received": 0, "stability": 0, "latency": 2},
    "CV2X": {"vehicle_count": 0, "pdr": 0, "packets_sent": 0, "packets_received": 0, "stability": 0, "latency": 10},
    "DSRC": {"vehicle_count": 0, "pdr": 0, "packets_sent": 0, "packets_received": 0, "stability": 0, "latency": 20}
}
sim_stats = all_sim_stats["DSRC"] # legacy support

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    global all_sim_stats, sim_stats
    all_sim_stats = {
        "5G": {"vehicle_count": 0, "pdr": 0, "packets_sent": 0, "packets_received": 0, "stability": 0, "latency": 2},
        "CV2X": {"vehicle_count": 0, "pdr": 0, "packets_sent": 0, "packets_received": 0, "stability": 0, "latency": 10},
        "DSRC": {"vehicle_count": 0, "pdr": 0, "packets_sent": 0, "packets_received": 0, "stability": 0, "latency": 20}
    }
    sim_stats = all_sim_stats["DSRC"]
    try:
        print(f"Starting simulation: {SIM_SCRIPT}")
        subprocess.Popen(["python3", SIM_SCRIPT], env=os.environ)
        return jsonify({"status": "success", "message": "Simulation started!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/update_stats', methods=['POST'])
def update_stats():
    global all_sim_stats, sim_stats
    data = request.json
    for proto, stats in data.items():
        if proto in all_sim_stats:
            all_sim_stats[proto].update(stats)
    
    active_proto = request.args.get('active', 'DSRC')
    if active_proto in all_sim_stats:
        sim_stats = all_sim_stats[active_proto]
        sim_stats["active_protocol"] = active_proto
        
    return jsonify({"status": "success"})

@app.route('/get_all_stats')
def get_all_stats():
    return jsonify(all_sim_stats)

@app.route('/get_stats')
def get_stats():
    return jsonify(sim_stats)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/settings')
def settings_view():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
