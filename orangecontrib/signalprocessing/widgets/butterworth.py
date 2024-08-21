import numpy as np
from scipy.signal import butter, filtfilt
from Orange.data import Table, Domain
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from AnyQt.QtCore import Qt
from AnyQt.QtGui import QDoubleValidator, QIntValidator
from AnyQt.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit


class Butterworth(OWWidget):
    name = "Butterworth Filter"
    description = "Apply low-pass, high-pass, or band-pass Butterworth filter to a time series signal"
    icon = "icons/butterworth.svg"
    priority = 7
    keywords = ["filter", "butterworth", "signal processing"]

    class Inputs:
        time_series = Input("Time Series Data", Table)

    class Outputs:
        filtered_data = Output("Filtered Data", Table, default=True)

    # Settings parameters
    filter_type = Setting("Low-pass")
    cutoff = Setting(1.0)
    low_cutoff = Setting(1.0)
    high_cutoff = Setting(10.0)
    order = Setting(4)
    sampling_rate = Setting(1.0)

    # Warnings
    class Warning(OWWidget.Warning):
        warning_invalid_params = Msg("Invalid filter parameters.")
        warning_data_length = Msg("Insufficient data length for the given filter order.")
        warning_filter_order = Msg("Invalid filter order. Must be > 0 and < 1")
        warning_high_pass = Msg("High pass cut-off frequency must be > 0 Hz")
        warning_low_pass = Msg("Low pass cut-off must be less that Nyquist rate")
        warning_sampling_rate = Msg("Sampling rate must be atleast 2Hz")


    def __init__(self):
        super().__init__()
        self.time_series = None

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Filter Settings")
        self.controlArea.setFixedWidth(300)

        # Filter type selection
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["Low-pass", "High-pass", "Band-pass"])
        self.filter_type_combo.currentTextChanged.connect(self.update_filter_inputs)
        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(QLabel("Filter Type:"))
        filter_type_layout.addWidget(self.filter_type_combo)
        self.controlArea.layout().addLayout(filter_type_layout)

        # Generic cutoff frequency
        self.cutoff_layout, self.cutoff_input = self.create_left_aligned_input(
            "cutoff", "Cut-off Frequency (Hz):", QDoubleValidator(1.0, 50000.0, 2, self)
        )

        # Low cutoff frequency input (capped at minimum 1 Hz)
        self.low_cutoff_layout, self.low_cutoff_input = self.create_left_aligned_input(
            "low_cutoff", "Low Cutoff Frequency (Hz):", QDoubleValidator(1.0, 20000.0, 2, self)
        )

        # High cutoff frequency input (will be updated dynamically based on the Nyquist rate)
        self.high_cutoff_layout, self.high_cutoff_input = self.create_left_aligned_input(
            "high_cutoff", "High Cutoff Frequency (Hz):", QDoubleValidator(1.0, 50000.0, 2, self)
        )

        # Filter order input (capped at a maximum of 5)
        self.order_layout, self.order_input = self.create_left_aligned_input(
            "order", "Filter Order:", QIntValidator(1, 5, self)
        )

        # Sampling rate input (minimum 2 Hz)
        self.sampling_rate_layout, self.sampling_rate_input = self.create_left_aligned_input(
            "sampling_rate", "Sampling Rate (Hz):", QDoubleValidator(2.0, 10000.0, 2, self)
        )

        # Apply filter button - placed in a fixed position
        apply_button_layout = QVBoxLayout()
        apply_button_layout.setAlignment(Qt.AlignBottom)
        self.apply_button = gui.button(None, self, "Apply Filter", callback=self.apply_filter)
        apply_button_layout.addWidget(self.apply_button)
        self.controlArea.layout().addLayout(apply_button_layout)

        # Right half: Placeholder for plot or additional info (if needed in the future)
        self.right_half = QVBoxLayout()
        self.mainArea.layout().addLayout(self.right_half)

        # Initial update of filter inputs
        self.update_filter_inputs()

    def create_left_aligned_input(self, attribute_name, label_text, validator):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        label = QLabel(label_text)
        line_edit = gui.lineEdit(None, self, attribute_name, valueType=float, validator=validator)
        line_edit.setAlignment(Qt.AlignLeft)
        line_edit.setFixedWidth(100)

        layout.addWidget(label)
        layout.addWidget(line_edit)
        self.controlArea.layout().addLayout(layout)

        return layout, line_edit

    def update_filter_inputs(self):
        filter_type = self.filter_type_combo.currentText()
        nyquist = 0.5 * float(self.sampling_rate_input.text())

        # Update the validator for the high cutoff input based on the Nyquist rate
        self.high_cutoff_input.setValidator(QDoubleValidator(1.0, nyquist - 0.1, 2, self))

        if filter_type == "Low-pass" or filter_type == "High-pass":
            self.low_cutoff_layout.itemAt(0).widget().hide()
            self.low_cutoff_layout.itemAt(1).widget().hide()
            self.high_cutoff_layout.itemAt(0).widget().hide()
            self.high_cutoff_layout.itemAt(1).widget().hide()
            self.cutoff_layout.itemAt(0).widget().show()
            self.cutoff_layout.itemAt(1).widget().show()
        elif filter_type == "Band-pass":
            self.cutoff_layout.itemAt(0).widget().hide()
            self.cutoff_layout.itemAt(1).widget().hide()
            self.low_cutoff_layout.itemAt(0).widget().show()
            self.low_cutoff_layout.itemAt(1).widget().show()
            self.high_cutoff_layout.itemAt(0).widget().show()
            self.high_cutoff_layout.itemAt(1).widget().show()

    def apply_filter(self):
        if self.time_series:
            error_check_fail = False
            try:
                # Clear previous warnings
                self.Warning.clear()

                data_col = self.time_series.X[:, 0]  # Assuming single column time series data
                filter_type = self.filter_type_combo.currentText()
                sampling_rate = self.sampling_rate
                nyquist = 0.5 * sampling_rate
                order = self.order

                print(order)

                if filter_type == "Low-pass":
                    cutoff = self.cutoff
                    if cutoff >= nyquist:
                        self.Warning.warning_low_pass()
                        error_check_fail = True
                elif filter_type == "High-pass":
                    cutoff = self.cutoff
                    if cutoff < 1:
                        self.Warning.warning_high_pass()
                        error_check_fail = True
                else:
                    low_cutoff = self.low_cutoff
                    high_cutoff = self.high_cutoff
                    if low_cutoff >= nyquist and high_cutoff < 1:
                        self.Warning.warning_invalid_params()
                        error_check_fail = True

                # Check data length for the given filter order
                if len(data_col) <= order * 3:
                    self.Warning.warning_data_length()
                    error_check_fail = True
                if sampling_rate < 2:
                    self.Warning.warning_sampling_rate()
                    error_check_fail = True

                if error_check_fail:
                    return

                if filter_type == "Low-pass":
                    normal_cutoff = cutoff / nyquist
                    b, a = butter(order, normal_cutoff, btype="low", analog=False)
                elif filter_type == "High-pass":
                    normal_cutoff = cutoff / nyquist
                    b, a = butter(order, normal_cutoff, btype="high", analog=False)
                elif filter_type == "Band-pass":
                    low = low_cutoff / nyquist
                    high = high_cutoff / nyquist
                    b, a = butter(order, [low, high], btype="band", analog=False)

                filtered_signal = filtfilt(b, a, data_col)
                new_data = Table.from_numpy(Domain(self.time_series.domain.attributes), filtered_signal[:, np.newaxis])

                self.Outputs.filtered_data.send(new_data)
            except ValueError:
                self.Warning.warning_invalid_params()

    @Inputs.time_series
    def set_data(self, data):
        self.time_series = data

    def send_report(self):
        self.report_caption(f"Butterworth Filter: {self.filter_type_combo.currentText()} with Order: {self.order_input.text()}")

if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Butterworth).run()