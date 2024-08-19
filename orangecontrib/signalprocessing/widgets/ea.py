import numpy as np
from scipy.signal import hilbert, butter, sosfilt
from scipy.fft import ifft, fft
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets.utils.signals import Input as SignalInput, Output as SignalOutput
from AnyQt.QtGui import QDoubleValidator
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QVBoxLayout, QComboBox, QLineEdit, QPushButton
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import RectangleSelector


class EnvelopAnalysis(OWWidget):
    name = "Envelope Analysis"
    description = "Perform envelope analysis on the FFT output of a time series signal"
    icon = "icons/ea.svg"
    priority = 3
    keywords = ["widget", "envelope", "analysis"]
    want_main_area = True
    want_control_area = True

    # Settings parameters
    sampling_rate = Setting(1.0)

    class Inputs:
        time_series = SignalInput("Time Series Data", Table)

    class Outputs:
        envelope_data = SignalOutput("Envelope Data", Table, default=True)

    class Warning(OWWidget.Warning):
        warning = Msg("Envelope analysis computation failed.")
        no_sampling_rate = Msg("No sampling rate provided.")

    def __init__(self):
        super().__init__()
        self.time_series = None
        self.freqs = None
        self.selected_range = None

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")

        # Sampling rate input
        self.sampling_rate_input = gui.lineEdit(
            self.controlArea, self, "sampling_rate",
            label="Sampling Rate (Hz):", valueType=float, validator=QDoubleValidator(0.1, 1e6, 2)
        )
        self.sampling_rate_input.setAlignment(Qt.AlignCenter)
        self.sampling_rate_input.setToolTip("Set the sampling rate in Hz.")

        # Update plot button
        self.update_plot_button = gui.button(self.controlArea, self, "Update Plot", callback=self.update_plot)
        # Compute envelope button
        self.compute_envelope_button = gui.button(self.controlArea, self, "Compute Envelope",
                                                  callback=self.compute_envelope)

        # Plot area
        self.figure, self.ax = plt.subplots(facecolor="none")
        self.figure.patch.set_facecolor('none')
        self.ax.set_facecolor('none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.mainArea.layout().addWidget(self.toolbar)
        self.mainArea.layout().addWidget(self.canvas)

        # Rectangle selector for selecting window on plot
        self.rectangle_selector = RectangleSelector(self.ax, self.onselect, useblit=True,
                                                    button=[1], minspanx=5, minspany=5, spancoords='pixels',
                                                    interactive=True)

    @Inputs.time_series
    def set_data(self, data):
        self.time_series = data
        self.update_plot()

    def update_plot(self):
        if self.time_series and self.sampling_rate:
            try:
                data_col = self.time_series.X[:, 0]  # Assuming single column time series data
                n = len(data_col)
                dt = 1.0 / self.sampling_rate
                self.freqs = np.fft.fftfreq(n, d=dt)

                # Compute FFT
                fft_data = fft(data_col)

                # Plot FFT data
                self.ax.clear()
                self.ax.plot(self.freqs[:n // 2], np.abs(fft_data[:n // 2]), label="FFT Data")
                self.ax.set_title("FFT Data")
                self.ax.set_xlabel("Frequency (Hz)")
                self.ax.set_ylabel("Amplitude")
                self.ax.legend()
                self.canvas.draw()
            except Exception as e:
                print(e)
                self.Warning.warning()

    def onselect(self, eclick, erelease):
        x1, x2 = sorted([eclick.xdata, erelease.xdata])
        self.selected_range = (x1, x2)
        print(f"Selected range: {self.selected_range}")

    def compute_envelope(self):
        if self.time_series and self.selected_range:
            if self.sampling_rate is None:
                self.Warning.no_sampling_rate()
                return

            try:
                data_col = self.time_series.X[:, 0]  # Assuming single column time series data
                n = len(data_col)
                dt = 1.0 / self.sampling_rate
                dfq = 1.0 / (dt * n)
                lowcut, highcut = self.selected_range

                # Compute FFT
                fft_data = fft(data_col)

                # Compute indices for low and high cut
                idxLow = int(lowcut / dfq)
                idxHi = int(highcut / dfq)

                # Zero out frequencies outside the selected range
                D = np.zeros_like(fft_data)
                D[idxLow:idxHi + 1] = fft_data[idxLow:idxHi + 1]
                D[-idxHi:-idxLow + 1] = fft_data[-idxHi:-idxLow + 1]

                # Compute iFFT
                filtered_signal = np.abs(ifft(D))

                # Compute envelope
                envelope = np.abs(hilbert(filtered_signal))

                # Compute FFT of the envelope
                envelope_fft = fft(envelope)

                # Plot the new FFT data
                self.ax.clear()
                self.ax.plot(self.freqs[:n // 2], np.abs(envelope_fft[:n // 2]), label="Envelope FFT")
                self.ax.set_title("Envelope Analysis")
                self.ax.set_xlabel("Frequency (Hz)")
                self.ax.set_ylabel("Amplitude")
                self.ax.legend()
                self.canvas.draw()

                # Output envelope FFT data
                domain = Domain([ContinuousVariable("Envelope FFT")])
                new_data = Table(domain, np.abs(envelope_fft[:n // 2]).reshape(-1, 1))
                self.Outputs.envelope_data.send(new_data)
            except Exception as e:
                print(e)
                self.Warning.warning()

    def send_report(self):
        self.report_caption("Envelope Analysis")

if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(EnvelopAnalysis).run()