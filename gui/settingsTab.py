import customtkinter as ctk
from tkinter import messagebox, filedialog


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, file_manager, logging_var, sensor_tab):
        super().__init__(parent)

        self.file_manager = file_manager
        self.logging_var = logging_var
        self.sensor_tab = sensor_tab

        # Configure grid layout for the entire tab
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create a frame to center all content
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0, padx=480, pady=20, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Create widgets
        self.filename_label = ctk.CTkLabel(content_frame, text="CSV Filename:", font=ctk.CTkFont(size=14))
        self.filename_label.grid(row=0, column=0, padx=20, pady=10, sticky="n")

        self.filename_entry = ctk.CTkEntry(content_frame, placeholder_text="Enter filename", textvariable=self.file_manager.filename_var)
        self.filename_entry.grid(row=1, column=0, padx=20, pady=10, sticky="n")

        self.logging_checkbox = ctk.CTkCheckBox(content_frame, text="Enable Data Logging", variable=self.logging_var)
        self.logging_checkbox.grid(row=2, column=0, padx=20, pady=10, sticky="n")

        self.save_button = ctk.CTkButton(content_frame, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=3, column=0, padx=20, pady=10, sticky="n")

        self.clear_plot_button = ctk.CTkButton(content_frame, text="Clear Plot", command=self.clear_plot)
        self.clear_plot_button.grid(row=4, column=0, padx=20, pady=10, sticky="n")

        self.plot_button = ctk.CTkButton(content_frame, text="Plot Data", command=self.plot_data)
        self.plot_button.grid(row=5, column=0, padx=20, pady=10, sticky="n")

        self.theme_label = ctk.CTkLabel(content_frame, text="Appearance Mode:", font=ctk.CTkFont(size=14))
        self.theme_label.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="n")

        self.theme_option_menu = ctk.CTkOptionMenu(content_frame, values=["Light", "Dark", "System"], command=self.change_theme)
        self.theme_option_menu.set("Dark")  # Default to dark mode
        self.theme_option_menu.grid(row=7, column=0, padx=20, pady=10, sticky="n")

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
        self.sensor_tab.clear_all_plots()
        messagebox.showinfo("Clear Plot", "All plots have been cleared!")

    def plot_data(self):
        """
        Open file explorer to select a data file and plot the data.
        """
        # Open file explorer dialog
        filename = filedialog.askopenfilename(
            initialdir="Logs",  # Default directory
            title="Select Data File",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
        )

        if filename:  # If a file is selected
            try:
                self.sensor_tab.plot_from_file(filename)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to plot data: {e}")
        else:
            messagebox.showinfo("Plot Data", "No file selected.")

    def change_theme(self, new_theme):
        """
        Change the appearance mode of the application.
        """
        ctk.set_appearance_mode(new_theme)