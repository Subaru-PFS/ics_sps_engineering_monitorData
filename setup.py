import distutils
from distutils.core import setup, Extension

import sdss3tools
import os

sdss3tools.setup(
    name = 'ics_sps_engineering_monitorData',
    description = "Toy SDSS-3 actor.",
    )

