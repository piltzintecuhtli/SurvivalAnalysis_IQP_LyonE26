import streamlit as st
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import NelsonAalenFitter
import altair as alt

from analysisFunctions import *

colors = ["blue", "red", "yellow", "orange", "green", "purple"]
tabs = ["Data Visualization", "Missing Data Treatment", "Descriptive Statistics", "Graphical Representation of Variables", "Survival Probabilities and Survival Curves", "Individual Survival Prediction", "Cox Regression Model"]
dataVis, missingData, descStats, graphRep, probsAndCurves, indivPredictions, coxModel = st.tabs(tabs)

with missingData:
    st.header("Uploading and Parsing Data")

    file = st.file_uploader("Upload dataset here:", type="csv", accept_multiple_files=False, width="stretch")

    # Data reading :
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
if file is not None:
    with st.sidebar:
        selectedVals = []
        for col in colNames:
            options = orderOptions(df, col)
            selectedVals.append(st.pills(col, options, selection_mode="multi", default=None))
    # df with only filtered rows:
    filtereddf = df
    for i in range(len(colNames)):
        if not selectedVals[i]:
            selectedVals[i] = findUnique(df.iloc[:, i])

        # get rows with the column's filter
        filteredData = filtereddf.iloc[:, i].isin(selectedVals[i])

        # apply filtered data rows to df
        filtereddf = filtereddf[filteredData]
        # :)

with dataVis:
    st.write("In progress")

with descStats:
    st.write("In progress")

with graphRep:
    st.write("In progress")

with probsAndCurves:
    st.header("Kaplan-Meier Analysis")

    if file is not None:
        st.subheader("Filtered Data:")
        filtereddf

        # Survival Analysis with the Kaplan-Meier Method
        # 4. Compare survival according to a criterion(e.g., sex M / F) by plotting Kaplan - Meier curves for each group
        if not filtereddf.empty:
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
                alt.Y().axis(format="%").title("Survival Probability")
            )

            st.altair_chart(newchart)

            st.subheader("Table of Survivor Proportions")
            st.write(kmf.survival_function_)

            st.subheader("Compare by Category")
            # pick a category
            category = st.pills("Categories", colNames, selection_mode="single")

            if category is not None:
                # get all possible values for the chosen category
                categoryValues = findUnique(df[category])

                # filter by category
                categoryDataframes = []
                for value in categoryValues:
                    filteredCategory = df[df[category] == value]
                    categoryDataframes.append(filteredCategory)


                # make graphs for all the mini dataframes
                categoryGraphs = []
                for i in range(len(categoryDataframes)):
                    df = categoryDataframes[i]
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
                        title="Kaplan-Meier Estimate for " + category
                    ).encode(
                        alt.X().title("Time to Event"),
                        alt.Y().axis(format="%").title("Survival Probability"),
                        color = alt.value(colors[i%len(categoryDataframes)])
                    )

                    st.write("KM graph for those with a/an " + category + " of " + str(categoryValues[i]))
                    st.altair_chart(newchart)

                    categoryGraphs.append(newchart)

                # display all graphs as one big one
                allGraphs = categoryGraphs[0]
                for i in range(1, len(categoryGraphs)):
                    allGraphs = allGraphs + categoryGraphs[i]
                allGraphs = allGraphs.encode(
                )

                # Create legend
                legend = "Legend: "
                for i in range(len(categoryGraphs)):
                    color = colors[i%len(categoryGraphs)]
                    value = categoryValues[i]
                    combined  = ":" + color + "[" + color + ": " + str(value) + "]"

                    if i is not len(categoryGraphs) - 1:
                        combined = combined + " | "
                    legend =  legend + combined

                st.altair_chart(allGraphs)
                st.write(legend)
            else:
                st.write("Please reselect filters; the current ones return no results!")
        else:
            st.write("Please upload data.")

with indivPredictions:
    st.header("Nelson-Aalen (Hazard Function) Estimation")
    if file is not None:
        if not filtereddf.empty:
            naf = NelsonAalenFitter()
            naf.fit(filtereddf[eventCol], filtereddf[eventObservedCol])

            nafdf = naf.cumulative_hazard_.reset_index()
            nafConfIntervaldf = naf.confidence_interval_.reset_index()

            line = alt.Chart(nafdf).mark_line().encode(
                x='timeline',
                y='NA_estimate'
            )

            band = alt.Chart(nafConfIntervaldf).mark_errorband(
                opacity=0.3
            ).encode(
                x='index',
                y='NA_estimate_lower_0.95',
                y2='NA_estimate_upper_0.95'
            )

            newchart = (line + band).properties(
                title="Nelson-Aalen Estimator - Hazard Function"
            ).encode(
                alt.X().title("Time since Start Event"),
                alt.Y().title("Cumulative Hazard")
            )

            st.altair_chart(newchart)

            # estimated hazard with user input
            number = st.text_input("Time to estimate: ")
            if number is None:
                number = float(number)
            else:
                number = 0
            units = st.selectbox("Units: ", ["Months", "Years"])

            if (type(number) is int) or (type(number) is float):
                if units == "Months":
                    number = number * 4
                else:
                    number = number * 52

                num = naf.cumulative_hazard_at_times(number)

                estimated_time = round(num.iloc[0], 2)

                st.write("Cumulative hazard: " + str(estimated_time))

            else:
                st.write("You have entered a " + str(type(number)) + "Please enter a number for time.")
        else:
            st.write("Please reselect filters; the current ones return no results!")

with coxModel:
    st.write("In progress")