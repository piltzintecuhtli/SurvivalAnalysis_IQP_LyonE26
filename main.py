import streamlit as st
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines import NelsonAalenFitter
import altair as alt
from lifelines.statistics import multivariate_logrank_test
from lifelines import CoxPHFitter
from pandas.errors import ParserError

from analysisFunctions import *

colors = ["blue", "red", "yellow", "orange", "green", "purple"]
tabs = ["Data Upload and Visualization", "Missing Data Treatment", "Summary of Statistics",  "Survival Probabilities and Survival Curves", "Cox Regression Model", "Log-Rank Test"]
data_vis, missing_data, stats_sum, probs_and_curves, cox_model, lr_test  = st.tabs(tabs)

col_names = []
all_stats = []

with data_vis:
    st.header("Uploading Data")

    file = st.file_uploader("Upload dataset here:", type="csv", accept_multiple_files=False, width="stretch")

    st.header("Data Visualization")

    if file is not None:
        st.write("Uploaded file successfully!")
        st.write("Data:")
        try:
            df = pd.read_csv(file, on_bad_lines='warn', sep=None, engine='python')
        except ParserError:
            st.write("It seems like your file could not be uploaded. Please ensure your file is encoded using UTF-8 and values are separated with commas.")

        df_filtered = df.copy(deep=True)
        st.dataframe(df)

with missing_data:
    if file is not None:
        # choose event and event observed columns
        # dataframe column names
        col_names = list(df)

        st.write("Choose the event column")
        event_col = select_with_default(df, col_names, "Time_to_Event")

        col_names.remove(event_col)

        st.write("Choose the event observed column")
        event_observed_col = select_with_default(df, col_names, "Event_Observed")

        col_names.remove(event_observed_col)

        # Data filtering and replacement

        # Replace empty strings with NaN
        df = df.replace('', np.nan)

        # Delete rows with missing event/event observed data
        df = df.dropna(subset=[event_col, event_observed_col])

        # Remove duplicate rows
        df_censored = df[df[event_observed_col] == 0]
        df = df[df[event_observed_col] == 1]

        df_censored = df_censored.drop_duplicates()

        df = pd.concat([df, df_censored])

        # highlight empty cells
        st.write("Missing data highlighted")
        df_missing = df.copy(deep=True)
        df_missing = df_missing[df_missing.isnull().any(axis=1)]
        st.dataframe(data=df_missing.style.highlight_null('yellow'))


        # TODO: ERROR HERE
        # TODO: TRY HAVING A LOT OF VARIABLES
        # Find average of each column and replace missing data with means
        df = replace_with_averages(df)

        # Ask user for columns to group
        group_cols = select_groupings_with_default(df, ["Age", "BMI"])

        # Add group columns
        group_cols_indices = []
        group_names = []
        group_data = []
        df_all = df.copy(deep=True)
        for col in group_cols:
            # if col is age, do age things
            if col == "Age":
                bins_age = pd.qcut(x=df[col], q=3, retbins=True, precision=1)
                age_group = []
                group_names.append("Age_Group")
                col_names.remove("Age")
                for item in df[col]:
                    if item < bins_age[1][1]:
                        age_group.append("<" + str(round(bins_age[1][1], 2)))
                    elif bins_age[1][1] <= item <= bins_age[1][2]:
                        age_group.append(str(round(bins_age[1][1], 2)) + "-" + str(round(bins_age[1][2], 2)))
                    elif item > bins_age[1][2]:
                        age_group.append(">" + str(round(bins_age[1][2], 2)))
                group_cols_indices.append(df.columns.get_loc("Age"))
                group_data.append(age_group)
                df_all['Age_Group'] = age_group
            # if col is BMI, do BMI things
            if col == "BMI":
                bins_bmi = pd.qcut(x=df[col], q=3, retbins=True, precision=1)
                bmi_group = []
                group_names.append("BMI_Group")
                col_names.remove("BMI")
                for item in df[col]:
                    if item < bins_bmi[1][1]:
                        bmi_group.append("<" + str(round(bins_bmi[1][1], 2)))
                    elif bins_bmi[1][1] <= item <= bins_bmi[1][2]:
                        bmi_group.append(str(round(bins_bmi[1][1], 2)) + "-" + str(round(bins_bmi[1][2], 2)))
                    elif item > bins_bmi[1][2]:
                        bmi_group.append(">" + str(round(bins_bmi[1][2], 2)))
                group_cols_indices.append(df.columns.get_loc("BMI"))
                group_data.append(bmi_group)
                df_all['BMI_Group'] = bmi_group

        for _ in df_all:
            all_stats.append(0)

        # Drop raw data columns
        for col in group_cols:
            df = df.drop(col, axis=1)

        for i in range(len(group_cols)):
            df.insert(group_cols_indices[i], group_names[i], group_data[i])
            col_names.insert(group_cols_indices[i], group_names[i])

        df

# TODO: LOOK AT WHAT A LOT OF VARIABLES LOOKS LIKE
selected_vals = []
if file is not None:
    with st.sidebar:
        selected_vals = []
        for col in col_names:
            options = order_options(df, col)
            selected_vals.append(st.pills(col, options, selection_mode="multi", default=None))

    # df with only filtered rows:
    df_filtered = df
    for i in range(len(col_names)):
        if not selected_vals[i]:
            selected_vals[i] = find_unique(df.iloc[:, i])

        # get rows with the column's filter
        filteredData = df_filtered.iloc[:, i].isin(selected_vals[i])

        # apply filtered data rows to df
        df_filtered = df_filtered[filteredData]
        # :)

with probs_and_curves:
    st.header("Kaplan-Meier Analysis")

    if file is not None:
        # Survival Analysis with the Kaplan-Meier Method
        if not df_filtered.empty:
            kmf = KaplanMeierFitter()
            kmf.fit(df_filtered[event_col], df_filtered[event_observed_col])

            kmdf = kmf.survival_function_.reset_index()

            df_conf_interval_km = kmf.confidence_interval_.reset_index()

            line = alt.Chart(kmdf).mark_line().encode(
                x='timeline',
                y='KM_estimate'
            )

            band = alt.Chart(df_conf_interval_km.reset_index()).mark_errorband(
                opacity=0.3
            ).encode(
                x="index",
                y="KM_estimate_lower_0.95",
                y2="KM_estimate_upper_0.95"
            )

            line_and_band = line + band
            line_and_band = line_and_band.properties(
                title = "Kaplan-Meier Estimate"
            ).encode(
                alt.X().title("Time to Event"),
                alt.Y().axis(format="%").title("Survival Probability")
            )

            st.altair_chart(line_and_band)

            st.subheader("Table of Survivor Proportions")
            st.write(kmf.survival_function_)

            st.subheader("Kaplan-Meier Calculator")
            # estimated hazard with user input
            st.write("Note: meaningful values will be in the range [0, " + str(round(max(df[event_col]), 2)) + "]")
            number_km = st.text_input("Time to estimate: ", placeholder="0", key="km_calculator_input")
            if number_km is not None:
                try:
                    number_km = float(number_km)
                except ValueError:
                    st.write("You have entered a " + str(type(number_km)) + ". Please enter a number for time.")
                    number_km = 0

            else:
                number_km = 0

            num = kmf.survival_function_at_times(number_km)

            estimated_time_km = round(num.iloc[0], 3)

            st.write("Probability of survival: " + str(estimated_time_km * 100) + "%")

            st.subheader("Compare by Category")
            # pick a category
            category_km = st.pills("Categories", col_names, selection_mode="single", key="km-pills")

            if category_km is not None:
                # get all possible values for the chosen category
                category_values = find_unique(df[category_km])

                # filter by category
                category_dfs_km = []
                for value in category_values:
                    filtered_category = df[df[category_km] == value]
                    category_dfs_km.append(filtered_category)


                # make graphs for all the mini dataframes
                category_graphs_km = []
                for i in range(len(category_dfs_km)):
                    df = category_dfs_km[i]
                    kmf = KaplanMeierFitter()
                    kmf.fit(df[event_col], df[event_observed_col])

                    kmdf = kmf.survival_function_.reset_index()

                    df_conf_interval_km = kmf.confidence_interval_.reset_index()

                    line = alt.Chart(kmdf).mark_line().encode(
                        x='timeline',
                        y='KM_estimate'
                    )

                    band = alt.Chart(df_conf_interval_km.reset_index()).mark_errorband(
                        opacity=0.3
                    ).encode(
                        x="index",
                        y="KM_estimate_lower_0.95",
                        y2="KM_estimate_upper_0.95"
                    )

                    line_and_band = line + band
                    line_and_band = line_and_band.properties(
                        title="Kaplan-Meier Estimate for " + category_km + ": " + str(category_values[i])
                    ).encode(
                        alt.X().title("Time to Event"),
                        alt.Y().axis(format="%").title("Survival Probability"),
                        color = alt.value(colors[i%len(category_dfs_km)])
                    )

                    st.altair_chart(line_and_band)

                    category_graphs_km.append(line_and_band)

                # display all graphs as one big one
                all_graphs_km = category_graphs_km[0]
                for i in range(1, len(category_graphs_km)):
                    all_graphs_km = all_graphs_km + category_graphs_km[i]
                all_graphs_km = all_graphs_km.encode(
                )

                # Create legend
                legend = "Legend: "
                for i in range(len(category_graphs_km)):
                    color = colors[i%len(category_graphs_km)]
                    value = category_values[i]
                    combined  = ":" + color + "[" + color + ": " + str(value) + "]"

                    if i is not len(category_graphs_km) - 1:
                        combined = combined + " | "
                    legend =  legend + combined

                st.altair_chart(all_graphs_km)
                st.write(legend)
            else:
                st.write("Please choose a category")
        else:
            st.write("Please reselect filters; the current ones return no results!")

        st.header("Nelson-Aalen (Hazard Function) Estimation")
        naf = NelsonAalenFitter()
        naf.fit(df_filtered[event_col], df_filtered[event_observed_col])

        df_naf = naf.cumulative_hazard_.reset_index()
        df_naf_conf_interval_km = naf.confidence_interval_.reset_index()

        line = alt.Chart(df_naf).mark_line().encode(
            x='timeline',
            y='NA_estimate'
        )

        band = alt.Chart(df_naf_conf_interval_km).mark_errorband(
            opacity=0.3
        ).encode(
            x='index',
            y='NA_estimate_lower_0.95',
            y2='NA_estimate_upper_0.95'
        )

        line_and_band = (line + band).properties(
            title="Nelson-Aalen Estimator - Hazard Function"
        ).encode(
            alt.X().title("Time since Start Event"),
            alt.Y().title("Cumulative Hazard")
        )

        st.altair_chart(line_and_band)

        st.subheader("Hazard Calculator")
        # estimated hazard with user input
        st.write("Note: meaningful values will be in the range [0, " + str(round(max(df[event_col]), 2)) + "]")
        number = st.text_input("Time to estimate: ", placeholder="0")
        if number is not None:
            try:
                number = float(number)
            except ValueError:
                st.write("You have entered a " + str(type(number)) + ". Please enter a number for time.")
                number = 0

        else:
            number = 0

        num = naf.cumulative_hazard_at_times(number)

        estimated_time = round(num.iloc[0], 3)

        st.write("Cumulative hazard: " + str(estimated_time))
    else:
        st.write("Please upload data.")

with stats_sum:
    st.header("Descriptive Statistics")
    if file is not None:
        all_stats = generate_stats(df_all)

        st.write("Please choose a column:")
        category = st.pills("Categories", list(df_all), selection_mode="single", key="stats-pills")

        if category is not None:
            col = df_all[category]
            substats = all_stats[df_all.columns.get_loc(category)]
            if df_all.dtypes[category] == int or df_all.dtypes[category] == float:
                stats_names = ["Mean", "Median", "Mode", "Min", "25th percentile", "75th percentile", "Max",
                               "Range", "Standard Deviation", "Variation", "Skewness", "Kurtosis"]

                dfStats = pd.DataFrame(data = {'Statistic': stats_names, 'Value': substats[0]})

                st.dataframe(dfStats, hide_index=True, height=((len(stats_names) + 1) * 35 + 3))

                st.write("Outliers: ")
                df_outliers = pd.DataFrame(data={'Outliers': substats[1][1]}, index=substats[1][0])
                st.dataframe(df_outliers, hide_index=True)

            st.write("Frequency and Percentages")

            if df_all.dtypes[category] == int or df_all.dtypes[category] == float:
                df_non_numerical = pd.DataFrame(data = {'Value': substats[2][0], 'Frequency': substats[2][1], 'Percentage': substats[2][3]})
            else:
                df_non_numerical = pd.DataFrame(data = {'Value': substats[0][0], 'Frequency': substats[0][1], 'Percentage': substats[0][3]})

            df_non_numerical = df_non_numerical.sort_values(by=['Value'])
            st.dataframe(df_non_numerical, hide_index=True)

            st.header("Graphical Representation of Variables")
            if category is not None:
                substats = all_stats[df_all.columns.get_loc(category)]
                col = df_all[category]
                st.subheader("Distribution of Values")
                if df_all.dtypes[category] == int or df_all.dtypes[category] == float:
                    # box and whisker plot
                    st.write("Box Plot Representation")
                    chart = alt.Chart(df_all).mark_boxplot(extent="min-max").encode(
                        alt.X(str(category)).scale(zero=False)
                    )
                    st.altair_chart(chart, height=40, theme=None)
                # bar graph
                st.write("Bar Chart Representation")
                values = col
                x, counts = np.unique(values, return_counts=True)
                df_count = pd.DataFrame({str(category): x, "Count": counts})
                df_count = df_count.sort_values(by=[str(category)])

                if df_all.dtypes[category] == int or df_all.dtypes[category] == float:
                    bar_str = str(category) + ":Q"
                    barGraph = alt.Chart(df_count).mark_bar().encode(
                        x=alt.X(bar_str, axis=alt.Axis(tickMinStep=1)),
                        y=alt.Y('Count:Q', axis=alt.Axis(tickMinStep=1))
                    )
                else:
                    bar_str = str(category) + ":N"
                    barGraph = alt.Chart(df_count).mark_bar().encode(
                        x=alt.X(bar_str),
                        y=alt.Y('Count:Q', axis=alt.Axis(tickMinStep=1))
                    )
                st.altair_chart(barGraph)
    else:
        st.write("Please upload a file")

with cox_model:
    st.header("Cox Proportional Hazards Regression")

    if file is not None:
        if not df_filtered.empty:

            st.subheader("Model Configuration")
            st.write("Select covariates to include in the Cox model")
            covariates = st.pills("Covariates", col_names, selection_mode="multi", key="cox-covariates")

            if covariates:
                # coxdf uses selected covariates — drives the model
                coxInputCols = covariates + [event_col, event_observed_col]
                coxdf = df_filtered[coxInputCols].copy(deep=True)

                categorical_cols = coxdf[covariates].select_dtypes(exclude='number').columns.tolist()

                # treat Comorbidities as numeric if present
                if "Comorbidities" in categorical_cols:
                    coxdf["Comorbidities"] = pd.to_numeric(coxdf["Comorbidities"], errors='coerce')
                    categorical_cols.remove("Comorbidities")

                if categorical_cols:
                    df_cox = pd.get_dummies(coxdf, columns=categorical_cols, drop_first=True)

                encoded_covariates = [c for c in df_cox.columns if c not in [event_col, event_observed_col]]

                # predCoxdf uses ALL colNames columns from filtereddf — drives the prediction
                predCovariates = [c for c in col_names if c in df_filtered.columns]
                predInputCols = predCovariates + [event_col, event_observed_col]
                predCoxdf = df_filtered[predInputCols].copy(deep=True)

                predCategoricalCols = predCoxdf[predCovariates].select_dtypes(exclude='number').columns.tolist()
                if "Comorbidities" in predCategoricalCols:
                    predCoxdf["Comorbidities"] = pd.to_numeric(predCoxdf["Comorbidities"], errors='coerce')
                    predCategoricalCols.remove("Comorbidities")
                if predCategoricalCols:
                    predCoxdf = pd.get_dummies(predCoxdf, columns=predCategoricalCols, drop_first=True)

                cph = CoxPHFitter()
                try:
                    cph.fit(df_cox, duration_col=event_col, event_col=event_observed_col)

                    # --- Model Summary ---
                    st.subheader("Model Summary")
                    df_cox_summary = cph.summary.copy()
                    formatCols = {col: "{:.4f}" for col in df_cox_summary.select_dtypes(include='number').columns}
                    st.dataframe(df_cox_summary.style.format(formatCols))

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
                    cox_summary = cph.summary[["coef", "coef lower 95%", "coef upper 95%"]].reset_index()
                    cox_summary.columns = ["covariate", "coef", "lower", "upper"]
                    cox_summary["direction"] = cox_summary["coef"].apply(lambda x: "Positive" if x > 0 else "Negative")

                    points = alt.Chart(cox_summary).mark_point(filled=True, size=80).encode(
                        x=alt.X("coef:Q", title="Log Hazard Ratio"),
                        y=alt.Y("covariate:N", title="Covariate"),
                        color=alt.Color("direction:N", scale=alt.Scale(
                            domain=["Positive", "Negative"],
                            range=["red", "blue"]
                        ))
                    )

                    errorbars = alt.Chart(cox_summary).mark_errorbar().encode(
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
                    df_baseline = cph.baseline_survival_.reset_index()
                    df_baseline.columns = ["timeline", "baseline_survival"]

                    baseline_line = alt.Chart(df_baseline).mark_line(color="blue").encode(
                        x=alt.X("timeline:Q", title="Time to Event"),
                        y=alt.Y("baseline_survival:Q", title="Survival Probability", scale=alt.Scale(domain=[0, 1]))
                    ).properties(
                        title="Cox Model — Baseline Survival Function"
                    )

                    st.altair_chart(baseline_line, width='stretch')

                    # --- Individual Survival Prediction (sidebar only) ---
                    st.subheader("Individual Survival Prediction")
                    st.write("Use the sidebar to filter the patient profile. The prediction updates automatically.")

                    try:
                        from concurrent.futures import ThreadPoolExecutor, as_completed

                        # build patient profile from means/modes of predCoxdf (sidebar-driven, all covariates)
                        # then restrict to only the encodedCovariates the model was trained on
                        patientInput = {}
                        for cov in encoded_covariates:
                            if cov in predCoxdf.columns:
                                uniqueVals = sorted(predCoxdf[cov].unique())
                                if set(uniqueVals).issubset({0, 1, 0.0, 1.0}):
                                    patientInput[cov] = float(predCoxdf[cov].mode().iloc[0])
                                else:
                                    patientInput[cov] = float(predCoxdf[cov].mean())
                            else:
                                patientInput[cov] = 0.0

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
                                cphBoot.fit(sampleDf, duration_col=event_col, event_col=event_observed_col)
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
                        st.warning("Could not generate prediction for the selected profile. Please try adjusting the sidebar filters.")

                except Exception as e:
                    st.error("Could not fit Cox model: " + str(e))
                    st.write("This may be due to multicollinearity, insufficient data, or non-numeric covariates that could not be encoded.")

            else:
                st.write("Please select at least one covariate to fit the Cox model.")

        else:
            st.write("Please reselect filters; the current ones return no results.")
    else:
        st.write("Please upload data.")

with lr_test:
    st.header("Log-Rank Test")
    if file is not None:
        st.subheader("Compare by Category")
        # pick a category
        lr_category = st.pills("Categories", col_names, selection_mode="single", key="lr-pills")

        if lr_category is not None:
            df_vis = df.copy(deep=True)
            # get all possible values for the chosen category
            category_values = find_unique(df_vis[lr_category])

            # filter by category
            category_dfs = []
            for value in category_values:
                filtered_category = df_vis[df_vis[lr_category] == value]
                category_dfs.append(filtered_category)

            # format data for analysis
            durations = []
            events = []
            group = []
            for i in range(len(category_dfs)):
                df = category_dfs[i]
                survival_times = list(df[event_col])
                survivalObserved = list(df[event_observed_col])
                groupNum = i

                for j in range(len(survival_times)):
                    durations.append(survival_times[j])
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
                st.write("Null hypothesis is retained; " + lr_category + " does not affect survival time")
            else:
                st.write("Null hypothesis is rejected; " + lr_category + " affect(s) survival time")
        else:
            st.write("Please select a category!")
    else:
        st.write("Please upload data.")
