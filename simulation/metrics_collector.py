"""
Metrics collection and analysis for VANET simulation
"""
import json
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class MetricsCollector:
    """Collects and analyzes simulation metrics"""
    
    def __init__(self):
        self.time_series_data = {
            'DSRC': {'time': [], 'pdr': [], 'latency': [], 'throughput': []},
            'C-V2X': {'time': [], 'pdr': [], 'latency': [], 'throughput': []},
            '5G-V2X': {'time': [], 'pdr': [], 'latency': [], 'throughput': []}
        }
        
        self.distance_based_data = {
            'DSRC': {'distances': [], 'pdr': [], 'latency': []},
            'C-V2X': {'distances': [], 'pdr': [], 'latency': []},
            '5G-V2X': {'distances': [], 'pdr': [], 'latency': []}
        }
        
        self.density_based_data = {
            'DSRC': {'density': [], 'pdr': [], 'latency': []},
            'C-V2X': {'density': [], 'pdr': [], 'latency': []},
            '5G-V2X': {'density': [], 'pdr': [], 'latency': []}
        }
        
        self.speed_based_data = {
            'DSRC': {'speed': [], 'pdr': [], 'latency': []},
            'C-V2X': {'speed': [], 'pdr': [], 'latency': []},
            '5G-V2X': {'speed': [], 'pdr': [], 'latency': []}
        }
        
        self.summary_stats = {}
    
    def record_time_series(self, simulation_time: float, protocols: dict):
        """Record time-series metrics"""
        for protocol_name, protocol in protocols.items():
            self.time_series_data[protocol_name]['time'].append(simulation_time)
            self.time_series_data[protocol_name]['pdr'].append(protocol.get_pdr() * 100)
            self.time_series_data[protocol_name]['latency'].append(protocol.get_average_latency())
            
            # Calculate throughput (Mbps)
            if protocol.transmitted_packets > 0:
                avg_packet_size = 300  # bytes
                throughput = (protocol.received_packets * avg_packet_size * 8) / (simulation_time * 1e6)
                throughput = throughput * 1000  # Convert to Mbps
            else:
                throughput = 0
            self.time_series_data[protocol_name]['throughput'].append(throughput)
    
    def record_distance_test(self, protocol_name: str, distance: float, 
                            success: bool, latency: float):
        """Record distance-based test results"""
        self.distance_based_data[protocol_name]['distances'].append(distance)
        self.distance_based_data[protocol_name]['pdr'].append(100 if success else 0)
        self.distance_based_data[protocol_name]['latency'].append(latency if success else 0)
    
    def record_density_test(self, protocol_name: str, density: int, 
                           pdr: float, latency: float):
        """Record density-based test results"""
        self.density_based_data[protocol_name]['density'].append(density)
        self.density_based_data[protocol_name]['pdr'].append(pdr * 100)
        self.density_based_data[protocol_name]['latency'].append(latency)
    
    def record_speed_test(self, protocol_name: str, speed: float, 
                         pdr: float, latency: float):
        """Record speed-based test results"""
        self.speed_based_data[protocol_name]['speed'].append(speed)
        self.speed_based_data[protocol_name]['pdr'].append(pdr * 100)
        self.speed_based_data[protocol_name]['latency'].append(latency)
    
    def calculate_summary_statistics(self, protocols: dict):
        """Calculate summary statistics for all protocols"""
        self.summary_stats = {}
        
        for protocol_name, protocol in protocols.items():
            pdr = protocol.get_pdr() * 100
            avg_latency = protocol.get_average_latency()
            
            self.summary_stats[protocol_name] = {
                'total_transmitted': protocol.transmitted_packets,
                'total_received': protocol.received_packets,
                'failed_transmissions': protocol.failed_transmissions,
                'pdr': round(pdr, 2),
                'average_latency': round(avg_latency, 2),
                'max_range': protocol.specs.max_range,
                'bandwidth': protocol.specs.bandwidth,
                'reliability': protocol.specs.reliability * 100
            }
    
    def export_to_json(self, filename: str):
        """Export all collected data to JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'time_series': self.time_series_data,
            'distance_based': self.distance_based_data,
            'density_based': self.density_based_data,
            'speed_based': self.speed_based_data,
            'summary': self.summary_stats
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Metrics exported to {filename}")
    
    def get_comparison_report(self) -> str:
        """Generate a text comparison report"""
        if not self.summary_stats:
            return "No data collected yet"
        
        report = "\n" + "="*70 + "\n"
        report += "VANET PROTOCOL COMPARISON REPORT\n"
        report += "="*70 + "\n\n"
        
        for protocol_name, stats in self.summary_stats.items():
            report += f"\n{protocol_name}:\n"
            report += f"  Transmitted Packets: {stats['total_transmitted']}\n"
            report += f"  Received Packets: {stats['total_received']}\n"
            report += f"  Failed Transmissions: {stats['failed_transmissions']}\n"
            report += f"  Packet Delivery Ratio: {stats['pdr']}%\n"
            report += f"  Average Latency: {stats['average_latency']} ms\n"
            report += f"  Maximum Range: {stats['max_range']} m\n"
            report += f"  Bandwidth: {stats['bandwidth']} Mbps\n"
            report += f"  Base Reliability: {stats['reliability']}%\n"
        
        report += "\n" + "="*70 + "\n"
        report += "KEY INSIGHTS:\n"
        report += "="*70 + "\n"
        
        # Find best in each category
        best_pdr = max(self.summary_stats.items(), key=lambda x: x[1]['pdr'])
        best_latency = min(self.summary_stats.items(), key=lambda x: x[1]['average_latency'])
        best_range = max(self.summary_stats.items(), key=lambda x: x[1]['max_range'])
        
        report += f"\n✓ Best PDR: {best_pdr[0]} ({best_pdr[1]['pdr']}%)\n"
        report += f"✓ Best Latency: {best_latency[0]} ({best_latency[1]['average_latency']} ms)\n"
        report += f"✓ Best Range: {best_range[0]} ({best_range[1]['max_range']} m)\n"
        
        report += "\n5G-V2X Advantages:\n"
        report += "  • Ultra-low latency (~1ms base latency)\n"
        report += "  • Extended range up to 1000m\n"
        report += "  • High bandwidth (1000 Mbps)\n"
        report += "  • Superior reliability (99%)\n"
        report += "  • Better performance in high-density scenarios\n"
        report += "  • Enhanced beamforming capabilities\n"
        
        return report
    
    def get_data_for_dashboard(self) -> dict:
        """Get all data formatted for the web dashboard"""
        return {
            'timeSeries': self.time_series_data,
            'distanceBased': self.distance_based_data,
            'densityBased': self.density_based_data,
            'speedBased': self.speed_based_data,
            'summary': self.summary_stats
        }