from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import gui
from Orange.widgets.widget import OWWidget, Input, Output
from AnyQt.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QScrollArea, QWidget


class UpdateColumns(OWWidget):
    # Set the widget configuration
    name = "Update Column Names"
    description = "Update the names of columns in a data table"
    icon = "icons/updatecolumnnames.svg"
    priority = 1
    keywords = ["update", "columns", "rename"]
    want_main_area = True
    want_control_area = False

    class Inputs:
        data = Input("Data", Table)

    class Outputs:
        updated_data = Output("Updated Data", Table, default=True)

    def __init__(self):
        super().__init__()
        self.data = None
        self.new_names = []

        # Main layout setup
        self.scroll_area = QScrollArea(self)
        self.scroll_widget = QWidget()
        self.main_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_widget.setLayout(self.main_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.mainArea.layout().addWidget(self.scroll_area)

        # Apply button
        self.apply_button = gui.button(self.mainArea, self, "Apply Changes", callback=self.apply_changes)
        self.apply_button.setDisabled(True)

    @Inputs.data
    def set_data(self, data):
        self.data = data
        if self.data is not None:
            self.display_column_inputs()
            self.apply_button.setDisabled(False)
        else:
            self.clear_display()
            self.apply_button.setDisabled(True)

    def display_column_inputs(self):
        # Clear previous inputs
        self.clear_display()

        self.new_names = []
        for idx, attribute in enumerate(self.data.domain.attributes):
            hbox = QHBoxLayout()
            label = QLabel(f"{idx + 1}. ({attribute.name}):")
            line_edit = QLineEdit(attribute.name)
            hbox.addWidget(label)
            hbox.addWidget(line_edit)
            self.main_layout.addLayout(hbox)
            self.new_names.append(line_edit)

    def apply_changes(self):
        # Get the updated column names
        updated_names = [line_edit.text() for line_edit in self.new_names]

        # Create a new domain with the updated names
        new_attributes = [ContinuousVariable(name) for name in updated_names]
        new_domain = Domain(new_attributes, self.data.domain.class_vars, self.data.domain.metas)

        # Create a new data table with the updated domain
        updated_data = Table(new_domain, self.data.X, self.data.Y, self.data.metas)

        # Send the updated data to the output
        self.Outputs.updated_data.send(updated_data)

    def clear_display(self):
        # Clear all the widgets in the main layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # If the item is a layout, remove it
                layout = item.layout()
                if layout is not None:
                    for j in reversed(range(layout.count())):
                        layout_item = layout.itemAt(j)
                        layout_widget = layout_item.widget()
                        if layout_widget is not None:
                            layout_widget.setParent(None)

    def send_report(self):
        self.report_caption("Updated Columns in Data Table")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(UpdateColumns).run()