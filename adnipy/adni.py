# -*- coding: utf-8 -*-

"""Pandas dataframe extension for ADNI."""

# pylint: disable=R0914

# Third party imports
import pandas as pd


@pd.api.extensions.register_dataframe_accessor("adni")
class ADNI:
    """Dataframe deals with ADNI data.

    This class presents methods, which are designed to work with data from the
    ADNI database.
    """

    DATES = [
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
    INDEX = ["Subject ID", "Image ID"]
    MAPPER = {
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

    def __init__(self, pandas_dataframe):
        """Pass dataframe to the _df attribute of ADNI object.

        Parameters
        ----------
        pandas_dataframe : pd.DataFrame
            This dataframe will be stored in the _df attribute.

        Attributes
        ----------
        _df : pd.DataFrame
            This represents the dataframe object, which calls the method.

        """
        self._df = pandas_dataframe

    def standard_column_names(self):
        """Rename dataframe columns to module standard.

        This function helps when working with multiple dataframes,
        since the same data can have different names.
        It will also call `rid()` on the dataframe.

        Returns
        -------
        pd.DataFrame
            This will have standardized columns names.

        See Also
        --------
        rid

        Examples
        --------
        >>> subjects = pd.DataFrame({"Subject": ["101_S_1001", "102_S_1002"]})
        >>> subjects
              Subject
        0  101_S_1001
        1  102_S_1002
        >>> subjects.adni.standard_column_names()
        "VISCODE2" not included.
           Subject ID   RID
        0  101_S_1001  1001
        1  102_S_1002  1002

        >>> images = pd.DataFrame({"Image": [100001, 100002]})
        >>> images
            Image
        0  100001
        1  100002
        >>> images.adni.standard_column_names()
        "VISCODE2" not included.
           Image ID
        0    100001
        1    100002

        """
        self._df = self._df.rename(mapper=self.MAPPER, axis="columns")

        if "VISCODE2" in self._df.columns:
            self._df["VISCODE"] = self._df["VISCODE2"]
            del self._df["VISCODE2"]

        else:
            print('"VISCODE2" not included.')

        self._df = self.rid()

        return self._df

    def standard_dates(self):
        """Change type of date columns to datetime.

        Returns
        -------
        pd.DataFrame
            Dates will have the appropriate dtype.

        """
        for date in self.DATES:
            if date in self._df.columns:
                self._df.loc[:, date] = pd.to_datetime(self._df.loc[:, date])

        return self._df

    def standard_index(self, index=None):
        """Process dataframes into a standardized format.

        The output is easy to read.
        Applying functions the the output may not work as expected.

        Parameters
        ----------
        index : list of str, default None
            These columns will be the new index.

        Returns
        -------
        pd.DataFrame
            An easy to read dataframe for humans.

        """
        if index is None:
            index = ["Subject ID", "Image ID", "RID", "Visit", "SCANDATE"]

        dataframe = self._df.reset_index()
        dataframe = dataframe.set_index(
            [column for column in index if column in dataframe.columns]
        )

        if "index" in dataframe.columns:
            dataframe = dataframe.drop(columns="index")
        dataframe = dataframe.dropna(axis="columns", how="all")
        dataframe = dataframe.sort_index()

        return dataframe

    def rid(self):
        """Add a roster ID column.

        Will not work if 'RID' is already present or 'Subject ID' is missing.

        Returns
        -------
        pd.DataFrame
            Dataframe with a 'RID' column.

        Examples
        --------
        >>> subjects = {"Subject ID": ["100_S_1000", "101_S_1001"]}
        >>> collection = pd.DataFrame(subjects)
        >>> collection
           Subject ID
        0  100_S_1000
        1  101_S_1001
        >>> collection.adni.rid()
           Subject ID   RID
        0  100_S_1000  1000
        1  101_S_1001  1001

        """
        collection = self._df
        missing_rid = "RID" not in collection.columns
        contains_subject_id = "Subject ID" in collection.columns
        if missing_rid and contains_subject_id:
            collection["RID"] = collection["Subject ID"].map(
                lambda subject_id: pd.to_numeric(subject_id[-4:])
            )

        return collection

    def drop_dynamic(self):
        """Remove images which are dynamic.

        Drops all rows, in which the Description contains 'Dynamic'.

        Returns
        -------
        pd.DataFrame
            All images that are not dynamic.

        """
        no_dynamic = self._df[~self._df["Description"].str.contains("Dynamic")]

        return no_dynamic

    def groups(self, grouped_mci=True):
        """Create a dataframe for each group and save it to a csv file.

        Parameters
        ----------
        grouped_mci : bool, default True
            If true, 'LMCI' and 'EMCI' are treated like 'MCI'.
            However, the original values will stills be in the output.

        Returns
        -------
        dict
            Dictionnairy with a dataframe for each group.

        """
        collection = self._df

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

    def longitudinal(self):
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

        See Also
        --------
        drop_dynamic

        """
        images = self.rid()

        longitudinal = images[images["RID"].duplicated(keep=False)]

        return longitudinal

    def timepoints(self, second="first"):
        """Extract timepoints from a dataframe.

        Parameters
        ----------
        second : {'first' or 'last'}, default 'first'
            'last' to have the latest, 'first' to have the earliest values
            for timepoint 2.

        """
        dataframe = self._df

        dataframe.reset_index(inplace=True)
        dataframe.set_index(self.INDEX, inplace=True)
        dataframe.sort_index(inplace=True)
        if "index" in dataframe.columns:
            dataframe = dataframe.drop(columns="index")
        if "Description" in dataframe.columns:
            raise ValueError(
                "Make sure that 'Description' is not in columns "
                "and only one image per timepoint is in the pd.DataFrame."
            )
        df_subjects = dataframe.index.get_level_values(0)
        df_images = dataframe.index.get_level_values(1)

        timepoints = {}

        if second == "first":
            total_timepoints = max(df_subjects.value_counts())
            for i in range(total_timepoints):
                timepoint = i + 1
                timepoint_df = dataframe[~df_subjects.duplicated(keep="first")]
                timepoint_str = "Timepoint " + str(timepoint)
                timepoints[timepoint_str] = timepoint_df
                dataframe = dataframe[
                    ~df_images.isin(timepoint_df.index.get_level_values(1))
                ]
                df_subjects = dataframe.index.get_level_values(0)
                df_images = dataframe.index.get_level_values(1)

        elif second == "last":
            timepoint_1 = dataframe[~df_subjects.duplicated()]
            timepoints["Timepoint 1"] = timepoint_1
            timepoint_1_images = timepoint_1.index.get_level_values(1)
            after_timepoint_1 = dataframe[~df_images.isin(timepoint_1_images)]

            after_tp_1_images = after_timepoint_1.index.get_level_values(0)
            timepoint_2_last = after_timepoint_1[
                ~after_tp_1_images.duplicated(keep="last")
            ]
            timepoints["Timepoint 2"] = timepoint_2_last

        return timepoints
