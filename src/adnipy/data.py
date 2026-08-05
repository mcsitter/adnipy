"""Process data created in Matlab."""

# Standard library imports
import re


def image_id_from_filename(filename: str) -> int:
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
    match = re.search(image_id_format, filename)
    if match is None:
        msg = f"Filename '{filename}' does not contain a valid image ID. "
        raise ValueError(msg)
    image_id = match.group(1)
    return int(image_id)
