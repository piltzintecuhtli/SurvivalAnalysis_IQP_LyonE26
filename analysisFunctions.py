import numpy as np
import streamlit as st
from lifelines import KaplanMeierFitter
import altair as alt

def findMode(col):
    values = []
    valuesCount = []
    for value in col:
        if value in values and (value is not None or value is not np.nan):
            index = values.index(value)
            valuesCount[index] += 1
        else:
            values.append(value)
            valuesCount.append(0)
    modeIndex = 0
    for i in range(0, len(values)):
        if valuesCount[i] > valuesCount[modeIndex]:
            modeIndex = i
    return values[modeIndex]

def findUnique(col):
    vals = []
    for value in col:
        if value not in vals and (value is not None or value is not np.nan):
            vals.append(value)
    return vals

def selectWithDefault(df, colNames, colName):
    hasCol = False

    for col in df:
        if col == colName:
            hasCol = df.columns.get_loc(colName)
            if hasCol > len(colNames) - 1:
                hasCol = len(colNames) - 1
    if hasCol is not False:
        eventCol = st.selectbox("Column names", colNames, accept_new_options=False, index=hasCol)
    else:
        eventCol = st.selectbox("Column names", colNames, accept_new_options=False)

    return eventCol

def replaceWithAverages(df):
    averages = []

    for col in df:
        if df[col].dtypes is float or df[col].dtypes is int:
            avg = df[col].mean()
        else:
            avg = findMode(df[col])
        averages.append(avg)
        df[col] = df[col].replace(np.nan, avg)

    return df

def filterDataframe(df, filters, colNames):
    # df with only filtered rows:
    filtereddf = df
    for i in range(len(colNames)):
        if not filters[i]:
            filters[i] = findUnique(df.iloc[:, i])

        # get rows with the column's filter
        filteredData = filtereddf.iloc[:, i].isin(filters[i])

        # apply filtered data rows to df
        filtereddf = filtereddf[filteredData]
        # :)

        return filtereddf

def selectGroupingsWithDefault(df, colNames):
    st.write("Choose columns to group:")

    addIndices = []

    ageCol = False
    BMICol = False

    for col in df:
        if col == "Age":
            ageCol = "Age"
        if col == "BMI":
            BMICol = "BMI"

    if ageCol is not False:
        addIndices.append(ageCol)
    if BMICol is not False:
        addIndices.append(BMICol)

    if addIndices:  # if there are columns to automatically account for
        groupCols = st.multiselect("Column names", colNames, accept_new_options=False, default=addIndices)
    else:
        groupCols = st.multiselect("Column names", colNames, accept_new_options=False)

    return groupCols

def orderOptions(df, col):
    options = findUnique(df[col])
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