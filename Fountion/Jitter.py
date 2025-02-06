import subprocess
import threading
import time
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta

class JitterMonitor:
    def __init__(self, window_size=30, log_interval=24*60*60):
        """
        Initialize Jitter Monitoring System
        :param window_size: Number of seconds to keep in real-time display
        :param log_interval: Interval for logging 24-hour average
        """
        # Data storage
        self.timestamps = []
        self.jitter_values = []
        
        # Configuration
        self.window_size = window_size
        self.log_interval = log_interval
        
        # Logging setup
        self.daily_jitter_rates = []
        self.last_log_time = datetime.now()
        
        # Threading for jitter monitoring
        self.running = True
        self.jitter_thread = threading.Thread(target=self._monitor_jitter)
        self.jitter_thread.daemon = True
        
        # Matplotlib setup
        plt.style.use('default')
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.suptitle('Real-Time Network Jitter Monitor')

    def _ping_test(self, host='8.8.8.8', count=10):
        """
        Perform ping test to calculate jitter
        :param host: Target host for ping
        :param count: Number of ping attempts
        :return: Jitter value
        """
        try:
            # Use subprocess to run ping command
            if subprocess.os.name == 'nt':  # Windows
                ping_cmd = f"ping -n {count} {host}"
            else:  # Unix-like systems
                ping_cmd = f"ping -c {count} {host}"
            
            # Run ping command
            ping_output = subprocess.check_output(ping_cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            
            # Extract latency values
            latencies = re.findall(r'time[=<](\d+\.?\d*)ms', ping_output)
            
            # Convert to float
            latencies = [float(lat) for lat in latencies]
            
            # Calculate jitter (variation in latency)
            if len(latencies) > 1:
                # Jitter is the average absolute difference between consecutive latency measurements
                jitter = sum(abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))) / (len(latencies) - 1)
                return jitter
            return 0
        except Exception as e:
            print(f"Ping test error: {e}")
            return 0

    def _monitor_jitter(self):
        """
        Continuously monitor network jitter
        """
        while self.running:
            # Get current jitter
            jitter = self._ping_test()
            
            # Add timestamp and jitter
            current_time = datetime.now()
            self.timestamps.append(current_time)
            self.jitter_values.append(jitter)
            
            # Prune old data
            cutoff = current_time - timedelta(seconds=self.window_size)
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.pop(0)
                self.jitter_values.pop(0)
            
            # Print current jitter to terminal
            print(f"Current Jitter: {jitter:.2f} ms")
            
            # Log 24-hour average
            if (current_time - self.last_log_time).total_seconds() >= self.log_interval:
                self._log_daily_average()
                self.last_log_time = current_time
            
            # Wait before next test
            time.sleep(5)

    def _log_daily_average(self):
        """
        Log 24-hour average jitter to CSV
        """
        if self.jitter_values:
            avg_jitter = sum(self.jitter_values) / len(self.jitter_values)
            log_entry = {
                'timestamp': datetime.now(),
                'avg_jitter': avg_jitter
            }
            self.daily_jitter_rates.append(log_entry)
            
            # Save to CSV
            df = pd.DataFrame(self.daily_jitter_rates)
            df.to_csv('jitter_log.csv', index=False)
            print(f"24-hour average jitter logged: {avg_jitter:.2f} ms")

    def update_plot(self, frame):
        """
        Update matplotlib plot
        """
        self.ax.clear()
        self.ax.set_title('Network Jitter Monitor')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Jitter (ms)')
        
        if self.timestamps:
            self.ax.plot(self.timestamps, self.jitter_values, color='red', marker='o')
            
            # Highlight current jitter
            current_jitter = self.jitter_values[-1] if self.jitter_values else 0
            self.ax.text(0.02, 0.95, f'Current Jitter: {current_jitter:.2f} ms', 
                         transform=self.ax.transAxes, 
                         verticalalignment='top',
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.tight_layout()
        return self.ax

    def start(self):
        """
        Start jitter monitoring and visualization
        """
        # Start jitter monitoring thread
        self.jitter_thread.start()
        
        # Set up real-time plot
        animation = FuncAnimation(self.fig, self.update_plot, interval=1000)
        plt.show()

    def stop(self):
        """
        Stop monitoring
        """
        self.running = False
        self.jitter_thread.join()

def main():
    # Dependency check
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError:
        print("Please install required libraries: pip install pandas matplotlib")
        return

    monitor = JitterMonitor()
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nJitter monitoring stopped by user.")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()