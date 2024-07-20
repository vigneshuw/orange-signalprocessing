import sys
from os import path, walk
from setuptools import setup, find_packages

NAME = "Orange Signal Processing"

VERSION = "0.0.1"

AUTHOR = "Vignesh Selvaraj"
AUTHOR_EMAIL = "vignesh-selvaraj@outlook.com"

URL = "https://github.com/vigneshuw/orange-signalprocessing"
DESCRIPTION = "Add-on for signal processing"
LONG_DESCRIPTION = open(path.join(path.dirname(__file__), 'README.pypi'),
                        'r', encoding='utf-8').read()
LICENSE = "BSD"

KEYWORDS = [
    'orange3 add-on',
    'orange3 signalprocessing',
]

PACKAGES = find_packages()
PACKAGE_DATA = {
    'orangecontrib.signalprocessing.widgets': ['icons/*'],
}

INSTALL_REQUIRES = [
    'Orange3',
    'numpy'
]

ENTRY_POINTS = {
    'orange3.addon': (
        'signalprocessing = orangecontrib.signalprocessing',
    ),
    'orange.widgets': (
        'Signal Processing = orangecontrib.signalprocessing.widgets',
    ),
}

NAMESPACE_PACKAGES = ["orangecontrib"]


if __name__ == '__main__':
    setup(
        name=NAME,
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/markdown',
        license=LICENSE,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        install_requires=INSTALL_REQUIRES,
        entry_points=ENTRY_POINTS,
        keywords=KEYWORDS,
        namespace_packages=NAMESPACE_PACKAGES,
        zip_safe=False,
    )
