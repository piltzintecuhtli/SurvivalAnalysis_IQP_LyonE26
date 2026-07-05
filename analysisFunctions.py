import numpy as np
import streamlit as st

def find_mode(col):
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
    vals = []
    for value in col:
        if value not in vals and (value is not None or value is not np.nan):
            vals.append(value)
    return vals

def select_with_default(df, col_names, col_name):
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
    averages = []

    for col in df:
        if df[col].dtypes is float or df[col].dtypes is int:
            avg = df[col].mean()
        else:
            avg = find_mode(df[col])
        averages.append(avg)
        df[col] = df[col].replace(np.nan, avg)

    return df

def select_groupings_with_default(df, col_names):
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