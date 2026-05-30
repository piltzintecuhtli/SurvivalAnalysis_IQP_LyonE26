import streamlit as st
import pandas as pd
from lifelines import KaplanMeierFitter
import altair as alt

from analysisFunctions import *

file = st.file_uploader("Upload dataset here:", type="csv", accept_multiple_files=False, width="stretch")

# Data reading :
# • Offer the possibility to choose the CSV data format (formats: UTF8, Latin, ...).
# • Check that a patient appears only once in the data file. Delete duplicate rows for patients with "Event_Observed=0".

if file is not None:
    st.write("Uploaded file successfully!")
    st.write("Data:")
    df = pd.read_csv(file)
    df

    # choose event and event observed columns
    # dataframe column names
    colNames = list(df)

    st.write("Choose the event column")
    eventCol = selectWithDefault(df, colNames, "Time_to_Event")

    colNames.remove(eventCol)

    st.write("Choose the event observed column")
    eventObservedCol = selectWithDefault(df, colNames, "Event_Observed")

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
    df = replaceWithAverages(df)

    # TODO: highlight all cells that had their values replaced by a mean
    # df


    # Print table with highlighted replaced values

    # Ask user for columns to group
    groupCols = selectGroupingsWithDefault(df, colNames)

    # Add group columns
    groupColsIndices = []
    groupNames = []
    groupData = []
    for col in groupCols:
        # if col is age, do age things
        if col == "Age":
            ageGroup = []
            groupNames.append("Age_Group")
            colNames.remove("Age")
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
            colNames.remove("BMI")
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
    for col in groupCols:
        df = df.drop(col, axis=1)
    for i in range(len(groupCols)):
        df.insert(groupColsIndices[i], groupNames[i], groupData[i])
        colNames.insert(groupColsIndices[i], groupNames[i])

    df

    selectedVals = []
    with st.sidebar:
        selectedVals = []
        for col in colNames:
            options = orderOptions(df, col)
            selectedVals.append(st.pills(col, options, selection_mode="multi", default=None))

    # # df with only filtered rows:
    filtereddf = filterDataframe(df, selectedVals, colNames)

    st.write("Filtered Data:")
    filtereddf

    # Survival Analysis with the Kaplan-Meier Method
    # 4. Compare survival according to a criterion(e.g., sex M / F) by plotting Kaplan - Meier curves for each group

    kmf = KaplanMeierFitter()
    kmf.fit(filtereddf[eventCol], filtereddf[eventObservedCol])

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