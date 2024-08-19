import numpy as np
from scipy.fft import fft
from scipy.signal import welch
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLineEdit, QSpacerItem, QSizePolicy


class FrequencyDomainFeatures(OWWidget):
    name = "Frequency Domain Features"
    description = "Compute various frequency domain features from a time series signal"
    icon = "icons/frequencydomainfeatures.svg"
    priority = 6
    keywords = ["frequency domain", "features", "signal processing"]

    class Inputs:
        time_series = Input("Time Series Data", Table)

    class Outputs:
        features_data = Output("Features Data", Table, default=True)

    # Settings parameters
    sampling_rate = Setting(1.0)
    segment_size = Setting(1.0)
    overlap_rate = Setting(0.0)

    class Warning(OWWidget.Warning):
        warning = Msg("Feature computation failed.")
        warning_invalid_params = Msg("Invalid segment size or overlap rate.")

    def __init__(self):
        super().__init__()
        self.time_series = None
        self.selected_features = []
        self.feature_inputs = {}
        self.feature_descriptions = {
            "PeakValueFFT": "Peak Value of FFT: The maximum value of the FFT magnitude spectrum.",
            "EnergyFFT": "Energy of FFT: The sum of the squared FFT magnitudes.",
            "PowerSpectralDensity": "FFT Power Spectral Density: Estimate the power spectral density using Welch's method."
        }

        # Control area with settings
        self.controlArea = gui.widgetBox(self.controlArea, "Settings")

        # Sampling rate input
        self.sampling_rate_input = gui.lineEdit(
            self.controlArea, self, "sampling_rate", label="Sampling Rate (Hz):", valueType=float)
        self.sampling_rate_input.setAlignment(Qt.AlignCenter)
        self.sampling_rate_input.setToolTip("Sampling rate in Hz.")

        # Segment size input
        self.segment_size_input = gui.lineEdit(
            self.controlArea, self, "segment_size", label="Segment Size (s):", valueType=float)
        self.segment_size_input.setAlignment(Qt.AlignCenter)
        self.segment_size_input.setToolTip("Segment size in seconds.")

        # Overlap rate input
        self.overlap_rate_input = gui.lineEdit(
            self.controlArea, self, "overlap_rate", label="Overlap Rate (%):", valueType=float)
        self.overlap_rate_input.setAlignment(Qt.AlignCenter)
        self.overlap_rate_input.setToolTip("Overlap rate as a percentage.")

        # Feature selection list
        self.feature_list = QListWidget()
        self.feature_list.setSelectionMode(QListWidget.SingleSelection)
        self.feature_list.itemSelectionChanged.connect(self.update_feature_description)
        for feature in self.feature_descriptions.keys():
            item = QListWidgetItem(feature)
            self.feature_list.addItem(item)
        self.controlArea.layout().addWidget(self.feature_list)

        # Confirm button
        self.confirm_button = gui.button(self.controlArea, self, "Confirm Feature", callback=self.select_feature)

        # Compute button
        self.compute_button = gui.button(self.controlArea, self, "Compute Features", callback=self.compute_features)

        # Reset button
        self.reset_button = gui.button(self.controlArea, self, "Reset", callback=self.reset_features)

        # Right half: Feature description and inputs
        self.right_half = QVBoxLayout()
        self.mainArea.layout().addLayout(self.right_half)

        self.description_label = QLabel("Select a feature to see its description and input options.")
        self.right_half.addWidget(self.description_label)
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_half.addItem(spacer)

        self.input_layout = QVBoxLayout()
        self.right_half.addLayout(self.input_layout)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_half.addItem(spacer)

        self.current_feature = None

    def update_feature_description(self):
        # Get the selected feature
        selected_items = self.feature_list.selectedItems()
        if selected_items:
            feature = selected_items[0].text()

            # Clear previous inputs
            for i in reversed(range(self.input_layout.count())):
                item = self.input_layout.itemAt(i)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    # If the item is a layout, remove it
                    layout = item.layout()
                    if layout is not None:
                        for j in reversed(range(layout.count())):
                            layout_item = layout.itemAt(j)
                            layout_widget = layout_item.widget()
                            if layout_widget is not None:
                                layout_widget.setParent(None)

            # Update the description label
            self.description_label.setText(self.feature_descriptions[feature])

            # Example: Add specific inputs based on the feature selected
            if feature == "PowerSpectralDensity":
                layout = QHBoxLayout()
                nperseg_label = QLabel("Nperseg:")
                nperseg_input = QLineEdit()
                nperseg_input.setText("256")
                nperseg_input.setAlignment(Qt.AlignCenter)
                nperseg_input.setFixedWidth(100)  # Reduced width

                layout.addWidget(nperseg_label)
                layout.addWidget(nperseg_input)
                layout.addStretch()

                self.input_layout.addLayout(layout)
                self.feature_inputs[feature] = nperseg_input
            # Add other features and their specific inputs here

            self.current_feature = feature

    def select_feature(self):
        if self.current_feature:
            self.selected_features.append(self.current_feature)
            selected_item = self.feature_list.selectedItems()[0]
            selected_item.setFlags(selected_item.flags() & ~Qt.ItemIsEnabled)
            self.feature_list.clearSelection()
            self.description_label.setText(f"Feature '{self.current_feature}' configured. Select another feature or click Compute.")
            self.current_feature = None

    def reset_features(self):
        # Clear the selected features
        self.selected_features = []

        # Re-enable all items in the feature list
        for index in range(self.feature_list.count()):
            item = self.feature_list.item(index)
            item.setFlags(item.flags() | Qt.ItemIsEnabled)

        # Clear the right half (input_layout and description)
        self.description_label.setText("Select a feature to see its description and input options.")
        for i in reversed(range(self.input_layout.count())):
            item = self.input_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def segment_signal(self, data, segment_size, overlap_rate, sampling_rate):
        segment_samples = int(segment_size * sampling_rate)
        step_size = int(segment_samples * (1 - overlap_rate / 100))
        segments = [
            data[i:i + segment_samples]
            for i in range(0, len(data) - segment_samples + 1, step_size)
        ]
        return segments

    def compute_features(self):
        if self.time_series:
            data_col = self.time_series.X[:, 0]  # Assuming single column time series data
            sampling_rate = float(self.sampling_rate_input.text())
            segment_size = float(self.segment_size_input.text())
            overlap_rate = float(self.overlap_rate_input.text())

            # Error checking
            self.Warning.clear()
            if segment_size <= 0 or overlap_rate < 0 or overlap_rate >= 100 or sampling_rate < 1:
                self.Warning.warning_invalid_params()
                return

            segments = self.segment_signal(data_col, segment_size, overlap_rate, sampling_rate)
            all_features = []

            for segment in segments:
                fft_values = np.abs(fft(segment))[:len(segment) // 2]
                segment_features = []
                for feature in self.selected_features:
                    if feature == "PeakValueFFT":
                        segment_features.append(np.max(fft_values))
                    elif feature == "EnergyFFT":
                        segment_features.append(np.sum(fft_values ** 2))
                    elif feature == "PowerSpectralDensity":
                        nperseg = int(self.feature_inputs["PowerSpectralDensity"].text())
                        freqs, psd = welch(segment, fs=sampling_rate, nperseg=nperseg)
                        segment_features.append(np.sum(psd))
                all_features.append(segment_features)

            # Create the output table
            domain = Domain([ContinuousVariable(f) for f in self.selected_features])
            new_data = Table(domain, np.array(all_features))
            self.Outputs.features_data.send(new_data)

    @Inputs.time_series
    def set_data(self, data):
        self.time_series = data

    def send_report(self):
        self.report_caption("Frequency Domain Features Analysis")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(FrequencyDomainFeatures).run()