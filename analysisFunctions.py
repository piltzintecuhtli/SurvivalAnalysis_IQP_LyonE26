import numpy as np
import streamlit as st

def find_mode(col):
    """
    Finds the first mode of the data
    :param col: an iterable object to find the mode of
    :return: the first mode in col
    """
    values = []
    values_count = []
    for value in col:
        if value is not None or value is not np.nan:
            if value in values:
                index = values.index(value)
                values_count[index] += 1
            else:
                values.append(value)
                values_count.append(0)
    modeIndex = 0
    for i in range(0, len(values)):
        if values_count[i] > values_count[modeIndex]:
            modeIndex = i
    return values[modeIndex]

def find_unique(col):
    """
    Finds all unique values in data, ignoring None and NaN values
    :param col: an iterable object
    :return: a list of all unique values in col
    """
    vals = []
    for value in col:
        if value not in vals and (value is not None or value is not np.nan):
            vals.append(value)
    return vals

def select_with_default(df, col_names, col_name):
    """
    Creates a selectbox with any applicable autofill items
    :param df: a DataFrame with columns, from which the autofill items derive
    :param col_names: a list of all possible options for the selectbox to contain
    :param col_name: the column name to autofill the selectboc with, if the column name is in df
    :return: the selectbox object
    """
    has_col = False

    for col in df:
        if col == col_name:
            has_col = df.columns.get_loc(col_name)
            if has_col > len(col_names) - 1:
                has_col = len(col_names) - 1
    if has_col is not False:
        event_col = st.selectbox("Column names", col_names, accept_new_options=False, index=has_col)
    else:
        event_col = st.selectbox("Column names", col_names, accept_new_options=False)

    return event_col

def replace_with_averages(df):
    """
    Replaces all empty cells in a DataFrame with the mean (for numerical values) or first mode (for non-numerical values) of its column.
    :param df: the DataFrame
    :return: df with empty cells
    """
    for col in df:
        if df[col].dtypes == float or df[col].dtypes == int:
            avg = df[col].mean()
        else:
            avg = find_mode(df[col])
        df[col] = df[col].replace(np.nan, avg)

    return df

def select_groupings_with_default(df, col_names):
    """
    Creates a multiselect dropdown with any applicable autofills (out of “Age” and “BMI”)
    :param df: the DataFrame with columns that may or may not have columns specified by col_names to autofill the dropdown.
    :param col_names: a list of Strings representing potential column names in df that the dropdown should autofill with, if those columns exist.
    :return: A multiselect object autofilled with columns “Age” and “BMI,” if they are in col_names and if they are present in df.
    """
    st.write("Choose columns to group:")

    add_indices = []

    age_col = False
    bmi_col = False

    for col in df:
        if col == "Age":
            age_col = "Age"
        if col == "BMI":
            bmi_col = "BMI"

    if age_col is not False:
        add_indices.append(age_col)
    if bmi_col is not False:
        add_indices.append(bmi_col)

    if add_indices:  # if there are columns to automatically account for
        group_cols = st.multiselect("Column names", col_names, accept_new_options=False, default=add_indices)
    else:
        group_cols = st.multiselect("Column names", col_names, accept_new_options=False)

    return group_cols

def order_options(df, col):
    """
    Sorts the unique values of a column
    :param df: the DataFrame to get values from
    :param col: a String representing the name of a column in the DataFrame to sort
    :return: A sorted list of the unique values from the specified DataFrame column.
    """
    options = find_unique(df[col])
    match col:
        case "Age_Group":
            options = ["<50", "50-60", ">60"]
        case "Physical_Activity":
            options = ["Low", "Moderate", "High"]
        case "Comorbidities":
            options = sorted(options)
        case "BMI_Group":
            options = ["<18", "18-26", ">26"]

    return options

def generate_stats(df):
    """
    Generates descriptive statistics for a DataFrame
    :param df: the DataFrame to generate statistics on
    :return: A multi-dimensional list containing the descriptive statistics of all columns in df. Each list item is organized as so:
Numerical columns:
[
[mean, median, mode, min, 25th percentile, 75th percentile, max, range, std, variation, skewness, kurtosis],
[[indicies from 0 to the number of outliers - 1], [outliers]],
[[unique values], [counts of each unique value], [percentages], [percentages
formatted]]
]
Non-numerical columns:
[
[[unique values], [counts of each unique value], [percentages], [percentages
formatted]]
]

    """
    all_stats = []
    
    for _ in df:
        all_stats.append(0)

    for cat in df:
        stats = []
        col = df[cat]
        if df.dtypes[cat] == int or df.dtypes[cat] == float:
            # mean
            stat_mean = col.mean()
            # median
            stat_median = col.median()
            # mode
            stat_mode = float(col.mode().iloc[0])
            # min
            stat_min = col.min()
            # 25th precentile
            stat_percentile1 = col.quantile(0.25)
            # 75th percentile
            stat_percentile2 = col.quantile(0.75)
            # max
            stat_max = float(col.max())
            # range
            stat_range = stat_max - stat_min
            # std
            stat_std = col.std()
            # outliers
            iqr = stat_percentile2 - stat_percentile1
            oulier_lower_bound = stat_percentile1 - (1.5 * iqr)
            oulier_upper_bound = stat_percentile2 + (1.5 * iqr)

            outliers = []
            index = []
            i = 0
            for num in col:
                if (num < oulier_lower_bound or num > oulier_upper_bound) and num not in outliers:
                    index.append(i)
                    outliers.append(num)
                    i += 1
            outliers = sorted(outliers)

            # variation
            stat_variation = col.var()
            # skewness?
            stat_skewness = col.skew()
            # kurtosis
            stat_kurtosis = col.kurtosis()

            stats.append([stat_mean, stat_median, stat_mode, stat_min, stat_percentile1, stat_percentile2, stat_max,
                          stat_range, stat_std, stat_variation, stat_skewness, stat_kurtosis])

            stats.append([index, outliers])

        # frequencies and percentages
        unique = find_unique(col)
        counts = []  # = frequency
        total = len(col)

        for _ in unique:
            counts.append(0)

        for data in col:
            index = unique.index(data)
            counts[index] += 1

        percentages = []
        for i in counts:
            percentages.append(i / total)

        percentage_formatted = []
        for i in percentages:
            percentage_formatted.append(str(round(i * 100, 3)) + '%')

        stats.append([unique, counts, percentages, percentage_formatted])

        all_stats[df.columns.get_loc(cat)] = stats

    return all_stats