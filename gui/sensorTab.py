import customtkinter as ctk
from tkinter import messagebox
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import threading
from scipy.optimize import curve_fit
# import logging


class SensorTab(ctk.CTkFrame):
    def __init__(self, parent, file_manager):
        super().__init__(parent)

        self.file_manager = file_manager
        self.x_data = [[] for _ in range(8)]
        self.y_data = [[] for _ in range(8)]
        self.pass_fail_labels = []
        self.data_plotted = False

        # Load LUT data
        # self.lut_pressure, self.lut_average, self.lut_values = self.load_lut_data("LUT of gauge tubes.csv")
        self.lut_pressure, self.lut_average, self.lut_values = self.load_lut_data("PLookUp.csv")

        # Fit logistic functions for limit lines
        self.lower_params, self.upper_params = self.calculate_logistic_limits()

        # Precompute logistic curves for LUT pressures
        self.lower_limits = [self.logistic_with_offset(np.log10(p), *self.lower_params) for p in self.lut_pressure]
        self.upper_limits = [self.logistic_with_offset(np.log10(p), *self.upper_params) for p in self.lut_pressure]

        # Configure grid layout for the entire tab
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create a frame to center all content
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0, padx=215, pady=20, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Create tabs for each sensor
        self.tabview = ctk.CTkTabview(content_frame)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        for i in range(8):
            self.create_sensor_tab(i)

    def load_lut_data(self, file_path):
        """
        Load LUT data from a CSV file and calculate averages and percentage differences.
        """
        try:
            df = pd.read_csv(file_path)
            # df['Average'] = df[['Tube 1', 'Tube 2', 'Tube 3', 'Tube 4', 'Tube 5']].mean(axis=1)
            df['Average'] = df[['PLookUp']].mean(axis=1)
            df['Pressure'] = df['Pressure'] * 0.00133322  # Convert mTorr to mBar
            # lut_values = df[['Tube 1', 'Tube 2', 'Tube 3', 'Tube 4', 'Tube 5']].values.tolist()
            lut_values = df[['PLookUp']].values.tolist()

            # # Calculate percentage differences
            # percentage_differences = []
            # for row in lut_values:
            #     min_val = min(row)
            #     max_val = max(row)
            #     percentage_diff = ((max_val - min_val) / min_val)
            #     percentage_differences.append(percentage_diff)

            return df['Pressure'].tolist(), np.array(df['Average'].tolist()), lut_values#, percentage_differences
        except Exception as e:
            print(f"Error loading LUT data: {e}")
            return [], np.array([]), [], []

    def calculate_logistic_limits(self):
        """
        Fit logistic functions to the LUT data to calculate the upper and lower limit lines.
        """
        p_log = np.log10(self.lut_pressure)  # Use log10(pressure) for fitting

        # Define custom percentage adjustments
        #                                   1    2    3     4      5      6     7      8     9     10    11    12    13    14    15
        # percentage_adjustments = np.array([0.1, 0.1, 0.09, 0.09, 0.10, 0.100, 0.130, 0.13, 0.15, 0.18, 0.20, 0.30, 0.40, 0.60, 0.80])
                                          # 1     2    3      4     5     6     7     8     9      10     11    12     13    14    15    16    17    18    19   20   21
        percentage_adjustments = np.array([0.1, 0.13, 0.16, 0.18, 0.20, 0.20, 0.20, 0.20, 0.220, 0.240, 0.250, 0.350, 0.45, 0.50, 0.55, 0.60, 0.62, 0.65, 0.7, 0.8, 0.9])
        # percentage_adjustments = np.array([0.1, 0.1, 0.14, 0.15, 0.17, 0.18, 0.18, 0.18, 0.190, 0.200, 0.250, 0.350, 0.45, 0.50, 0.55, 0.60, 0.62, 0.65, 0.7, 0.8, 0.9])



        # Ensure the array matches the number of pressure points
        if len(percentage_adjustments) != len(self.lut_pressure):
            raise ValueError("Percentage adjustments array must have the same length as the pressure array.")

        # Calculate the adjusted limit curves
        lower_v = self.lut_average * (1 - percentage_adjustments)
        upper_v = self.lut_average * (1 + percentage_adjustments)

        # Lower limit fit
        lower_params, _ = curve_fit(
            self.logistic_with_offset,
            p_log,
            lower_v,
            p0=[min(lower_v), max(lower_v) - min(lower_v), 1, np.median(p_log)]
        )

        # Upper limit fit
        upper_params, _ = curve_fit(
            self.logistic_with_offset,
            p_log,
            upper_v,
            p0=[min(upper_v), max(upper_v) - min(upper_v), 1, np.median(p_log)]
        )

        return lower_params, upper_params

    def create_sensor_tab(self, sensor_index):
        """
        Create a tab for each sensor.
        """
        tab = self.tabview.add(f"Sensor {sensor_index + 1}")

        # Create a Matplotlib figure for the sensor
        fig, ax = plt.subplots()
        ax.set_title(f"Sensor {sensor_index + 1}: Voltage vs Pressure", fontsize=14)
        ax.set_xlabel("Gauge Pressure [mbar]", fontsize=12)
        ax.set_ylabel("Sensor Voltage [mV]", fontsize=12)
        ax.set_xscale("log")

        # Plot LUT data (static)
        ax.plot(self.lut_pressure, self.lut_average, label="LUT Average", color="red", linestyle="-")

        # Plot precomputed logistic limit lines
        # ax.plot(self.lut_pressure, self.upper_limits, label="Upper Limit", color="green", linestyle="--")
        # ax.plot(self.lut_pressure, self.lower_limits, label="Lower Limit", color="green", linestyle="--")
        ax.plot(self.lut_pressure, self.upper_limits, label="Upper Limit", color="green", linewidth=1.5)
        ax.plot(self.lut_pressure, self.lower_limits, label="Lower Limit", color="green", linewidth=1.5)

        # Add Pass/Fail label
        pass_fail_label = ax.text(
            0.05, 0.95, "", color="green", fontsize=12, transform=ax.transAxes, verticalalignment="top"
        )

        # Plot sensor data (dynamic)
        line_sensor, = ax.plot([], [], label=f"Sensor {sensor_index + 1} Data", color="blue", marker="o", linestyle="")
        ax.legend()

        # Embed the Matplotlib figure in the tab
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Add Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, tab)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        # Store references for later updates
        self.pass_fail_labels.append(pass_fail_label)
        self.x_data[sensor_index] = []
        self.y_data[sensor_index] = []
        self.tabview.tab(f"Sensor {sensor_index + 1}").canvas = canvas
        self.tabview.tab(f"Sensor {sensor_index + 1}").line_sensor = line_sensor
        self.tabview.tab(f"Sensor {sensor_index + 1}").ax = ax

    def clear_all_plots(self):
        """
        Clear all points from the plots and reset the pass/fail labels.
        """
        for i in range(8):
            self.x_data[i] = []
            self.y_data[i] = []
            self.pass_fail_labels[i].set_text("")
            self.tabview.tab(f"Sensor {i + 1}").line_sensor.set_data([], [])
            self.tabview.tab(f"Sensor {i + 1}").canvas.draw()

    def plot_from_file(self, filename):
        """
        Plot data from the specified CSV file and re-evaluate pass/fail criteria.
        """
        def plot_task():
            try:
                # Load and process data in the background thread
                df = pd.read_csv(filename)

                # Extract pressure and sensor voltages
                pressure_data = df.iloc[:, -1].tolist()  # Pressure is the last column
                sensor_data = df.iloc[:, :-1]  # Sensor voltages are the first 8 columns

                processed_data = []
                for i in range(8):  # Loop through each sensor
                    x_data = pressure_data
                    y_data = sensor_data.iloc[:, i].tolist()

                    # Separate pass and fail points
                    pass_x = []
                    pass_y = []
                    fail_x = []
                    fail_y = []

                    for x, y in zip(x_data, y_data):
                        if self.check_point_within_limits(x, y):
                            pass_x.append(x)
                            pass_y.append(y)
                        else:
                            fail_x.append(x)
                            fail_y.append(y)

                    processed_data.append((x_data, y_data, pass_x, pass_y, fail_x, fail_y))

                # Schedule GUI updates in the main thread
                self.after(0, lambda: self.update_plots(processed_data, filename))

            except Exception as e:
                # Schedule the error popup in the main thread
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to plot data: {e}"))

        # Run the plotting task in a separate thread
        threading.Thread(target=plot_task, daemon=True).start()

    def update_plots(self, processed_data, filename):
        """
        Update the plots with the processed data and display Vout, R9, and R10 when applicable.
        """
        self.clear_all_plots()
        self.data_plotted = True

        for i, (x_data, y_data, pass_x, pass_y, fail_x, fail_y) in enumerate(processed_data):
            # Update the plot
            ax = self.tabview.tab(f"Sensor {i + 1}").ax
            ax.clear()

            # Re-plot LUT data
            ax.plot(self.lut_pressure, self.lut_average, label="LUT Average", color="red", linestyle="-")

            # Plot precomputed logistic limit lines
            ax.plot(self.lut_pressure, self.upper_limits, label="Upper Limit", color="green", linestyle="--")
            ax.plot(self.lut_pressure, self.lower_limits, label="Lower Limit", color="green", linestyle="--")

            # Plot pass points
            ax.scatter(pass_x, pass_y, label=f"Sensor {i + 1} Pass", color="blue", marker="o")

            # Plot fail points only if there are any
            if fail_x:
                ax.scatter(fail_x, fail_y, label=f"Sensor {i + 1} Failure", color="purple", marker="o")
                self.pass_fail_labels[i].set_text("Fail")
                self.pass_fail_labels[i].set_color("red")
            else:
                self.pass_fail_labels[i].set_text("Pass")
                self.pass_fail_labels[i].set_color("green")

            # Add pass/fail text back to the plot
            ax.text(
                0.05, 0.95, self.pass_fail_labels[i].get_text(),
                color=self.pass_fail_labels[i].get_color(),
                fontsize=12, transform=ax.transAxes, verticalalignment="top"
            )

            # Check if pressure is <= 2.5E-5 mbar and capture Vout
            for pressure, voltage in zip(x_data, y_data):
                if pressure <= 2.5E-5:
                    if not hasattr(self, f"captured_voltage_{i}"):  # Capture voltage once
                        captured_voltage = voltage
                        setattr(self, f"captured_voltage_{i}", captured_voltage)

                        # Get resistor values
                        resistor_values = self.get_resistor_values(captured_voltage)
                        if resistor_values:
                            r9, r10 = resistor_values
                            print(f"Sensor {i + 1}: Vout = {captured_voltage:.2f} mV, R9 = {r9} ohm, R10 = {r10}")
                            ax.text(
                                0.05, 0.85, f"Vout = {captured_voltage:.2f} mV\nR9 = {r9} Ω\nR10 = {r10}",
                                color="blue", fontsize=10, transform=ax.transAxes, verticalalignment="top"
                            )
                        else:
                            print(f"Sensor {i + 1}: Vout = {captured_voltage:.2f} mV is out of range!")
                            ax.text(
                                0.05, 0.85, f"Vout = {captured_voltage:.2f} mV\nOut of Range!",
                                color="red", fontsize=10, transform=ax.transAxes, verticalalignment="top"
                            )

            # Set plot labels and legend
            ax.set_title(f"Sensor {i + 1}: Voltage vs Pressure", fontsize=14)
            ax.set_xlabel("Gauge Pressure [mbar]", fontsize=12)
            ax.set_ylabel("Sensor Voltage [mV]", fontsize=12)
            ax.set_xscale("log")
            ax.legend()

            # Redraw the canvas
            self.tabview.tab(f"Sensor {i + 1}").canvas.draw()

        # Show confirmation popup
        messagebox.showinfo("Plot Data", f"Data from {filename} has been plotted!")

    # def interpolate_limits(self, pressure):
    #     """
    #     Interpolate the min and max allowable voltages for a given pressure.
    #     Use the LUT to calculate limits based on the percentage difference applied to the average sensor value.
    #     """
    #     if pressure < self.lut_pressure[0] or pressure > self.lut_pressure[-1]:
    #         return None, None

    #     for i in range(len(self.lut_pressure) - 1):
    #         if self.lut_pressure[i] <= pressure <= self.lut_pressure[i + 1]:
    #             # Determine the multiplication factor based on the pressure
    #             if pressure < 5E-2:  # Pressure less than 0.05 mbar
    #                 multiplication_factor = 5
    #             else:  # Pressure greater than or equal to 0.05 mbar
    #                 multiplication_factor = 7.5

    #             # Calculate the min and max limits for the two closest pressures
    #             min_limit_1 = self.lut_average[i] * (1 - self.percentage_differences[i] * multiplication_factor)
    #             max_limit_1 = self.lut_average[i] * (1 + self.percentage_differences[i] * multiplication_factor)
    #             min_limit_2 = self.lut_average[i + 1] * (1 - self.percentage_differences[i + 1] * multiplication_factor)
    #             max_limit_2 = self.lut_average[i + 1] * (1 + self.percentage_differences[i + 1] * multiplication_factor)

    #             # Interpolate the min and max limits for the given pressure
    #             min_limit = min_limit_1 + (min_limit_2 - min_limit_1) * (pressure - self.lut_pressure[i]) / (self.lut_pressure[i + 1] - self.lut_pressure[i])
    #             max_limit = max_limit_1 + (max_limit_2 - max_limit_1) * (pressure - self.lut_pressure[i]) / (self.lut_pressure[i + 1] - self.lut_pressure[i])

    #             return min_limit, max_limit

    #     return None, None

    # def update_graph(self, frame, ser_manager, update_active, logging_var, file_manager):
    #     """
    #     Update the sensor graph with new data from the serial manager.
    #     """
    #     try:
    #         # Read data from the serial manager
    #         with ser_manager.serial_lock:
    #             if ser_manager.ser and ser_manager.ser.in_waiting > 0:
    #                 raw_data = ser_manager.ser.readline().decode('utf-8').strip()
    #                 print(f"Debug: Received data: {raw_data}")

    #                 # Parse the data
    #                 data_parts = raw_data.split(",")
    #                 if len(data_parts) != 9:
    #                     print("Error: Invalid data format received.")
    #                     return

    #                 # Extract sensor voltages and pressure
    #                 sensor_voltages = [(float(value) / 300) * 1000 for value in data_parts[:8]]  # Convert volts to millivolts
    #                 pressure = float(data_parts[8])  # Pressure remains unchanged

    #                 # Update each sensor's plot
    #                 for i in range(8):
    #                     self.x_data[i].append(pressure)
    #                     self.y_data[i].append(sensor_voltages[i])

    #                     # Separate pass and fail points
    #                     pass_x = []
    #                     pass_y = []
    #                     fail_x = []
    #                     fail_y = []

    #                     for j, (x, y) in enumerate(zip(self.x_data[i], self.y_data[i])):
    #                         min_limit, max_limit = self.interpolate_limits(x)
    #                         if min_limit is not None and max_limit is not None:
    #                             if y < min_limit or y > max_limit:
    #                                 fail_x.append(x)
    #                                 fail_y.append(y)
    #                             else:
    #                                 pass_x.append(x)
    #                                 pass_y.append(y)
    #                         else:
    #                             pass_x.append(x)
    #                             pass_y.append(y)

    #                     # Update the plot
    #                     ax = self.tabview.tab(f"Sensor {i + 1}").ax

    #                     # Save current zoom level
    #                     xlim = ax.get_xlim()
    #                     ylim = ax.get_ylim()

    #                     ax.clear()

    #                     # Re-plot LUT data
    #                     ax.plot(self.lut_pressure, self.lut_average, label="LUT Average", color="red", linestyle="-")

    #                     # Plot precomputed logistic limit lines
    #                     ax.plot(self.lut_pressure, self.upper_limits, label="Upper Limit", color="green", linestyle="--")
    #                     ax.plot(self.lut_pressure, self.lower_limits, label="Lower Limit", color="green", linestyle="--")

    #                     # Plot pass points
    #                     ax.scatter(pass_x, pass_y, label=f"Sensor {i + 1} Pass", color="blue", marker="o")

    #                     # Plot fail points only if there are any
    #                     if fail_x:
    #                         ax.scatter(fail_x, fail_y, label=f"Sensor {i + 1} Failure", color="purple", marker="o")
    #                         self.pass_fail_labels[i].set_text("Fail")
    #                         self.pass_fail_labels[i].set_color("red")
    #                     else:
    #                         self.pass_fail_labels[i].set_text("Pass")
    #                         self.pass_fail_labels[i].set_color("green")

    #                     # Add pass/fail text back to the plot
    #                     ax.text(
    #                         0.05, 0.95, self.pass_fail_labels[i].get_text(),
    #                         color=self.pass_fail_labels[i].get_color(),
    #                         fontsize=12, transform=ax.transAxes, verticalalignment="top"
    #                     )

    #                     # Restore zoom level
    #                     ax.set_xlim(xlim)
    #                     ax.set_ylim(ylim)

    #                     # Set plot labels and legend
    #                     ax.set_title(f"Sensor {i + 1}: Voltage vs Pressure", fontsize=14)
    #                     ax.set_xlabel("Gauge Pressure [mbar]", fontsize=12)
    #                     ax.set_ylabel("Sensor Voltage [mV]", fontsize=12)
    #                     ax.set_xscale("log")
    #                     ax.legend()

    #                     # Redraw the canvas
    #                     self.tabview.tab(f"Sensor {i + 1}").canvas.draw()

    #                 # Save the data to a CSV file if logging is enabled
    #                 if logging_var.get():
    #                     data_row = sensor_voltages + [pressure]
    #                     file_manager.save_to_csv(file_manager.filename_var.get(), data_row, logging_var.get())

    #     except Exception as e:
    #         print(f"Error updating graph: {e}")
    
    def process_serial_data(self, raw_data, logging_var, file_manager):
        """
        Process raw data received from the serial port and dynamically update the plots.
        """
        try:
            # Debug: Print the raw data received
            print(f"Raw data received: {raw_data}")

            # Parse the data
            data_parts = raw_data.split(",")
            if len(data_parts) != 9:
                print("Error: Invalid data format received.")  # Debugging statement
                return  # Ignore invalid data

            # Validate and convert sensor voltages and pressure
            try:
                sensor_voltages = [(float(value) / 300) * 1000 for value in data_parts[:8]]  # Convert volts to millivolts
                pressure = float(data_parts[8])  # Pressure remains unchanged
            except ValueError as e:
                print(f"Error: Could not convert data to float: {e}")  # Debugging statement
                return  # Ignore invalid data

            # Ignore zero pressure values
            if pressure == 0:
                print("Warning: Pressure value is zero. Ignoring this data point.")
                return

            # Evaluate and plot each sensor's data point
            for i in range(8):
                voltage = sensor_voltages[i]
                ax = self.tabview.tab(f"Sensor {i + 1}").ax
                line_sensor = self.tabview.tab(f"Sensor {i + 1}").line_sensor

                # Update the data for the line plot
                self.x_data[i].append(pressure)
                self.y_data[i].append(voltage)
                line_sensor.set_data(self.x_data[i], self.y_data[i])

                # Check if the point passes or fails
                if self.check_point_within_limits(pressure, voltage):
                    # Update pass/fail labels and legend only if the state changes
                    if not hasattr(self, f"state_{i}") or getattr(self, f"state_{i}") != "Fail":
                        # Only update to "Pass" if the state is not already "Fail"
                        self.pass_fail_labels[i].set_text("Pass")
                        self.pass_fail_labels[i].set_color("green")
                        setattr(self, f"state_{i}", "Pass")
                        # Update the legend
                        legend = ax.get_legend()
                        if legend:
                            legend_texts = [t.get_text() for t in legend.get_texts()]
                            legend_texts = [t for t in legend_texts if f"Sensor {i + 1}" not in t]
                            legend_texts.append(f"Sensor {i + 1} Pass")
                            ax.legend(legend_texts)
                else:
                    # Update to "Fail" and ensure it remains
                    self.pass_fail_labels[i].set_text("Fail")
                    self.pass_fail_labels[i].set_color("red")
                    setattr(self, f"state_{i}", "Fail")
                    # Update the legend
                    legend = ax.get_legend()
                    if legend:
                        legend_texts = [t.get_text() for t in legend.get_texts()]
                        legend_texts = [t for t in legend_texts if f"Sensor {i + 1}" not in t]
                        legend_texts.append(f"Sensor {i + 1} Fail")
                        ax.legend(legend_texts)

                # Check if pressure is <= 2.5E-5 mbar and capture Vout
                if 0 < pressure <= 2.5E-5:  # Ensure pressure is greater than 0
                    if not hasattr(self, f"captured_voltage_{i}"):  # Capture voltage once
                        captured_voltage = voltage
                        setattr(self, f"captured_voltage_{i}", captured_voltage)

                        # Get resistor values
                        resistor_values = self.get_resistor_values(captured_voltage)
                        if resistor_values:
                            r9, r10 = resistor_values
                            print(f"Sensor {i + 1}: Vout = {captured_voltage:.2f} mV, R9 = {r9} ohm, R10 = {r10}")
                            ax.text(
                                0.05, 0.85, f"Vout = {captured_voltage:.2f} mV\nR9 = {r9} Ω\nR10 = {r10}",
                                color="blue", fontsize=10, transform=ax.transAxes, verticalalignment="top"
                            )
                        else:
                            print(f"Sensor {i + 1}: Vout = {captured_voltage:.2f} mV is out of range!")
                            ax.text(
                                0.05, 0.85, f"Vout = {captured_voltage:.2f} mV\nOut of Range!",
                                color="red", fontsize=10, transform=ax.transAxes, verticalalignment="top"
                            )

                # Redraw only the updated canvas
                self.tabview.tab(f"Sensor {i + 1}").canvas.draw_idle()

            # Save the data to a CSV file if logging is enabled
            if logging_var.get():
                data_row = sensor_voltages + [pressure]
                file_manager.save_to_csv(file_manager.filename_var.get(), data_row, logging_var.get())

        except Exception as e:
            print(f"Error processing serial data: {e}")

    def check_point_within_limits(self, pressure, voltage):
        """
        Check if a given point (pressure, voltage) falls within the logistic limit lines.

        Parameters:
            pressure (float): The pressure value to test.
            voltage (float): The voltage value to test.

        Returns:
            bool: True if the point is within the limits, False otherwise.
        """
        # Handle zero pressure by using the previous valid pressure
        if pressure == 0:
            if hasattr(self, 'last_valid_pressure'):
                pressure = self.last_valid_pressure
            else:
                print("Error: No valid previous pressure value available.")
                return False  # Cannot check limits without a valid pressure

        # Store the current pressure as the last valid pressure
        self.last_valid_pressure = pressure

        # Calculate the logistic limits
        p_log = np.log10(pressure)
        lower_limit = self.logistic_with_offset(p_log, *self.lower_params)
        upper_limit = self.logistic_with_offset(p_log, *self.upper_params)

        # Check if the voltage is within the limits
        return lower_limit <= voltage <= upper_limit

    def logistic_with_offset(self, x, C, L, k, x0):
        """
        Logistic function with an offset.
        """
        return C + L / (1 + np.exp(-k * (x - x0)))

    def get_resistor_values(self, voltage):
        """
        Get the resistor values (R9 and R10) based on the sensor voltage.

        Parameters:
            voltage (float): The captured sensor voltage in mV.

        Returns:
            tuple: (R9, R10) resistor values or None if out of range.
        """
        resistor_table = [
            (9.00, 150, "18k"), (9.05, 150, "36k"), (9.10, 150, "100M"),
            (9.15, 154, "8.2k"), (9.20, 154, "12k"), (9.25, 154, "18k"),
            (9.30, 154, "100k"), (9.35, 158, "6.8k"), (9.40, 158, "8.2k"),
            (9.45, 158, "12k"), (9.50, 158, "22k"), (9.55, 158, "100k"),
            (9.60, 162, "8.2k"), (9.65, 162, "10k"), (9.70, 162, "15k"),
            (9.75, 162, "30k"), (9.80, 162, "100k"), (9.85, 165, "12k"),
            (9.90, 165, "22k"), (9.95, 165, "47k"), (10.00, 169, "6.8k"),
            (10.05, 169, "10k"), (10.10, 169, "15k"), (10.15, 169, "22k"),
            (10.20, 169, "100k"), (10.25, 174, "6.8k"), (10.30, 174, "8.2k"),
            (10.35, 174, "10k"), (10.40, 174, "15k"), (10.45, 174, "22k"),
            (10.50, 174, "100k"), (10.55, 178, "8.2k"), (10.60, 178, "10k"),
            (10.65, 178, "15k"), (10.70, 178, "30k"), (10.75, 178, "100k"),
            (10.80, 182, "10k"), (10.85, 182, "12k"), (10.90, 182, "18k"),
            (10.95, 182, "30k"), (11.00, 182, "100k")
        ]

        # Check if the voltage is out of range
        if voltage < 9.0 or voltage > 11.0:
            return None

        # Find the closest voltage in the table
        closest_entry = min(resistor_table, key=lambda x: abs(x[0] - voltage))
        return closest_entry[1], closest_entry[2]