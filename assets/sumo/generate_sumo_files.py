import os
import subprocess

def generate_network():
    # Generate a grid network using netgenerate
    # We'll use a grid with some randomized features if possible, 
    # but for curved roads and complexity, a custom node/edge file is better.
    # However, for simplicity and reliability, let's start with a grid.
    net_file = "assets/sumo/city.net.xml"
    
    # netgenerate --grid --grid.number=5 --grid.length=200 --output-file=...
    cmd = [
        "netgenerate",
        "--grid",
        "--grid.number=6",
        "--grid.length=300",
        "--grid.attach-length=100",
        "--default.lanenumber=2",
        "--default.speed=13.89", # 50 km/h
        "--output-file=" + net_file,
        "--tls.guess=true",
        "--tls.layout=opposites"
    ]
    
    print("Generating network...")
    subprocess.run(cmd, check=True)

def generate_routes():
    # Generate random trips using randomTrips.py
    # SUMO_HOME must be set
    sumo_home = os.environ.get("SUMO_HOME", "/usr/local/opt/sumo/share/sumo")
    random_trips = os.path.join(sumo_home, "tools", "randomTrips.py")
    
    if not os.path.exists(random_trips):
        # Try finding it in common mac locations
        potential_paths = [
            "/opt/homebrew/share/sumo/tools/randomTrips.py",
            "/usr/local/share/sumo/tools/randomTrips.py"
        ]
        for p in potential_paths:
            if os.path.exists(p):
                random_trips = p
                break

    net_file = "assets/sumo/city.net.xml"
    route_file = "assets/sumo/city.rou.xml"
    
    cmd = [
        "python3", random_trips,
        "-n", net_file,
        "-r", route_file,
        "-e", "10000", 
        "-p", "0.5", 
        "--vehicle-class", "passenger",
        "--fringe-factor", "10",
        "--validate"
    ]
    
    print("Generating routes...")
    subprocess.run(cmd, check=True)

def create_config():
    config_content = """<configuration>
    <input>
        <net-file value="city.net.xml"/>
        <route-files value="city.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="10000"/>
    </time>
    <report>
        <no-step-log value="true"/>
    </report>
    <gui_only>
        <gui-settings-file value="settings.xml"/>
    </gui_only>
</configuration>"""
    
    with open("assets/sumo/city.sumocfg", "w") as f:
        f.write(config_content)
        
    # Create a basic settings file for colors
    settings_content = """<viewsettings>
    <scheme name="real world"/>
    <delay value="20"/>
</viewsettings>"""
    with open("assets/sumo/settings.xml", "w") as f:
        f.write(settings_content)

if __name__ == "__main__":
    if not os.path.exists("assets/sumo"):
        os.makedirs("assets/sumo")
    generate_network()
    generate_routes()
    create_config()
    print("SUMO files generated successfully.")
