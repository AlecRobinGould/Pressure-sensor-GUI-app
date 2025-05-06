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

        # Use the filename from settings.ini but prepend the Logs folder
        base_filename = config['Settings']['csv_filename']
        self.filename_var.set(self.get_incremented_log_filename(base_filename))

    def save_settings(self, logging_enabled):
        """
        Save settings to the configuration file.
        """
        config = configparser.ConfigParser()
        config['Settings'] = {
            'csv_filename': self.filename_var.get(),  # Keep the current filename
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

    def get_incremented_log_filename(self, base_filename, folder="Logs"):
        """
        Generate a unique log filename by incrementing the number in the filename.
        If the file exists and is empty, or if the file does not exist, do not increment.
        """
        # Ensure the folder exists
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Check if the folder is already part of the filename
        if base_filename.startswith(folder + os.sep):
            base_filename = base_filename[len(folder) + 1:]  # Remove the folder prefix

        # Extract the base name and number
        base_name, extension = os.path.splitext(base_filename)
        if "_" in base_name and base_name.split("_")[-1].isdigit():
            name_part = "_".join(base_name.split("_")[:-1])
            number = int(base_name.split("_")[-1])
        else:
            name_part = base_name
            number = 0

        # Construct the full file path
        current_filename = f"{name_part}_{number}{extension}"
        file_path = os.path.join(folder, current_filename)

        # Check if the file exists and is empty
        if os.path.exists(file_path):
            if os.path.getsize(file_path) == 0:  # File exists but is empty
                return file_path  # Return the current filename without incrementing
        else:
            return file_path  # File does not exist, return the current filename

        # Increment the number if the file exists and is not empty
        number += 1
        new_filename = f"{name_part}_{number}{extension}"
        file_path = os.path.join(folder, new_filename)

        # Ensure the filename is unique
        while os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            number += 1
            new_filename = f"{name_part}_{number}{extension}"
            file_path = os.path.join(folder, new_filename)

        return file_path