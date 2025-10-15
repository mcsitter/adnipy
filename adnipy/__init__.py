# -*- coding: utf-8 -*-

"""Top-level package for adnipy."""

__author__ = """Maximilian Cosmo Sitter"""
__email__ = "msitter@smail.uni-koeln.de"
__version__ = "1.0.0"

# Let users know if they're missing any of our hard dependencies
import matplotlib
import pandas as pd

from .adni import ADNI
from .adnipy import get_matching_images, read_csv, timedelta

del matplotlib, pd


# module level doc-string
__doc__ = """Process ADNI study data with adnipy."""
