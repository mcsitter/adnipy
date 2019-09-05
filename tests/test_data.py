# -*- coding: utf-8 -*-

"""Test the data module."""

from adnipy import data


def test_image_id_from_filename():
    """Test extracting image id from filename."""
    correct = 123456789
    filename = "_I123456789.nii"
    image_id = data.image_id_from_filename(filename)
    assert correct == image_id
