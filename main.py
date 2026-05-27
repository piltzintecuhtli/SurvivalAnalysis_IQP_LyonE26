import streamlit as st
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
import altair as alt
from altair.datasets import data

from dataFilteringFunctions import findMode

file = st.file_uploader("Upload dataset here:", type="csv", accept_multiple_files=False, width="stretch")

# Data reading :
# • Offer the possibility to choose the CSV data format (formats: UTF8, Latin, ...).
# • Select the "Time_to_Event" variable and the "Event_Observed" variable.
# • Check that a patient appears only once in the data file. Delete duplicate rows for patients with
# "Event_Observed=0".

if file is not None:
    st.write("Uploaded file successfully!")
    st.write("Data:")
    df = pd.read_csv(file)
    df

    # choose event and event observed columns
    # dataframe column names
    colNames = list(df)

    st.write("Choose the event column:")

    tte = False

    for col in df:
        if col == "Time_to_Event":
            tte = df.columns.get_loc("Time_to_Event")
    if tte is not False:
        eventCol = st.selectbox("Column names", colNames, accept_new_options=False, index=tte)
    else:
        eventCol = st.selectbox("Column names", colNames, accept_new_options=False)

    colNames.remove(eventCol)

    st.write("Choose the event observed column")

    eo = False

    for col in df:
        if col == "Event_Observed":
            eo = df.columns.get_loc("Event_Observed")
            if eo > len(colNames) - 1:
                eo = eo - 1
    if eo is not False:
        eventObservedCol = st.selectbox("Column names", colNames, accept_new_options=False, index=eo)
    else:
        eventObservedCol = st.selectbox("Column names", colNames, accept_new_options=False)

    colNames.remove(eventObservedCol)

    # Data filtering and replacement

    # Replace empty strings with NaN
    df = df.replace('', np.nan)

    # Delete rows with missing event/event observed data
    df = df.dropna(subset=[eventCol, eventObservedCol])

    # highlight empty cells
    # TODO: find empty cells and mark locations in an array
    st.write("Missing data highlighted")
    st.dataframe(data=df.style.highlight_null('yellow'))


    # Find average of each column and replace missing data with means

    averages = []

    for col in df:
        if df[col].dtypes is float or df[col].dtypes is int:
            avg = df[col].mean()
        else:
            avg = findMode(df[col])
        averages.append(avg)
        df[col] = df[col].replace(np.nan, avg)

    # TODO: highlight all cells that had their values replaced by a mean
    # df


    # Print table with highlighted replaced values

    # Ask user for columns to group
    st.write("Choose columns to group:")
    # TODO: automatically add Age and BMI cols
    ageCol = False
    BMICol = False

    addIndices = []

    for col in df:
        if col == "Age":
            ageCol = "Age"
        if col == "BMI":
            BMICol = "BMI"

    if ageCol is not False:
        addIndices.append(ageCol)
    if BMICol is not False:
        addIndices.append(BMICol)

    if addIndices: # if there are columns to automatically account for
        groupCols = st.multiselect("Column names", colNames, accept_new_options=False, default=addIndices)
    else:
        groupCols = st.multiselect("Column names", colNames, accept_new_options=False)

    # Add group columns
    groupColsIndices = []
    groupNames = []
    groupData = []
    for col in groupCols:
        # if col is age, do age things
        if col == "Age":
            ageGroup = []
            groupNames.append("Age_Group")
            for item in df[col]:
                if item < 50:
                    ageGroup.append("<50")
                elif 50 <= item <= 60:
                    ageGroup.append("50-60")
                elif item > 60:
                    ageGroup.append(">60")
            groupColsIndices.append(df.columns.get_loc("Age"))
            groupData.append(ageGroup)
        # if col is BMI, do BMI things
        if col == "BMI":
            BMIGroup = []
            groupNames.append("BMI_Group")
            for item in df[col]:
                if item < 18:
                    BMIGroup.append("<18")
                elif 18 <= item <= 26:
                    BMIGroup.append("18-26")
                elif item > 26:
                    BMIGroup.append(">26")
            groupColsIndices.append(df.columns.get_loc("BMI"))
            groupData.append(BMIGroup)
        # TODO: if col is smth else, ask user for range

    # Drop raw data columns
    # TODO: add columns to a hide list instead
    for col in groupCols:
        df = df.drop(col, axis=1)
    for i in range(len(groupCols)):
        df.insert(groupColsIndices[i], groupNames[i], groupData[i])

    df

    # Survival Analysis with the Kaplan-Meier Method
    # 1. Estimate the survival probability and the confidence interval using the Kaplan - Meier method.
    # 2. Display the table of survivor proportions at each time t(t=0, ..., n).
    # 3. Plot the overall survival curve with its confidence interval.
    # 4. Compare survival according to a criterion(e.g., sex M / F) by plotting Kaplan - Meier curves for each group

    kmf = KaplanMeierFitter()
    kmf.fit(df[eventCol], df[eventObservedCol])
    kmdf = kmf.survival_function_.reset_index()

    confIntervalDf = kmf.confidence_interval_.reset_index()

    line = alt.Chart(kmdf).mark_line().encode(
        x='timeline',
        y='KM_estimate'
    )

    band = alt.Chart(confIntervalDf.reset_index()).mark_errorband(
        opacity=0.3
    ).encode(
        x="index",
        y="KM_estimate_lower_0.95",
        y2="KM_estimate_upper_0.95"
    )

    newchart = line + band
    newchart = newchart.properties(
        title = "Kaplan-Meier Estimate"
    ).encode(
        alt.X().title("Time to Event"),
        alt.Y().axis(format="%").title("Probability")
    )

    st.altair_chart(newchart)

    st.write("Table of Survivor Proportions")
    st.write(kmf.survival_function_)