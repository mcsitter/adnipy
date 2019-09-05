# -*- coding: utf-8 -*-

"""Top-level package for adnipy."""

__author__ = """Maximilian Cosmo Sitter"""
__email__ = "msitter@smail.uni-koeln.de"
__version__ = "0.0.1"

# Let users know if they're missing any of our hard dependencies
import matplotlib
import pandas as pd

from .adnipy import (
    drop_dynamic,
    get_matching_images,
    groups,
    longitudinal,
    read_csv,
    rid,
    standard_column_names,
    standard_dates,
    standard_index,
    timedelta,
    timepoints,
)

del matplotlib, pd


# module level doc-string
__doc__ = """Process ADNI study data with adnipy."""
