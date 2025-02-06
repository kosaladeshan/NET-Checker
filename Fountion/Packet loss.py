import subprocess
import threading
import time
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta

class PacketLossMonitor:
    def __init__(self, window_size=30, log_interval=24*60*60):
        """
        Initialize Packet Loss Monitoring System
        :param window_size: Number of seconds to keep in real-time display
        :param log_interval: Interval for logging 24-hour average
        """
        # Data storage
        self.timestamps = []
        self.packet_loss_values = []
        
        # Configuration
        self.window_size = window_size
        self.log_interval = log_interval
        
        # Logging setup
        self.daily_packet_loss_rates = []
        self.last_log_time = datetime.now()
        
        # Threading for packet loss monitoring
        self.running = True
        self.packet_loss_thread = threading.Thread(target=self._monitor_packet_loss)
        self.packet_loss_thread.daemon = True
        
        # Matplotlib setup
        plt.style.use('seaborn-v0_8-darkgrid')  # Updated style name
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Real-Time Internet Packet Loss Monitor')

    def _ping_test(self, host='8.8.8.8', count=10):
        """
        Perform ping test to calculate packet loss
        :param host: Target host for ping
        :param count: Number of ping attempts
        :return: Packet loss percentage
        """
        try:
            # Use subprocess to run ping command
            if subprocess.os.name == 'nt':  # Windows
                ping_cmd = f"ping -n {count} {host}"
            else:  # Unix-like systems
                ping_cmd = f"ping -c {count} {host}"
            
            # Run ping command
            ping_output = subprocess.check_output(ping_cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            
            # Extract packet loss percentage
            packet_loss_match = re.search(r'(\d+)%\s*packet loss', ping_output, re.IGNORECASE)
            
            if packet_loss_match:
                packet_loss = float(packet_loss_match.group(1))
                return packet_loss
            
            return 0
        except Exception as e:
            print(f"Packet loss test error: {e}")
            return 0

    def _monitor_packet_loss(self):
        """
        Continuously monitor network packet loss
        """
        while self.running:
            # Get current packet loss
            packet_loss = self._ping_test()
            
            # Add timestamp and packet loss
            current_time = datetime.now()
            self.timestamps.append(current_time)
            self.packet_loss_values.append(packet_loss)
            
            # Prune old data
            cutoff = current_time - timedelta(seconds=self.window_size)
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.pop(0)
                self.packet_loss_values.pop(0)
            
            # Print current packet loss to terminal
            print(f"Current Packet Loss: {packet_loss:.2f}%")
            
            # Log 24-hour average
            if (current_time - self.last_log_time).total_seconds() >= self.log_interval:
                self._log_daily_average()
                self.last_log_time = current_time
            
            # Wait before next test
            time.sleep(5)

    def _log_daily_average(self):
        """
        Log 24-hour average packet loss to CSV
        """
        if self.packet_loss_values:
            avg_packet_loss = sum(self.packet_loss_values) / len(self.packet_loss_values)
            log_entry = {
                'timestamp': datetime.now(),
                'avg_packet_loss': avg_packet_loss
            }
            self.daily_packet_loss_rates.append(log_entry)
            
            # Save to CSV
            df = pd.DataFrame(self.daily_packet_loss_rates)
            df.to_csv('packet_loss_log.csv', index=False)
            print(f"24-hour average packet loss logged: {avg_packet_loss:.2f}%")

    def update_plot(self, frame):
        """
        Update matplotlib plots
        """
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        
        # Packet Loss Line Plot
        if self.timestamps:
            self.ax1.plot(self.timestamps, self.packet_loss_values, color='red', marker='o')
            self.ax1.set_title('Packet Loss Percentage Over Time')
            self.ax1.set_xlabel('Time')
            self.ax1.set_ylabel('Packet Loss (%)')
            
            # Highlight current packet loss
            current_packet_loss = self.packet_loss_values[-1] if self.packet_loss_values else 0
            self.ax1.text(0.02, 0.95, f'Current Packet Loss: {current_packet_loss:.2f}%', 
                          transform=self.ax1.transAxes, 
                          verticalalignment='top',
                          bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        # Packet Loss Histogram
        if self.packet_loss_values:
            self.ax2.hist(self.packet_loss_values, bins=10, color='blue', alpha=0.7)
            self.ax2.set_title('Packet Loss Distribution')
            self.ax2.set_xlabel('Packet Loss (%)')
            self.ax2.set_ylabel('Frequency')
        
        plt.tight_layout()
        return self.ax1, self.ax2

    def start(self):
        """
        Start packet loss monitoring and visualization
        """
        # Start packet loss monitoring thread
        self.packet_loss_thread.start()
        
        # Set up real-time plot
        animation = FuncAnimation(self.fig, self.update_plot, interval=1000)
        plt.show()

    def stop(self):
        """
        Stop monitoring
        """
        self.running = False
        self.packet_loss_thread.join()

def main():
    # Dependency check
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError:
        print("Please install required libraries: pip install pandas matplotlib")
        return

    monitor = PacketLossMonitor()
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nPacket Loss monitoring stopped by user.")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()