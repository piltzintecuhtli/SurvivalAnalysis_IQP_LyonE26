import streamlit as st
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import NelsonAalenFitter
import altair as alt
from lifelines.statistics import multivariate_logrank_test

from analysisFunctions import *

colors = ["blue", "red", "yellow", "orange", "green", "purple"]
tabs = ["Data Visualization", "Missing Data Treatment", "Descriptive Statistics", "Graphical Representation of Variables", "Survival Probabilities and Survival Curves", "Individual Survival Prediction", "Cox Regression Model"]
dataVis, missingData, descStats, graphRep, probsAndCurves, indivPredictions, coxModel = st.tabs(tabs)

colNames = []
allStats = []

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
        dfAll = df.copy(deep=True)
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
                dfAll['Age_Group'] = ageGroup
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
                dfAll['BMI_Group'] = BMIGroup
            # TODO: if col is smth else, ask user for range

        for _ in dfAll:
            allStats.append(0)

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

with dataVis:
    st.header("Log-Rank Analysis")
    st.subheader("Compare by Category")
    # pick a category
    category = st.pills("Categories", colNames, selection_mode="single", key="lr-pills")

    if category is not None:
        # get all possible values for the chosen category
        categoryValues = findUnique(df[category])

        # filter by category
        categoryDataframes = []
        for value in categoryValues:
            filteredCategory = df[df[category] == value]
            categoryDataframes.append(filteredCategory)

        # format data for analysis
        durations = []
        events = []
        group = []
        for i in range(len(categoryDataframes)):
            df = categoryDataframes[i]
            survivalTimes = list(df[eventCol])
            survivalObserved = list(df[eventObservedCol])
            groupNum = i

            for j in range(len(survivalTimes)):
                durations.append(survivalTimes[j])
                events.append(survivalObserved[j])
                group.append(groupNum)

        lrdf = pd.DataFrame({
            'durations': durations,
            'events': events,
            'groups': group
        })

        result = multivariate_logrank_test(lrdf['durations'], lrdf['groups'], lrdf['events'])

        st.write("Test statistic: " + str(result.test_statistic))
        st.write("p-value: " + str(result.p_value))

        if result.p_value > 0.05:
            st.write("Null hypothesis is retained; " + category + " does not affect survival time" )
        else:
            st.write("Null hypothesis is rejected; " + category + " affect(s) survival time")
    else:
        st.write("Please reselect filters; the current ones return no results!")

with descStats:
    st.header("Descriptive Statistics")
    if file is not None:
        st.write("All data:")
        dfAll
        st.write("Please choose a column:")
        category = st.pills("Categories", list(dfAll), selection_mode="single", key="stats-pills")

        stats = []

        if category is not None:
            col = dfAll[category]
            if dfAll.dtypes[category] == int or dfAll.dtypes[category] == float:
                statsNames = ["Mean", "Median", "Mode", "Min", "25th percentile", "75th percentile", "Max", "Range",
                              "Standard Deviation", "Variation", "Skewness", "Kurtosis"]
                # mean
                mean = col.mean()
                # median
                median = col.median()
                # mode
                mode = float(col.mode().iloc[0])
                # min
                min = float(col.min())
                # 25th precentile
                percentile1 = col.quantile(0.25)
                # 75th percentile
                percentile2 = col.quantile(0.75)
                # max
                max = float(col.max())
                # range
                range = max - min
                # std
                std = col.std()
                # outliers
                iqr = percentile2 - percentile1
                outlierBound1 = percentile1 - (1.5 * iqr)
                outlierBound2 = percentile2 + (1.5 * iqr)
                outliers = []
                index = []
                i = 0
                for num in col:
                    if (num < outlierBound1 or num > outlierBound2) and num not in outliers:
                        index.append(i)
                        outliers.append(num)
                    i += 1
                outliers = sorted(outliers)

                # variation?
                variation = col.var()
                # skewness?
                skewness = col.skew()
                # kurtosis
                kurtosis = col.kurtosis()

                stats = [mean, median, mode, min, percentile1, percentile2, max, range, std, variation, skewness, kurtosis]
                dfStats = pd.DataFrame(data = {'Statistic': statsNames, 'Value': stats})

                st.dataframe(dfStats, hide_index=True, height=((len(statsNames) + 1) * 35 + 3))

                st.write("Outliers: ")
                dfOutliers = pd.DataFrame(data={'Outliers': outliers}, index=index)
                st.dataframe(dfOutliers, hide_index=True)

                stats.append(outliers)

            st.write("Frequency and Percentages")
            unique = findUnique(col)
            counts = [] # = frequency
            total = len(col)

            for data in unique:
                counts.append(0)

            for data in col:
                index = unique.index(data)
                counts[index] += 1

            percentages = []
            for i in counts:
                percentages.append(i / total)

            fancyPercentage = []
            for i in percentages:
                fancyPercentage.append(str(round(i * 100, 3)) + '%')

            dfNonNumerical = pd.DataFrame(data = {'Value': unique, 'Frequency': counts, 'Percentage': fancyPercentage})
            dfNonNumerical = dfNonNumerical.sort_values(by=['Value'])
            st.dataframe(dfNonNumerical, hide_index=True)

            stats.append(counts)
            stats.append(percentages)

            if allStats[dfAll.columns.get_loc(category)] == 0:
                allStats[dfAll.columns.get_loc(category)] = stats
    else:
        st.write("Please upload a file")

with graphRep:
    st.write("In progress")

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