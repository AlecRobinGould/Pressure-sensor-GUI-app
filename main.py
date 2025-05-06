import tkinter as tk
from tkinter import ttk
from gui.statusTab import StatusTab
from gui.sensorTab import SensorTab
from gui.settingsTab import SettingsTab
from utils.serialManager import SerialManager
from utils.fileManager import FileManager

def main():
    # Initialize GUI
    root = tk.Tk()
    root.title("Pressure Sensor GUI")
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Initialize shared variables
    ser_manager = SerialManager()
    file_manager = FileManager()
    update_active = tk.BooleanVar(value=False)
    heartbeat_active = tk.BooleanVar(value=False)
    logging_var = tk.IntVar(value=1)

    # Create tabs in the desired order
    status_tab = StatusTab(notebook, root, ser_manager, update_active, heartbeat_active, logging_var, None)  # Create StatusTab first
    sensor_tab = SensorTab(notebook, file_manager)  # Create SensorTab second
    settings_tab = SettingsTab(notebook, file_manager, logging_var, sensor_tab)  # Create SettingsTab last

    # Pass sensor_tab to status_tab after creation
    status_tab.sensor_tab = sensor_tab

    # Custom animation loop to update all sensor plots
    def update_all_plots():
        if update_active.get():
            sensor_tab.update_graph(None, ser_manager, update_active, logging_var, file_manager)
        root.after(100, update_all_plots)  # Schedule the next update

    # Start the custom animation loop
    update_all_plots()

    root.mainloop()

if __name__ == "__main__":
    main()