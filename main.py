import threading
import queue
import customtkinter as ctk
from gui.statusTab import StatusTab
from gui.sensorTab import SensorTab
from gui.settingsTab import SettingsTab
from utils.serialManager import SerialManager
from utils.fileManager import FileManager
from tkinter import messagebox
from PIL import Image, ImageTk  # Import PIL for image processing
# import logging

# Configure logging
# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

class PressureSensorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure the main window
        self.title("Pressure Sensor GUI")
        self.geometry("1200x700")
        ctk.set_appearance_mode("Dark")  # Default to dark mode
        ctk.set_default_color_theme("blue")  # Use the "blue" theme

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Add a Canvas for the watermark
        self.canvas = ctk.CTkCanvas(self, width=1200, height=700, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Load and place the watermark image
        self.add_watermark("EMSS.png")

        # Create a frame for the main content
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")  # Transparent frame
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        # Ensure the content_frame is raised above the canvas
        self.content_frame.tkraise()

        # Create a notebook (tab view)
        self.notebook = ctk.CTkTabview(self.content_frame, width=1200, height=700)
        self.notebook.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Add tabs to the notebook
        self.notebook.add("Status")
        self.notebook.add("Sensors")
        self.notebook.add("Settings")

        # Initialize shared variables
        self.ser_manager = SerialManager()
        self.file_manager = FileManager()
        self.update_active = ctk.BooleanVar(value=False)
        self.heartbeat_active = ctk.BooleanVar(value=False)
        self.logging_var = ctk.IntVar(value=1)

        # Create tab content
        self.sensor_tab = SensorTab(self.notebook.tab("Sensors"), self.file_manager)
        self.sensor_tab.grid(row=0, column=0, sticky="nsew")  # Add SensorTab to the "Sensors" tab

        self.status_tab = StatusTab(self.notebook.tab("Status"), self, self.ser_manager, self.update_active, self.heartbeat_active, self.logging_var, self.sensor_tab)
        self.status_tab.grid(row=0, column=0, sticky="nsew")  # Add StatusTab to the "Status" tab

        self.settings_tab = SettingsTab(self.notebook.tab("Settings"), self.file_manager, self.logging_var, self.sensor_tab)
        self.settings_tab.grid(row=0, column=0, sticky="nsew")  # Add SettingsTab to the "Settings" tab

        # Handle app close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start the custom animation loop
        self.update_all_plots()

    def add_watermark(self, image_path):
        """
        Add a watermark image to the canvas with reduced opacity.
        """
        try:
            # Load the image
            image = Image.open(image_path)

            # Adjust opacity
            alpha = image.split()[3]  # Get the alpha channel
            alpha = alpha.point(lambda p: p * 0.2)  # Reduce opacity to 20%
            image.putalpha(alpha)

            # Convert to a format usable by Tkinter
            self.watermark_image = ctk.CTkImage(image,
                                  image,
                                  size=(300, 300))

            # Place the image on the canvas
            # self.canvas.create_image(600, 350, image=self.watermark_image, anchor="center")
            self.canvas.create_image(600, 350, image=self.watermark_image, anchor="center", tags="watermark")
        except Exception as e:
            print(f"Error loading watermark image: {e}")

    def update_all_plots(self):
        """
        Custom animation loop to update all sensor plots and handle errors.
        """
        if self.update_active.get() and self.ser_manager.ser:
            try:
                with self.ser_manager.serial_lock:
                    if self.ser_manager.ser.in_waiting > 0:
                        raw_data = self.ser_manager.ser.readline().decode('utf-8').strip()
                        if raw_data:
                            # Check if the response contains error status
                            if "Error status format" in raw_data:
                                # Parse the next line for error status
                                error_status = self.ser_manager.ser.readline().decode('utf-8').strip()
                                error_status_list = error_status.split(", ")
                                self.status_tab.update_error_status(error_status_list)
                            else:
                                # Process normal sensor data
                                self.sensor_tab.process_serial_data(raw_data, self.logging_var, self.file_manager)
            except Exception as e:
                # logging.error(f"Error reading serial data: {e}")
                pass

        # Schedule the next update
        self.after(100, self.update_all_plots)

    def on_closing(self):
        """
        Handle the app close event.
        """
        if self.update_active.get():
            # Send stop test command to Arduino
            self.ser_manager.send_command("r")
            # logging.debug("Stop test command sent to Arduino.")

        # Close the serial connection
        self.ser_manager.close()

        # Confirm exit
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()


if __name__ == "__main__":
    app = PressureSensorApp()
    app.mainloop()