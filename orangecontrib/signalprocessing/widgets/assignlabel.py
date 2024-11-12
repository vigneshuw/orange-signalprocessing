import numpy as np
from Orange.data import Table, Domain, DiscreteVariable
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output
from AnyQt.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem

class AddLabelWidget(OWWidget):
    name = "Add Label to Data"
    description = "Add a label to all rows of the data table and set it as the target variable."
    icon = "icons/addlabel.svg"
    priority = 7

    class Inputs:
        data = Input("Data", Table)

    class Outputs:
        output_data = Output("Labeled Data", Table)

    # Widget settings
    label_value = Setting("")  # Default value for label input

    def __init__(self):
        super().__init__()
        self.data = None
        self.new_data = None

        # Layout setup
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")

        # Input field for label name
        label_input_layout = QHBoxLayout()
        label_input_layout.addWidget(QLabel("Enter Label Value:"))
        self.label_input = QLineEdit(self)
        self.label_input.setText(self.label_value)
        label_input_layout.addWidget(self.label_input)
        self.controlArea.layout().addLayout(label_input_layout)

        # Submit button
        self.submit_button = QPushButton("Assign")
        self.submit_button.clicked.connect(self.add_label_to_data)
        self.controlArea.layout().addWidget(self.submit_button)

        # Table widget on the right side
        self.table_widget = QTableWidget()
        self.mainArea.layout().addWidget(self.table_widget)

    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.update_table_view()

    def add_label_to_data(self):
        if self.data is not None and self.label_input.text().strip():
            # Read label from input and save setting
            label = self.label_input.text().strip()
            self.label_value = label  # Save input as a setting

            # Define a new DiscreteVariable for the label
            label_var = DiscreteVariable("Label", values=[label])

            # Create a new domain with the label as a class variable
            domain = Domain(self.data.domain.attributes, class_vars=[label_var])

            # Create a column with the label repeated for each row, as class values
            label_column = np.array([label_var.values.index(label)] * len(self.data)).reshape(-1, 1)

            # Create the new Table, passing `label_column` as Y for class values
            self.new_data = Table(domain, self.data.X, Y=label_column, metas=self.data.metas)

            # Send labeled data to output
            self.Outputs.output_data.send(self.new_data)

            # Update the table view
            self.update_table_view()

            # Clear the input field
            self.label_input.clear()

    def update_table_view(self):
        if self.new_data is not None:
            # Set table dimensions
            self.table_widget.setRowCount(len(self.new_data))
            self.table_widget.setColumnCount(len(self.new_data.domain.attributes) + 1)  # Attributes + Label column

            # Set table headers
            headers = [var.name for var in self.new_data.domain.attributes] + ["Label"]
            self.table_widget.setHorizontalHeaderLabels(headers)

            # Populate table with data
            for row_idx, row in enumerate(self.new_data):
                # Iterate over each attribute in the domain
                for col_idx, attribute in enumerate(self.new_data.domain.attributes):
                    value = row[attribute]
                    item = QTableWidgetItem(str(value))
                    self.table_widget.setItem(row_idx, col_idx, item)

                # Set the label in the last column
                label_item = QTableWidgetItem(str(self.label_value))
                self.table_widget.setItem(row_idx, len(self.new_data.domain.attributes), label_item)

if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(AddLabelWidget).run()