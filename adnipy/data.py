# -*- coding: utf-8 -*-

"""Process data created in Matlab."""

# Standard library imports
import re

# Third party imports
import pandas as pd


def image_id_from_filename(filename):
    """Extract image ID of single ADNI .nii filename.

    Images from the ADNI database have a specific formatting.
    Using regular expressions the image ID can be extracted from filenames.

    Parameters
    ----------
    filename : str
        It must contain the Image ID at the end.

    Returns
    -------
    numpy.int64
        Image as a integer.

    Examples
    --------
    >>> image_id_from_filename("*_I123456.nii")
    123456

    """
    image_id_format = re.compile("_I([0-9]*).nii")
    image_id = re.search(image_id_format, filename).group(1)
    image_id = int(image_id)
    return image_id
