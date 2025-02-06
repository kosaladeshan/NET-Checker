import matplotlib.pyplot as plt
import matplotlib.animation as animation
import psutil
import time

# Initialize lists to store data
times = []
download_speeds = []
upload_speeds = []

# Store the initial network stats
net_io = psutil.net_io_counters()
prev_download = net_io.bytes_recv
prev_upload = net_io.bytes_sent
prev_time = time.time()

# Function to update the plot
def update_plot(frame):
    global times, download_speeds, upload_speeds, prev_download, prev_upload, prev_time

    # Get current network stats
    net_io = psutil.net_io_counters()
    current_download = net_io.bytes_recv
    current_upload = net_io.bytes_sent
    current_time = time.time()

    # Calculate the speed
    download_speed = (current_download - prev_download) * 8 / (current_time - prev_time) / 1e6  # Convert to Mbps
    upload_speed = (current_upload - prev_upload) * 8 / (current_time - prev_time) / 1e6  # Convert to Mbps

    # Update previous values
    prev_download = current_download
    prev_upload = current_upload
    prev_time = current_time

    # Update lists
    times.append(current_time - times[0] if times else 0)  # Time in seconds from start
    download_speeds.append(download_speed)
    upload_speeds.append(upload_speed)

    # Print the current speeds to the terminal
    print(f"Download Speed: {download_speed:.2f} Mbps, Upload Speed: {upload_speed:.2f} Mbps")

    # Clear the plot every 10 seconds
    if len(times) > 1 and (times[-1] - times[0]) > 10:
        times = times[-10:]
        download_speeds = download_speeds[-10:]
        upload_speeds = upload_speeds[-10:]

    # Clear the plot
    ax.clear()

    # Plot the data using fill_between
    ax.fill_between(times, download_speeds, label='Download Speed (Mbps)', alpha=0.5)
    ax.fill_between(times, upload_speeds, label='Upload Speed (Mbps)', alpha=0.5)

    # Format the plot
    ax.legend(loc='upper left')
    ax.set_title('Real-Time Network Bandwidth')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Speed (Mbps)')
    ax.set_xlim(left=max(0, times[-1] - 10), right=times[-1])  # Keep the x-axis range to the last 10 seconds

# Create the plot
fig, ax = plt.subplots()
ani = animation.FuncAnimation(fig, update_plot, interval=1000)

# Show the plot
plt.show()