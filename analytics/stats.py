import csv
import os
import time

class AnalyticsReport:
    def __init__(self):
        self.data_history = []
        self.report_dir = "reports"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def log_step(self, step, protocols_data):
        # protocols_data is a dict of protocol stats
        entry = {"step": step}
        for p_name, stats in protocols_data.items():
            for key, val in stats.items():
                entry[f"{p_name}_{key}"] = val
        self.data_history.append(entry)

    def export_csv(self):
        if not self.data_history: return
        filename = f"reports/data_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        keys = self.data_history[0].keys()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.data_history)
        print(f"Data saved to: {filename}")
        return filename
