import numpy as np
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import gaussian
from Orange.data import Table
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Msg
from Orange.widgets.utils.signals import Input as SignalInput
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QSizePolicy, QHBoxLayout, QComboBox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar


class STFTPlotter(OWWidget):
    # Set the widget configuration
    name = "STFT Plotter"
    description = "Compute and plot STFT for each column of the input data"
    icon = "icons/stftplotter.svg"
    priority = 3
    keywords = ["widget", "stft", "plot"]
    want_main_area = True
    want_control_area = True

    # Settings parameters
    hop_size = Setting(1.0)     # In seconds
    fs = Setting(1)   # In Hz
    window_size = Setting(1.0)  # In seconds

    class Inputs:
        data = SignalInput("Data", Table)

    class Warning(OWWidget.Warning):
        warning = Msg("STFT computation failed.")
        warning_incorrect_params = Msg("Incorrect settings parameters.")
        warning_low_fs = Msg("Sampling rate is low.")
        warning_window_fs = Msg("Incorrect window size and sampling rate combination")

    def __init__(self):
        super().__init__()
        self.data = None
        self.colorbar = None

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")

        # Settings for hop size, fs, and window size
        self.hop_size_input = gui.lineEdit(
            self.controlArea, self, "hop_size", label="Hop Size:", valueType=float)
        self.hop_size_input.setAlignment(Qt.AlignCenter)
        self.hop_size_input.setToolTip("Hop for the window in seconds.")
        self.fs_input = gui.lineEdit(
            self.controlArea, self, "fs", label="Sampling Frequency (Hz):", valueType=int)
        self.fs_input.setAlignment(Qt.AlignCenter)
        self.fs_input.setToolTip("Sampling rate in Samples/s or Hertz.")
        self.window_size_input = gui.lineEdit(
            self.controlArea, self, "window_size", label="Window Size:", valueType=float)
        self.window_size_input.setAlignment(Qt.AlignCenter)
        self.window_size_input.setToolTip("Window size in seconds.")

        # Dropdown for selecting column
        self.column_selector_layout = QHBoxLayout()
        self.column_selector = QComboBox()
        self.column_selector.currentIndexChanged.connect(self.update_plot)
        self.column_selector_layout.addWidget(QLabel("Select Column:"))
        self.column_selector_layout.addWidget(self.column_selector)
        self.controlArea.layout().addLayout(self.column_selector_layout)

        # Update button
        self.update_button = gui.button(self.controlArea, self, "Update Plot", callback=self.update_plot)

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

    @Inputs.data
    def set_data(self, data):
        if data:
            self.data = data
            self.populate_column_selector()
            self.update_plot()
        else:
            self.data = None
            self.ax.clear()
            self.canvas.draw()

    def populate_column_selector(self):
        self.column_selector.clear()
        if self.data:
            for var in self.data.domain.attributes:
                self.column_selector.addItem(var.name)

    def compute_stft(self, data, window_size_samples, hop_samples):

        w = gaussian(window_size_samples, std=int(window_size_samples/3))
        SFT = ShortTimeFFT(w, hop=hop_samples, fs=self.fs, scale_to="magnitude")

        # Compute STFT
        Sx = SFT.stft(data)
        t_lo, t_hi = SFT.extent(len(data))[:2]

        return Sx, t_lo, t_hi, SFT, int(window_size_samples/3)

    def update_plot(self):
        if self.data:
            selected_column = self.column_selector.currentText()
            col_idx = self.column_selector.currentIndex()
            if col_idx >= 0:

                # Check for errors before proceeding
                window_size_samples = int(self.window_size * self.fs)
                hop_samples = int(self.hop_size * self.fs)

                # Error checking
                self.Warning.clear()
                if hop_samples <= 1 or window_size_samples <= 1:
                    self.Warning.warning_incorrect_params()
                elif window_size_samples <= 1 and self.fs <= 1:
                    self.Warning.warning_window_fs()
                elif self.fs <= 1:
                    self.Warning.warning_low_fs()
                else:
                    try:
                        data_col = self.data[:, col_idx].X.flatten()
                        Sx, t_lo, t_hi, SFT, g_std = self.compute_stft(data_col, window_size_samples, hop_samples)

                        # Plot
                        self.ax.clear()
                        self.ax.set_title(rf"STFT for {selected_column}; ({SFT.m_num * SFT.T:g}$\,s$ Gaussian window, " +
                                      rf"$\sigma_t={round(g_std * SFT.T, 2)}\,$s)")
                        self.ax.set(xlabel=f"Time $t$ in seconds ({SFT.p_num(len(self.data))} slices, " +
                                           rf"$\Delta t = {SFT.delta_t:g}\,$s)",
                                    ylabel=f"Freq. $f$ in Hz ({SFT.f_pts} bins, " + rf"$\Delta f = {SFT.delta_f:g}\,$Hz)",
                                    xlim=(t_lo, t_hi))
                        t = np.linspace(t_lo, t_hi, Sx.shape[1])
                        f = np.linspace(0, self.fs / 2, Sx.shape[0])
                        im1 = self.ax.pcolormesh(t, f, np.abs(Sx), shading='gouraud', cmap='viridis')
                        # TODO: Multiple color bars displayed - Need a fix
                        colorbar = self.figure.colorbar(im1, ax=self.ax)
                        self.canvas.draw()
                        colorbar.remove()
                    except Exception as e:
                        print(e)
                        self.Warning.warning()

    def settings_changed(self):
        pass

    def send_report(self):
        self.report_caption(f"STFT Plot for column: {self.column_selector.currentText()}")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(STFTPlotter).run()