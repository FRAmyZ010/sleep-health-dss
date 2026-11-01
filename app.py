"""Sleep Health and Lifestyle decision-support app.

Three sidebar pages share one trained pipeline from model.py:
an individual assessment, the stored recommendation, and an
exploratory view of the training table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from model import (
    BMI_CATEGORIES,
    CLASS_ORDER,
    DISPLAY_NAMES,
    FEATURES,
    GENDERS,
    INPUT_LIMITS,
    OCCUPATIONS,
    TARGET,
    InputError,
    get_bundle,
    predict_record,
)

PAGE_ASSESS = "Individual Sleep Risk Assessment"
PAGE_RESULT = "Assessment Result & Decision Recommendations"
PAGE_EDA = "Interactive Data Analytics & EDA"
PAGES = [PAGE_ASSESS, PAGE_RESULT, PAGE_EDA]

DISORDER_COLORS = {
    "None": "#2563EB",
    "Insomnia": "#D97706",
    "Sleep Apnea": "#DC2626",
}
RISK_STYLE = {
    "Low": ("#1E3A8A", "#DBEAFE"),
    "Medium": ("#9A3412", "#FFEDD5"),
    "High": ("#991B1B", "#FEE2E2"),
}
HEATMAP_COLUMNS = [
    "Stress Level",
    "Sleep Duration",
    "Quality of Sleep",
    "Systolic_BP",
    "Diastolic_BP",
    "Disorder Risk",
]
HEATMAP_LABELS = {
    "Stress Level": "Stress level",
    "Sleep Duration": "Sleep duration",
    "Quality of Sleep": "Sleep quality",
    "Systolic_BP": "Systolic BP",
    "Diastolic_BP": "Diastolic BP",
    "Disorder Risk": "Disorder risk",
}
PLOTLY_CONFIG = {"displaylogo": False, "responsive": True}

STYLE = """
<style>
.stApp {
    background-color: #F8FAFC;
}
[data-testid="stSidebar"] {
    background-color: #F8FAFC;
    border-right: 1px solid #DBEAFE;
}
[data-testid="stHeading"] h1,
[data-testid="stHeading"] h2,
[data-testid="stHeading"] h3,
[data-testid="stHeading"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #1E3A8A !important;
}
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] p {
    color: #0F172A;
}
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stBaseButton-primary"] > button,
.stButton > button[kind="primary"] {
    background-color: #2563EB;
    border: 1px solid #2563EB;
    color: #FFFFFF;
}
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stBaseButton-primary"] > button:hover,
.stButton > button[kind="primary"]:hover {
    background-color: #1E3A8A;
    border-color: #1E3A8A;
    color: #FFFFFF;
}
</style>
"""

st.set_page_config(
    page_title="Sleep Health and Lifestyle Decision Support",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Loading the sleep-disorder model...")
def load_bundle() -> dict:
    """Load the cached pipeline, or train it on first use."""

    return get_bundle()


def open_recommendations() -> None:
    """Switch the sidebar to the stored assessment."""

    st.session_state["nav_page"] = PAGE_RESULT


def main() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)

    try:
        bundle = load_bundle()
    except Exception as exc:
        st.error(f"The model could not be loaded: {exc}")
        st.stop()

    st.sidebar.header("Sleep Health")
    st.sidebar.caption("Lifestyle decision support")
    st.sidebar.caption("1501418 Selected Topics in Data Science and AI")
    page = st.sidebar.radio("Pages", PAGES, key="nav_page")

    if page == PAGE_ASSESS:
        render_assessment(bundle)
    elif page == PAGE_RESULT:
        render_result()
    else:
        render_eda(bundle)

    st.sidebar.divider()
    st.sidebar.caption(
        "Coursework decision-support tool. A clinician makes any diagnosis."
    )


def render_assessment(bundle: dict) -> None:
    """Collect one profile and store predict_record output for page 2."""

    st.header(PAGE_ASSESS)
    st.caption(
        "Enter demographic, lifestyle, and cardiovascular values. "
        "Evaluate Risk stores the screening result for the recommendations page."
    )

    with st.form("sleep_assessment"):
        st.subheader("Personal information")
        personal_left, personal_right = st.columns(2)
        with personal_left:
            gender = st.selectbox("Gender", GENDERS)
            age = st.number_input(
                "Age (years)",
                min_value=_low("Age"),
                max_value=_high("Age"),
                value=40,
                step=1,
            )
        with personal_right:
            occupation = st.selectbox(
                "Occupation",
                OCCUPATIONS,
                index=OCCUPATIONS.index("Nurse"),
            )
            bmi = st.selectbox(
                "BMI category",
                BMI_CATEGORIES,
                index=BMI_CATEGORIES.index("Normal"),
            )

        st.subheader("Sleep and lifestyle")
        sleep_left, sleep_right = st.columns(2)
        with sleep_left:
            sleep_duration = st.number_input(
                "Sleep duration (hours)",
                min_value=float(INPUT_LIMITS["Sleep Duration"][0]),
                max_value=float(INPUT_LIMITS["Sleep Duration"][1]),
                value=7.0,
                step=0.1,
                format="%.1f",
            )
            quality = st.slider(
                "Quality of sleep",
                _low("Quality of Sleep"),
                _high("Quality of Sleep"),
                7,
                help="1 is the lowest quality and 10 is the highest.",
            )
            activity = st.number_input(
                "Physical activity (minutes/day)",
                min_value=_low("Physical Activity Level"),
                max_value=_high("Physical Activity Level"),
                value=60,
                step=1,
            )
        with sleep_right:
            stress = st.slider(
                "Stress level",
                _low("Stress Level"),
                _high("Stress Level"),
                5,
                help="1 is the lowest stress and 10 is the highest.",
            )
            steps = st.number_input(
                "Daily steps",
                min_value=_low("Daily Steps"),
                max_value=_high("Daily Steps"),
                value=6000,
                step=100,
            )

        st.subheader("Cardiovascular")
        sys_col, dia_col, hr_col = st.columns(3)
        with sys_col:
            systolic = st.number_input(
                "Systolic blood pressure (mmHg)",
                min_value=_low("Systolic_BP"),
                max_value=_high("Systolic_BP"),
                value=120,
                step=1,
                help="Systolic pressure must be higher than diastolic pressure.",
            )
        with dia_col:
            diastolic = st.number_input(
                "Diastolic blood pressure (mmHg)",
                min_value=_low("Diastolic_BP"),
                max_value=_high("Diastolic_BP"),
                value=80,
                step=1,
            )
        with hr_col:
            heart_rate = st.number_input(
                "Heart rate (bpm)",
                min_value=_low("Heart Rate"),
                max_value=_high("Heart Rate"),
                value=72,
                step=1,
            )

        submitted = st.form_submit_button("Evaluate Risk", type="primary")

    if submitted:
        payload = {
            "Gender": gender,
            "Age": int(age),
            "Occupation": occupation,
            "BMI Category": bmi,
            "Sleep Duration": round(float(sleep_duration), 1),
            "Quality of Sleep": int(quality),
            "Physical Activity Level": int(activity),
            "Stress Level": int(stress),
            "Daily Steps": int(steps),
            "Systolic_BP": int(systolic),
            "Diastolic_BP": int(diastolic),
            "Heart Rate": int(heart_rate),
        }
        try:
            result = predict_record(bundle, payload)
        except InputError as error:
            st.error("The assessment could not be scored.")
            for message in error.errors:
                st.markdown(f"- {message}")
            if st.session_state.get("assessment_result"):
                st.caption(
                    "The last successful assessment is still available on the recommendations page."
                )
        else:
            st.session_state["assessment_result"] = result
            st.session_state["assessment_payload"] = payload
            risk_level = result["recommendation"]["risk_level"]
            st.success(
                f"Assessment saved. Predicted class: {result['label']} ({risk_level} risk)."
            )

    if st.session_state.get("assessment_result"):
        st.button(
            "View recommendations",
            type="primary",
            on_click=open_recommendations,
        )


def render_result() -> None:
    """Show the assessment stored by page 1."""

    st.header(PAGE_RESULT)
    result = st.session_state.get("assessment_result")
    if not result:
        st.info(
            "No assessment is stored yet. Open Individual Sleep Risk Assessment, "
            "enter a profile, and choose Evaluate Risk."
        )
        return

    st.caption(
        "The class below is the model's screening result. "
        "Clinical decisions stay with a qualified professional."
    )
    recommendation = result["recommendation"]
    _risk_banner(result["label"], recommendation["risk_level"])

    st.subheader("Class probabilities")
    probability_columns = st.columns(len(CLASS_ORDER))
    for column, label in zip(probability_columns, CLASS_ORDER):
        column.metric(label, f"{result['probabilities'][label]:.1%}")
    show_chart(_probability_figure(result["probabilities"]), height=320)

    st.subheader("Feature importance")
    st.caption(
        "Grouped share of each original input in the trained random forest, "
        "after one-hot encoding. This describes the model as a whole."
    )
    show_chart(_importance_figure(result["importances"]))

    st.subheader("Profile comparison")
    st.caption(
        "Each note compares this profile with medians in the training table. "
        "The comparison describes association in that table."
    )
    factors = result["factors"]
    if factors:
        for factor in factors:
            st.markdown(f"- {factor['sentence']}")
    else:
        st.info("No comparison note was produced for this profile.")

    st.subheader("Decision and actions")
    with st.container(border=True):
        st.markdown(f"**{recommendation['risk_level']} risk**")
        st.markdown(recommendation["decision"])
        for index, action in enumerate(recommendation["actions"], start=1):
            st.markdown(f"{index}. {action}")

    notes = result["support_notes"]
    if notes:
        st.subheader("Values outside the training range")
        for note in notes:
            st.warning(note)

    payload = st.session_state.get("assessment_payload")
    if payload:
        with st.expander("Submitted profile"):
            rows = [
                {"Field": DISPLAY_NAMES[feature], "Value": str(payload.get(feature, ""))}
                for feature in FEATURES
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def render_eda(bundle: dict) -> None:
    """Filter the training table and draw the exploratory charts."""

    st.header(PAGE_EDA)
    st.caption(
        "Explore the training table. Sidebar filters apply to the charts on this page. "
        "Cross-validation scores stay on the full training table."
    )

    frame = bundle["frame"].copy()
    filtered = apply_chart_filters(frame)
    st.caption(f"Training table: {len(frame)} rows ({_source_label(bundle['meta'])}).")

    if filtered is None:
        st.warning("Select at least one gender and one occupation.")
    elif filtered.empty:
        st.info("No rows match the current filters.")
    else:
        st.caption(f"Charts use {len(filtered)} filtered rows.")
        _class_count_metrics(filtered)
        render_heatmap(filtered)
        st.divider()
        render_scatter(filtered)
        st.divider()
        render_prevalence(filtered)

    st.divider()
    render_model_evaluation(bundle["meta"])


def apply_chart_filters(frame: pd.DataFrame) -> pd.DataFrame | None:
    """Return the filtered analysis table. None means the selection is empty."""

    st.sidebar.subheader("Chart filters")
    genders = sorted(frame["Gender"].astype(str).unique())
    occupations = sorted(frame["Occupation"].astype(str).unique())
    age_low = int(frame["Age"].min())
    age_high = int(frame["Age"].max())

    chosen_genders = st.sidebar.multiselect(
        "Gender",
        genders,
        default=genders,
        key="filter_gender",
    )
    chosen_occupations = st.sidebar.multiselect(
        "Occupation",
        occupations,
        default=occupations,
        key="filter_occupation",
    )
    if age_low == age_high:
        age_range = (age_low, age_high)
        st.sidebar.caption(f"Every row is age {age_low}.")
    else:
        age_range = st.sidebar.slider(
            "Age range",
            min_value=age_low,
            max_value=age_high,
            value=(age_low, age_high),
            key="filter_age",
        )

    if not chosen_genders or not chosen_occupations:
        return None

    return frame[
        frame["Gender"].isin(chosen_genders)
        & frame["Occupation"].isin(chosen_occupations)
        & frame["Age"].between(age_range[0], age_range[1])
    ].copy()


def render_heatmap(filtered: pd.DataFrame) -> None:
    st.subheader("Correlation heatmap")
    if len(filtered) < 3:
        st.info("At least three filtered rows are needed for a correlation heatmap.")
        return

    corr = filtered.loc[:, HEATMAP_COLUMNS].corr(numeric_only=True)
    labels = [HEATMAP_LABELS[column] for column in HEATMAP_COLUMNS]
    rounded = corr.round(2)
    text = [
        [f"{value:.2f}" if pd.notna(value) else "" for value in row]
        for row in rounded.to_numpy()
    ]
    figure = go.Figure(
        data=go.Heatmap(
            z=corr.to_numpy(),
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[[0.0, "#B91C1C"], [0.5, "#F8FAFC"], [1.0, "#1E3A8A"]],
            colorbar={"title": "Pearson r"},
            text=text,
            texttemplate="%{text}",
            hovertemplate="%{y} and %{x}: %{z:.2f}<extra></extra>",
            xgap=2,
            ygap=2,
        )
    )
    style_figure(figure, 540, grid=False)
    figure.update_yaxes(autorange="reversed")
    figure.update_xaxes(tickangle=-30)
    figure.update_layout(margin={"l": 120, "r": 24, "t": 24, "b": 110})
    show_chart(figure)
    st.caption(_correlation_note(corr))


def render_scatter(filtered: pd.DataFrame) -> None:
    st.subheader("Sleep duration and stress")
    figure = px.scatter(
        filtered,
        x="Sleep Duration",
        y="Stress Level",
        color=TARGET,
        color_discrete_map=DISORDER_COLORS,
        category_orders={TARGET: CLASS_ORDER},
        hover_data=["Gender", "Occupation", "BMI Category", "Quality of Sleep", "Age"],
        labels={
            "Sleep Duration": "Sleep duration (hours)",
            "Stress Level": "Stress level",
            TARGET: "Sleep disorder",
        },
        opacity=0.75,
    )
    style_figure(figure, 460)
    show_chart(figure)
    st.caption(_scatter_note(filtered))


def render_prevalence(filtered: pd.DataFrame) -> None:
    st.subheader("Sleep disorder prevalence by occupation")
    share = _disorder_share(filtered)
    figure = px.bar(
        share,
        x="Occupation",
        y="percent",
        color="Sleep Disorder",
        barmode="group",
        custom_data=["count"],
        color_discrete_map=DISORDER_COLORS,
        category_orders={"Sleep Disorder": CLASS_ORDER},
        labels={
            "percent": "Share of occupation (%)",
            "Sleep Disorder": "Sleep disorder",
        },
    )
    figure.update_traces(
        hovertemplate="%{x}<br>%{fullData.name}: %{y:.1f}%<br>Rows: %{customdata[0]}<extra></extra>"
    )
    style_figure(figure, 480)
    figure.update_xaxes(tickangle=-35)
    figure.update_layout(margin={"l": 48, "r": 24, "t": 24, "b": 120})
    show_chart(figure)
    st.caption(_prevalence_note(share))


def render_model_evaluation(meta: dict) -> None:
    """Show stratified cross-validation and the duplicate-row caveat."""

    st.subheader("Cross-validation")
    metrics = meta["metrics"]
    st.caption(
        f"Stratified {metrics['folds']}-fold scores on the full training table "
        f"of {meta['row_count']} rows. Chart filters do not change these scores."
    )
    metric_columns = st.columns(4)
    labels = [
        ("accuracy", "Accuracy"),
        ("precision_macro", "Precision (macro)"),
        ("recall_macro", "Recall (macro)"),
        ("f1_macro", "F1 (macro)"),
    ]
    for column, (key, label) in zip(metric_columns, labels):
        column.metric(label, _mean_std_text(metrics[key]))

    per_class_rows = []
    for label in CLASS_ORDER:
        scores = metrics["per_class"][label]
        per_class_rows.append({
            "Class": label,
            "Precision": _mean_std_text(scores["precision"]),
            "Recall": _mean_std_text(scores["recall"]),
            "F1": _mean_std_text(scores["f1"]),
        })
    st.dataframe(pd.DataFrame(per_class_rows), hide_index=True, width="stretch")

    counts = meta["class_counts"]
    count_text = ", ".join(f"{label} {counts.get(label, 0)}" for label in CLASS_ORDER)
    st.caption(
        f"Class counts: {count_text}. "
        f"Duplicate feature rows: {meta['duplicate_feature_rows']}. "
        f"Normal Weight rows mapped to Normal: {meta['bmi_relabeled']}."
    )
    if meta.get("caveat"):
        st.warning(meta["caveat"])


def _class_count_metrics(filtered: pd.DataFrame) -> None:
    columns = st.columns(len(CLASS_ORDER) + 1)
    columns[0].metric("Filtered rows", len(filtered))
    for column, label in zip(columns[1:], CLASS_ORDER):
        column.metric(label, int((filtered[TARGET] == label).sum()))


def _disorder_share(filtered: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for occupation in sorted(filtered["Occupation"].astype(str).unique()):
        part = filtered[filtered["Occupation"] == occupation]
        total = len(part)
        for label in CLASS_ORDER:
            count = int((part[TARGET] == label).sum())
            rows.append({
                "Occupation": occupation,
                "Sleep Disorder": label,
                "count": count,
                "percent": (100.0 * count / total) if total else 0.0,
            })
    return pd.DataFrame(rows)


def _probability_figure(probabilities: dict) -> go.Figure:
    labels = list(CLASS_ORDER)
    values = [float(probabilities[label]) for label in labels]
    figure = go.Figure(
        data=go.Bar(
            x=labels,
            y=values,
            marker_color=[DISORDER_COLORS[label] for label in labels],
            text=[f"{value:.1%}" for value in values],
            textposition="outside",
            hovertemplate="%{x}: %{y:.1%}<extra></extra>",
        )
    )
    style_figure(figure, 320)
    figure.update_yaxes(range=[0, 1.18], tickformat=".0%", title="Probability")
    figure.update_layout(margin={"l": 48, "r": 16, "t": 24, "b": 40})
    return figure


def _importance_figure(importances: list[dict]) -> go.Figure:
    table = pd.DataFrame(importances)
    if table.empty:
        figure = go.Figure()
        style_figure(figure, 240)
        return figure
    ordered = table.iloc[::-1]
    figure = go.Figure(
        data=go.Bar(
            x=ordered["importance"],
            y=ordered["label"],
            orientation="h",
            marker_color="#2563EB",
            hovertemplate="%{y}: %{x:.1%}<extra></extra>",
        )
    )
    style_figure(figure, max(280, 32 * len(table) + 80))
    figure.update_xaxes(tickformat=".0%", title="Share of model importance")
    peak = float(table["importance"].max())
    figure.update_layout(
        margin={"l": 160, "r": 24, "t": 16, "b": 48},
        xaxis_range=[0, max(0.2, peak * 1.25)],
    )
    return figure


def _correlation_note(corr: pd.DataFrame) -> str:
    value = corr.loc["Stress Level", "Sleep Duration"]
    if pd.isna(value):
        relation = "Stress level and sleep duration do not vary enough to summarize."
    elif abs(float(value)) < 0.1:
        relation = (
            f"Pearson correlation between stress level and sleep duration is {value:.2f}, "
            "a weak linear association in the filtered rows."
        )
    elif float(value) < 0:
        relation = (
            f"Pearson correlation between stress level and sleep duration is {value:.2f}. "
            "Higher stress accompanies shorter sleep in the filtered rows."
        )
    else:
        relation = (
            f"Pearson correlation between stress level and sleep duration is {value:.2f}. "
            "Higher stress accompanies longer sleep in the filtered rows."
        )
    return (
        f"{relation} Disorder risk is an exploration code on this page only: "
        "None = 0, Insomnia = 1, Sleep Apnea = 2."
    )


def _scatter_note(filtered: pd.DataFrame) -> str:
    medians = filtered.groupby(TARGET)[["Sleep Duration", "Stress Level"]].median()
    parts = []
    for label in CLASS_ORDER:
        if label not in medians.index:
            continue
        parts.append(
            f"{label}: {medians.loc[label, 'Sleep Duration']:.1f} h, "
            f"stress {medians.loc[label, 'Stress Level']:.0f}/10"
        )
    duplicate_rows = int(filtered.duplicated(subset=["Sleep Duration", "Stress Level"]).sum())
    overlap = (
        f" {duplicate_rows} filtered rows share a sleep-duration and stress point with another row, so those markers overlap."
        if duplicate_rows
        else ""
    )
    return "Median of the filtered rows — " + "; ".join(parts) + "." + overlap


def _prevalence_note(share: pd.DataFrame) -> str:
    apnea = share[share["Sleep Disorder"] == "Sleep Apnea"].copy()
    if apnea.empty:
        return "No occupation remains in the current filter."
    totals = share.groupby("Occupation")["count"].sum()
    apnea["total"] = apnea["Occupation"].map(totals)
    if float(apnea["percent"].max()) == 0:
        return "None of the filtered rows are labeled Sleep Apnea."
    stable = apnea[apnea["total"] >= 10]
    pool = stable if not stable.empty else apnea
    top = pool.sort_values(["percent", "count"], ascending=False).iloc[0]
    scope = (
        "Among occupations with at least 10 filtered rows, "
        if not stable.empty
        else "In this filter, "
    )
    return (
        f"{scope}{top['Occupation']} has the highest Sleep Apnea share "
        f"at {top['percent']:.0f}% ({int(top['count'])} of {int(top['total'])} rows)."
    )


def _risk_banner(label: str, risk_level: str) -> None:
    foreground, background = RISK_STYLE[risk_level]
    st.markdown(
        (
            f"<div style='background:{background};color:{foreground};"
            "padding:1rem 1.25rem;border-radius:12px;"
            f"border:1px solid {foreground};margin:0.5rem 0 1rem 0;'>"
            f"<div style='font-size:0.8rem;letter-spacing:0.04em;text-transform:uppercase;'>"
            f"{risk_level} risk</div>"
            f"<div style='font-size:1.8rem;font-weight:700;line-height:1.2;'>{label}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def style_figure(figure: go.Figure, height: int, grid: bool = True) -> go.Figure:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font={"family": "Arial, sans-serif", "color": "#0F172A", "size": 13},
        height=height,
        margin={"l": 48, "r": 24, "t": 24, "b": 48},
    )
    if grid:
        figure.update_xaxes(gridcolor="#E2E8F0", zeroline=False)
        figure.update_yaxes(gridcolor="#E2E8F0", zeroline=False)
    return figure


def show_chart(figure: go.Figure, height: int | None = None) -> None:
    if height is not None:
        figure.update_layout(height=height)
    st.plotly_chart(
        figure,
        width="stretch",
        theme=None,
        config=PLOTLY_CONFIG,
    )


def _mean_std_text(stats: dict) -> str:
    return f"{stats['mean']:.3f} ± {stats['std']:.3f}"


def _source_label(meta: dict) -> str:
    source = str(meta.get("source_path", ""))
    if source == "synthetic":
        return "synthetic stand-in"
    name = Path(source).name
    return name or "training table"


def _low(feature: str) -> int:
    return int(INPUT_LIMITS[feature][0])


def _high(feature: str) -> int:
    return int(INPUT_LIMITS[feature][1])


main()
