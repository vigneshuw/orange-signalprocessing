# Orange3 Signal Processing

Orange3 Signal Processing toolbox is developed for the course ME529-SmartManufacturing at the University of Wisconsin-Madison.
This toolbox provides widgets that can be used to process time series sensor data.

The widgets currently available are,

- FFT Computation
- STFT Computation
- Envelop Analysis
- Butterworth Filters - LP, HP, and BP
- Time Domain Feature Extraction
- Frequency Domain Feature Extraction
- Time-Frequency Domain Feature Extraction

## Anaconda Installation

The easiest way to install this package is through Anaconda distribution. Download [Anaconda](https://docs.anaconda.com/anaconda/install/) for your OS.
In your Anaconda prompt first add the conda-forge to your channels:

```shell
conda config --add channels conda-forge
```

```shell
conda config --set channel_priority strict
```

Then install Orange3

```shell
conda install orange3 -y
```

Clone the repository or download it as a Zip file.

Navigate to the inside the repository.

Then Run

```shell
pip install -e .
```

## Usage

After the installation, the widget should by default be available in Orange. To run orange from the terminal, use

```shell
python3 -m Orange.canvas
```

or

```shell
orange-canvas
```
