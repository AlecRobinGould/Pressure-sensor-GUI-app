import tkinter as tk
from tkinter import ttk, messagebox

class SettingsTab:
    def __init__(self, notebook, file_manager, logging_var):
        self.file_manager = file_manager
        self.logging_var = logging_var

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

    def save_settings(self):
        """
        Save the settings to the file manager.
        """
        self.file_manager.save_settings(self.logging_var.get())
        messagebox.showinfo("Settings", "Settings saved successfully!")