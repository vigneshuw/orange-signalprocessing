from Orange.data import Table
from Orange.widgets import gui
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets.utils.signals import Input as SignalInput
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar


class FFTPlotter(OWWidget):
    # Set the widget configuration
    name = "FFT Plotter"
    description = "Plot FFT results from multiple FFT widgets"
    icon = "icons/fftplotter.svg"
    priority = 100
    keywords = ["widget", "fft", "plot"]
    want_main_area = True
    want_control_area = True

    class Inputs:
        data = SignalInput("FFT Data", Table, multiple=True)
        sampling_rate = SignalInput("Sampling Rate", float, multiple=True, auto_summary=False)

    class Warning(OWWidget.Warning):
        missing_column = Msg("Each input must have exactly one column.")
        missing_sampling_rate = Msg("Missing or invalid sampling rate.")

    def __init__(self):
        super().__init__()
        self.data_list = []
        self.sampling_rate_list = []
        self.current_inputs = []

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")

        # Filter for selecting inputs
        self.input_filter = QListWidget()
        self.input_filter.setSelectionMode(QListWidget.MultiSelection)
        self.controlArea.layout().addWidget(QLabel("Select Inputs:"))
        self.controlArea.layout().addWidget(self.input_filter)

        # Update button
        self.update_button = gui.button(self.controlArea, self, "Update Plot", callback=self.update_plot)

        # Main area layout
        main_area_layout = self.mainArea.layout()

        # Plot area
        self.figure, self.ax = plt.subplots(facecolor="none")
        self.figure.patch.set_facecolor('none')
        self.ax.set_facecolor('none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        main_area_layout.addWidget(self.toolbar)
        main_area_layout.addWidget(self.canvas)

    @Inputs.data
    def set_data(self, data, id):
        if data is not None:
            if len(data.domain.attributes) == 1:
                self.data_list.append((id[0], data))
            else:
                self.Warning.missing_column()
        else:
            self.data_list = [d for d in self.data_list if d[0] != id]
        self.update_input_filter()

    @Inputs.sampling_rate
    def set_sampling_rate(self, rate, id):
        if rate is not None and isinstance(rate, float):
            self.sampling_rate_list.append((id[0], rate))
        else:
            self.Warning.missing_sampling_rate()
        self.update_input_filter()

    def update_input_filter(self):
        self.input_filter.clear()
        data_ids = {id for id, data in self.data_list}
        rate_ids = {id for id, rate in self.sampling_rate_list}
        common_ids = data_ids & rate_ids
        for idx, (id, data) in enumerate(self.data_list):
            if id in common_ids:
                self.input_filter.addItem(QListWidgetItem(f"FFT Data {idx+1}"))

    def get_selected_data(self):
        selected_data = []
        selected_items = [item.text() for item in self.input_filter.selectedItems()]
        data_ids = {id for id, data in self.data_list}
        rate_ids = {id for id, rate in self.sampling_rate_list}
        common_ids = data_ids & rate_ids

        for idx, (id, data) in enumerate(self.data_list):
            if f"FFT Data {idx+1}" in selected_items and id in common_ids:
                rate = next(rate for rate_id, rate in self.sampling_rate_list if rate_id == id)
                selected_data.append((data, rate))
        return selected_data

    def update_plot(self):
        self.ax.clear()
        selected_data = self.get_selected_data()
        for idx, (data, rate) in enumerate(selected_data):
            freqs = np.fft.fftfreq(len(data.X) * 2, d=1.0 / rate)[:len(data.X)]
            self.ax.plot(freqs, data.X[:, 0], label=f"FFT {idx+1}")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title("FFT Spectrum")
        legend = self.ax.legend()
        legend.get_frame().set_facecolor('none')
        legend.get_frame().set_edgecolor('none')
        self.canvas.draw()

    def send_report(self):
        self.report_caption(f"Selected FFT Data: {[item.text() for item in self.input_filter.selectedItems()]}")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview  # since Orange 3.20.0
    WidgetPreview(FFTPlotter).run()