# -*- coding: utf-8 -*-

"""Process ADNI study data with adnipy."""

# Standard library imports
import warnings

# Third party imports
import pandas as pd

# TODO df = df.reindex(columns=columns)
# TODO def common_columns(left, right) --> list


def read_csv(file):
    """Return a csv file as a pandas.DataFrame.

    Recognizes missing values used in the ADNI database.

    Parameters
    ----------
    file : str, pathlib.Path
        The path to the .csv file.

    Returns
    -------
    pd.DataFrame
        Returns the file as a dataframe.

    See also
    --------
    standard_column_names
    standard_dates
    standard_index

    """
    # empty values
    na_values = ["-1", "-4"]

    # prevents UserWarnings on large files like ADNIMERGE
    dtype = {
        "ABETA": object,
        "TAU": object,
        "TAU_bl": object,
        "PTAU": object,
        "PTAU_bl": object,
    }

    df = pd.read_csv(file, dtype=dtype, na_values=na_values)

    return df


def standard_column_names(dataframe):
    """Rename dataframe columns to module standard.

    This function helps when working with multiple dataframes,
    since the same data can have different names.
    It will also call `rid()` on the dataframe.

    Parameters
    ----------
    dataframe : pd.DataFrame
        This dataframe will be modified.

    Returns
    -------
    pd.DataFrame
        This will have standardized columns names.

    See also
    --------
    rid

    Examples
    --------
    >>> subjects = pd.DataFrame({"Subject": ["101_S_1001", "102_S_1002"]})
    >>> subjects
          Subject
    0  101_S_1001
    1  102_S_1002
    >>> standard_column_names(subjects)
       Subject ID   RID
    0  101_S_1001  1001
    1  102_S_1002  1002

    >>> images = pd.DataFrame({"Image": [100001, 100002]})
    >>> images
        Image
    0  100001
    1  100002
    >>> standard_column_names(images)
       Image ID
    0    100001
    1    100002

    """
    mapper = {
        # Collections
        "Image": "Image ID",
        "Image Data ID": "Image ID",
        "Subject": "Subject ID",
        "Acq Date": "SCANDATE",
        # ADNIMERGE
        "PTID": "Subject ID",
        # TAUMETA3
        "ASSAYTIME": "TAUTIME",
    }

    dataframe = dataframe.rename(mapper=mapper, axis="columns")

    if "VISCODE2" in dataframe.columns:
        dataframe["VISCODE"] = dataframe["VISCODE2"]
        del dataframe["VISCODE2"]

    dataframe = rid(dataframe)

    return dataframe


def standard_dates(dataset):
    """Change type of date columns to datetime.

    Parameters
    ----------
    dataset : pd.DataFrame
            This dataframe will be modified.

    Returns
    -------
    pd.DataFrame
        Dates will have the appropriate dtype.

    """
    dates = [
        # Collections
        "Acq Date",
        "Downloaded",
        # ADNIMERGE
        "EXAMDATE",
        "EXAMDATE_bl",
        "update_stamp",
        # DESIKANLAB
        "USERDATE",
        "update_stamp",
        # TAUMETA
        "USERDATE",
        "USERDATE2",
        "SCANDATE",
        "TAUTRANDT",
        "update_stamp",
        # TAUMETA3
        "USERDATE",
        "USERDATE2",
        "SCANDATE",
        "TRANDATE",
        "update_stamp",
    ]

    for date in set(dates):
        if date in dataset.columns:
            dataset.loc[:, date] = pd.to_datetime(dataset.loc[:, date])

    return dataset


def standard_index(df, index=None):
    """Process dataframes into a standardized format.

    The output is easy to read.
    Applying functions the the output may not work as expected.

    Parameters
    ----------
    df : pd.DataFrame
        This dataframe will be modified.

    index : list of str, default None
        These columns will be the new index.

    Returns
    -------
    pd.DataFrame
        An easy to read dataframe for humans.

    """
    if index is None:
        index = ["Subject ID", "Image ID", "RID", "Visit", "SCANDATE"]

    df = df.reset_index()
    df = df.set_index([column for column in index if column in df.columns])

    if "index" in df.columns:
        df = df.drop(columns="index")
    df = df.dropna(axis="columns", how="all")
    df = df.sort_index()

    return df


def rid(collection):
    """Add a roster ID column.

    Will not work if 'RID' is already present or 'Subject ID' is missing.

    Parameters
    ----------
    collection : pd.DataFrame
        This dataframe will be modified.

    Returns
    -------
    pd.DataFrame
        Dataframe with a 'RID' column.

    Examples
    --------
    >>> collection = pd.DataFrame({"Subject ID": ["100_S_1000", "101_S_1001"]})
    >>> collection
       Subject ID
    0  100_S_1000
    1  101_S_1001
    >>> rid(collection)
       Subject ID   RID
    0  100_S_1000  1000
    1  101_S_1001  1001

    """
    missing_rid = "RID" not in collection.columns
    contains_subject_id = "Subject ID" in collection.columns
    if missing_rid and contains_subject_id:
        collection["RID"] = collection["Subject ID"].map(
            lambda subject_id: pd.to_numeric(subject_id[-4:])
        )

    return collection


def drop_dynamic(images):
    """Remove images which are dynamic.

    Drops all rows, in which the Description contains 'Dynamic'.

    Parameters
    ----------
    images : pd.DataFrame
        This dataframe will be modified.

    Returns
    -------
    pd.DataFrame
        All images that are not dynamic.

    """
    no_dynamic = images[~images["Description"].str.contains("Dynamic")]

    return no_dynamic


def groups(collection, grouped_mci=True):
    """Create a dataframe for each group and save it to a csv file.

    Parameters
    ----------
    collection : pd.DataFrame
        DataFrame has to have a Group column.
    grouped_mci : bool, default True
        If true, 'LMCI' and 'EMCI' are treated like 'MCI'.
        However, the original values will stills be in the output.

    Returns
    -------
    dict
        Dictionnairy with a dataframe for each group.

    """
    collection = collection.copy()

    # creates dataframe for each group
    group_names = collection["Group"].unique()
    groups = {}
    for group in group_names:
        group_df = collection[collection["Group"] == group]
        groups[group] = group_df

    # groups MCIs
    if grouped_mci is True:
        mci = collection[collection["Group"].isin(["MCI", "LMCI", "EMCI"])]
        if not mci.empty:
            groups["MCI"] = mci
        if "LMCI" in group_names:
            del groups["LMCI"]
        if "EMCI" in group_names:
            del groups["EMCI"]

    return groups


def longitudinal(images):
    """
    Keep only longitudinal data.

    This requires an 'RID' or 'Subject ID' column in the dataframe.
    Do not use if multiple images are present for a single timepoint.

    Parameters
    ----------
    images : pd.DataFrame
        This dataframe will be modified.

    Returns
    -------
    pd.DataFrame
        A dataframe with only longitudinal data.

    See also
    --------
    drop_dynamic

    """
    images = rid(images)

    longitudinal = images[images["RID"].duplicated(keep=False)]

    return longitudinal


def timepoints(df, second="first"):
    """Extract timepoints from a dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        This dataframe will be used as a base.

    second : {'first' or 'last'}, default 'first'
        'last' to have the latest, 'first' to have the earliest values
        for timepoint 2.

    """
    index = ["Subject ID", "Image ID"]

    df = df.reset_index()
    df = df.set_index(index)
    df = df.sort_index()
    if "index" in df.columns:
        df = df.drop(columns="index")
    if "Description" in df.columns:
        raise ValueError(
            "Make sure that 'Description' is not in columns "
            "and only one image per timepoint is in the pd.DataFrame."
        )
    df_subjects = df.index.get_level_values(0)
    df_images = df.index.get_level_values(1)

    timepoints = {}

    if second == "first":
        total_timepoints = max(df_subjects.value_counts())
        for i in range(total_timepoints):
            timepoint = i + 1
            timepoint_df = df[~df_subjects.duplicated(keep="first")]
            timepoint_str = "Timepoint " + str(timepoint)
            timepoints[timepoint_str] = timepoint_df
            df = df[~df_images.isin(timepoint_df.index.get_level_values(1))]
            df_subjects = df.index.get_level_values(0)
            df_images = df.index.get_level_values(1)

    elif second == "last":
        timepoint_1 = df[~df_subjects.duplicated()]
        timepoints["Timepoint 1"] = timepoint_1
        timepoint_1_images = timepoint_1.index.get_level_values(1)
        after_timepoint_1 = df[~df_images.isin(timepoint_1_images)]

        after_timepoint_1_images = after_timepoint_1.index.get_level_values(0)
        timepoint_2_last = after_timepoint_1[
            ~after_timepoint_1_images.duplicated(keep="last")
        ]
        timepoints["Timepoint 2"] = timepoint_2_last

    return timepoints


def timedelta(old, new):
    """Get timedelta between timepoints.

    Parameters
    ----------
    old : pd.DataFrame
        This is the older dataframe.
    new : pd.DataFrame
        This is the newer dataframe.

    Returns
    -------
    pd.Series
        The content will be timedelta values. Look into numpy for more options.

    """
    old = old.reset_index()
    old = old.set_index("Subject ID")

    new = new.reset_index()
    new = new.set_index("Subject ID")

    timedeltas = old["SCANDATE"] - new["SCANDATE"]

    return timedeltas


def get_matching_images(left, right):
    """Match different scan types based on closest date.

    The columns 'Subject ID' and 'SCANDATE' are required.

    Parameters
    ----------
    left : pd.DataFrame
        Dataframe containing the tau scans.
    right : pd.DataFrame
        Dataframe containing the mri scans.

    Returns
    -------
    pd.DataFrame
        For each timepoint there is a match from both inputs.

    """
    left = left.set_index(["Subject ID", "SCANDATE"])
    left = left.sort_index()

    right = right.set_index(["Subject ID", "SCANDATE"])
    right = right.sort_index()

    missing_match = []
    matching_images = []
    right_subjects = right.index.get_level_values(0)

    def closest_date(subject):
        """Get closest date from list."""
        unique_dates = subject.index.unique()
        closest_date = min(
            unique_dates, key=lambda x, index=index: abs(x - index[1])
        )

        return closest_date

    for index in left.index:
        if index[0] in right_subjects:
            subject = right.loc[index[0]]
            date = closest_date(subject)
            matching_image = right.loc[index[0], date]
            image = left.loc[[index]]
            image["Image ID_r"] = matching_image.values[0]
            matching_images.append(image)
        else:
            missing_match.append(index)

    matching_images_df = pd.concat(matching_images)
    matching_images_df = matching_images_df.rename(
        columns={"Image ID": "Image ID_l"}
    )

    if missing_match:
        missing_match_str = str(set(missing_match))
        message = "Could not find matching images for:" + missing_match_str
        warnings.warn(message)

    return matching_images_df
