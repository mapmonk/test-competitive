import matplotlib.pyplot as plt
from typing import Dict
import streamlit as st
import pandas as pd
import pptx
from pptx.util import Inches
import io
from typing import Dict, List
from openpyxl import load_workbook
from pptx import Presentation
from pptx.util import Pt

# --- Helper Functions ---

def extract_brand_name(excel_file) -> str:
    wb = load_workbook(filename=excel_file, read_only=True, data_only=True)
    cover = wb['Cover']
    brand = cover['B4'].value
    wb.close()
    return brand

def parse_daily_tab(excel_file, tab_name: str) -> pd.DataFrame:
    return pd.read_excel(excel_file, sheet_name=tab_name)

def parse_slides_text(slides_file) -> str:
    prs = Presentation(slides_file)
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                text.append(shape.text)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            text.append(slide.notes_slide.notes_text_frame.text)
    return "\n".join(text)

def generate_pptx(selected_charts: Dict[str, plt.Figure]) -> bytes:
    prs = Presentation()
    for chart_title, fig in selected_charts.items():
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank slide
        left = Inches(1)
        top = Inches(1)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        slide.shapes.add_picture(buf, left, top, width=Inches(6), height=Inches(4))
        title_shape = slide.shapes.title
        if title_shape:
            title_shape.text = chart_title
    pptx_bytes = io.BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    return pptx_bytes.read()

# --- Streamlit UI ---

st.title("Competitive Media Spend Dashboard")

# Multi-file upload for Excel files (one per brand)
st.header("1. Upload Competitive Brand Excel Files")
uploaded_excel_files = st.file_uploader(
    "Upload one or more brand Excel files (with Cover, Daily Spend, Daily Impressions tabs):",
    type=["xlsx"], accept_multiple_files=True
)

# Upload last Google Slides export
st.header("2. (Optional) Upload Previous Google Slides Export")
uploaded_slide = st.file_uploader(
    "Upload previous exported competitive analysis (pptx, export from Google Slides):",
    type=["pptx"]
)

brand_data = {}
if uploaded_excel_files:
    for file in uploaded_excel_files:
        brand = extract_brand_name(file)
        spend_df = parse_daily_tab(file, "Daily Spend")
        imp_df = parse_daily_tab(file, "Daily Impressions")
        brand_data[brand] = {"spend": spend_df, "impressions": imp_df}

if uploaded_slide:
    previous_slide_text = parse_slides_text(uploaded_slide)
    st.text_area("Text from previous Google Slides (for reference to past analyses):", previous_slide_text, height=200)

# TODO: Data aggregation, trend/outlier detection, and chart generation
# Here you would implement: 
# - Spend mix comparisons
# - Partner/channel mix and ranking
# - Time period aggregation (daily/weekly/monthly)
# - Insights/explanations referencing previous analysis

st.header("3. Select Insights/Charts to Export")
# Placeholder: in real app, dynamically show generated charts/insights
selected_charts = {}
# Example: st.checkbox("Spend Trend by Brand"), add charts to selected_charts

# For now, just export a blank file for demonstration
if st.button("Export Selected Insights to PowerPoint"):
    pptx_bytes = generate_pptx(selected_charts)
    st.download_button(
        label="Download PPTX",
        data=pptx_bytes,
        file_name="competitive_analysis.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

st.info("This is a starter app. The next step is to implement data aggregation, insight generation, and chart rendering.")
