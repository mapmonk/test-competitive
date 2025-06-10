import os
import streamlit as st
import pandas as pd
import plotly.express as px
import io
import tempfile
import openai
from pptx import Presentation
from openpyxl import load_workbook
from datetime import datetime

# --- Helper Functions ---

def extract_brand_name(excel_file) -> str:
    wb = load_workbook(filename=excel_file, read_only=True, data_only=True)
    cover = wb['Cover']
    brand = cover['B4'].value
    wb.close()
    return brand.strip() if brand else "Unknown Brand"

def parse_daily_tab(excel_file, tab_name: str) -> pd.DataFrame:
    df = pd.read_excel(excel_file, sheet_name=tab_name)
    # Try to standardize date column
    date_col = next((col for col in df.columns if 'date' in col.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
    return df

def parse_slides_text(slides_file) -> str:
    prs = Presentation(slides_file)
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            text.append(slide.notes_slide.notes_text_frame.text)
    return "\n".join(text)

def aggregate_data(df, date_col, value_col, group_cols=[], freq='D'):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    agg = df.groupby(group_cols + [pd.Grouper(freq=freq)])[value_col].sum().reset_index()
    return agg

def find_outliers(df, value_col):
    q1 = df[value_col].quantile(0.25)
    q3 = df[value_col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = df[(df[value_col] < lower) | (df[value_col] > upper)]
    return outliers

def get_time_periods():
    return {
        "Daily": 'D',
        "Weekly": 'W',
        "Monthly": 'M',
        "Quarterly": 'Q',
        "Yearly": 'Y'
    }

def build_partner_mix_chart(agg_df, brand, value_col='Spend', time_period='Monthly'):
    fig = px.bar(
        agg_df, 
        x='Media Partner', 
        y=value_col,
        color='Media Partner',
        title=f"{brand}: {value_col} by Media Partner ({time_period})",
        labels={value_col: f"{value_col}", 'Media Partner': "Partner"}
    )
    return fig

def build_trend_chart(agg_df, brand, value_col='Spend', time_period='Monthly'):
    fig = px.line(
        agg_df, 
        x='Date', 
        y=value_col, 
        color='Media Partner',
        title=f"{brand}: {value_col} Trend by Partner ({time_period})"
    )
    return fig

def build_brand_comparison_chart(all_brands_agg, value_col='Spend', time_period='Monthly'):
    fig = px.bar(
        all_brands_agg, 
        x='Brand', 
        y=value_col, 
        color='Media Partner',
        barmode='group',
        title=f"Brand Comparison: {value_col} by Partner ({time_period})"
    )
    return fig

def build_seasonality_chart(agg_df, brand, value_col='Spend'):
    agg_df['Month'] = agg_df['Date'].dt.month
    fig = px.box(
        agg_df, 
        x='Month', 
        y=value_col, 
        color='Media Partner',
        title=f"{brand}: Seasonality of {value_col} by Month"
    )
    return fig

def summarize_insights_with_gpt(brand_data, previous_slide_text, period_label, outliers, top_partners, trends, seasonality, openai_api_key):
    openai.api_key = openai_api_key
    prompt = f"""
You are a media analyst. Write a concise outline of competitive media spend insights for a slide presentation. 
Reference findings compared to the last analysis (below) if relevant.

Previous Analysis Summary:
{previous_slide_text}

Current Key Findings ({period_label}):
- Spending outliers: {outliers}
- Top partners: {top_partners}
- Key trends: {trends}
- Seasonality notes: {seasonality}

Structure your outline with bullets and clear, actionable statements. Reference previous analysis as appropriate (e.g., "Similar to previous report...").
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()

# --- Streamlit UI ---

st.set_page_config(layout="wide")
st.title("Competitive Media Spend Dashboard")

# 1. Upload Brand Excel Files
st.header("1. Upload Competitive Brand Excel Files")
uploaded_excel_files = st.file_uploader(
    "Upload one or more brand Excel files (with Cover, Daily Spend, Daily Impressions tabs):",
    type=["xlsx"], accept_multiple_files=True
)

# 2. Upload Last Google Slides (pptx)
st.header("2. (Optional) Upload Previous Google Slides Export")
uploaded_slide = st.file_uploader(
    "Upload previous exported competitive analysis (.pptx):",
    type=["pptx"]
)

previous_slide_text = ""
if uploaded_slide:
    previous_slide_text = parse_slides_text(uploaded_slide)
    with st.expander("Previous Analysis Outline", expanded=False):
        st.write(previous_slide_text)

# 3. Data Processing
brand_data = {}
if uploaded_excel_files:
    for file in uploaded_excel_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        brand = extract_brand_name(tmp_path)
        spend_df = parse_daily_tab(tmp_path, "Daily Spend")
        imp_df = parse_daily_tab(tmp_path, "Daily Impressions")
        brand_data[brand] = {"spend": spend_df, "impressions": imp_df}
        os.remove(tmp_path)

if not brand_data:
    st.warning("Please upload at least one brand Excel file to proceed.")
    st.stop()

# 4. Visualization and Analysis Controls
st.header("3. Data Analysis & Visualization")
time_periods = get_time_periods()
time_period_label = st.selectbox("Select time period for analysis", list(time_periods.keys()), index=2)
freq = time_periods[time_period_label]
selected_charts = {}

all_brands_agg_list = []

for brand, data in brand_data.items():
    spend_df = data['spend']
    # Guess columns
    date_col = next((col for col in spend_df.columns if 'date' in col.lower()), spend_df.columns[0])
    partner_col = next((col for col in spend_df.columns if 'partner' in col.lower()), spend_df.columns[1])
    value_col = next((col for col in spend_df.columns if 'spend' in col.lower()), spend_df.columns[2])
    spend_df.rename(columns={date_col: 'Date', partner_col: 'Media Partner', value_col: 'Spend'}, inplace=True)
    # Aggregate for selected period
    agg = aggregate_data(spend_df, 'Date', 'Spend', group_cols=['Media Partner'], freq=freq)
    agg['Brand'] = brand
    all_brands_agg_list.append(agg)
    # Partner mix chart
    if st.checkbox(f"Show {brand}: Partner Spend Mix Chart"):
        fig_mix = build_partner_mix_chart(agg, brand, value_col='Spend', time_period=time_period_label)
        st.plotly_chart(fig_mix, use_container_width=True)
        selected_charts[f"{brand} Partner Mix"] = fig_mix
    # Trend chart
    if st.checkbox(f"Show {brand}: Spend Trend Chart"):
        agg_trend = aggregate_data(spend_df, 'Date', 'Spend', group_cols=['Media Partner'], freq=freq)
        agg_trend.rename(columns={f'Date': 'Date'}, inplace=True)
        fig_trend = build_trend_chart(agg_trend, brand, value_col='Spend', time_period=time_period_label)
        st.plotly_chart(fig_trend, use_container_width=True)
        selected_charts[f"{brand} Spend Trend"] = fig_trend
    # Seasonality chart
    if st.checkbox(f"Show {brand}: Spend Seasonality Chart"):
        daily_agg = aggregate_data(spend_df, 'Date', 'Spend', group_cols=['Media Partner'], freq='D')
        fig_season = build_seasonality_chart(daily_agg, brand, value_col='Spend')
        st.plotly_chart(fig_season, use_container_width=True)
        selected_charts[f"{brand} Seasonality"] = fig_season
    # Outliers
    outliers = find_outliers(agg, 'Spend')
    if not outliers.empty and st.checkbox(f"Show {brand}: Outlier Spend Bars"):
        st.dataframe(outliers)

# Brand comparison chart
all_brands_agg = pd.concat(all_brands_agg_list)
if st.checkbox("Show Brand Comparison Chart"):
    fig_comp = build_brand_comparison_chart(all_brands_agg, value_col='Spend', time_period=time_period_label)
    st.plotly_chart(fig_comp, use_container_width=True)
    selected_charts["Brand Comparison"] = fig_comp

# 5. Generate Insights Outline using GPT-4.1
st.header("4. Generate Insights Outline (AI)")
openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    st.info("Set your OpenAI API key in Streamlit secrets or the OPENAI_API_KEY environment variable to use AI insights.")

if st.button("Generate AI Insights Outline") and openai_api_key:
    # Gather some basic findings for the prompt
    outlier_brands = []
    top_partners = []
    trends = []
    seasonality = []
    for brand, data in brand_data.items():
        spend_df = data['spend']
        # Guess columns
        date_col = next((col for col in spend_df.columns if 'date' in col.lower()), spend_df.columns[0])
        partner_col = next((col for col in spend_df.columns if 'partner' in col.lower()), spend_df.columns[1])
        value_col = next((col for col in spend_df.columns if 'spend' in col.lower()), spend_df.columns[2])
        spend_df.rename(columns={date_col: 'Date', partner_col: 'Media Partner', value_col: 'Spend'}, inplace=True)
        agg = aggregate_data(spend_df, 'Date', 'Spend', group_cols=['Media Partner'], freq=freq)
        agg['Brand'] = brand
        outliers = find_outliers(agg, 'Spend')
        if not outliers.empty:
            outlier_brands.append(f"{brand}: {outliers['Media Partner'].tolist()}")
        # Top partners
        top = agg.sort_values('Spend', ascending=False).head(3)['Media Partner'].tolist()
        top_partners.append(f"{brand}: {top}")
        # Trends (simple slope check)
        trend = "increasing" if agg['Spend'].diff().mean() > 0 else "decreasing"
        trends.append(f"{brand}: Spend trend is {trend}")
        # Seasonality (variance by month)
        agg['Month'] = agg['Date'].dt.month
        by_month = agg.groupby('Month')['Spend'].mean()
        max_month = by_month.idxmax()
        seasonality.append(f"{brand}: peak spend in month {max_month}")

    period_label = time_period_label
    ai_outline = summarize_insights_with_gpt(
        brand_data, previous_slide_text, period_label, outlier_brands, top_partners, trends, seasonality, openai_api_key
    )
    st.subheader("AI-Generated Insights Outline")
    st.markdown(ai_outline)

# 6. Downloadable Export (PowerPoint)
from pptx.util import Inches
def generate_pptx(selected_charts):
    prs = Presentation()
    for chart_title, fig in selected_charts.items():
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank slide
        left = Inches(1)
        top = Inches(1)
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        buf.seek(0)
        slide.shapes.add_picture(buf, left, top, width=Inches(6), height=Inches(4))
        # Add the title above the image
        title_shape = slide.shapes.title
        if title_shape:
            title_shape.text = chart_title
    pptx_bytes = io.BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    return pptx_bytes.read()

st.header("5. Export Selected Charts/Insights")
if st.button("Export to PowerPoint"):
    if selected_charts:
        pptx_bytes = generate_pptx(selected_charts)
        st.download_button(
            label="Download PPTX",
            data=pptx_bytes,
            file_name="competitive_analysis.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    else:
        st.warning("Select at least one chart to export.")

st.info("Data analysis, chart visualization, and AI-generated outline are enabled. Further customization encouraged!")
