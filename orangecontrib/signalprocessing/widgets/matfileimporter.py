import scipy.io
import os
import numpy as np
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from AnyQt.QtWidgets import QFileDialog, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QLineEdit, \
    QPushButton
from AnyQt.QtCore import Qt


class MATFileImporter(OWWidget):
    # Set the widget configuration
    name = "MAT File Importer"
    description = "Import .mat files and display their information"
    icon = "icons/matfileimporter.svg"
    priority = 0
    keywords = ["widget", "import", "mat"]
    want_main_area = False
    want_control_area = True

    # Settings parameter
    recent_files = Setting([])

    class Outputs:
        data = Output("Data", Table)

    def __init__(self):
        super().__init__()

        self.data = None
        self.file_path = None
        self.column_names = []

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "MAT File Importer")

        # File browser
        self.file_browser_button = gui.button(self.controlArea, self, "Browse Files", callback=self.browse_files)

        # Recent files list
        self.recent_files_list = QListWidget()
        self.recent_files_list.itemClicked.connect(self.load_recent_file)
        self.controlArea.layout().addWidget(QLabel("Recent Files:"))
        self.controlArea.layout().addWidget(self.recent_files_list)
        self.update_recent_files_list()

        # Info section
        self.info_label = QLabel("Info: No file loaded")
        self.controlArea.layout().addWidget(self.info_label)

        # Column names section
        self.column_names_area = QVBoxLayout()
        self.controlArea.layout().addLayout(self.column_names_area)

        self.update_button = QPushButton("Load Data")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_column_names)
        self.controlArea.layout().addWidget(self.update_button)

    def browse_files(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open .mat File", "", "MAT files (*.mat)")
        if file_path:
            self.file_path = file_path
            self.load_file(file_path)

    def load_recent_file(self, item):
        file_path = item.text()
        if os.path.exists(file_path):
            self.file_path = file_path
            self.load_file(file_path)
        else:
            self.recent_files.remove(file_path)
            self.update_recent_files_list()

    def load_file(self, file_path):
        try:
            mat_data = scipy.io.loadmat(file_path)
            variable_name = [key for key in mat_data.keys() if not key.startswith('__')][0]
            data = mat_data[variable_name]
            if isinstance(data, np.ndarray) and data.ndim == 2:
                self.data = data
                self.column_names = [f"Var{i}" for i in range(data.shape[1])]
                self.display_column_name_inputs()
                self.info_label.setText(
                    f"Info: Loaded {data.shape[0]} rows and {data.shape[1]} columns from {os.path.basename(file_path)}")
                self.update_recent_files(file_path)

                # Enable the load button
                self.update_button.setEnabled(True)
                self.update_button.setText("Load Data")

            else:
                self.info_label.setText(f"Info: The file does not contain a valid 2D array.")
        except Exception as e:
            self.info_label.setText(f"Info: Error loading file: {e}")

    def update_recent_files(self, file_path):
        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
            if len(self.recent_files) > 5:
                self.recent_files.pop()
        self.update_recent_files_list()

    def update_recent_files_list(self):
        self.recent_files_list.clear()
        for file_path in self.recent_files:
            self.recent_files_list.addItem(QListWidgetItem(file_path))

    def display_column_name_inputs(self):
        # Clear previous column name inputs
        while self.column_names_area.count():
            child = self.column_names_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, name in enumerate(self.column_names):
            label = QLabel(f"Column {i + 1}:")
            line_edit = QLineEdit(name)
            line_edit.setObjectName(f"col_{i}")
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(line_edit)
            self.column_names_area.addLayout(hbox)

    def update_column_names(self):
        new_column_names = []
        for i in range(self.column_names_area.count()):
            hbox = self.column_names_area.itemAt(i).layout()
            line_edit = hbox.itemAt(1).widget()
            new_column_names.append(line_edit.text())
        self.column_names = new_column_names
        self.update_output_data()

        # Once the data is loaded
        self.update_button.setText("Reload")

    def update_output_data(self):
        if self.data is not None:
            domain = Domain([ContinuousVariable(name) for name in self.column_names])
            table = Table(domain, self.data)
            self.Outputs.data.send(table)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(MATFileImporter).run()