import scipy.io
import os
from Orange.data import Table
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input
from AnyQt.QtWidgets import QFileDialog, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox
from AnyQt.QtCore import Qt


class SaveToMATFile(OWWidget):
    name = "Save to .mat File"
    description = "Save a data table to a .mat file"
    icon = "icons/save_to_mat.svg"
    priority = 8
    keywords = ["save", "export", "mat file"]
    want_main_area = False
    want_control_area = True

    # Settings for recent save paths
    recent_paths = Setting([])

    class Inputs:
        data = Input("Data Table", Table)

    def __init__(self):
        super().__init__()
        self.data = None
        self.file_path = None
        self.column_names = []

        # Control Area: Save Options
        self.controlArea = gui.widgetBox(self.controlArea, "Save Options")

        # Save Location
        self.file_browser_button = gui.button(self.controlArea, self, "Choose Save Location", callback=self.choose_save_location)

        # Recent paths list
        self.recent_paths_list = QListWidget()
        self.recent_paths_list.itemClicked.connect(self.select_recent_path)
        self.controlArea.layout().addWidget(QLabel("Recent Save Paths:"))
        self.controlArea.layout().addWidget(self.recent_paths_list)
        self.update_recent_paths_list()

        # Column name configuration section
        self.column_names_area = QVBoxLayout()
        self.controlArea.layout().addLayout(self.column_names_area)

        # Save button
        self.save_button = QPushButton("Save to .mat")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_to_mat)
        self.controlArea.layout().addWidget(self.save_button)

    @Inputs.data
    def set_data(self, data):
        """Receive the input data table and populate column names."""
        if data:
            self.data = data
            self.column_names = [var.name for var in data.domain.attributes]
            self.display_column_name_inputs()
            self.save_button.setEnabled(True)
        else:
            self.data = None
            self.save_button.setEnabled(False)

    def choose_save_location(self):
        """Choose a save location for the .mat file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save as .mat File", "", "MAT files (*.mat)")
        if file_path:
            self.file_path = file_path if file_path.endswith(".mat") else file_path + ".mat"
            self.update_recent_paths(self.file_path)

    def select_recent_path(self, item):
        """Select a recent save path and set it as the current save path."""
        self.file_path = item.text()
        self.save_button.setEnabled(bool(self.file_path))

    def display_column_name_inputs(self):
        """Display input fields for modifying column names."""
        # Clear existing widgets in the column names area
        while self.column_names_area.count():
            child = self.column_names_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add label and input for each column
        for i, name in enumerate(self.column_names):
            label = QLabel(f"Column {i + 1}:")
            line_edit = QLineEdit(name)
            line_edit.setObjectName(f"col_{i}")
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(line_edit)
            self.column_names_area.addLayout(hbox)

    def update_column_names(self):
        """Update column names based on input fields."""
        updated_names = []
        for i in range(self.column_names_area.count()):
            hbox = self.column_names_area.itemAt(i).layout()
            line_edit = hbox.itemAt(1).widget()
            updated_names.append(line_edit.text())
        self.column_names = updated_names

    def save_to_mat(self):
        """Save the data table as a .mat file."""
        if not self.file_path or not self.data:
            QMessageBox.warning(self, "Save Error", "No file path or data available.")
            return

        try:
            # Prepare data dictionary for saving
            data_dict = {var_name: self.data[:, idx].X.flatten() for idx, var_name in enumerate(self.column_names)}
            scipy.io.savemat(self.file_path, data_dict, oned_as="column")
            QMessageBox.information(self, "Success", f"Data saved to {self.file_path}")
            self.update_recent_paths(self.file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def update_recent_paths(self, file_path):
        """Update the recent save paths list."""
        if file_path not in self.recent_paths:
            self.recent_paths.insert(0, file_path)
            if len(self.recent_paths) > 5:
                self.recent_paths.pop()
        self.update_recent_paths_list()

    def update_recent_paths_list(self):
        """Display the updated list of recent save paths."""
        self.recent_paths_list.clear()
        for path in self.recent_paths:
            self.recent_paths_list.addItem(QListWidgetItem(path))


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(SaveToMATFile).run()