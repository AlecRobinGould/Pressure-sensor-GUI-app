import customtkinter as ctk
from tkinter import messagebox
from threading import Lock
import time

class StatusTab(ctk.CTkFrame):
    def __init__(self, parent, root, ser_manager, update_active, heartbeat_active, logging_var, sensor_tab):
        super().__init__(parent)

        self.root = root
        self.ser_manager = ser_manager
        self.update_active = update_active
        self.heartbeat_active = heartbeat_active
        self.logging_var = logging_var
        self.sensor_tab = sensor_tab
        self.serial_lock = Lock()

        # Configure grid layout for the entire tab
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create a frame to center all content
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0, padx=460, pady=20, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Create a sub-frame for widgets
        widget_frame = ctk.CTkFrame(content_frame)
        widget_frame.grid(row=0, column=0, sticky="nsew")
        widget_frame.grid_columnconfigure(0, weight=1)

        # Status label
        self.status_label = ctk.CTkLabel(widget_frame, text="Status: Not Initialized", font=("Helvetica", 16))
        self.status_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        # Buttons
        self.initialize_button = ctk.CTkButton(widget_frame, text="Initialize Comms", command=self.initialize_comms)
        self.initialize_button.grid(row=1, column=0, padx=10, pady=10, sticky="n")

        self.start_stop_button = ctk.CTkButton(widget_frame, text="Start Test", command=self.toggle_test, state="disabled")
        self.start_stop_button.grid(row=2, column=0, padx=10, pady=10, sticky="n")

        # Create a frame for error indicators
        error_frame = ctk.CTkFrame(widget_frame)
        error_frame.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")
        error_frame.grid_columnconfigure(0, weight=1)

        # Error indicators
        self.error_indicators = {}
        error_types = ["SD card initialisation", "SD card log", "ADC", "RS485"]
        for i, error in enumerate(error_types):
            label = ctk.CTkLabel(error_frame, text=f"{error}: N/A", font=("Helvetica", 14), fg_color="gray", corner_radius=5)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            self.error_indicators[error] = label

    def initialize_comms(self):
        """
        Initialize the serial communication with the Arduino device.
        """
        # Close the serial port if it's already open
        self.ser_manager.close()

        # Initialize the serial communication
        error_status = self.ser_manager.initialize()
        if not error_status:
            messagebox.showerror("Error", "Failed to initialize serial communication!")
            return

        # Update the error indicators with the initial error status
        self.update_error_status(error_status)

        # Update the status label and buttons
        self.status_label.configure(text="Status: Initialized")
        self.initialize_button.configure(state="disabled")
        self.start_stop_button.configure(state="normal")
        self.heartbeat_active.set(True)
        print("Starting heartbeat...")
        self.root.after(2000, self.heartbeat)

    def update_error_status(self, error_status):
        """
        Update the error indicators based on the received error status.
        """
        error_types = ["SD card initialisation", "SD card log", "ADC", "RS485"]
        has_error = False  # Track if any error is active

        for i, error in enumerate(error_types):
            if error_status[i] == "1":
                self.error_indicators[error].configure(text=f"{error}: ERROR", fg_color="red")
                has_error = True  # An error is active
            elif error_status[i] == "0":
                self.error_indicators[error].configure(text=f"{error}: OK", fg_color="green")
            else:
                self.error_indicators[error].configure(text=f"{error}: N/A", fg_color="gray")

        # Disable the "Start Test" button if there is any error
        if has_error:
            self.start_stop_button.configure(state="disabled")
        else:
            self.start_stop_button.configure(state="normal")

    def toggle_test(self):
        if self.update_active.get():
            # Stop Test
            with self.serial_lock:
                self.ser_manager.send_command("r")
                confirmation = self.ser_manager.ser.readline().decode('utf-8').strip()
                while confirmation != "":
                    print(f"Confirmation Debug: confirmation={confirmation}")
                    confirmation = self.ser_manager.ser.readline().decode('utf-8').strip()
            self.update_active.set(False)
            self.start_stop_button.configure(text="Start Test")
            print("Test stopped!")
            self.heartbeat_active.set(True)
            self.root.after(5000, self.heartbeat)
        else:
            # Stop heartbeat before starting the test
            self.heartbeat_active.set(False)
            print("Stopping heartbeat...")
            # Clear the graph only if data has been plotted from a file
            if self.sensor_tab.data_plotted:
                self.sensor_tab.clear_all_plots()

            confirm = False
            timeout = 2  # Timeout in seconds
            start_time = time.time()

            with self.serial_lock:
                confirmation = self.ser_manager.ser.readline().decode('utf-8').strip()
                while confirmation != "":
                    print(f"Confirmation Debug: confirmation={confirmation}")
                    confirmation = self.ser_manager.ser.readline().decode('utf-8').strip()

                self.ser_manager.send_command("p")
                while not confirm:
                    # Check for timeout
                    if time.time() - start_time > timeout:
                        self.ser_manager.send_command("p")
                        # print("Timeout waiting for confirmation from Arduino.")
                        # messagebox.showerror("Error", "Timeout waiting for confirmation from Arduino.")
                        # return

                    # Read confirmation from Arduino
                    confirmation = self.ser_manager.ser.readline().decode('utf-8').strip()
                    print(f"Confirmation Debug: confirmation={confirmation}")
                    if confirmation == "Simulated button press from serial.":
                        print("Button press confirmed!")
                        confirm = True
                    time.sleep(0.1)

            self.update_active.set(True)
            self.start_stop_button.configure(text="Stop Test")
            print("Test started!")

    def heartbeat(self):
        """
        Periodically send a heartbeat signal to check if the serial connection is active.
        """
        if not self.heartbeat_active.get():
            print("Heartbeat stopped.")
            return

        with self.serial_lock:
            try:
                if self.ser_manager.ser:
                    print("Sending heartbeat...")
                    response = self.ser_manager.ser.readline().decode('utf-8').strip()
                    while response != "":
                        # Parse error status if present
                        if response.startswith("1") or response.startswith("0"):
                            error_status_list = response.split(", ")
                            print(f"Heartbeat Debug: response={response}")
                            self.update_error_status(error_status_list)
                        response = self.ser_manager.ser.readline().decode('utf-8').strip()

                    self.ser_manager.ser.write(b'ENQ\n')  # Send heartbeat command
                    response = self.ser_manager.ser.readline().decode('utf-8').strip()
                    print(f"Heartbeat response: {response}")

                    if response == "ACK":
                        print("Heartbeat successful.")
                    else:
                        print("Heartbeat failed.")
                        raise Exception("No ACK received.")
                else:
                    print("Serial connection is not active.")
                    raise Exception("Serial connection lost.")
            except Exception as e:
                print(f"Heartbeat error: {e}")
                # Mark the connection as not initialized
                self.ser_manager.close()
                self.status_label.configure(text="Status: Not Initialized")
                self.initialize_button.configure(state="normal")
                self.start_stop_button.configure(state="disabled")
                # Reset error indicators to "N/A"
                for label in self.error_indicators.values():
                    label.configure(text="N/A", fg_color="gray")
                return

        # Schedule the next heartbeat
        self.root.after(1000, self.heartbeat)