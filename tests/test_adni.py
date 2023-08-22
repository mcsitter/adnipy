# -*- coding: utf-8 -*-

"""Tests for dataframe `adni` extension."""

# pylint: disable=W0621, R0801


# Third party imports
import pandas as pd
import pytest

from adnipy import adni  # noqa: F401 pylint: disable=W0611


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
def test_timepoints(test_df):
    """Dictionairy for the timepoints in test_df if Description is ignored."""
    test_df = test_df.drop(columns=["Description"])
    timepoints = {
        "Timepoint 1": test_df.iloc[[0, 2, 4, 5]].set_index(["Subject ID", "Image ID"]),
        "Timepoint 2": test_df.iloc[[1, 3]].set_index(["Subject ID", "Image ID"]),
    }
    return timepoints


def test_rid_from_subject_id(test_df):
    """Test creating RID from Subject ID."""
    correct = test_df
    test_df = test_df.drop(columns="RID")
    with_rid = test_df.adni.rid()
    pd.testing.assert_frame_equal(correct, with_rid)


def test_longitundal_only(test_df):
    """Test output dataframe being longitudinal only."""
    correct = test_df.drop(index=[4, 5])
    longitundal_only = test_df.adni.longitudinal()
    pd.testing.assert_frame_equal(correct, longitundal_only)


def test_drop_dynamic_images(test_df):
    """Test dropping entries with dynamic description."""
    correct = test_df.drop(index=[3])
    no_dynamics = test_df.adni.drop_dynamic()
    pd.testing.assert_frame_equal(correct, no_dynamics)


def test_drop_dynamic_without_description_columns(test_df):
    """Test dropping dynamic images without description column present."""
    test_df = test_df.drop(columns=["Description"])
    with pytest.raises(KeyError):
        test_df.adni.drop_dynamic()


def test_standardizing_index(test_df):
    """Test conversion of index to standard."""
    correct_index = ["Subject ID", "Image ID", "RID"]
    standard_index = test_df.adni.standard_index().index.names
    assert correct_index == standard_index


def test_renaming_columns_to_standard(test_df):
    """Test renaming of column Acq Date to SCANDATE."""
    correct = test_df.drop(columns=["VISCODE2"]).rename(
        columns={"Acq Date": "SCANDATE"}
    )
    renamed = test_df.adni.standard_column_names()
    pd.testing.assert_frame_equal(correct, renamed)


def test_extracting_groups_grouped_mci(test_df):
    """Test creating a datframe for each group."""
    correct = {
        "AD": test_df.iloc[[2, 3]],
        "MCI": test_df.iloc[[0, 1]],
        "EMCI": test_df.loc[[5]],
        "LMCI": test_df.loc[[4]],
    }
    group_dict = test_df.adni.groups(grouped_mci=False)
    pd.testing.assert_frame_equal(correct["AD"], group_dict["AD"])
    pd.testing.assert_frame_equal(correct["MCI"], group_dict["MCI"])
    pd.testing.assert_frame_equal(correct["LMCI"], group_dict["LMCI"])
    pd.testing.assert_frame_equal(correct["EMCI"], group_dict["EMCI"])


def test_extracting_groups_sperate_mci_groups(test_df):
    """Test creating a datframe for each group."""
    correct = {"MCI": test_df.iloc[[0, 1, 4, 5]], "AD": test_df.iloc[[2, 3]]}
    group_dict = test_df.adni.groups()
    pd.testing.assert_frame_equal(correct["MCI"], group_dict["MCI"])
    pd.testing.assert_frame_equal(correct["AD"], group_dict["AD"])


def test_timepoint_extracting_raises_error_with_description(test_df):
    """Test raising error if Description in columns."""
    with pytest.raises(ValueError):
        test_df.adni.timepoints()


def test_timepoint_extraction_second_timepoint_earliest(test_df, test_timepoints):
    """Test timepoint extraction with second='first'."""
    correct = test_timepoints
    test_df = test_df.drop(columns="Description")
    timepoints = test_df.adni.timepoints()
    pd.testing.assert_frame_equal(correct["Timepoint 1"], timepoints["Timepoint 1"])


def test_timepoint_extraction_second_timepoint_latest(test_df, test_timepoints):
    """Test timepoint extraction with second='last'."""
    correct = test_timepoints
    test_df = test_df.drop(columns="Description")
    timepoints = test_df.adni.timepoints(second="last")
    pd.testing.assert_frame_equal(correct["Timepoint 1"], timepoints["Timepoint 1"])
