DESCRIPTION = "Analysis of sleepin' newborns data"
LONG_DESCRIPTION = """"""

DISTNAME = "guanas_rue"
MAINTAINER = ""
MAINTAINER_EMAIL = "ruggero.basanisi@imtlucca.it"
URL = "https://github.com/StanSStanman/closedloop_lsl"
LICENSE = "The Unlicense"
DOWNLOAD_URL = "https://github.com/StanSStanman/closedloop_lsl"
VERSION = "0.0.1"
PACKAGE_DATA = {}

INSTALL_REQUIRES = [
    "numpy",
    "scipy",
    "matplotlib",
    "xarray",
    "pandas",
    "h5py",
    "netCDF4",
    "mne"
]

PACKAGES = []

CLASSIFIERS = []

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if __name__ == "__main__":
    setup(
        name=DISTNAME,
        author=MAINTAINER,
        author_email=MAINTAINER_EMAIL,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        url=URL,
        version=VERSION,
        download_url=DOWNLOAD_URL,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        classifiers=CLASSIFIERS,
    )
