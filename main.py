import streamlit as st
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import NelsonAalenFitter
import altair as alt
from lifelines.statistics import multivariate_logrank_test
from lifelines import CoxPHFitter

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
            cat_km = st.pills("Categories", colNames, selection_mode="single", key="km-pills")

            if cat_km is not None:
                # get all possible values for the chosen category
                categoryValues = findUnique(df[cat_km])

                # filter by category
                categoryDataframes = []
                for value in categoryValues:
                    filteredCategory = df[df[cat_km] == value]
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
                        title="Kaplan-Meier Estimate for " + cat_km
                    ).encode(
                        alt.X().title("Time to Event"),
                        alt.Y().axis(format="%").title("Survival Probability"),
                        color = alt.value(colors[i%len(categoryDataframes)])
                    )

                    st.write("KM graph for those with a/an " + cat_km + " of " + str(categoryValues[i]))
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
    lr_category = st.pills("Categories", colNames, selection_mode="single", key="lr-pills")

    if lr_category is not None:
        df_vis = df.copy(deep=True)
        # get all possible values for the chosen category
        categoryValues = findUnique(df_vis[lr_category])

        # filter by category
        categoryDataframes = []
        for value in categoryValues:
            filteredCategory = df_vis[df_vis[lr_category] == value]
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

        st.write("Test statistic: " + str(round(result.test_statistic, 5)))
        st.write("p-value: " + str(round(result.p_value, 5)))

        if result.p_value > 0.05:
            st.write("Null hypothesis is retained; " + lr_category + " does not affect survival time" )
        else:
            st.write("Null hypothesis is rejected; " + lr_category + " affect(s) survival time")
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

        for cat in dfAll:
            stats = []
            col = dfAll[cat]
            if dfAll.dtypes[cat] == int or dfAll.dtypes[cat] == float:
                # mean
                mean = col.mean()
                # median
                median = col.median()
                # mode
                mode = float(col.mode().iloc[0])
                # min
                min_ = float(col.min())
                # 25th precentile
                percentile1 = col.quantile(0.25)
                # 75th percentile
                percentile2 = col.quantile(0.75)
                # max
                max_ = float(col.max())
                # range
                range_ = max_ - min_
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

                # variation
                variation = col.var()
                # skewness?
                skewness = col.skew()
                # kurtosis
                kurtosis = col.kurtosis()

                stats.append([mean, median, mode, min_, percentile1, percentile2, max_, range_, std, variation, skewness,
                         kurtosis])

                stats.append([index, outliers])

            # frequencies and percentages
            unique = findUnique(col)
            counts = []  # = frequency
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

            stats.append([unique, counts, percentages, fancyPercentage])

            allStats[dfAll.columns.get_loc(cat)] = stats

        if category is not None:
            col = dfAll[category]
            substats = allStats[dfAll.columns.get_loc(category)]
            if dfAll.dtypes[category] == int or dfAll.dtypes[category] == float:
                statsNames = ["Mean", "Median", "Mode", "Min", "25th percentile", "75th percentile", "Max", "Range",
                              "Standard Deviation", "Variation", "Skewness", "Kurtosis"]

                dfStats = pd.DataFrame(data = {'Statistic': statsNames, 'Value': substats[0]})

                st.dataframe(dfStats, hide_index=True, height=((len(statsNames) + 1) * 35 + 3))

                st.write("Outliers: ")
                dfOutliers = pd.DataFrame(data={'Outliers': substats[1][1]}, index=substats[1][0])
                st.dataframe(dfOutliers, hide_index=True)

                stats.append(outliers)

            st.write("Frequency and Percentages")

            if dfAll.dtypes[category] == int or dfAll.dtypes[category] == float:
                dfNonNumerical = pd.DataFrame(data = {'Value': substats[2][0], 'Frequency': substats[2][1], 'Percentage': substats[2][3]})
            else:
                dfNonNumerical = pd.DataFrame(data = {'Value': substats[0][0], 'Frequency': substats[0][1], 'Percentage': substats[0][3]})
            dfNonNumerical = dfNonNumerical.sort_values(by=['Value'])
            st.dataframe(dfNonNumerical, hide_index=True)
    else:
        st.write("Please upload a file")

with graphRep:
    st.header("Graphical Representation of Variables")
    if file is not None:
        st.write("Please choose a column:")
        category_gr = st.pills("Categories", list(dfAll), selection_mode="single", key="graphrep-pills")

        stats = []

        if category_gr is not None:
            substats = allStats[dfAll.columns.get_loc(category_gr)]
            col = dfAll[category_gr]
            st.subheader("Distribution of Values")
            if dfAll.dtypes[category_gr] == int or dfAll.dtypes[category_gr] == float:
                # box and whisker plot
                st.write("Box Plot Representation")
                chart = alt.Chart(dfAll).mark_boxplot(extent="min-max").encode(
                    alt.X(str(category_gr)).scale(zero=False)
                )
                st.altair_chart(chart, height=40, theme=None)
            # bar graph
            st.write("Bar Chart Representation")
            values = col
            x, counts = np.unique(values, return_counts=True)
            df_count = pd.DataFrame({str(category_gr): x, "Count": counts})
            df_count = df_count.sort_values(by=[str(category_gr)])

            if dfAll.dtypes[category_gr] == int or dfAll.dtypes[category_gr] == float:
                bar_str = str(category_gr) + ":Q"
                barGraph = alt.Chart(df_count).mark_bar().encode(
                    x=bar_str,
                    y=alt.Y('Count:Q', axis=alt.Axis(tickMinStep=1))
                )
            else:
                bar_str = str(category_gr) + ":N"
                barGraph = alt.Chart(df_count).mark_bar().encode(
                    x=bar_str,
                    y=alt.Y('Count:Q', axis=alt.Axis(tickMinStep=1))
                )
            st.altair_chart(barGraph)
    else:
        st.write("Please upload a file")

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
                alt.X().title("Time since Start Event (weeks)"),
                alt.Y().title("Cumulative Hazard")
            )

            st.altair_chart(newchart)

            st.subheader("Hazard Calculator")
            # estimated hazard with user input
            number = st.text_input("Time to estimate: ", placeholder="0")
            if number is not None:
                try:
                    number = float(number)
                except ValueError:
                    st.write("You have entered a " + str(type(number)) + ". Please enter a number for time.")
                    number = 0

            else:
                number = 0
            units = st.selectbox("Units: ", ["Months", "Years"])

            if units == "Months":
                number = number * 4
            else:
                number = number * 52

            num = naf.cumulative_hazard_at_times(number)

            estimated_time = round(num.iloc[0], 3)

            st.write("Cumulative hazard: " + str(estimated_time))
        else:
            st.write("Please reselect filters; the current ones return no results!")
    else:
        st.write("Please upload a file")

with coxModel:
    st.header("Cox Proportional Hazards Regression")

    if file is not None:
        if not filtereddf.empty:

            st.subheader("Model Configuration")
            st.write("Select covariates to include in the Cox model")
            covariates = st.pills("Covariates", colNames, selection_mode="multi", key="cox-covariates")

            if covariates:
                coxInputCols = covariates + [eventCol, eventObservedCol]
                coxdf = filtereddf[coxInputCols].copy(deep=True)

                categoricalCols = coxdf[covariates].select_dtypes(exclude='number').columns.tolist()

                # treat Comorbidities as numeric if present
                if "Comorbidities" in categoricalCols:
                    coxdf["Comorbidities"] = pd.to_numeric(coxdf["Comorbidities"], errors='coerce')
                    categoricalCols.remove("Comorbidities")

                if categoricalCols:
                    coxdf = pd.get_dummies(coxdf, columns=categoricalCols, drop_first=True)

                encodedCovariates = [c for c in coxdf.columns if c not in [eventCol, eventObservedCol]]

                cph = CoxPHFitter()
                try:
                    cph.fit(coxdf, duration_col=eventCol, event_col=eventObservedCol)

                    # --- Model Summary ---
                    st.subheader("Model Summary")
                    summaryDf = cph.summary.copy()
                    formatCols = {col: "{:.4f}" for col in summaryDf.select_dtypes(include='number').columns}
                    st.dataframe(summaryDf.style.format(formatCols))

                    st.write("Concordance Index: " + str(round(cph.concordance_index_, 4)))

                    # --- Significance of Covariates ---
                    st.subheader("Significance of Covariates")
                    for covariate in cph.summary.index:
                        pval = cph.summary.loc[covariate, "p"]
                        hr = cph.summary.loc[covariate, "exp(coef)"]
                        if pval <= 0.05:
                            st.write(
                                f"**{covariate}** is statistically significant (p={round(pval, 4)}), "
                                f"with a hazard ratio of {round(hr, 4)}."
                            )
                        else:
                            st.write(
                                f"**{covariate}** is not statistically significant (p={round(pval, 4)})."
                            )

                    # --- Log Hazard Ratio Plot ---
                    st.subheader("Log Hazard Ratio Plot")
                    coxSummary = cph.summary[["coef", "coef lower 95%", "coef upper 95%"]].reset_index()
                    coxSummary.columns = ["covariate", "coef", "lower", "upper"]
                    coxSummary["direction"] = coxSummary["coef"].apply(lambda x: "Positive" if x > 0 else "Negative")

                    points = alt.Chart(coxSummary).mark_point(filled=True, size=80).encode(
                        x=alt.X("coef:Q", title="Log Hazard Ratio"),
                        y=alt.Y("covariate:N", title="Covariate"),
                        color=alt.Color("direction:N", scale=alt.Scale(
                            domain=["Positive", "Negative"],
                            range=["red", "blue"]
                        ))
                    )

                    errorbars = alt.Chart(coxSummary).mark_errorbar().encode(
                        x=alt.X("lower:Q", title="Log Hazard Ratio"),
                        x2="upper:Q",
                        y=alt.Y("covariate:N", title="Covariate")
                    )

                    rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(
                        strokeDash=[4, 4], color="gray"
                    ).encode(x="x:Q")

                    forestPlot = (errorbars + points + rule).properties(
                        title="Forest Plot - Log Hazard Ratio with 95% CI"
                    )

                    st.altair_chart(forestPlot, width='stretch')

                    # --- Baseline Survival Function ---
                    st.subheader("Baseline Survival Function")
                    baselinedf = cph.baseline_survival_.reset_index()
                    baselinedf.columns = ["timeline", "baseline_survival"]

                    baselineLine = alt.Chart(baselinedf).mark_line(color="blue").encode(
                        x=alt.X("timeline:Q", title="Time to Event"),
                        y=alt.Y("baseline_survival:Q", title="Survival Probability", scale=alt.Scale(domain=[0, 1]))
                    ).properties(
                        title="Cox Model — Baseline Survival Function"
                    )

                    st.altair_chart(baselineLine, width='stretch')

                    # --- Individual Survival Prediction ---
                    st.subheader("Individual Survival Prediction")
                    st.write("Enter covariate values to predict survival for a specific patient profile:")

                    formKey = "cox_prediction_form_" + "_".join(encodedCovariates).replace("<", "lt").replace(">", "gt").replace("-", "to").replace(" ", "_")
                    with st.form(formKey):
                        patientInput = {}
                        inputCols = st.columns(int(min(len(encodedCovariates), 3)))
                        for i, cov in enumerate(encodedCovariates):
                            with inputCols[i % int(min(len(encodedCovariates), 3))]:
                                uniqueVals = sorted(coxdf[cov].unique())
                                if cov == "Comorbidities":
                                    patientInput[cov] = float(st.selectbox(
                                        cov, options=[0, 1, 2, 3, 4, 5]
                                    ))
                                elif set(uniqueVals).issubset({0, 1, 0.0, 1.0}):
                                    selection = st.selectbox(cov, options=["No", "Yes"])
                                    patientInput[cov] = 1.0 if selection == "Yes" else 0.0
                                else:
                                    patientInput[cov] = st.number_input(
                                        cov, value=float(coxdf[cov].mean())
                                    )
                        submitted = st.form_submit_button("Predict")

                    if submitted:
                        try:
                            from concurrent.futures import ThreadPoolExecutor, as_completed

                            patientDf = pd.DataFrame([patientInput])
                            survivalPred = cph.predict_survival_function(patientDf)

                            predDf = pd.DataFrame({
                                "timeline": survivalPred.index.astype(float),
                                "survival": survivalPred.iloc[:, 0].astype(float).values
                            }).reset_index(drop=True)

                            # bootstrap confidence intervals
                            nBootstrap = 50

                            def runBootstrap(_):
                                try:
                                    sampleDf = coxdf.sample(n=len(coxdf), replace=True)
                                    cphBoot = CoxPHFitter()
                                    cphBoot.fit(sampleDf, duration_col=eventCol, event_col=eventObservedCol)
                                    bootPred = cphBoot.predict_survival_function(patientDf)
                                    return bootPred.reindex(survivalPred.index).iloc[:, 0].values
                                except:
                                    return None

                            bootstrapPreds = []
                            with ThreadPoolExecutor(max_workers=4) as executor:
                                futures = [executor.submit(runBootstrap, i) for i in range(nBootstrap)]
                                for future in as_completed(futures):
                                    result = future.result()
                                    if result is not None:
                                        bootstrapPreds.append(result)

                            if len(bootstrapPreds) > 0:
                                bootstrapDf = pd.DataFrame(bootstrapPreds)
                                predDf["lower"] = bootstrapDf.quantile(0.025).values
                                predDf["upper"] = bootstrapDf.quantile(0.975).values
                            else:
                                predDf["lower"] = predDf["survival"]
                                predDf["upper"] = predDf["survival"]

                            line = alt.Chart(predDf).mark_line(color="green").encode(
                                x=alt.X("timeline:Q", title="Time to Event"),
                                y=alt.Y("survival:Q", title="Survival Probability", scale=alt.Scale(domain=[0, 1]))
                            )

                            band = alt.Chart(predDf).mark_area(opacity=0.3, color="green").encode(
                                x=alt.X("timeline:Q", title="Time to Event"),
                                y=alt.Y("lower:Q", scale=alt.Scale(domain=[0, 1])),
                                y2=alt.Y2("upper:Q")
                            )

                            predChart = (band + line).properties(
                                title="Predicted Survival Curve for Patient Profile with 95% CI"
                            )

                            st.altair_chart(predChart, width='stretch')

                            medianSurvival = cph.predict_median(patientDf)
                            if hasattr(medianSurvival, 'iloc'):
                                medianSurvival = medianSurvival.iloc[0]
                            st.write("Estimated median survival time: " + str(round(float(medianSurvival), 2)) + " time units")

                        except Exception as e:
                            st.warning("Could not generate prediction for the selected profile. Please try adjusting the covariate values.")

                except Exception as e:
                    st.error("Could not fit Cox model: " + str(e))
                    st.write("This may be due to multicollinearity, insufficient data, or non-numeric covariates that could not be encoded.")

            else:
                st.write("Please select at least one covariate to fit the Cox model.")

        else:
            st.write("Please reselect filters; the current ones return no results.")
    else:
        st.write("Please upload data.")