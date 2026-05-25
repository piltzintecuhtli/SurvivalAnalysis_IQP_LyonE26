import streamlit as st
import pandas as pd
import numpy as np

file = st.file_uploader("Upload dataset here:", type="csv", accept_multiple_files=False, width="stretch")

# Data reading :
# • Propose reading the CSV data file using a dialog box to choose the file.
# • Offer the possibility to choose the CSV data format (formats: UTF8, Latin, ...).
# • Use the CSV file "survival_data_1000.csv" to test the different functions.
# • Select the "Time_to_Event" variable and the "Event_Observed" variable.
# • From the Age variable, create a new variable Age_Group (<50, 50-60, >60).
# • From the BMI variable, create a new variable BMI_Group (<18, 18-26, >26).
# • Check that a patient appears only once in the data file. Delete duplicate rows for patients with
# "Event_Observed=0".
# Application Functionalities
# Handling Missing Data.
# eplace missing data as appropriate (deleting rows, deleting columns, replacing with a mean or median
# value, etc.).

if file is not None:
    st.write("Uploaded file successfully!")
    st.write("Data:")
    df = pd.read_csv(file)
    df

    # choose event and event observed columns
    # dataframe column names
    colNames = list(df)

    st.write("Choose the event column:")
    # TODO: automatically populate with any column named event or time_to_event
    eventCol = st.selectbox("Column names", colNames, accept_new_options=False)
    st.write(df[eventCol])

    colNames.remove(eventCol)

    st.write("Choose the event observed column")
    eventObservedCol = st.selectbox("Column names", colNames, accept_new_options=False)

    colNames.remove(eventObservedCol)

    # Data filtering and replacement

    # Replace empty strings with NaN
    df.replace('', np.nan, inplace=True)
    df

    # Delete rows with missing event/event observed data
    df.dropna(subset=[eventCol, eventObservedCol], inplace=True)
    df

    # highlight empty cells
    st.dataframe(data=df.style.highlight_null('yellow'))


    # Find average of each column and replace missing data with means

    averages = []

    for col in df:
        avg = df[col].mean()
        averages.append(avg)
        st.write(f"{col}: {avg}")
        df[col] = df[col].replace(np.nan, avg)

    df


    # Print table with highlighted replaced values

    # Ask user for columns to group
    # TODO: automatically add Age and BMI cols
    st.write("Choose columns to group:")
    groupCols = st.multiselect("Column names", colNames, accept_new_options=False)

    st.write(groupCols)

    # Add group columns
    for col in groupCols:
        st.write(col)
        # if col is age, do age things
        if col == "Age":
            ageGroup = []
            for item in df[col]:
                if item < 50:
                    ageGroup.append("<50")
                elif 50 <= item <= 60:
                    ageGroup.append("50-60")
                elif item > 60:
                    ageGroup.append(">60")
            st.write(ageGroup)
        # if col is BMi, do BMI things
        if col == "BMI":
            BMIGroup = []
            for item in df[col]:
                if item < 18:
                    BMIGroup.append("<18")
                elif 18 <= item <= 26:
                    BMIGroup.append("18-26")
                elif item > 26:
                    BMIGroup.append(">26")
            st.write(BMIGroup)
        # if col is smth else, ask user for range

    # Drop raw data columns


