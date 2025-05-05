import tkinter as tk
from tkinter import ttk, messagebox
from threading import Lock
import time

class StatusTab:
    def __init__(self, notebook, root, ser_manager, update_active, heartbeat_active, logging_var):
        self.root = root
        self.ser_manager = ser_manager
        self.update_active = update_active
        self.heartbeat_active = heartbeat_active
        self.logging_var = logging_var
        self.serial_lock = Lock()

        # Create the tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Status")

        # Status light
        self.status_light = tk.Label(self.tab, text="Not Initialized", bg="red", fg="white", width=15)
        self.status_light.grid(row=0, column=1, pady=10)

        # Initialize Comms button
        self.initialize_button = ttk.Button(self.tab, text="Initialize Comms", command=self.initialize_comms)
        self.initialize_button.grid(row=0, column=0, pady=10)

        # Start/Stop Test button
        self.start_stop_button = ttk.Button(self.tab, text="Start Test", command=self.toggle_test, state=tk.DISABLED)
        self.start_stop_button.grid(row=1, column=0, pady=20)

        # Center the buttons
        self.tab.grid_rowconfigure(0, weight=1)
        self.tab.grid_rowconfigure(1, weight=1)
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_columnconfigure(1, weight=1)

    def initialize_comms(self):
        """
        Initialize the serial communication with the Arduino device.
        """
        # Close the serial port if it's already open
        self.ser_manager.close()

        if not self.ser_manager.initialize():
            messagebox.showerror("Error", "Failed to initialize serial communication!")
            return

        self.status_light.config(text="Initialized", bg="green")
        self.initialize_button.config(state=tk.DISABLED)
        self.start_stop_button.config(state=tk.NORMAL)
        self.heartbeat_active.set(True)
        print("Starting heartbeat...")
        self.root.after(5000, self.heartbeat)

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
            self.start_stop_button.config(text="Start Test")
            print("Test stopped!")
            self.heartbeat_active.set(True)
            self.root.after(5000, self.heartbeat)
        else:
            # Stop heartbeat before starting the test
            self.heartbeat_active.set(False)
            print("Stopping heartbeat...")
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
            self.start_stop_button.config(text="Stop Test")
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
                        response = self.ser_manager.ser.readline().decode('utf-8').strip()
                        print(f"Heartbeat Debug: response={response}")
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
                self.status_light.config(text="Not Initialized", bg="red")
                self.initialize_button.config(state=tk.NORMAL)
                self.start_stop_button.config(state=tk.DISABLED)
                return

        # Schedule the next heartbeat
        self.root.after(5000, self.heartbeat)