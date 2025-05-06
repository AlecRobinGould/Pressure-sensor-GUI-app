import pandas as pd
import numpy as np  # Add this import at the top of the file
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
        self.pass_fail_labels = []  # Add this line to store pass/fail labels
        self.data_plotted = False  # Add a flag to track if data has been plotted

        # Load LUT data
        self.lut_pressure, self.lut_average = self.load_lut_data("LUT of gauge tubes.csv")

        for i in range(8):
            self.create_sensor_tab(notebook, i)
        
        # Ensure pass/fail labels are empty on startup
        for label in self.pass_fail_labels:
            label.set_text("")  # Set the label to an empty string

    def load_lut_data(self, file_path):
        """
        Load LUT data from a CSV file and calculate averages.
        """
        try:
            df = pd.read_csv(file_path)
            df['Average'] = df[['Tube 1', 'Tube 2', 'Tube 3', 'Tube 4', 'Tube 5']].mean(axis=1)
            df['Pressure'] = df['Pressure'] * 0.00133322  # Convert mTorr to mBar
            return df['Pressure'].tolist(), np.array(df['Average'].tolist())  # Convert Average to NumPy array
        except Exception as e:
            print(f"Error loading LUT data: {e}")
            return [], np.array([])

    def create_sensor_tab(self, notebook, sensor_index):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=f"Sensor {sensor_index + 1}")

        fig, ax = plt.subplots()
        ax.set_title(f"Sensor {sensor_index + 1}: Voltage vs Pressure")
        ax.set_xlabel("Gauge Pressure [mbar]")
        ax.set_ylabel("Sensor Voltage [mV]")
        ax.set_xscale("log")

        # Plot LUT data (static)
        ax.plot(self.lut_pressure, self.lut_average, label="LUT Average", color="red", linestyle="-")
        ax.plot(self.lut_pressure, self.lut_average * 1.1, label="Upper limit", color="green", linestyle="--")
        ax.plot(self.lut_pressure, self.lut_average * 0.9, label="Lower limit", color="green", linestyle="--")

        # Add Pass/Fail label
        pass_fail_label = ax.text(
            0.05, 0.95, "Pass", color="green", fontsize=12, transform=ax.transAxes, verticalalignment="top"
        )

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
        self.pass_fail_labels.append(pass_fail_label)  # Store the label for later updates

    def clear_all_plots(self):
        """
        Clear all points from the plots and reset the pass/fail labels.
        """
        for i in range(8):
            self.x_data[i].clear()
            self.y_data[i].clear()
            self.lines[i].set_data([], [])
            self.pass_fail_labels[i].set_text("")  # Reset the label to an empty string
            self.canvases[i].draw_idle()

    def plot_from_file(self, filename):
        """
        Plot data from the specified CSV file and re-evaluate pass/fail criteria.
        """
        self.clear_all_plots()  # Automatically clear the graph before plotting
        self.data_plotted = True  # Set the flag to True after plotting data
        try:
            df = pd.read_csv(filename)
            for i in range(8):
                self.x_data[i] = df["Gauge Pressure"].tolist()
                self.y_data[i] = df[f"Sensor {i + 1}"].tolist()
                self.lines[i].set_data(self.x_data[i], self.y_data[i])

                self.axes[i].relim()
                self.axes[i].autoscale_view()

                # Re-evaluate pass/fail criteria
                for j, pressure in enumerate(self.x_data[i]):
                    min_limit, max_limit = self.interpolate_limits(pressure)
                    if min_limit is not None and max_limit is not None:
                        if self.y_data[i][j] < min_limit or self.y_data[i][j] > max_limit:
                            self.pass_fail_labels[i].set_text("Fail")
                            self.pass_fail_labels[i].set_color("red")
                            print(f"Sensor {i + 1}: Voltage={self.y_data[i][j]}, Min={min_limit}, Max={max_limit}, Result=Fail")
                            break
                        else:
                            self.pass_fail_labels[i].set_text("Pass")
                            self.pass_fail_labels[i].set_color("green")
                            print(f"Sensor {i + 1}: Voltage={self.y_data[i][j]}, Min={min_limit}, Max={max_limit}, Result=Pass")
                    else:
                        self.pass_fail_labels[i].set_text("")  # Clear the label if limits cannot be interpolated

                self.canvases[i].draw_idle()
        except Exception as e:
            print(f"Error plotting data from file: {e}")
            raise

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

                        # Interpolate min and max limits for the current pressure
                        min_limit, max_limit = self.interpolate_limits(gauge_pressure)
                        if min_limit is not None and max_limit is not None:
                            if pressures[i] < min_limit or pressures[i] > max_limit:
                                self.pass_fail_labels[i].set_text("Fail")
                                self.pass_fail_labels[i].set_color("red")
                                print(f"Sensor {i + 1}: Voltage={pressures[i]}, Min={min_limit}, Max={max_limit}, Result=Fail")
                            else:
                                self.pass_fail_labels[i].set_text("Pass")
                                self.pass_fail_labels[i].set_color("green")
                                print(f"Sensor {i + 1}: Voltage={pressures[i]}, Min={min_limit}, Max={max_limit}, Result=Pass")
                        else:
                            self.pass_fail_labels[i].set_text("")  # Clear the label if limits cannot be interpolated

                    # Force all canvases to update
                    for canvas in self.canvases:
                        canvas.draw_idle()

                    file_manager.save_to_csv(file_manager.filename_var.get(), [gauge_pressure] + pressures, logging_var.get())
            except ValueError:
                print(f"Invalid data received: {line_data}")

    def interpolate_limits(self, pressure):
        """
        Interpolate the min and max allowable voltages for a given pressure.
        """
        if pressure < self.lut_pressure[0] or pressure > self.lut_pressure[-1]:
            # Pressure is out of bounds of the lookup table
            return None, None

        # Find the indices of the two closest pressures in the lookup table
        for i in range(len(self.lut_pressure) - 1):
            if self.lut_pressure[i] <= pressure <= self.lut_pressure[i + 1]:
                # Perform linear interpolation for min and max limits
                min_limit = (
                    self.lut_average[i] * 0.9 +
                    (self.lut_average[i + 1] * 0.9 - self.lut_average[i] * 0.9) *
                    (pressure - self.lut_pressure[i]) / (self.lut_pressure[i + 1] - self.lut_pressure[i])
                )
                max_limit = (
                    self.lut_average[i] * 1.1 +
                    (self.lut_average[i + 1] * 1.1 - self.lut_average[i] * 1.1) *
                    (pressure - self.lut_pressure[i]) / (self.lut_pressure[i + 1] - self.lut_pressure[i])
                )
                return min_limit, max_limit

        return None, None