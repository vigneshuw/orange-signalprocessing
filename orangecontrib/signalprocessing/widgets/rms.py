from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets.utils.itemmodels import TableModel
from Orange.widgets.utils.signals import Input as SignalInput, Output as SignalOutput
from AnyQt.QtGui import QIntValidator, QDoubleValidator
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel
import numpy as np


class RMS(OWWidget):
    # Set widget configuration
    name = "Root Mean Square"
    description = "Compute Root Mean Square (RMS) across each column"
    icon = "icons/rms.svg"
    priority = 100
    keywords = ["widget", "data"]
    want_main_menu = True

    # Settings parameter
    segment_size = Setting(1)   # RMS Segment size in seconds
    sampling_rate = Setting(1.0)    # Samping rate in Hz
    overlap_rate = Setting(0)   # Overlap rate in percentage

    class Inputs:
        data = SignalInput("Data", Table)

    class Outputs:
        data = SignalOutput("Data", Table, default=True)

    class Warning(OWWidget.Warning):
        warning = Msg("Signal Processing Warning")
        window_size_large = Msg("Window size is larger than the data length. Adjusting to data length.")

    def __init__(self):
        super().__init__()
        self.data = None

        # Control Area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")
        # Segment Size Input
        self.segment_size_input = gui.lineEdit(
            self.controlArea, self, "segment_size",
            label="Segment Size (s):", valueType=int, validator=QIntValidator(1, 10000, self))
        self.segment_size_input.setText(str(self.segment_size))
        self.segment_size_input.setAlignment(Qt.AlignCenter)
        self.segment_size_input.setToolTip("Set the window size in seconds.")
        # Sampling Rate Input
        self.sampling_rate_input = gui.lineEdit(
            self.controlArea, self, "sampling_rate",
            label="Sampling Rate (Hz):", valueType=float, validator=QDoubleValidator(0.1, 10000.0, 2, self))
        self.sampling_rate_input.setText(str(self.sampling_rate))
        self.sampling_rate_input.setAlignment(Qt.AlignCenter)
        self.sampling_rate_input.setToolTip("Set the sampling rate in Hz.")
        # Overlap Rate Input
        self.overlap_rate_input = gui.lineEdit(
            self.controlArea, self, "overlap_rate",
            label="Overlap Rate (%)", valueType=int, validator=QIntValidator(0, 99, self)
        )
        self.overlap_rate_input.setAlignment(Qt.AlignCenter)
        self.overlap_rate_input.setText(str(self.overlap_rate))
        self.overlap_rate_input.setToolTip("Set the overlap rate that controls the stride.")

        # Compute Button
        self.compute_button = gui.button(self.controlArea, self, "Compute", callback=self.commit)

        # Main area to display the data table with header
        self.header_label = QLabel("Input Data")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.mainArea.layout().addWidget(self.header_label)

        self.data_table = gui.TableView(self.mainArea)
        self.mainArea.layout().addWidget(self.data_table)

    @Inputs.data
    def set_data(self, data):
        if data:
            self.data = data
            self.update_table_view()
        else:
            self.data = None
            self.data_table.setModel(None)

    def update_table_view(self):
        if self.data:
            self.data_table.setModel(TableModel(self.data[:10]))

    def compute_rms(self, data, window_size, step_size):
        rms_values = []
        for column in data.X.T:
            if window_size > len(column):
                self.Warning.window_size_large()
                window_size = len(column)
            rms_column = [
                np.sqrt(np.mean(column[i:i + window_size] ** 2))
                for i in range(0, len(column) - window_size + 1, step_size)
            ]
            rms_values.append(rms_column)
        rms_values = np.array(rms_values).T
        return rms_values

    def commit(self):
        if self.data:
            try:
                segment_size = int(self.segment_size_input.text())
                sampling_rate = float(self.sampling_rate_input.text())
                overlap_rate = int(self.overlap_rate_input.text())
                window_size = int(segment_size * sampling_rate)
                step_size = int(window_size * (1 - overlap_rate / 100))
                if step_size < 1:
                    step_size = 1
                # Compute RMS
                rms_data = self.compute_rms(self.data, window_size, step_size)

                domain = Domain([ContinuousVariable(f"RMS_{var.name}") for var in self.data.domain.attributes])
                new_data = Table(domain, rms_data)

                self.Outputs.data.send(new_data)
            except ValueError:
                self.Warning.warning("Invalid segment size or sampling rate.")
        else:
            self.Outputs.data.send(None)

    def send_report(self):
        # self.report_plot() includes visualizations in the report
        self.report_caption(f"RMS Segment Size: {self.segment_size_input.text()} seconds")
        self.report_caption(f"Sampling Rate: {self.sampling_rate_input.text()} Hz")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview  # since Orange 3.20.0
    WidgetPreview(RMS).run()
