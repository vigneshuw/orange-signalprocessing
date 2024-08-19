from Orange.data import Table
from Orange.widgets import gui
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets.utils.signals import Input as SignalInput
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QToolTip
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar


class TimeSeriesPlotter(OWWidget):
    # Set the widget configuration
    name = "Time Series Plotter"
    description = "Plot time series data from multiple widgets"
    icon = "icons/timeseriesplotter.svg"
    priority = 3
    keywords = ["widget", "time series", "plot"]
    want_main_area = True
    want_control_area = True

    class Inputs:
        data = SignalInput("Time Series Data", Table, multiple=True)

    class Warning(OWWidget.Warning):
        missing_column = Msg("Each input must have exactly one column.")

    def __init__(self):
        super().__init__()
        self.data_list = []
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

        # Connect the click event
        self.canvas.mpl_connect('button_press_event', self.on_click)

    @Inputs.data
    def set_data(self, data, id):
        if data is not None:
            if len(data.domain.attributes) == 1:
                self.data_list.append((id[0], data))
                self.Warning.clear()
            else:
                self.Warning.missing_column()
        else:
            self.data_list = [d for d in self.data_list if d[0] != id]
        self.update_input_filter()

    def update_input_filter(self):
        self.input_filter.clear()
        for idx, (id, data) in enumerate(self.data_list):
            column_name = data.domain.attributes[0].name if data.domain.attributes[0].name else f"Data {idx + 1}"
            self.input_filter.addItem(QListWidgetItem(column_name))

    def get_selected_data(self):
        selected_data = []
        selected_items = [item.text() for item in self.input_filter.selectedItems()]

        for idx, (id, data) in enumerate(self.data_list):
            column_name = data.domain.attributes[0].name if data.domain.attributes[0].name else f"Data {idx + 1}"
            if column_name in selected_items:
                selected_data.append((data, column_name))
        return selected_data

    def update_plot(self):
        self.ax.clear()
        selected_data = self.get_selected_data()
        for idx, (data, column_name) in enumerate(selected_data):
            samples = np.arange(len(data.X))
            self.ax.plot(samples, data.X[:, 0], label=column_name)
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title("Time Series")
        legend = self.ax.legend()
        legend.get_frame().set_facecolor('none')
        legend.get_frame().set_edgecolor('none')
        self.canvas.draw()

    def send_report(self):
        self.report_caption(f"Selected Time Series Data: {[item.text() for item in self.input_filter.selectedItems()]}")

    def on_click(self, event):
        if event.inaxes is not None:
            x, y = event.xdata, event.ydata
            QToolTip.showText(event.guiEvent.globalPos(), f"x: {x:.2f}, y: {y:.2f}")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(TimeSeriesPlotter).run()