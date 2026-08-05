"""Process ADNI study data with ADNIpy."""

__author__ = """Maximilian Cosmo Sitter"""
__email__ = "msitter@smail.uni-koeln.de"
__version__ = "1.0.1"
__all__ = ["ADNI", "get_matching_images", "read_csv", "timedelta"]

# Let users know if they're missing any of our hard dependencies
import matplotlib.pyplot as plt
import pandas as pd

from .adni import ADNI
from .adnipy import get_matching_images, read_csv, timedelta

del plt, pd
