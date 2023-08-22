# -*- coding: utf-8 -*-

"""Tests for `adnipy` package."""

# pylint: disable=W0621, R0801

# Standard library imports
import io

# Third party imports
import numpy as np
import pandas as pd
import pytest

from adnipy import adnipy


@pytest.fixture
def test_df():
    """Provide sample dataframe for standardized testing."""
    columns = [
        "Subject ID",
        "Description",
        "Group",
        "VISCODE",
        "VISCODE2",
        "Image ID",
        "Acq Date",
        "RID",
    ]
    subjects = [
        ["101_S_1001", "Average", "MCI", "m12", "m12", 100001, "1/01/2001", 1001],
        ["101_S_1001", "Average", "MCI", "m24", "m24", 200001, "1/01/2002", 1001],
        ["102_S_1002", "Average", "AD", "m12", "m12", 100002, "2/02/2002", 1002],
        ["102_S_1002", "Dynamic", "AD", "m12", "m12", 200002, "2/02/2002", 1002],
        ["103_S_1003", "Average", "LMCI", "m12", "m12", 100003, "3/03/2003", 1003],
        ["104_S_1004", "Average", "EMCI", "m12", "m12", 100004, "4/04/2004", 1004],
    ]

    dataframe = pd.DataFrame(subjects, columns=columns)

    return dataframe


@pytest.fixture
def test_file():
    """Provide sample file which contains same data as test_df."""
    file = io.StringIO(
        "Subject ID,Description,Group,VISCODE,VISCODE2,Image ID,Acq Date,RID\n"
        "101_S_1001,Average,MCI,m12,m12,100001,1/01/2001,1001\n"
        "101_S_1001,Average,MCI,m24,m24,200001,1/01/2002,1001\n"
        "102_S_1002,Average,AD,m12,m12,100002,2/02/2002,1002\n"
        "102_S_1002,Dynamic,AD,m12,m12,200002,2/02/2002,1002\n"
        "103_S_1003,Average,LMCI,m12,m12,100003,3/03/2003,1003\n"
        "104_S_1004,Average,EMCI,m12,m12,100004,4/04/2004,1004\n"
    )
    return file


@pytest.fixture
def test_timepoints(test_df):
    """Dictionairy for the timepoints in test_df if Description is ignored."""
    test_df = test_df.drop(columns=["Description"])
    timepoints = {
        "Timepoint 1": test_df.iloc[[0, 2, 4, 5]].set_index(["Subject ID", "Image ID"]),
        "Timepoint 2": test_df.iloc[[1, 3]].set_index(["Subject ID", "Image ID"]),
    }
    return timepoints


def test_calculating_timedelta_of_scandate(test_timepoints):
    """Test calculating timedelta of 2 dataframes."""
    for timepoint, dataframe in test_timepoints.items():
        timepoint_df = dataframe.rename(columns={"Acq Date": "SCANDATE"})
        timepoint_df["SCANDATE"] = pd.to_datetime(timepoint_df["SCANDATE"])
        test_timepoints[timepoint] = timepoint_df
    correct_dtype = np.dtype("<m8[ns]")
    timedeltas = adnipy.timedelta(
        test_timepoints["Timepoint 1"], test_timepoints["Timepoint 2"]
    )
    assert timedeltas.dtypes == correct_dtype
    assert timedeltas.iloc[1] == np.timedelta64(0)


def test_read_csv(test_df, test_file):
    """Test reading a sample .csv file."""
    correct = test_df
    file = test_file
    reading = adnipy.read_csv(file)
    pd.testing.assert_frame_equal(correct, reading)


def test_find_matching_images_without_missing_match():
    """Test finding matching images based on 'SCANDATE'."""
    # defining left dataframe
    left_subject_ids = ["101_S_1001", "102_S_1002", "104_S_1004"]
    left_scandates = pd.to_datetime(["1/01/2001", "2/02/2002", "4/04/2004"])
    left_image_ids = [100001, 100002, 100004]
    left = pd.DataFrame(
        {
            "Subject ID": left_subject_ids,
            "SCANDATE": left_scandates,
            "Image ID": left_image_ids,
        }
    )

    # defining right dataframe
    right_subject_ids = [
        "101_S_1001",
        "102_S_1002",
        "104_S_1004",
        "104_S_1004",
    ]
    right_scandates = pd.to_datetime(
        ["1/01/2001", "2/02/2003", "4/04/2004", "4/04/2005"]
    )
    right_image_ids = [100011, 200012, 100014, 200014]
    right = pd.DataFrame(
        {
            "Subject ID": right_subject_ids,
            "SCANDATE": right_scandates,
            "Image ID": right_image_ids,
        }
    )

    # defining correct result
    correct = pd.DataFrame(
        {
            "Subject ID": ["101_S_1001", "102_S_1002", "104_S_1004"],
            "SCANDATE": pd.to_datetime(["1/01/2001", "2/02/2002", "4/04/2004"]),
            "Image ID_l": [100001, 100002, 100004],
            "Image ID_r": [100011, 200012, 100014],
        }
    )

    correct = correct.set_index(["Subject ID", "SCANDATE"])
    matches = adnipy.get_matching_images(left, right)
    pd.testing.assert_frame_equal(correct, matches)


def test_find_matching_images_with_missing_match():
    """Test finding matching images based on 'SCANDATE' with missing match."""
    # defining left dataframe
    left_subject_ids = ["101_S_1001", "102_S_1002", "103_S_1003", "104_S_1004"]
    left_scandates = pd.to_datetime(
        ["1/01/2001", "2/02/2002", "3/03/2003", "4/04/2004"]
    )
    left_image_ids = [100001, 100002, 100003, 100004]
    left = pd.DataFrame(
        {
            "Subject ID": left_subject_ids,
            "SCANDATE": left_scandates,
            "Image ID": left_image_ids,
        }
    )

    # defining right dataframe
    right_subject_ids = [
        "101_S_1001",
        "102_S_1002",
        "104_S_1004",
        "104_S_1004",
    ]
    right_scandates = pd.to_datetime(
        ["1/01/2001", "2/02/2003", "4/04/2004", "4/04/2005"]
    )
    right_image_ids = [100011, 200012, 100014, 200014]
    right = pd.DataFrame(
        {
            "Subject ID": right_subject_ids,
            "SCANDATE": right_scandates,
            "Image ID": right_image_ids,
        }
    )

    # defining correct result
    correct = pd.DataFrame(
        {
            "Subject ID": ["101_S_1001", "102_S_1002", "104_S_1004"],
            "SCANDATE": pd.to_datetime(["1/01/2001", "2/02/2002", "4/04/2004"]),
            "Image ID_l": [100001, 100002, 100004],
            "Image ID_r": [100011, 200012, 100014],
        }
    )

    correct = correct.set_index(["Subject ID", "SCANDATE"])
    with pytest.warns(UserWarning):
        matches = adnipy.get_matching_images(left, right)
    pd.testing.assert_frame_equal(correct, matches)
