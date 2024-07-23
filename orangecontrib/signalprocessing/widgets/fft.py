from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets.utils.itemmodels import TableModel
from Orange.widgets.utils.signals import Input as SignalInput, Output as SignalOutput
from AnyQt.QtGui import QIntValidator, QDoubleValidator
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QSizePolicy, QComboBox, QVBoxLayout, QHBoxLayout
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class FFT(OWWidget):
    # Set the widget configuration
    name = "Fast Fourier Transform"
    description = "Compute Fast Fourier Transform (FFT) across each column"
    icon = "icons/fft.svg"
    priority = 2
    keywords = ["widget", "fft"]
    want_main_area = True
    want_control_area = True

    # Settings parameter
    start_segment_size = Setting(1)  # Start of FFT segment size in seconds
    end_segment_size = Setting(1)  # End of FFT segment size in seconds
    sampling_rate = Setting(1.0)    # Sampling rate in Hz
    auto_send = Setting(False)  # Automatically send output when settings change

    class Inputs:
        data = SignalInput("Data", Table)

    class Outputs:
        fft_data = SignalOutput("Data", Table, default=True)
        sampling_rate_out = SignalOutput("Sampling Rate", float, auto_summary=False)

    class Warning(OWWidget.Warning):
        warning = Msg("Signal Processing Warning")
        window_size_large = Msg("Window size is larger than the data length. Adjusting to data length.")
        invalid_range = Msg("Invalid range for segment size.")

    def __init__(self):
        super().__init__()
        self.data = None
        self.fft_data = None

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")
        # Validators with initial high upper limit
        self.start_segment_size_validator = QIntValidator(1, 10000, self)
        self.end_segment_size_validator = QIntValidator(1, 10000, self)

        # Start Segment Size Input
        self.start_segment_size_input = gui.lineEdit(
            self.controlArea, self, "start_segment_size",
            label="Start Segment Size (s):", valueType=int, validator=self.start_segment_size_validator,
            callback=self.settings_changed
        )
        self.start_segment_size_input.setText(str(self.start_segment_size))
        self.start_segment_size_input.setAlignment(Qt.AlignCenter)
        self.start_segment_size_input.setToolTip("Set the start window size in seconds.")

        # End Segment Size Input
        self.end_segment_size_input = gui.lineEdit(
            self.controlArea, self, "end_segment_size",
            label="End Segment Size (s):", valueType=int, validator=self.end_segment_size_validator,
            callback=self.settings_changed
        )
        self.end_segment_size_input.setText(str(self.end_segment_size))
        self.end_segment_size_input.setAlignment(Qt.AlignCenter)
        self.end_segment_size_input.setToolTip("Set the end window size in seconds.")

        # Sampling Rate Input
        self.sampling_rate_input = gui.lineEdit(
            self.controlArea, self, "sampling_rate",
            label="Sampling Rate (Hz):", valueType=float, validator=QDoubleValidator(0.1, 10e9, 2, self),
            callback=self.settings_changed
        )
        self.sampling_rate_input.setText(str(self.sampling_rate))
        self.sampling_rate_input.setAlignment(Qt.AlignCenter)
        self.sampling_rate_input.setToolTip("Set the sampling rate in Hz. Max 1GHz.")

        # Horizontal layout for checkbox and apply button
        auto_send_layout = QHBoxLayout()
        self.auto_send_checkbox = gui.checkBox(
            None, self, "auto_send", label="", callback=self.settings_changed
        )
        self.apply_button = gui.button(None, self, "Apply", callback=self.commit)
        auto_send_layout.addWidget(self.auto_send_checkbox)
        auto_send_layout.addWidget(self.apply_button)
        auto_send_layout.addStretch()
        self.controlArea.layout().addLayout(auto_send_layout)

        # Main area layout
        main_area_layout = self.mainArea.layout()
        # Dropdown for column selection
        self.column_selector_layout = QHBoxLayout()
        self.column_selector = QComboBox()
        self.column_selector.currentIndexChanged.connect(self.update_plot)
        self.column_selector_layout.addWidget(QLabel("Select Column: "))
        self.column_selector_layout.addWidget(self.column_selector)
        self.column_selector_layout.addStretch()
        main_area_layout.addLayout(self.column_selector_layout)
        # Plot area
        self.figure, self.ax = plt.subplots(facecolor="none")
        self.figure.patch.set_facecolor('none')
        self.ax.set_facecolor('none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_area_layout.addWidget(self.canvas)

    @Inputs.data
    def set_data(self, data):
        if data:
            self.data = data
            max_segment_size = int(len(data) / float(self.sampling_rate_input.text()))
            self.start_segment_size_validator.setTop(max_segment_size)
            self.end_segment_size_validator.setTop(max_segment_size)
            self.populate_column_selector()
            if self.auto_send:
                self.commit()
        else:
            self.data = None
            self.column_selector.clear()
            self.ax.clear()
            self.canvas.draw()

    def populate_column_selector(self):
        self.column_selector.clear()
        self.column_selector.addItem("All")
        if self.data:
            for var in self.data.domain.attributes:
                self.column_selector.addItem(var.name)

    def compute_fft(self, data, start_idx, end_idx):
        fft_values = []
        for column in data.X.T:
            segment = column[start_idx:end_idx]
            fft_column = np.fft.fft(segment)
            fft_values.append(np.abs(fft_column[:len(fft_column) // 2]))
        fft_values = np.array(fft_values).T
        return fft_values

    def update_plot(self):
        if self.fft_data is not None:
            self.ax.clear()
            freqs = np.fft.fftfreq(len(self.fft_data) * 2,
                                   d=1/float(self.sampling_rate_input.text()))[:len(self.fft_data)]
            selected_column = self.column_selector.currentText()
            if selected_column == "All":
                for i, fft_col in enumerate(self.fft_data.T):
                    self.ax.plot(freqs, fft_col, label=f"{i + 1}")
            else:
                col_idx = self.column_selector.currentIndex() - 1  # Adjust for "All Columns" option
                if col_idx >= 0:
                    self.ax.plot(freqs, self.fft_data[:, col_idx], label=f"{selected_column}")
            self.ax.set_xlabel("Frequency (Hz)")
            self.ax.set_ylabel("Amplitude")
            self.ax.set_title("FFT Spectrum")
            legend = self.ax.legend()
            legend.get_frame().set_facecolor('none')
            legend.get_frame().set_edgecolor('none')
            self.canvas.draw()

    def settings_changed(self):
        if self.auto_send:
            self.commit()

    def commit(self):
        if self.data:
            try:
                start_segment_size = int(self.start_segment_size_input.text())
                end_segment_size = int(self.end_segment_size_input.text())
                sampling_rate = float(self.sampling_rate_input.text())
                if start_segment_size >= end_segment_size:
                    self.Warning.invalid_range()
                    return

                # Get the data index
                start_idx = int(start_segment_size * sampling_rate)
                end_idx = int(end_segment_size * sampling_rate)
                if end_idx > len(self.data):
                    end_idx = len(self.data)
                    self.Warning.window_size_large()

                # Compute FFT
                self.fft_data = self.compute_fft(self.data, start_idx, end_idx)

                domain = Domain([ContinuousVariable(f"FFT_{var.name}") for var in self.data.domain.attributes])
                new_data = Table(domain, self.fft_data)

                self.Outputs.fft_data.send(new_data)
                self.Outputs.sampling_rate_out.send(sampling_rate)
                self.update_plot()
            except ValueError:
                self.Warning.warning("Invalid segment size or sampling rate.")
        else:
            self.Outputs.fft_data.send(None)
            self.Outputs.sampling_rate_out.send(None)

    def send_report(self):
        self.report_caption(f"FFT Start Segment Size: {self.start_segment_size_input.text()} seconds")
        self.report_caption(f"FFT End Segment Size: {self.end_segment_size_input.text()} seconds")
        self.report_caption(f"Sampling Rate: {self.sampling_rate_input.text()} Hz")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview  # since Orange 3.20.0
    WidgetPreview(FFT).run()
