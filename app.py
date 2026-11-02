"""Sleep Health and Lifestyle decision-support app.

Three sidebar pages share one trained pipeline from model.py:
an individual assessment, the stored recommendation, and an
exploratory view of the training table.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from model import (
    CLASS_ORDER,
    FEATURES,
    GENDERS,
    INPUT_LIMITS,
    OCCUPATIONS,
    TARGET,
    InputError,
    get_bundle,
    predict_record,
)

PAGE_ASSESS = "assess"
PAGE_RESULT = "result"
PAGE_EDA = "eda"
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
ASSET_DIR = Path(__file__).resolve().parent / "assets"
WEIGHT_LIMITS_KG = (30.0, 250.0)
HEIGHT_LIMITS_CM = (120.0, 220.0)

STYLE = """
<style>
.stApp {
    background-color: #F8FAFC;
}
[data-testid="stMainBlockContainer"] {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #DBEAFE;
    border-radius: 16px;
    padding: 0.85rem 1rem 1.25rem 1rem;
    margin-top: 0.4rem;
}
html, [data-testid="stAppViewContainer"] {
    font-size: 18px;
}
[data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] p {
    font-size: 1.05rem;
    line-height: 1.45;
}
[data-testid="stWidgetLabel"] p {
    font-weight: 650;
}
.stButton > button,
div[data-testid="stBaseButton-primary"] > button,
div[data-testid="stBaseButton-secondary"] > button {
    min-height: 3.1rem;
    font-size: 1.15rem;
    border-radius: 12px;
}
[data-testid="stNumberInput"] input {
    min-height: 3rem;
    font-size: 1.2rem;
}
.bmi-card {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 14px;
    padding: 0.55rem 0.75rem;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-height: 5.5rem;
}
.bmi-card img {
    width: 72px;
    height: 72px;
    object-fit: contain;
    flex: 0 0 auto;
}
.bmi-kicker {
    color: #1E3A8A;
    font-size: 0.75rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin: 0;
}
.bmi-value {
    color: #1E3A8A;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
    margin: 0.15rem 0 0 0;
}
.bmi-meta,
.bmi-note {
    color: #0F172A;
    margin: 0.35rem 0 0 0;
}
.bmi-note {
    color: #334155;
    font-size: 0.92rem;
}
.clinic-banner {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-radius: 16px;
    overflow: hidden;
    margin: 0.25rem 0 0.75rem 0;
}
.clinic-banner img {
    width: 168px;
    height: 84px;
    object-fit: cover;
    flex: 0 0 auto;
}
.clinic-banner div {
    padding: 0.75rem 1rem 0.75rem 0;
}
[data-testid="stSidebar"] {
    background-color: #F8FAFC;
    border-right: 1px solid #E2E8F0;
}
.side-brand {
    margin: 0.25rem 0 0.85rem 0;
}
.side-kicker {
    color: #2563EB;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin: 0;
}
.side-title {
    color: #1E3A8A;
    font-size: 1.45rem;
    font-weight: 750;
    line-height: 1.15;
    margin: 0.2rem 0 0 0;
}
.side-sub {
    color: #475569;
    font-size: 0.95rem;
    margin: 0.2rem 0 0 0;
}
.side-note {
    color: #64748B;
    font-size: 0.82rem;
    line-height: 1.35;
    margin: 1.1rem 0 0 0;
}
[data-testid="stSidebar"] [data-testid="stButton"] {
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    min-height: 2.55rem;
    font-size: 1.02rem;
    font-weight: 650;
    display: flex;
    justify-content: flex-start;
    text-align: left;
    padding-left: 0.9rem;
    border-radius: 10px;
}
[data-testid="stSidebar"] .stButton > button p {
    text-align: left !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent;
    color: #1E3A8A;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: #EFF6FF;
    color: #1E3A8A;
    border-color: #DBEAFE;
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
@media (max-width: 820px) {
    [data-testid="stMainBlockContainer"] {
        padding: 0.65rem 0.55rem 1rem 0.55rem;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }
    [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .clinic-banner {
        flex-direction: column;
        align-items: stretch;
    }
    .clinic-banner img {
        width: 100%;
        height: 92px;
    }
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


def classify_bmi(weight_kg: float, height_cm: float) -> tuple[float, str]:
    """Return adult BMI and the category the classifier expects."""

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)
    return bmi, bmi_category_of(bmi)


def bmi_category_of(bmi: float) -> str:
    """Map one BMI value onto the adult category."""

    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def format_bmi(bmi: float, category: str) -> str:
    """Show one decimal, or two when rounding would imply another category."""

    if bmi_category_of(round(bmi, 1)) != category:
        return f"{bmi:.2f}"
    return f"{bmi:.1f}"


TEXT = {
    "en": {
        "app_name": "Sleep Health",
        "tagline": "Decision support",
        "course": "1501418",
        "footer": "Screening aid. A clinician diagnoses.",
        "nav_assess": "Assessment",
        "nav_result": "Result",
        "nav_eda": "Explore",
        "language": "Language",
        "pages": "Pages",
        "page_assess": "Individual Sleep Risk Assessment",
        "page_result": "Assessment Result & Decision Recommendations",
        "page_eda": "Interactive Data Analytics & EDA",
        "banner_kicker": "Clinical screening",
        "banner_body": "Enter weight and height. BMI is calculated for you. This is a screen, not a diagnosis.",
        "banner_alt": "Bright, quiet clinic room",
        "assess_intro": "Fill in one section at a time, then press Evaluate Risk.",
        "personal": "Personal information",
        "personal_hint": "Weight is in kilograms. Height is in centimeters.",
        "gender": "Gender",
        "age": "Age (years)",
        "weight": "Weight (kg)",
        "height": "Height (cm)",
        "occupation": "Occupation",
        "weight_help": "Kilograms.",
        "height_help": "Centimeters, standing.",
        "sleep_section": "Sleep and lifestyle",
        "sleep_duration": "Sleep duration (hours)",
        "quality": "Quality of sleep",
        "quality_help": "1 is lowest and 10 is highest.",
        "activity": "Physical activity (minutes/day)",
        "stress": "Stress level",
        "stress_help": "1 is lowest and 10 is highest.",
        "steps": "Daily steps",
        "cardio": "Heart and blood pressure",
        "systolic": "Systolic blood pressure",
        "diastolic": "Diastolic blood pressure",
        "heart_rate": "Heart rate (bpm)",
        "bp_help": "The upper number must be higher than the lower number.",
        "evaluate": "Evaluate Risk",
        "view_result": "View recommendations",
        "saved": "Saved. BMI {bmi} ({category}). Result: {label}, {risk} risk.",
        "score_failed": "This entry could not be scored.",
        "bp_order": "Systolic blood pressure must be higher than diastolic blood pressure.",
        "kept_result": "The last successful result is still on the recommendations page.",
        "empty_result": "No result yet. Open the assessment page, enter the details, and press Evaluate Risk.",
        "result_caption": "This is a screening result. A clinician confirms the decision.",
        "body": "Body measurements",
        "bmi_short": "BMI",
        "bmi_category": "BMI category",
        "bmi_formula": "BMI = kg / m². Below 18.5 underweight, 18.5 to 25 normal, 25 to 30 overweight, 30 or higher obese.",
        "probabilities": "Class probabilities",
        "probability": "Probability",
        "importance": "Feature importance",
        "importance_caption": "How much each input contributes to this model.",
        "importance_axis": "Share of model importance",
        "comparison": "Profile comparison",
        "comparison_caption": "Compared with typical values in the training table. This is not a cause.",
        "no_factors": "No comparison note was produced for this profile.",
        "decision": "Decision and actions",
        "risk_word": "{level} risk",
        "outside": "Values outside the training range",
        "submitted": "Submitted profile",
        "field": "Field",
        "value": "Value",
        "eda_intro": "Filters change the charts. The scores at the bottom stay on the full table.",
        "training_rows": "Training table: {count} rows ({source}).",
        "chart_rows": "Charts use {count} filtered rows.",
        "need_filter": "Select at least one gender and one occupation.",
        "no_rows": "No rows match the current filters.",
        "filters": "Chart filters",
        "age_range": "Age range",
        "every_age": "Every row is age {age}.",
        "filtered_rows": "Filtered rows",
        "heatmap": "Correlation heatmap",
        "heatmap_need3": "At least three filtered rows are needed for a correlation heatmap.",
        "scatter": "Sleep duration and stress",
        "prevalence": "Sleep disorder prevalence by occupation",
        "cv": "Cross-validation",
        "cv_caption": "Stratified {folds}-fold scores on all {count} rows. Filters do not change these scores.",
        "accuracy": "Accuracy",
        "precision": "Precision (macro)",
        "recall": "Recall (macro)",
        "f1": "F1 (macro)",
        "class_header": "Class",
        "counts_line": "Class counts: {counts}. Duplicate feature rows: {duplicates}. Normal Weight mapped to Normal: {relabeled}.",
        "caveat": "Some profiles are repeated, so these scores can look higher than real performance.",
        "synthetic": "synthetic stand-in",
        "pearson_na": "Stress and sleep duration do not vary enough to summarize.",
        "pearson_weak": "Correlation between stress and sleep duration is {value}. The link is weak in these rows.",
        "pearson_neg": "Correlation between stress and sleep duration is {value}. Higher stress goes with shorter sleep.",
        "pearson_pos": "Correlation between stress and sleep duration is {value}. Higher stress goes with longer sleep.",
        "disorder_code": "On this chart only, no disorder = 0, insomnia = 1, sleep apnea = 2.",
        "scatter_median": "Typical values here — {parts}.",
        "scatter_item": "{label}: {hours} h, stress {stress}/10",
        "scatter_overlap": " {count} rows sit on the same point, so the dots overlap.",
        "prev_empty": "No occupation remains in the current filter.",
        "prev_zero": "None of the filtered rows are labeled sleep apnea.",
        "prev_stable": "Among occupations with at least 10 rows, {job} has the highest sleep apnea share at {percent}% ({count} of {total}).",
        "prev_any": "In this filter, {job} has the highest sleep apnea share at {percent}% ({count} of {total}).",
        "factor_none": "{name} is {user}, compared with the no-disorder median of {none}.",
        "factor_shift": "{name} is {user}, {relation} the no-disorder median of {none}. The {label} group median is {predicted}.",
        "factor_cat": "{name} is {category}. In this dataset, {rate} of {category} records are {label}, compared with {base} overall.",
        "rel_higher": "higher than",
        "rel_lower": "lower than",
        "rel_equal": "equal to",
        "outside_range": "{name} is outside the training range ({low} to {high}).",
        "unknown_category": "{name} value '{value}' does not appear in the training data.",
        "share_axis": "Share of occupation (%)",
        "rows_hover": "Rows",
        "hours_axis": "Sleep duration (hours)",
        "pearson": "Pearson r",
    },
    "th": {
        "app_name": "สุขภาพการนอน",
        "tagline": "ช่วยตัดสินใจ",
        "course": "1501418",
        "footer": "เครื่องมือคัดกรอง แพทย์เป็นผู้วินิจฉัย",
        "nav_assess": "ประเมิน",
        "nav_result": "ผลแนะนำ",
        "nav_eda": "สำรวจ",
        "language": "ภาษา",
        "pages": "หน้า",
        "page_assess": "ประเมินความเสี่ยงรายบุคคล",
        "page_result": "ผลประเมินและคำแนะนำ",
        "page_eda": "สำรวจข้อมูล",
        "banner_kicker": "คัดกรองเบื้องต้น",
        "banner_body": "ใส่น้ำหนักและส่วนสูง ระบบคำนวณ BMI ให้ ผลนี้เป็นการคัดกรอง ไม่ใช่การวินิจฉัย",
        "banner_alt": "ห้องตรวจที่สว่างและเงียบ",
        "assess_intro": "กรอกทีละส่วน แล้วกดประเมินความเสี่ยง",
        "personal": "ข้อมูลส่วนตัว",
        "personal_hint": "น้ำหนักเป็นกิโลกรัม ส่วนสูงเป็นเซนติเมตร",
        "gender": "เพศ",
        "age": "อายุ (ปี)",
        "weight": "น้ำหนัก (กก.)",
        "height": "ส่วนสูง (ซม.)",
        "occupation": "อาชีพ",
        "weight_help": "หน่วยเป็นกิโลกรัม",
        "height_help": "ส่วนสูงท่ายืน หน่วยเป็นเซนติเมตร",
        "sleep_section": "การนอนและไลฟ์สไตล์",
        "sleep_duration": "ระยะเวลานอน (ชั่วโมง)",
        "quality": "คุณภาพการนอน",
        "quality_help": "1 น้อยที่สุด 10 มากที่สุด",
        "activity": "กิจกรรมทางกาย (นาที/วัน)",
        "stress": "ความเครียด",
        "stress_help": "1 น้อยที่สุด 10 มากที่สุด",
        "steps": "จำนวนก้าวต่อวัน",
        "cardio": "หัวใจและความดัน",
        "systolic": "ความดันตัวบน",
        "diastolic": "ความดันตัวล่าง",
        "heart_rate": "ชีพจร (ครั้ง/นาที)",
        "bp_help": "ตัวบนต้องสูงกว่าตัวล่าง",
        "evaluate": "ประเมินความเสี่ยง",
        "view_result": "ดูคำแนะนำ",
        "saved": "บันทึกแล้ว BMI {bmi} ({category}) ผลคือ {label} ความเสี่ยง{risk}",
        "score_failed": "ประเมินรายการนี้ไม่ได้",
        "bp_order": "ความดันตัวบนต้องสูงกว่าความดันตัวล่าง",
        "kept_result": "ผลล่าสุดที่ประเมินได้ยังอยู่ที่หน้าคำแนะนำ",
        "empty_result": "ยังไม่มีผล เปิดหน้าประเมิน กรอกข้อมูล แล้วกดประเมินความเสี่ยง",
        "result_caption": "นี่คือผลคัดกรอง แพทย์เป็นผู้ยืนยันการตัดสินใจ",
        "body": "ขนาดร่างกาย",
        "bmi_short": "BMI",
        "bmi_category": "หมวด BMI",
        "bmi_formula": "BMI = น้ำหนัก (กก.) / ส่วนสูง (ม.)² ต่ำกว่า 18.5 น้ำหนักน้อย 18.5 ถึง 25 ปกติ 25 ถึง 30 น้ำหนักเกิน 30 ขึ้นไปอ้วน",
        "probabilities": "ความน่าจะเป็นของแต่ละกลุ่ม",
        "probability": "ความน่าจะเป็น",
        "importance": "ความสำคัญของปัจจัย",
        "importance_caption": "แต่ละปัจจัยมีผลต่อโมเดลนี้มากน้อยเพียงใด",
        "importance_axis": "สัดส่วนความสำคัญ",
        "comparison": "เทียบกับข้อมูลฝึก",
        "comparison_caption": "เทียบกับค่าที่พบบ่อยในตารางฝึก ไม่ได้แปลว่าเป็นสาเหตุ",
        "no_factors": "ไม่มีข้อความเทียบสำหรับโปรไฟล์นี้",
        "decision": "การตัดสินใจและสิ่งที่ควรทำ",
        "risk_word": "ความเสี่ยง{level}",
        "outside": "ค่านอกช่วงข้อมูลฝึก",
        "submitted": "ข้อมูลที่ส่ง",
        "field": "รายการ",
        "value": "ค่า",
        "eda_intro": "ตัวกรองมีผลกับกราฟ คะแนนด้านล่างคำนวณจากตารางทั้งหมด",
        "training_rows": "ตารางฝึก {count} แถว ({source})",
        "chart_rows": "กราฟใช้ {count} แถวที่กรองแล้ว",
        "need_filter": "เลือกอย่างน้อยหนึ่งเพศและหนึ่งอาชีพ",
        "no_rows": "ไม่มีแถวที่ตรงกับตัวกรอง",
        "filters": "ตัวกรองกราฟ",
        "age_range": "ช่วงอายุ",
        "every_age": "ทุกแถวอายุ {age} ปี",
        "filtered_rows": "แถวที่กรอง",
        "heatmap": "แผนภาพความสัมพันธ์",
        "heatmap_need3": "ต้องมีอย่างน้อย 3 แถวจึงจะวาดแผนภาพความสัมพันธ์ได้",
        "scatter": "ระยะเวลานอนและความเครียด",
        "prevalence": "สัดส่วนความผิดปกติของการนอนตามอาชีพ",
        "cv": "การตรวจสอบไขว้",
        "cv_caption": "คะแนนแบ่ง {folds} ส่วน จาก {count} แถวทั้งหมด ตัวกรองไม่เปลี่ยนคะแนนนี้",
        "accuracy": "ความถูกต้อง",
        "precision": "ความแม่นยำ (มาโคร)",
        "recall": "ความครอบคลุม (มาโคร)",
        "f1": "เอฟวัน (มาโคร)",
        "class_header": "กลุ่ม",
        "counts_line": "จำนวนแต่ละกลุ่ม: {counts} แถวที่คุณลักษณะซ้ำ: {duplicates} แมป Normal Weight เป็น Normal: {relabeled}",
        "caveat": "มีโปรไฟล์ซ้ำ จึงทำให้คะแนนนี้อาจสูงกว่าความสามารถจริง",
        "synthetic": "ข้อมูลจำลอง",
        "pearson_na": "ความเครียดและระยะเวลานอนไม่กระจายพอที่จะสรุป",
        "pearson_weak": "ความสัมพันธ์ระหว่างความเครียดกับระยะเวลานอนคือ {value} ความสัมพันธ์ในแถวเหล่านี้ไม่ชัด",
        "pearson_neg": "ความสัมพันธ์ระหว่างความเครียดกับระยะเวลานอนคือ {value} ความเครียดสูงไปพร้อมกับการนอนสั้นลง",
        "pearson_pos": "ความสัมพันธ์ระหว่างความเครียดกับระยะเวลานอนคือ {value} ความเครียดสูงไปพร้อมกับการนอนยาวขึ้น",
        "disorder_code": "ในกราฟนี้เท่านั้น ไม่มีความผิดปกติ = 0 นอนไม่หลับ = 1 หยุดหายใจขณะหลับ = 2",
        "scatter_median": "ค่ากลางของแถวที่แสดง — {parts}",
        "scatter_item": "{label}: {hours} ชม. ความเครียด {stress}/10",
        "scatter_overlap": " {count} แถวอยู่จุดเดียวกัน จุดในกราฟจึงทับกัน",
        "prev_empty": "ไม่มีอาชีพเหลือในตัวกรองนี้",
        "prev_zero": "ไม่มีแถวที่ถูกระบุว่าหยุดหายใจขณะหลับ",
        "prev_stable": "ในอาชีพที่มีอย่างน้อย 10 แถว {job} มีสัดส่วนหยุดหายใจขณะหลับสูงสุด {percent}% ({count} จาก {total})",
        "prev_any": "ในตัวกรองนี้ {job} มีสัดส่วนหยุดหายใจขณะหลับสูงสุด {percent}% ({count} จาก {total})",
        "factor_none": "{name} คือ {user} เทียบกับค่ามัธยฐานของกลุ่มไม่มีความผิดปกติที่ {none}",
        "factor_shift": "{name} คือ {user} {relation}ค่ามัธยฐานของกลุ่มไม่มีความผิดปกติ ({none}) ค่ามัธยฐานของกลุ่ม{label} คือ {predicted}",
        "factor_cat": "{name} คือ {category} ในชุดข้อมูลนี้ {rate} ของ{category}เป็น{label} เทียบกับ {base} ของทั้งหมด",
        "rel_higher": "สูงกว่า",
        "rel_lower": "ต่ำกว่า",
        "rel_equal": "เท่ากับ",
        "outside_range": "{name} อยู่นอกช่วงข้อมูลฝึก ({low} ถึง {high})",
        "unknown_category": "ค่า '{value}' ของ{name} ไม่ปรากฏในข้อมูลฝึก",
        "share_axis": "สัดส่วนในอาชีพ (%)",
        "rows_hover": "จำนวนแถว",
        "hours_axis": "ระยะเวลานอน (ชั่วโมง)",
        "pearson": "เพียร์สัน r",
    },
}

LABELS = {
    "en": {
        "class": {"None": "None", "Insomnia": "Insomnia", "Sleep Apnea": "Sleep Apnea"},
        "risk": {"Low": "Low", "Medium": "Medium", "High": "High"},
        "gender": {"Female": "Female", "Male": "Male"},
        "bmi": {
            "Underweight": "Underweight",
            "Normal": "Normal",
            "Overweight": "Overweight",
            "Obese": "Obese",
        },
        "job": {job: job for job in (
            "Accountant", "Doctor", "Engineer", "Lawyer", "Manager", "Nurse",
            "Sales Representative", "Salesperson", "Scientist", "Software Engineer", "Teacher",
        )},
        "feature": {
            "Age": "Age",
            "Sleep Duration": "Sleep duration",
            "Quality of Sleep": "Sleep quality",
            "Physical Activity Level": "Physical activity",
            "Stress Level": "Stress level",
            "Heart Rate": "Heart rate",
            "Daily Steps": "Daily steps",
            "Systolic_BP": "Systolic blood pressure",
            "Diastolic_BP": "Diastolic blood pressure",
            "Gender": "Gender",
            "Occupation": "Occupation",
            "BMI Category": "BMI category",
            "Disorder Risk": "Disorder risk",
        },
    },
    "th": {
        "class": {
            "None": "ไม่มีความผิดปกติ",
            "Insomnia": "นอนไม่หลับ",
            "Sleep Apnea": "หยุดหายใจขณะหลับ",
        },
        "risk": {"Low": "ต่ำ", "Medium": "ปานกลาง", "High": "สูง"},
        "gender": {"Female": "หญิง", "Male": "ชาย"},
        "bmi": {
            "Underweight": "น้ำหนักน้อย",
            "Normal": "ปกติ",
            "Overweight": "น้ำหนักเกิน",
            "Obese": "อ้วน",
        },
        "job": {
            "Accountant": "นักบัญชี",
            "Doctor": "แพทย์",
            "Engineer": "วิศวกร",
            "Lawyer": "ทนายความ",
            "Manager": "ผู้จัดการ",
            "Nurse": "พยาบาล",
            "Sales Representative": "ตัวแทนขาย",
            "Salesperson": "พนักงานขาย",
            "Scientist": "นักวิทยาศาสตร์",
            "Software Engineer": "วิศวกรซอฟต์แวร์",
            "Teacher": "ครู",
        },
        "feature": {
            "Age": "อายุ",
            "Sleep Duration": "ระยะเวลานอน",
            "Quality of Sleep": "คุณภาพการนอน",
            "Physical Activity Level": "กิจกรรมทางกาย",
            "Stress Level": "ความเครียด",
            "Heart Rate": "ชีพจร",
            "Daily Steps": "จำนวนก้าว",
            "Systolic_BP": "ความดันตัวบน",
            "Diastolic_BP": "ความดันตัวล่าง",
            "Gender": "เพศ",
            "Occupation": "อาชีพ",
            "BMI Category": "หมวด BMI",
            "Disorder Risk": "รหัสความเสี่ยง",
        },
    },
}

ADVICE = {
    "en": {
        "None": {
            "decision": "Maintain current routine.",
            "actions": [
                "Keep a regular sleep and wake schedule.",
                "Sleep in a dark, quiet room.",
                "Limit caffeine in the hours before bed.",
            ],
        },
        "Insomnia": {
            "decision": "Behavioral and lifestyle intervention.",
            "actions": [
                "Practice stress management and relaxation techniques.",
                "Limit screen time for one hour before sleep.",
                "Consider consulting a wellness coach.",
            ],
        },
        "Sleep Apnea": {
            "decision": "Medical evaluation required.",
            "actions": [
                "Treat this result as a red flag, not a diagnosis.",
                "Schedule a clinical polysomnography (sleep test).",
                "Consult a pulmonologist or sleep specialist.",
            ],
        },
    },
    "th": {
        "None": {
            "decision": "คงกิจวัตรเดิม",
            "actions": [
                "นอนและตื่นให้เป็นเวลา",
                "นอนในห้องมืดและเงียบ",
                "เลี่ยงคาเฟอีนก่อนนอน",
            ],
        },
        "Insomnia": {
            "decision": "ปรับพฤติกรรมและการใช้ชีวิต",
            "actions": [
                "ฝึกจัดการความเครียดและผ่อนคลาย",
                "ลดเวลาหน้าจออย่างน้อย 1 ชั่วโมงก่อนนอน",
                "พิจารณาปรึกษาผู้ดูแลด้านสุขภาพ",
            ],
        },
        "Sleep Apnea": {
            "decision": "ควรพบแพทย์",
            "actions": [
                "ถือว่าเป็นสัญญาณเตือน ไม่ใช่การวินิจฉัย",
                "นัดตรวจการนอนในโรงพยาบาล",
                "ปรึกษาแพทย์ด้านการนอนหลับ",
            ],
        },
    },
}


def current_lang() -> str:
    """Return the selected interface language."""

    lang = st.session_state.get("lang", "en")
    return lang if lang in TEXT else "en"


def tr(key: str, **values: object) -> str:
    """Look up one interface string in the active language."""

    catalog = TEXT[current_lang()]
    template = catalog.get(key, TEXT["en"].get(key, key))
    return template.format(**values) if values else template


def named(group: str, value: str) -> str:
    """Translate a stored model value without changing the stored value."""

    table = LABELS[current_lang()][group]
    fallback = LABELS["en"][group]
    return table.get(value, fallback.get(value, value))


def render_language_switch() -> None:
    """Offer large English and Thai buttons above the form."""

    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    label_col, english, thai, _spacer = st.columns([1.1, 1, 1, 1.8])
    label_col.markdown(f"**{tr('language')}**")
    english_type = "primary" if current_lang() == "en" else "secondary"
    thai_type = "primary" if current_lang() == "th" else "secondary"
    if english.button("English", key="lang_en", type=english_type, width="stretch"):
        if current_lang() != "en":
            st.session_state["lang"] = "en"
            st.rerun()
    if thai.button("ไทย", key="lang_th", type=thai_type, width="stretch"):
        if current_lang() != "th":
            st.session_state["lang"] = "th"
            st.rerun()


def pretty_value(feature: str, value: float) -> str:
    """Format one measurement with a unit in the active language."""

    thai = current_lang() == "th"
    if feature in ("Quality of Sleep", "Stress Level"):
        return f"{value:.0f}/10"
    if feature == "Sleep Duration":
        unit = "ชม." if thai else "hours"
        return f"{value:.1f} {unit}"
    if feature == "Daily Steps":
        unit = "ก้าว" if thai else "steps"
        return f"{round(value):,.0f} {unit}"
    units = {
        "Physical Activity Level": ("นาที/วัน", "min/day"),
        "Heart Rate": ("ครั้ง/นาที", "bpm"),
        "Systolic_BP": ("มม.ปรอท", "mmHg"),
        "Diastolic_BP": ("มม.ปรอท", "mmHg"),
        "Age": ("ปี", "years"),
    }
    number = f"{value:.0f}" if abs(value - round(value)) < 1e-6 else f"{value:.1f}"
    pair = units.get(feature)
    if not pair:
        return number
    return f"{number} {pair[0 if thai else 1]}"


def factor_text(factor: dict) -> str:
    """Phrase one comparison in the active language."""

    if factor.get("kind") == "categorical" and "rate" in factor:
        category = named("job" if factor["feature"] == "Occupation" else "bmi", factor["category"])
        return tr(
            "factor_cat",
            name=named("feature", factor["feature"]),
            category=category,
            rate=f"{factor['rate']:.0%}",
            label=named("class", factor["class_label"]),
            base=f"{factor['base_rate']:.0%}",
        )
    if factor.get("kind") == "numeric" and "user_value" in factor:
        relation = factor["relation"]
        shared = {
            "name": named("feature", factor["feature"]),
            "user": pretty_value(factor["feature"], factor["user_value"]),
            "none": pretty_value(factor["feature"], factor["none_value"]),
        }
        if relation == "same_group":
            return tr("factor_none", **shared)
        return tr(
            "factor_shift",
            relation=tr(f"rel_{relation}"),
            label=named("class", factor.get("class_label", "")),
            predicted=pretty_value(factor["feature"], factor["predicted_value"]),
            **shared,
        )
    return str(factor.get("sentence", ""))


def note_text(note: dict | str) -> str:
    """Phrase one out-of-range warning in the active language."""

    if isinstance(note, str):
        return note
    if note.get("kind") == "range":
        return tr(
            "outside_range",
            name=named("feature", note["feature"]),
            low=pretty_value(note["feature"], note["low"]),
            high=pretty_value(note["feature"], note["high"]),
        )
    value = note.get("value", "")
    feature = note.get("feature", "")
    if feature == "Occupation":
        value = named("job", str(value))
    elif feature == "BMI Category":
        value = named("bmi", str(value))
    elif feature == "Gender":
        value = named("gender", str(value))
    return tr("unknown_category", name=named("feature", feature), value=value)


def bmi_card(bmi: float, category: str) -> str:
    """Render a compact BMI reading beside the body measurements."""

    icon = image_data_uri("body-measurements.jpg")
    return (
        "<div class='bmi-card'>"
        f"<img src='{icon}' alt=''>"
        "<div>"
        f"<p class='bmi-kicker'>{tr('bmi_short')}</p>"
        f"<p class='bmi-value'>{format_bmi(bmi, category)}</p>"
        f"<p class='bmi-meta'><strong>{named('bmi', category)}</strong></p>"
        "</div>"
        "</div>"
    )


def clinic_banner() -> str:
    """Show a short clinic photograph above the assessment form."""

    uri = image_data_uri("clinic-background.jpg")
    return (
        "<div class='clinic-banner'>"
        f"<img src='{uri}' alt='{tr('banner_alt')}'>"
        "<div>"
        f"<p class='bmi-kicker'>{tr('banner_kicker')}</p>"
        f"<p class='bmi-meta'>{tr('banner_body')}</p>"
        "</div>"
        "</div>"
    )


@st.cache_data(show_spinner=False)
def image_data_uri(filename: str) -> str:
    """Encode a local clinic image for the page background."""

    payload = base64.b64encode((ASSET_DIR / filename).read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


def background_style() -> str:
    """Wash a clinic photograph behind the page without hiding form labels."""

    uri = image_data_uri("clinic-background.jpg")
    return (
        "<style>"
        ".stApp {"
        "background-image: "
        "linear-gradient(180deg, rgba(248,250,252,0.82) 0%, rgba(248,250,252,0.72) 48%, rgba(248,250,252,0.86) 100%), "
        f"url('{uri}');"
        "background-size: cover;"
        "background-attachment: fixed;"
        "background-position: center top;"
        "}"
        "</style>"
    )


def render_sidebar() -> None:
    """Show a short brand lockup and one-line navigation."""

    st.sidebar.markdown(
        (
            "<div class='side-brand'>"
            f"<p class='side-kicker'>{tr('course')}</p>"
            f"<p class='side-title'>{tr('app_name')}</p>"
            f"<p class='side-sub'>{tr('tagline')}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    for page_id in PAGES:
        active = st.session_state.get("nav_page") == page_id
        if st.sidebar.button(
            tr(f"nav_{page_id}"),
            key=f"nav_btn_{page_id}",
            type="primary" if active else "secondary",
            width="stretch",
        ):
            st.session_state["nav_page"] = page_id
            st.rerun()


def main() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown(background_style(), unsafe_allow_html=True)
    if st.session_state.get("nav_page") not in PAGES:
        st.session_state["nav_page"] = PAGE_ASSESS

    try:
        bundle = load_bundle()
    except Exception as exc:
        st.error(f"The model could not be loaded: {exc}")
        st.stop()

    render_language_switch()
    render_sidebar()
    page = st.session_state.get("nav_page", PAGE_ASSESS)

    if page == PAGE_ASSESS:
        render_assessment(bundle)
    elif page == PAGE_RESULT:
        render_result()
    else:
        render_eda(bundle)

    st.sidebar.markdown(
        f"<p class='side-note'>{tr('footer')}</p>",
        unsafe_allow_html=True,
    )


def render_assessment(bundle: dict) -> None:
    """Collect one profile and store predict_record output for page 2."""

    st.markdown(clinic_banner(), unsafe_allow_html=True)
    st.header(tr("page_assess"))
    st.caption(tr("assess_intro"))

    st.subheader(tr("personal"))
    st.caption(tr("personal_hint"))
    with st.container(border=True):
        identity = st.columns(3)
        gender = identity[0].selectbox(
            tr("gender"),
            GENDERS,
            format_func=lambda value: named("gender", value),
            key="assess_gender",
        )
        age = identity[1].number_input(
            tr("age"),
            min_value=_low("Age"),
            max_value=_high("Age"),
            value=40,
            step=1,
            key="assess_age",
        )
        occupation = identity[2].selectbox(
            tr("occupation"),
            OCCUPATIONS,
            index=OCCUPATIONS.index("Nurse"),
            format_func=lambda value: named("job", value),
            key="assess_occupation",
        )
        measures = st.columns(3)
        weight = measures[0].number_input(
            tr("weight"),
            min_value=WEIGHT_LIMITS_KG[0],
            max_value=WEIGHT_LIMITS_KG[1],
            value=70.0,
            step=0.1,
            format="%.1f",
            key="assess_weight",
            help=tr("weight_help"),
        )
        height = measures[1].number_input(
            tr("height"),
            min_value=HEIGHT_LIMITS_CM[0],
            max_value=HEIGHT_LIMITS_CM[1],
            value=170.0,
            step=0.1,
            format="%.1f",
            key="assess_height",
            help=tr("height_help"),
        )
        bmi, bmi_category = classify_bmi(float(weight), float(height))
        measures[2].markdown(bmi_card(bmi, bmi_category), unsafe_allow_html=True)

    st.subheader(tr("sleep_section"))
    with st.container(border=True):
        sleep_left, sleep_right = st.columns(2)
        sleep_duration = sleep_left.number_input(
            tr("sleep_duration"),
            min_value=float(INPUT_LIMITS["Sleep Duration"][0]),
            max_value=float(INPUT_LIMITS["Sleep Duration"][1]),
            value=7.0,
            step=0.1,
            format="%.1f",
            key="assess_sleep",
        )
        quality = sleep_left.slider(
            tr("quality"),
            _low("Quality of Sleep"),
            _high("Quality of Sleep"),
            7,
            help=tr("quality_help"),
            key="assess_quality",
        )
        activity = sleep_right.number_input(
            tr("activity"),
            min_value=_low("Physical Activity Level"),
            max_value=_high("Physical Activity Level"),
            value=60,
            step=1,
            key="assess_activity",
        )
        stress = sleep_right.slider(
            tr("stress"),
            _low("Stress Level"),
            _high("Stress Level"),
            5,
            help=tr("stress_help"),
            key="assess_stress",
        )
        steps = sleep_right.number_input(
            tr("steps"),
            min_value=_low("Daily Steps"),
            max_value=_high("Daily Steps"),
            value=6000,
            step=100,
            key="assess_steps",
        )

    st.subheader(tr("cardio"))
    with st.container(border=True):
        sys_col, dia_col, hr_col = st.columns(3)
        systolic = sys_col.number_input(
            tr("systolic"),
            min_value=_low("Systolic_BP"),
            max_value=_high("Systolic_BP"),
            value=120,
            step=1,
            help=tr("bp_help"),
            key="assess_systolic",
        )
        diastolic = dia_col.number_input(
            tr("diastolic"),
            min_value=_low("Diastolic_BP"),
            max_value=_high("Diastolic_BP"),
            value=80,
            step=1,
            key="assess_diastolic",
        )
        heart_rate = hr_col.number_input(
            tr("heart_rate"),
            min_value=_low("Heart Rate"),
            max_value=_high("Heart Rate"),
            value=72,
            step=1,
            key="assess_heart_rate",
        )

    submitted = st.button(tr("evaluate"), type="primary", key="evaluate_risk", width="stretch")

    if submitted:
        payload = {
            "Gender": gender,
            "Age": int(age),
            "Occupation": occupation,
            "BMI Category": bmi_category,
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
            st.error(tr("score_failed"))
            for message in error.errors:
                if "higher than diastolic" in message:
                    st.markdown(f"- {tr('bp_order')}")
                else:
                    st.markdown(f"- {message}")
            if st.session_state.get("assessment_result"):
                st.caption(tr("kept_result"))
        else:
            st.session_state["assessment_result"] = result
            st.session_state["assessment_payload"] = payload
            st.session_state["assessment_body"] = {
                "weight_kg": float(weight),
                "height_cm": float(height),
                "bmi": bmi,
                "category": bmi_category,
            }
            risk_level = result["recommendation"]["risk_level"]
            st.success(
                tr(
                    "saved",
                    bmi=format_bmi(bmi, bmi_category),
                    category=named("bmi", bmi_category),
                    label=named("class", result["label"]),
                    risk=named("risk", risk_level),
                )
            )

    if st.session_state.get("assessment_result"):
        st.button(
            tr("view_result"),
            type="primary",
            on_click=open_recommendations,
            width="stretch",
        )


def render_result() -> None:
    """Show the assessment stored by page 1."""

    st.header(tr("page_result"))
    result = st.session_state.get("assessment_result")
    if not result:
        st.info(tr("empty_result"))
        return

    st.caption(tr("result_caption"))
    render_body_summary()
    risk_level = result["recommendation"]["risk_level"]
    advice = ADVICE[current_lang()][result["label"]]
    _risk_banner(result["label"], risk_level)

    st.subheader(tr("probabilities"))
    probability_columns = st.columns(len(CLASS_ORDER))
    for column, label in zip(probability_columns, CLASS_ORDER):
        column.metric(named("class", label), f"{result['probabilities'][label]:.1%}")
    show_chart(_probability_figure(result["probabilities"]), height=280)

    st.subheader(tr("importance"))
    st.caption(tr("importance_caption"))
    show_chart(_importance_figure(result["importances"]))

    st.subheader(tr("comparison"))
    st.caption(tr("comparison_caption"))
    factors = result["factors"]
    if factors:
        for factor in factors:
            st.markdown(f"- {factor_text(factor)}")
    else:
        st.info(tr("no_factors"))

    st.subheader(tr("decision"))
    with st.container(border=True):
        st.markdown(f"**{tr('risk_word', level=named('risk', risk_level))}**")
        st.markdown(advice["decision"])
        for index, action in enumerate(advice["actions"], start=1):
            st.markdown(f"{index}. {action}")

    notes = result["support_notes"]
    if notes:
        st.subheader(tr("outside"))
        for note in notes:
            st.warning(note_text(note))

    payload = st.session_state.get("assessment_payload")
    if payload:
        with st.expander(tr("submitted")):
            rows = [
                {
                    "Field": named("feature", feature),
                    "Value": _profile_value(feature, payload.get(feature, "")),
                }
                for feature in FEATURES
            ]
            table = pd.DataFrame(rows).rename(columns={"Field": tr("field"), "Value": tr("value")})
            st.dataframe(table, hide_index=True, width="stretch")


def _profile_value(feature: str, value: object) -> str:
    """Show a stored profile value in the active language."""

    text = str(value)
    if feature == "Gender":
        return named("gender", text)
    if feature == "Occupation":
        return named("job", text)
    if feature == "BMI Category":
        return named("bmi", text)
    return text


def render_body_summary() -> None:
    """Show the weight, height, and BMI stored with the latest assessment."""

    body = st.session_state.get("assessment_body")
    if not body:
        return
    st.subheader(tr("body"))
    weight, height, bmi, category = st.columns(4)
    unit_kg = "กก." if current_lang() == "th" else "kg"
    unit_cm = "ซม." if current_lang() == "th" else "cm"
    weight.metric(tr("weight"), f"{body['weight_kg']:.1f} {unit_kg}")
    height.metric(tr("height"), f"{body['height_cm']:.1f} {unit_cm}")
    bmi.metric(tr("bmi_short"), format_bmi(body["bmi"], body["category"]))
    category.metric(tr("bmi_category"), named("bmi", body["category"]))
    st.caption(tr("bmi_formula"))


def render_eda(bundle: dict) -> None:
    """Filter the training table and draw the exploratory charts."""

    st.header(tr("page_eda"))
    st.caption(tr("eda_intro"))

    frame = bundle["frame"].copy()
    filtered = apply_chart_filters(frame)
    st.caption(tr("training_rows", count=len(frame), source=_source_label(bundle["meta"])))

    if filtered is None:
        st.warning(tr("need_filter"))
    elif filtered.empty:
        st.info(tr("no_rows"))
    else:
        st.caption(tr("chart_rows", count=len(filtered)))
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

    st.sidebar.subheader(tr("filters"))
    genders = sorted(frame["Gender"].astype(str).unique())
    occupations = sorted(frame["Occupation"].astype(str).unique())
    age_low = int(frame["Age"].min())
    age_high = int(frame["Age"].max())

    chosen_genders = st.sidebar.multiselect(
        tr("gender"),
        genders,
        default=genders,
        format_func=lambda value: named("gender", value),
        key="filter_gender",
    )
    chosen_occupations = st.sidebar.multiselect(
        tr("occupation"),
        occupations,
        default=occupations,
        format_func=lambda value: named("job", value),
        key="filter_occupation",
    )
    if age_low == age_high:
        age_range = (age_low, age_high)
        st.sidebar.caption(tr("every_age", age=age_low))
    else:
        age_range = st.sidebar.slider(
            tr("age_range"),
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
    st.subheader(tr("heatmap"))
    if len(filtered) < 3:
        st.info(tr("heatmap_need3"))
        return

    corr = filtered.loc[:, HEATMAP_COLUMNS].corr(numeric_only=True)
    labels = [named("feature", column) for column in HEATMAP_COLUMNS]
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
            colorbar={"title": tr("pearson")},
            text=text,
            texttemplate="%{text}",
            hovertemplate="%{y} and %{x}: %{z:.2f}<extra></extra>",
            xgap=2,
            ygap=2,
        )
    )
    style_figure(figure, 420, grid=False)
    figure.update_yaxes(autorange="reversed")
    figure.update_xaxes(tickangle=-30)
    figure.update_layout(margin={"l": 120, "r": 24, "t": 24, "b": 110})
    show_chart(figure)
    st.caption(_correlation_note(corr))


def render_scatter(filtered: pd.DataFrame) -> None:
    st.subheader(tr("scatter"))
    plot = filtered.copy()
    plot["disorder_label"] = plot[TARGET].map(lambda value: named("class", value))
    figure = px.scatter(
        plot,
        x="Sleep Duration",
        y="Stress Level",
        color="disorder_label",
        color_discrete_map={named("class", key): value for key, value in DISORDER_COLORS.items()},
        category_orders={"disorder_label": [named("class", label) for label in CLASS_ORDER]},
        hover_data=["Gender", "Occupation", "BMI Category", "Quality of Sleep", "Age"],
        labels={
            "Sleep Duration": tr("hours_axis"),
            "Stress Level": tr("stress"),
            "disorder_label": tr("class_header"),
        },
        opacity=0.75,
    )
    style_figure(figure, 460)
    show_chart(figure)
    st.caption(_scatter_note(filtered))


def render_prevalence(filtered: pd.DataFrame) -> None:
    st.subheader(tr("prevalence"))
    share = _disorder_share(filtered)
    note = _prevalence_note(share)
    share = share.copy()
    share["Occupation"] = share["Occupation"].map(lambda value: named("job", value))
    share["Sleep Disorder"] = share["Sleep Disorder"].map(lambda value: named("class", value))
    figure = px.bar(
        share,
        x="Occupation",
        y="percent",
        color="Sleep Disorder",
        barmode="group",
        custom_data=["count"],
        color_discrete_map={named("class", key): value for key, value in DISORDER_COLORS.items()},
        category_orders={"Sleep Disorder": [named("class", label) for label in CLASS_ORDER]},
        labels={
            "percent": tr("share_axis"),
            "Sleep Disorder": tr("class_header"),
            "Occupation": tr("occupation"),
        },
    )
    figure.update_traces(
        hovertemplate="%{x}<br>%{fullData.name}: %{y:.1f}%<br>"
        + tr("rows_hover")
        + ": %{customdata[0]}<extra></extra>"
    )
    style_figure(figure, 480)
    figure.update_xaxes(tickangle=-35)
    figure.update_layout(margin={"l": 48, "r": 24, "t": 24, "b": 120})
    show_chart(figure)
    st.caption(note)


def render_model_evaluation(meta: dict) -> None:
    """Show stratified cross-validation and the duplicate-row caveat."""

    st.subheader(tr("cv"))
    metrics = meta["metrics"]
    st.caption(tr("cv_caption", folds=metrics["folds"], count=meta["row_count"]))
    metric_columns = st.columns(4)
    labels = [
        ("accuracy", tr("accuracy")),
        ("precision_macro", tr("precision")),
        ("recall_macro", tr("recall")),
        ("f1_macro", tr("f1")),
    ]
    for column, (key, label) in zip(metric_columns, labels):
        column.metric(label, _mean_std_text(metrics[key]))

    per_class_rows = []
    for label in CLASS_ORDER:
        scores = metrics["per_class"][label]
        per_class_rows.append({
            tr("class_header"): named("class", label),
            tr("precision"): _mean_std_text(scores["precision"]),
            tr("recall"): _mean_std_text(scores["recall"]),
            tr("f1"): _mean_std_text(scores["f1"]),
        })
    st.dataframe(pd.DataFrame(per_class_rows), hide_index=True, width="stretch")

    counts = meta["class_counts"]
    count_text = ", ".join(
        f"{named('class', label)} {counts.get(label, 0)}" for label in CLASS_ORDER
    )
    st.caption(tr(
        "counts_line",
        counts=count_text,
        duplicates=meta["duplicate_feature_rows"],
        relabeled=meta["bmi_relabeled"],
    ))
    if meta.get("caveat"):
        st.warning(tr("caveat"))


def _class_count_metrics(filtered: pd.DataFrame) -> None:
    columns = st.columns(len(CLASS_ORDER) + 1)
    columns[0].metric(tr("filtered_rows"), len(filtered))
    for column, label in zip(columns[1:], CLASS_ORDER):
        column.metric(named("class", label), int((filtered[TARGET] == label).sum()))


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
            x=[named("class", label) for label in labels],
            y=values,
            marker_color=[DISORDER_COLORS[label] for label in labels],
            text=[f"{value:.1%}" for value in values],
            textposition="outside",
            hovertemplate="%{x}: %{y:.1%}<extra></extra>",
        )
    )
    style_figure(figure, 320)
    figure.update_yaxes(range=[0, 1.18], tickformat=".0%", title=tr("probability"))
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
            y=ordered["feature"].map(lambda feature: named("feature", feature)),
            orientation="h",
            marker_color="#2563EB",
            hovertemplate="%{y}: %{x:.1%}<extra></extra>",
        )
    )
    style_figure(figure, max(280, 32 * len(table) + 80))
    figure.update_xaxes(tickformat=".0%", title=tr("importance_axis"))
    peak = float(table["importance"].max())
    figure.update_layout(
        margin={"l": 160, "r": 24, "t": 16, "b": 48},
        xaxis_range=[0, max(0.2, peak * 1.25)],
    )
    return figure


def _correlation_note(corr: pd.DataFrame) -> str:
    value = corr.loc["Stress Level", "Sleep Duration"]
    if pd.isna(value):
        relation = tr("pearson_na")
    elif abs(float(value)) < 0.1:
        relation = tr("pearson_weak", value=f"{value:.2f}")
    elif float(value) < 0:
        relation = tr("pearson_neg", value=f"{value:.2f}")
    else:
        relation = tr("pearson_pos", value=f"{value:.2f}")
    return f"{relation} {tr('disorder_code')}"


def _scatter_note(filtered: pd.DataFrame) -> str:
    medians = filtered.groupby(TARGET)[["Sleep Duration", "Stress Level"]].median()
    parts = []
    for label in CLASS_ORDER:
        if label not in medians.index:
            continue
        parts.append(tr(
            "scatter_item",
            label=named("class", label),
            hours=f"{medians.loc[label, 'Sleep Duration']:.1f}",
            stress=f"{medians.loc[label, 'Stress Level']:.0f}",
        ))
    duplicate_rows = int(filtered.duplicated(subset=["Sleep Duration", "Stress Level"]).sum())
    overlap = tr("scatter_overlap", count=duplicate_rows) if duplicate_rows else ""
    return tr("scatter_median", parts="; ".join(parts)) + overlap


def _prevalence_note(share: pd.DataFrame) -> str:
    apnea = share[share["Sleep Disorder"] == "Sleep Apnea"].copy()
    if apnea.empty:
        return tr("prev_empty")
    totals = share.groupby("Occupation")["count"].sum()
    apnea["total"] = apnea["Occupation"].map(totals)
    if float(apnea["percent"].max()) == 0:
        return tr("prev_zero")
    stable = apnea[apnea["total"] >= 10]
    pool = stable if not stable.empty else apnea
    top = pool.sort_values(["percent", "count"], ascending=False).iloc[0]
    key = "prev_stable" if not stable.empty else "prev_any"
    return tr(
        key,
        job=named("job", top["Occupation"]),
        percent=f"{top['percent']:.0f}",
        count=int(top["count"]),
        total=int(top["total"]),
    )


def _risk_banner(label: str, risk_level: str) -> None:
    foreground, background = RISK_STYLE[risk_level]
    st.markdown(
        (
            f"<div style='background:{background};color:{foreground};"
            "padding:1rem 1.25rem;border-radius:12px;"
            f"border:1px solid {foreground};margin:0.5rem 0 1rem 0;'>"
            f"<div style='font-size:1rem;font-weight:650;'>"
            f"{tr('risk_word', level=named('risk', risk_level))}</div>"
            f"<div style='font-size:1.8rem;font-weight:700;line-height:1.2;'>"
            f"{named('class', label)}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def style_figure(figure: go.Figure, height: int, grid: bool = True) -> go.Figure:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font={"family": "Arial, sans-serif", "color": "#0F172A", "size": 16},
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
        return tr("synthetic")
    name = Path(source).name
    return name or "training table"


def _low(feature: str) -> int:
    return int(INPUT_LIMITS[feature][0])


def _high(feature: str) -> int:
    return int(INPUT_LIMITS[feature][1])


main()
