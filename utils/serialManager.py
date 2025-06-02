import serial
import serial.tools.list_ports
import threading

class SerialManager:
    def __init__(self):
        self.ser = None
        self.serial_lock = threading.Lock()  # Add a threading lock for thread-safe access


    def find_com_port(self):
        """
        Find the correct COM port for the Arduino device.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"Found port: {port.device}")
            print(f"port hwid: {port.hwid}")
            print(f"port pid: {port.pid}")
            print(f"port description: {port.description}")

            if "Arduino Leonardo ETH" in port.description:
                return port.device
        return None

    def initialize(self, baud_rate=9600, timeout=1):
        """
        Initialize the serial communication with the Arduino device.
        """
        com_port = self.find_com_port()
        if not com_port:
            print("No COM port found!")
            return False

        try:
            self.ser = serial.Serial(com_port, baud_rate, timeout=timeout)
            self.ser.write(b'ENQ\n')  # Send handshake command
            response = self.ser.readline().decode('utf-8').strip()
            if response == "ACK":
                print("Handshake successful!")

                # Read the error status sent by the microcontroller
                error_status_format = self.ser.readline().decode('utf-8').strip()
                if "Error status format" in error_status_format:
                    error_status = self.ser.readline().decode('utf-8').strip()
                    print(f"Initial Error Status: {error_status}")
                    return error_status.split(", ")  # Return the parsed error status as a list
                else:
                    print("No error status received after handshake.")
                    return ["N/A", "N/A", "N/A", "N/A"]  # Default to "N/A" if no error status is received
            else:
                print("Handshake failed!")
                self.ser.close()
                self.ser = None
                return False
        except Exception as e:
            print(f"Error initializing serial communication: {e}")
            return False

    def send_command(self, command):
        """
        Send a command to the Arduino device.
        """
        if self.ser:
            self.ser.write(command.encode())

    def send_heartbeat(self):
        """
        Send a heartbeat signal to the Arduino device.
        """
        if self.ser:
            self.ser.write(b'ENQ\n')
            response = self.ser.readline().decode('utf-8').strip()
            return response == "ACK"
        return False

    def close(self):
        """
        Close the serial connection.
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            print("Serial connection closed.")