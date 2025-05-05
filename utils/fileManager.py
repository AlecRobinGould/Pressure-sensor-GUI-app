import os
import csv
import configparser
import tkinter as tk  # Import tkinter to use StringVar

class FileManager:
    def __init__(self):
        self.filename_var = tk.StringVar()  # Use StringVar for filename
        self.load_settings()

    def load_settings(self):
        """
        Load settings from the configuration file.
        """
        config = configparser.ConfigParser()
        if not os.path.exists('settings.ini'):
            config['Settings'] = {
                'csv_filename': 'pressure_data.csv',
                'logging_enabled': '1'
            }
            with open('settings.ini', 'w') as configfile:
                config.write(configfile)
        else:
            config.read('settings.ini')

        # Generate an incremented log filename
        base_name = config['Settings']['csv_filename'].split('.')[0]
        self.filename_var.set(self.get_incremented_log_filename(base_name=base_name, extension='.csv'))

    def save_settings(self, logging_enabled):
        """
        Save settings to the configuration file.
        """
        config = configparser.ConfigParser()
        config['Settings'] = {
            'csv_filename': self.filename_var.get(),
            'logging_enabled': str(logging_enabled)
        }
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)

    def save_to_csv(self, filename, data, logging_enabled):
        """
        Save data to a CSV file if logging is enabled.
        """
        if logging_enabled:
            if not os.path.exists(filename):
                with open(filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Gauge Pressure", "Sensor 1", "Sensor 2", "Sensor 3", "Sensor 4", "Sensor 5", "Sensor 6", "Sensor 7", "Sensor 8"])
            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)

    def get_incremented_log_filename(self, base_name="log", extension=".csv", folder="Logs"):
        """
        Generate a unique log filename by incrementing the filename if it already exists.
        """
        if not os.path.exists(folder):
            os.makedirs(folder)

        file_path = os.path.join(folder, f"{base_name}{extension}")
        counter = 1

        while os.path.exists(file_path):
            file_path = os.path.join(folder, f"{base_name}_{counter}{extension}")
            counter += 1

        return file_path