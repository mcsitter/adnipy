# -*- coding: utf-8 -*-

"""Process ADNI study data with adnipy."""

# Standard library imports
import warnings

# Third party imports
import pandas as pd


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

    See Also
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

    dataframe = pd.read_csv(file, dtype=dtype, na_values=na_values)

    return dataframe


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

    def closest_date(subject, index):
        """Get closest date from list."""
        unique_dates = subject.index.unique()
        closest_date = min(unique_dates, key=lambda x, index=index: abs(x - index[1]))

        return closest_date

    for index in left.index:
        if index[0] in right_subjects:
            subject = right.loc[index[0]]
            date = closest_date(subject, index)
            matching_image = right.loc[index[0], date]
            image = left.loc[[index]]
            image["Image ID_r"] = matching_image.values[0]
            matching_images.append(image)
        else:
            missing_match.append(index)

    matching_images_df = pd.concat(matching_images)
    matching_images_df = matching_images_df.rename(columns={"Image ID": "Image ID_l"})

    if missing_match:
        missing_match_str = str(set(missing_match))
        message = "Could not find matching images for:" + missing_match_str
        warnings.warn(message, stacklevel=1)

    return matching_images_df
