import tkinter as tk
from tkinter import ttk, messagebox

class SettingsTab:
    def __init__(self, notebook, file_manager, logging_var, sensor_tab):
        self.file_manager = file_manager
        self.logging_var = logging_var
        self.sensor_tab = sensor_tab  # Store the sensor_tab instance

        # Create the tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Settings")

        # Filename label and entry
        ttk.Label(self.tab, text="CSV Filename:").pack(pady=5)
        self.filename_entry = ttk.Entry(self.tab, textvariable=self.file_manager.filename_var, width=40)
        self.filename_entry.pack(pady=5)

        # Logging checkbox
        self.logging_checkbox = ttk.Checkbutton(self.tab, text="Enable Data Logging", variable=self.logging_var)
        self.logging_checkbox.pack(pady=5)

        # Save settings button
        save_button = ttk.Button(self.tab, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)

        # Clear plot button
        clear_plot_button = ttk.Button(self.tab, text="Clear Plot", command=self.clear_plot)
        clear_plot_button.pack(pady=5)

        # Plot button
        plot_button = ttk.Button(self.tab, text="Plot", command=self.plot_data)
        plot_button.pack(pady=5)

    def save_settings(self):
        """
        Save the settings to the file manager.
        """
        self.file_manager.save_settings(self.logging_var.get())
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def clear_plot(self):
        """
        Clear all points from the plots.
        """
        self.sensor_tab.clear_all_plots()  # Use the sensor_tab instance directly
        messagebox.showinfo("Clear Plot", "All plots have been cleared!")

    def plot_data(self):
        """
        Plot data from the file specified in the CSV filename textbox.
        """
        filename = self.file_manager.filename_var.get()
        try:
            self.sensor_tab.plot_from_file(filename)  # Use the sensor_tab instance directly
            messagebox.showinfo("Plot Data", f"Data from {filename} has been plotted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot data: {e}")