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

def build_partner_mix_chart(agg_df, brand, value_col='Spend', time_period*

