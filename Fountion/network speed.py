import matplotlib.pyplot as plt
import matplotlib.animation as animation
import speedtest
import time

# Initialize lists to store time and speed data
times = []
download_speeds = []
upload_speeds = []

# Function to get internet speed
def get_speed():
    st = speedtest.Speedtest()
    st.download()
    st.upload()
    return st.results.download / 1_000_000, st.results.upload / 1_000_000  # Convert to Mbps

# Function to update the plot
def update_plot(frame):
    download_speed, upload_speed = get_speed()
    current_time = time.strftime('%H:%M:%S')

    times.append(current_time)
    download_speeds.append(download_speed)
    upload_speeds.append(upload_speed)

    # Print the speeds to the terminal
    print(f"Time: {current_time} | Download Speed: {download_speed:.2f} Mbps | Upload Speed: {upload_speed:.2f} Mbps")

    ax.clear()
    ax.plot(times, download_speeds, label='Download Speed (Mbps)')
    ax.plot(times, upload_speeds, label='Upload Speed (Mbps)')
    ax.legend(loc='upper left')
    ax.set_xlabel('Time')
    ax.set_ylabel('Speed (Mbps)')
    ax.set_title('Real-Time Internet Speed')

    # Limit x-axis to show the last 10 measurements
    if len(times) > 10:
        times.pop(0)
        download_speeds.pop(0)
        upload_speeds.pop(0)

# Set up the plot
fig, ax = plt.subplots()
ani = animation.FuncAnimation(fig, update_plot, interval=100)  # Update every 1 second

plt.show()