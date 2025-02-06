import sys
import time
import requests
import subprocess
import psutil
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import re   
import random
import matplotlib.pyplot as plt
from PyQt5.QtCore import QThread, pyqtSignal


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.prev_bandwidth = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        self.bandwidth_data = [0] * 100
        self.bandwidth_plot = pg.PlotWidget()
        self.checking_error_rate = False
        



class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('app.ui', self)  
        self.setupUi(self)
        self.checking = False
        self.jitter_timer = None
        self.checking_error_rate = False
        self.error_rate_timer = QTimer()
        self.error_rate_timer.timeout.connect(self.display_data_usage)
        self.checking_packet_loss = False
        self.data_usage_accumulator =  0
        self.data_usage_start_time = time.time()
        self.progressBar_2.setValue(0)
        self.data_usage_timer = QTimer()
        self.data_usage_timer.timeout.connect(self.display_data_usage)
        self.data_usage_interval =  60  # One minute in seconds
        self.data_usage_start_time = None
        self.data_usage_accumulator =  0

        # Bandwidth
        self.prev_bandwidth_recv = psutil.net_io_counters().bytes_recv
        self.prev_bandwidth_sent = psutil.net_io_counters().bytes_sent
        self.bandwidth_data_recv = [0] *   100
        self.bandwidth_data_sent = [0] *   100
        self.bandwidth_data_total = [0] *   100
        self.bandwidth_plot = pg.PlotWidget()
        self.layout = QtWidgets.QVBoxLayout(self.graphicsView)
        self.layout.addWidget(self.bandwidth_plot)
        self.bandwidth_curve_recv = self.bandwidth_plot.plot(self.bandwidth_data_recv, pen=pg.mkPen(color=(0,   0,   255), width=1))
        self.bandwidth_curve_sent = self.bandwidth_plot.plot(self.bandwidth_data_sent, pen=pg.mkPen(color=(255,   0,   0), width=1))
        self.bandwidth_curve_total = self.bandwidth_plot.plot(self.bandwidth_data_total, pen=pg.mkPen(color=(255,   255,   255), width=1))
        self.bandwidth_timer = QTimer()
        self.bandwidth_timer.timeout.connect(self.update_bandwidth_chart)
        self.bandwidth_timer.start(1000)

        # Data Usage
        self.pushButton_2.clicked.connect(self.display_data_usage)

        self.pushButton_5.clicked.connect(self.display_network_jitter)
        
        # Packet loss
        self.pushButton_3.clicked.connect(self.display_packet_loss)

        self.packet_loss_data = [0] * 100
        self.packet_loss_plot = pg.PlotWidget()
        self.layout_packet_loss = QtWidgets.QVBoxLayout(self.graphicsView_4)
        self.layout_packet_loss.addWidget(self.packet_loss_plot)
        self.packet_loss_curve = self.packet_loss_plot.plot(self.packet_loss_data, pen=pg.mkPen(color=(255, 255, 0), width=1))

        
        # Throughput
        self.pushButton_4.clicked.connect(lambda: self.display_network_throughput(progress_callback=self.progressBar_3.setValue))

        
        # Latency
        self.pushButton.clicked.connect(self.display_network_latency)
                
        self.latency_plot = pg.PlotWidget()
        self.layout_latency = QtWidgets.QVBoxLayout(self.graphicsView_2)
        self.layout_latency.addWidget(self.latency_plot)
        self.latency_data = [0] * 100
        self.latency_curve = self.latency_plot.plot(self.latency_data, pen=pg.mkPen(color=(0, 255, 0), width=1))
        self.jitter_data = [0] * 100
        self.jitter_plot = pg.PlotWidget()
        self.layout_jitter = QtWidgets.QVBoxLayout(self.graphicsView_6)
        self.layout_jitter.addWidget(self.jitter_plot)
        self.jitter_curve = self.jitter_plot.plot(self.jitter_data, pen=pg.mkPen(color=(255, 0, 255), width=1))

    def display_data_usage(self):
        if self.data_usage_start_time is None:
            self.data_usage_start_time = time.time()
            self.data_usage_timer.start(1000)  # Start the timer to call display_data_usage every second
            self.pushButton_2.setText('Stop Checking')
        elif time.time() - self.data_usage_start_time >= self.data_usage_interval:
            self.data_usage_timer.stop()
            self.data_usage_start_time = None
            self.pushButton_2.setText('Start Checking')
            self.progressBar_2.setValue(0)  # Reset the progress bar
            data_usage = self.data_usage_accumulator / (1024 *  1024)  # Convert to megabytes
            self.textBrowser_4.append(f"Data Usage: The data usage over the past minute is {data_usage:.2f} MB.")
        else:
            current_io_counters = psutil.net_io_counters()
            diff_sent = current_io_counters.bytes_sent - self.prev_bandwidth_sent
            diff_recv = current_io_counters.bytes_recv - self.prev_bandwidth_recv
            self.data_usage_accumulator += diff_sent + diff_recv
            self.progressBar_2.setValue(int((time.time() - self.data_usage_start_time) / self.data_usage_interval *  100))
            self.prev_bandwidth_sent = current_io_counters.bytes_sent
            self.prev_bandwidth_recv = current_io_counters.bytes_recv

        
        self.progressBar_2.setValue(self.progressBar_2.value() +   1)
        if self.progressBar_2.value() >=   100:
            self.progressBar_2.reset()  # Reset the progress bar when complete
            data_usage = self.calculate_data_usage()
            if data_usage is not None:
                self.textBrowser_4.append(f"Data Usage: The data usage over the past minute is {data_usage:.2f} MB.")


    def calculate_data_usage(self):
        current_io_counters = psutil.net_io_counters()
        diff_sent = current_io_counters.bytes_sent - self.prev_bandwidth_sent
        diff_recv = current_io_counters.bytes_recv - self.prev_bandwidth_recv
        self.data_usage_accumulator += diff_sent + diff_recv

        if time.time() - self.data_usage_start_time >=  60:
            data_usage = self.data_usage_accumulator / (1024 *  1024)
            self.data_usage_accumulator =  0
            self.data_usage_start_time = time.time()
            return data_usage
        else:
            return None
        
    def update_bandwidth_chart(self):
        current_bandwidth_recv = psutil.net_io_counters().bytes_recv
        current_bandwidth_sent = psutil.net_io_counters().bytes_sent
        bandwidth_usage_recv = current_bandwidth_recv - self.prev_bandwidth_recv
        bandwidth_usage_sent = current_bandwidth_sent - self.prev_bandwidth_sent
        self.prev_bandwidth_recv = current_bandwidth_recv
        self.prev_bandwidth_sent = current_bandwidth_sent
        self.bandwidth_data_recv[:-1] = self.bandwidth_data_recv[1:]
        self.bandwidth_data_sent[:-1] = self.bandwidth_data_sent[1:]
        self.bandwidth_data_total[:-1] = self.bandwidth_data_total[1:]
        self.bandwidth_data_recv[-1] = bandwidth_usage_recv
        self.bandwidth_data_sent[-1] = bandwidth_usage_sent
        self.bandwidth_data_total[-1] = bandwidth_usage_recv + bandwidth_usage_sent
        self.bandwidth_curve_recv.setData(self.bandwidth_data_recv)
        self.bandwidth_curve_sent.setData(self.bandwidth_data_sent)
        self.bandwidth_curve_total.setData(self.bandwidth_data_total)
 
    

    def display_network_jitter(self):
        if self.jitter_timer is None:
            self.pushButton_5.setText('Stop Checking Jitter')
            self.jitter_timer = QTimer()
            self.jitter_timer.timeout.connect(self.update_network_jitter)
            self.jitter_timer.start(1000)
        else:
            self.pushButton_5.setText('Check Jitter')
            self.jitter_timer.stop()
            self.jitter_timer = None

    def get_network_jitter(self):
        latency_list = []
        for _ in range(3):
            result = subprocess.run(['ping', '-n', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()
            latency_line = output.split('\n')[-2]
            latency_match = re.search(r"(\d+(?:\.\d+)?)ms", latency_line)
            if latency_match:
                latency = float(latency_match.group(1))
                latency_list.append(latency)
            else:
                raise ValueError("No latency found in the output")
            time.sleep(1)
    
        jitter_list = [abs(latency_list[i] - latency_list[i - 1]) for i in range(1, len(latency_list))]
        jitter = sum(jitter_list) / len(jitter_list)
        return jitter
    
    def update_network_jitter(self):
        jitter = self.get_network_jitter()
        jitter_output = str(jitter)
        self.textBrowser_3.append(f"Network Jitter: The network jitter is {jitter_output} milliseconds.")
        self.jitter_data[:-1] = self.jitter_data[1:]
        self.jitter_data[-1] = jitter
        self.jitter_curve.setData(self.jitter_data)


    def display_packet_loss(self):
        if self.checking_packet_loss:
            self.pushButton_3.setText('Check Packet Loss')
            self.packet_loss_timer.stop()
        else:
            self.pushButton_3.setText('Stop Checking')
            self.packet_loss_timer = QTimer()
            self.packet_loss_timer.timeout.connect(self.update_packet_loss)
            self.packet_loss_timer.start(1000)
        self.checking_packet_loss = not self.checking_packet_loss


    def update_packet_loss(self):
        packet_loss = self.measure_packet_loss()
        if packet_loss is not None:
            self.textBrowser_5.append(f"Packet Loss Measurement Result: Packet loss: {packet_loss}%")
            self.packet_loss_data[:-1] = self.packet_loss_data[1:]
            self.packet_loss_data[-1] = packet_loss
            self.packet_loss_curve.setData(self.packet_loss_data)
        else:
            self.textBrowser_5.append("Packet Loss Measurement Result: Unable to measure packet loss")



    def measure_packet_loss(self):
        ping_output = subprocess.run(["ping", "-n", "3", "google.com"], capture_output=True, text=True)
        print("Ping output:", ping_output.stdout)
        packet_loss_str = ping_output.stdout.split('Lost = ')[1].split(' (')[0]
        print("Packet loss string:", packet_loss_str)
        try:
            packet_loss = float(packet_loss_str)
            return packet_loss
        except ValueError:
            print("Error: Could not convert packet loss string to float")
            return None



            
    def display_network_latency(self):
        if self.checking:
            self.pushButton.setText('Check Latency')
            self.latency_timer.stop()
        else:
            self.pushButton.setText('Stop Checking')
            self.latency_timer = QTimer()
            self.latency_timer.timeout.connect(self.update_network_latency)
            self.latency_timer.start(1000)
        self.checking = not self.checking

    
    def update_network_latency(self):
        result = subprocess.run(['ping', '-n', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        try:
            latency_line = output.split('\n')[-2]
            latency_match = re.search(r"(\d+(?:\.\d+)?)ms", latency_line)
            if latency_match:
                latency = float(latency_match.group(1))
                self.textBrowser_2.append(f"Latency: {latency:.2f} ms")
    
                # Update latency chart data
                self.latency_data[:-1] = self.latency_data[1:]
                self.latency_data[-1] = latency
                self.latency_curve.setData(self.latency_data)
    
            else:
                raise ValueError("No latency found in the output")
        except (IndexError, ValueError) as e:
            print(f"Error: {e}")
            self.textBrowser_2.append(f"Error: {e}")
    
    
    
    def handle_text_message_received(self, message):
        self.ui.textBrowser_2.append(message)

    def display_network_throughput(self, progress_callback=None):
        throughput = self.get_network_throughput(progress_callback)
        
        self.textBrowser_6.append(f"Network Throughput: The network throughput is {throughput:.2f} Mbps.")


    def get_network_throughput(self, progress_callback=None):
        sample_duration = 5
        initial_net_io = psutil.net_io_counters()

        for i in range(sample_duration):
            time.sleep(1)

            # Call the progress callback function with the current progress percentage
            if progress_callback:
                progress = int((i + 1) / sample_duration * 100)
                progress_callback(progress)

        final_net_io = psutil.net_io_counters()
        bytes_sent = final_net_io.bytes_sent - initial_net_io.bytes_sent
        bytes_received = final_net_io.bytes_recv - initial_net_io.bytes_recv
        total_bytes_transferred = bytes_sent + bytes_received
        total_megabits_transferred = (total_bytes_transferred * 8) / 1e6
        throughput = total_megabits_transferred / sample_duration
        return throughput
    


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
