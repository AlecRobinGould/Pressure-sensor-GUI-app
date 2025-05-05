import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import ttk
import matplotlib.pyplot as plt

class SensorTab:
    def __init__(self, notebook, file_manager):
        self.file_manager = file_manager
        self.x_data = [[] for _ in range(8)]
        self.y_data = [[] for _ in range(8)]
        self.lines = []
        self.axes = []
        self.canvases = []
        self.figures = []

        # Load LUT data
        self.lut_pressure, self.lut_average = self.load_lut_data("LUT of gauge tubes.csv")

        for i in range(8):
            self.create_sensor_tab(notebook, i)

    def load_lut_data(self, file_path):
        """
        Load LUT data from a CSV file and calculate averages.
        """
        try:
            df = pd.read_csv(file_path)
            df['Average'] = df[['Tube 1', 'Tube 2', 'Tube 3', 'Tube 4', 'Tube 5']].mean(axis=1)
            df['Pressure'] = df['Pressure'] * 0.00133322  # Convert mTorr to mBar
            return df['Pressure'].tolist(), df['Average'].tolist()
        except Exception as e:
            print(f"Error loading LUT data: {e}")
            return [], []

    def create_sensor_tab(self, notebook, sensor_index):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=f"Sensor {sensor_index + 1}")

        fig, ax = plt.subplots()
        ax.set_title(f"Sensor {sensor_index + 1}: Voltage vs Pressure")
        ax.set_xlabel("Gauge Pressure (log scale)")
        ax.set_ylabel("Voltage")
        ax.set_xscale("log")

        # Plot LUT data (static)
        ax.plot(self.lut_pressure, self.lut_average, label="LUT Average", color="red", linestyle="--")

        # Plot sensor data (dynamic)
        line_sensor, = ax.plot([], [], label=f"Sensor {sensor_index + 1} Data", color="blue", marker="o", linestyle="")
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, tab)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        self.lines.append(line_sensor)
        self.axes.append(ax)
        self.canvases.append(canvas)
        self.figures.append(fig)

    def update_graph(self, frame, ser_manager, update_active, logging_var, file_manager):
        if not update_active.get():
            return

        if ser_manager.ser and ser_manager.ser.in_waiting > 0:
            line_data = ser_manager.ser.readline().decode('utf-8', errors='replace').strip()
            while line_data == "Simulated button press from serial.":
                line_data = ser_manager.ser.readline().decode('utf-8', errors='replace').strip()
            print(f"Serial data: {line_data}")
            try:
                values = list(map(float, line_data.split(',')))
                if len(values) == 9:
                    pressures = values[:8]
                    gauge_pressure = values[8]

                    for i in range(8):
                        self.x_data[i].append(gauge_pressure)
                        self.y_data[i].append(pressures[i])
                        self.lines[i].set_data(self.x_data[i], self.y_data[i])

                        self.axes[i].relim()
                        self.axes[i].autoscale_view()

                    # Force all canvases to update
                    for canvas in self.canvases:
                        canvas.draw_idle()

                    file_manager.save_to_csv(file_manager.filename_var.get(), [gauge_pressure] + pressures, logging_var.get())
            except ValueError:
                print(f"Invalid data received: {line_data}")