# -*- coding: utf-8 -*-

"""Tests for `adnipy` package."""

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
        [
            "101_S_1001",
            "Average",
            "MCI",
            "m12",
            "m12",
            100001,
            "1/01/2001",
            1001,
        ],
        [
            "101_S_1001",
            "Average",
            "MCI",
            "m24",
            "m24",
            200001,
            "1/01/2002",
            1001,
        ],
        [
            "102_S_1002",
            "Average",
            "AD",
            "m12",
            "m12",
            100002,
            "2/02/2002",
            1002,
        ],
        [
            "102_S_1002",
            "Dynamic",
            "AD",
            "m12",
            "m12",
            200002,
            "2/02/2002",
            1002,
        ],
        [
            "103_S_1003",
            "Average",
            "LMCI",
            "m12",
            "m12",
            100003,
            "3/03/2003",
            1003,
        ],
        [
            "104_S_1004",
            "Average",
            "EMCI",
            "m12",
            "m12",
            100004,
            "4/04/2004",
            1004,
        ],
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
        "Timepoint 1": test_df.iloc[[0, 2, 4, 5]].set_index(
            ["Subject ID", "Image ID"]
        ),
        "Timepoint 2": test_df.iloc[[1, 3]].set_index(
            ["Subject ID", "Image ID"]
        ),
    }
    return timepoints


def test_rid_from_subject_id(test_df):
    """Test creating RID from Subject ID."""
    correct = test_df
    with_rid = adnipy.rid(test_df.drop(columns="RID"))
    pd.testing.assert_frame_equal(correct, with_rid)


def test_longitundal_only(test_df):
    """Test output dataframe being longitudinal only."""
    correct = test_df.drop(index=[4, 5])
    longitundal_only = adnipy.longitudinal(test_df)
    pd.testing.assert_frame_equal(correct, longitundal_only)


def test_drop_dynamic_images(test_df):
    """Test dropping entries with dynamic description."""
    correct = test_df.drop(index=(3))
    no_dynamics = adnipy.drop_dynamic(test_df)
    pd.testing.assert_frame_equal(correct, no_dynamics)


def test_drop_dynamic_without_description_columns(test_df):
    """Test dropping dynamic images without description column present."""
    test_df = test_df.drop(columns=("Description"))
    with pytest.raises(KeyError):
        adnipy.drop_dynamic(test_df)


def test_datetime_dtype_conversion(test_df):
    """Test converting dates to datetime dtype."""
    correct_dtype = np.dtype("<M8[ns]")
    date_column_type = adnipy.standard_dates(test_df)["Acq Date"].dtype
    assert correct_dtype == date_column_type


def test_standardizing_index(test_df):
    """Test conversion of index to standard."""
    correct_index = ["Subject ID", "Image ID", "RID"]
    standard_index = adnipy.standard_index(test_df).index.names
    assert correct_index == standard_index


def test_renaming_columns_to_standard(test_df):
    """Test renaming of column Acq Date to SCANDATE."""
    correct = test_df.drop(columns=["VISCODE2"]).rename(
        columns={"Acq Date": "SCANDATE"}
    )
    renamed = adnipy.standard_column_names(test_df)
    pd.testing.assert_frame_equal(correct, renamed)


def test_extracting_groups_grouped_mci(test_df):
    """Test creating a datframe for each group."""
    correct = {
        "AD": test_df.iloc[[2, 3]],
        "MCI": test_df.iloc[[0, 1]],
        "EMCI": test_df.loc[[5]],
        "LMCI": test_df.loc[[4]],
    }
    group_dict = adnipy.groups(test_df, grouped_mci=False)
    pd.testing.assert_frame_equal(correct["AD"], group_dict["AD"])
    pd.testing.assert_frame_equal(correct["MCI"], group_dict["MCI"])
    pd.testing.assert_frame_equal(correct["LMCI"], group_dict["LMCI"])
    pd.testing.assert_frame_equal(correct["EMCI"], group_dict["EMCI"])


def test_extracting_groups_sperate_mci_groups(test_df):
    """Test creating a datframe for each group."""
    correct = {"MCI": test_df.iloc[[0, 1, 4, 5]], "AD": test_df.iloc[[2, 3]]}
    group_dict = adnipy.groups(test_df)
    pd.testing.assert_frame_equal(correct["MCI"], group_dict["MCI"])
    pd.testing.assert_frame_equal(correct["AD"], group_dict["AD"])


def test_timepoint_extracting_raises_error_with_description(test_df):
    """Test raising error if Description in columns."""
    with pytest.raises(ValueError):
        adnipy.timepoints(test_df)


def test_timepoint_extraction_second_timepoint_earliest(
    test_df, test_timepoints
):
    """Test timepoint extraction with second='first'."""
    correct = test_timepoints
    test_df = test_df.drop(columns="Description")
    timepoints = adnipy.timepoints(test_df)
    pd.testing.assert_frame_equal(
        correct["Timepoint 1"], timepoints["Timepoint 1"]
    )


def test_timepoint_extraction_second_timepoint_latest(
    test_df, test_timepoints
):
    """Test timepoint extraction with second='last'."""
    correct = test_timepoints
    test_df = test_df.drop(columns="Description")
    timepoints = adnipy.timepoints(test_df, second="last")
    pd.testing.assert_frame_equal(
        correct["Timepoint 1"], timepoints["Timepoint 1"]
    )


def test_calculating_timedelta_of_scandate(test_timepoints):
    """Test calculating timedelta of 2 dataframes."""
    for timepoint, dataframe in test_timepoints.items():
        df = dataframe.rename(columns={"Acq Date": "SCANDATE"})
        df["SCANDATE"] = pd.to_datetime(df["SCANDATE"])
        test_timepoints[timepoint] = df
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
            "SCANDATE": pd.to_datetime(
                ["1/01/2001", "2/02/2002", "4/04/2004"]
            ),
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
            "SCANDATE": pd.to_datetime(
                ["1/01/2001", "2/02/2002", "4/04/2004"]
            ),
            "Image ID_l": [100001, 100002, 100004],
            "Image ID_r": [100011, 200012, 100014],
        }
    )

    correct = correct.set_index(["Subject ID", "SCANDATE"])
    with pytest.warns(UserWarning):
        matches = adnipy.get_matching_images(left, right)
    pd.testing.assert_frame_equal(correct, matches)
