import streamlit as st
import pandas as pd
import numpy as np
import io
from collections import defaultdict
import matplotlib.pyplot as plt

# ------------------- DATA UPLOAD AND PARSING -------------------

@st.cache_data(show_spinner=False)
def standardize_columns(df):
    # Rename 'Brand' to 'Advertiser' if 'Advertiser' not present
    if 'Advertiser' not in df.columns:
        for col in df.columns:
            if str(col).strip().lower() == 'brand':
                df = df.rename(columns={col: 'Advertiser'})
                break
    # Rename 'Media Type' to 'Media Channel' if 'Media Channel' not present
    if 'Media Channel' not in df.columns:
        for col in df.columns:
            if str(col).strip().lower() == 'media type':
                df = df.rename(columns={col: 'Media Channel'})
                break
    return df

@st.cache_data(show_spinner=False)
def parse_nielsen(file):
    # Detect if this is a Nielsen Ad Intel report with the special "Report" tab format
    xls = pd.ExcelFile(file)
    if "Report" in xls.sheet_names:
        df_raw = pd.read_excel(xls, sheet_name="Report", header=None)
        if df_raw.shape[0] >= 4 and str(df_raw.iloc[3, 0]).strip().lower() == "brand":
            # Try to find header row with "Spend" and "Media Channel"
            possible_headers = None
            for i in range(4, min(df_raw.shape[0], 15)):
                row = df_raw.iloc[i].astype(str).str.lower().tolist()
                if any("spend" in cell for cell in row) and (any("channel" in cell for cell in row) or any("media type" in cell for cell in row)):
                    possible_headers = i
                    break
            if possible_headers is not None:
                nielsen_data = pd.read_excel(
                    xls, sheet_name="Report", header=possible_headers)
                nielsen_data = standardize_columns(nielsen_data)
                nielsen_data = nielsen_data.rename(
                    columns={"Brand": "Advertiser", "brand": "Advertiser"}
                )
                return nielsen_data
            else:
                nielsen_data = pd.read_excel(
                    xls, sheet_name="Report", header=5)
                nielsen_data = standardize_columns(nielsen_data)
                return nielsen_data
        else:
            df = pd.read_excel(xls, sheet_name="Report")
            df = standardize_columns(df)
            return df
    else:
        df = pd.read_excel(file)
        df = standardize_columns(df)
        return df

@st.cache_data(show_spinner=False)
def parse_pathmatics(file):
    df = pd.read_excel(file)
    df = standardize_columns(df)
    return df

@st.cache_data(show_spinner=False)
def parse_semrush(file):
    df = pd.read_excel(file)
    df = standardize_columns(df)
    return df

def parse_files(files):
    data = []
    for file in files:
        name = file.name.lower()
        if "nielsen" in name:
            data.append(parse_nielsen(file))
        elif "pathmatics" in name:
            data.append(parse_pathmatics(file))
        elif "semrush" in name:
            data.append(parse_semrush(file))
        else:
            df = pd.read_excel(file)
            df = standardize_columns(df)
            data.append(df)
    return pd.concat(data, ignore_index=True)

# ------------------- HELPER FUNCTIONS -------------------

def get_advertisers(df):
    if 'Advertiser' not in df.columns:
        return []
    return sorted(df['Advertiser'].dropna().unique())

def get_media_channels(df):
    if 'Media Channel' not in df.columns:
        return []
    return sorted(df['Media Channel'].dropna().unique())

def filter_by_channel(df, selected_channels):
    if 'Media Channel' not in df.columns:
        return df.copy()
    return df[df['Media Channel'].isin(selected_channels)].copy()

def apply_channel_grouping(df, grouping_dict):
    if 'Media Channel' not in df.columns:
        st.error("The uploaded data does not have a 'Media Channel' column.")
        return df
    df = df.copy()
    df['Media Channel Grouped'] = df['Media Channel'].map(grouping_dict).fillna(df['Media Channel'])
    return df

def compute_pie_data(df, group_col='Media Channel'):
    pie_data = defaultdict(dict)
    if 'Advertiser' not in df.columns or group_col not in df.columns or 'Spend' not in df.columns:
        return pie_data
    for adv, subdf in df.groupby('Advertiser'):
        total = subdf['Spend'].sum()
        if total == 0:
            continue
        channel_sums = subdf.groupby(group_col)['Spend'].sum()
        for channel, spend in channel_sums.items():
            pie_data[adv][channel] = spend / total * 100
    return pie_data

def compute_total_spend(df):
    if 'Advertiser' not in df.columns or 'Spend' not in df.columns:
        return pd.Series(dtype=float)
    return df.groupby('Advertiser')['Spend'].sum().sort_values(ascending=False)

def get_top_channels(pie, threshold=0.5):
    sorted_channels = sorted(pie.items(), key=lambda x: x[1], reverse=True)
    total = 0
    top_channels = []
    for ch, pct in sorted_channels:
        total += pct / 100
        top_channels.append(ch)
        if total >= threshold:
            break
    return top_channels

def compare_pie(primary_pie, competitor_pies, threshold_similar=5, threshold_diff=20):
    summary = []
    channels = set(primary_pie.keys())
    for comp in competitor_pies:
        channels.update(comp.keys())

    for channel in channels:
        p_val = primary_pie.get(channel, 0)
        for comp_name, comp_pie in competitor_pies.items():
            c_val = comp_pie.get(channel, 0)
            diff = abs(p_val - c_val)
            if diff < threshold_similar:
                summary.append(f"- Similar spend on {channel} (within 5%) between Primary and {comp_name}.")
            elif diff > threshold_diff:
                direction = "more" if p_val > c_val else "less"
                summary.append(f"- Primary spends >20% {direction} on {channel} than {comp_name}.")
    return summary

def highlight_top_channels(primary_pie, competitor_pies):
    lines = []
    primary_top = get_top_channels(primary_pie)
    for comp_name, comp_pie in competitor_pies.items():
        comp_top = get_top_channels(comp_pie)
        shared = set(primary_top) & set(comp_top)
        if shared:
            lines.append(f"- Top channels shared with {comp_name}: {', '.join(shared)}.")
    return lines

# ------------------- UI LAYOUT -------------------

st.title("Advertiser (Brand) Media Mix Dashboard")

uploaded_files = st.file_uploader(
    "Upload Nielsen, Pathmatics, SEM Rush Excel files (multiple allowed):",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    # Parse and merge all files
    df = parse_files(uploaded_files)
    # Standardize columns if needed
    advertisers = get_advertisers(df)
    if not advertisers:
        st.warning("No advertisers found in the uploaded data.")
        st.stop()

    st.sidebar.header("Controls")
    primary_adv = st.sidebar.selectbox("Select Primary Advertiser", advertisers)
    media_channels = get_media_channels(df)
    selected_channels = st.sidebar.multiselect("Filter Media Channels", media_channels, default=media_channels)
    
    df_filtered = filter_by_channel(df, selected_channels)

    # Channel grouping
    st.sidebar.subheader("Custom Channel Grouping")
    channel_grouping = {}
    for channel in media_channels:
        group = st.sidebar.text_input(f"Group for {channel}", value=channel)
        channel_grouping[channel] = group
    df_grouped = apply_channel_grouping(df_filtered, channel_grouping)
    
    # Pie data
    group_col = "Media Channel Grouped" if "Media Channel Grouped" in df_grouped.columns else "Media Channel"
    pie_data = compute_pie_data(df_grouped, group_col=group_col)

    if primary_adv not in pie_data:
        st.warning(f"No data for primary advertiser: {primary_adv}")
        st.stop()

    competitor_pies = {adv: pie for adv, pie in pie_data.items() if adv != primary_adv}

    # Pie charts
    st.subheader("Media Mix Pie Charts")
    cols = st.columns(len(pie_data))
    for idx, (adv, pie) in enumerate(pie_data.items()):
        with cols[idx]:
            plt.figure(figsize=(4, 4))
            plt.pie(pie.values(), labels=pie.keys(), autopct='%1.1f%%', startangle=140)
            plt.title(adv)
            st.pyplot(plt)
            plt.close()

    # Summary
    st.subheader("Summary Statistics")
    summary = compare_pie(pie_data[primary_adv], competitor_pies)
    shared_top = highlight_top_channels(pie_data[primary_adv], competitor_pies)
    st.markdown("#### Similarities/Differences")
    st.markdown("\n".join(summary) if summary else "No major similarities or differences found.")
    st.markdown("#### Shared Top Channels")
    st.markdown("\n".join(shared_top) if shared_top else "No top channels shared.")

    # Rankings
    st.subheader("Advertiser Ranking by Total Spend")
    total_spend = compute_total_spend(df_grouped)
    st.dataframe(total_spend)

    # Export options
    st.subheader("Export")
    out_excel = io.BytesIO()
    df_grouped.to_excel(out_excel, index=False, engine='xlsxwriter')
    st.download_button("Download Data as Excel", out_excel.getvalue(), file_name="media_mix.xlsx")

    # Pie chart export
    for adv, pie in pie_data.items():
        plt.figure(figsize=(4, 4))
        plt.pie(pie.values(), labels=pie.keys(), autopct='%1.1f%%', startangle=140)
        plt.title(adv)
        out_img = io.BytesIO()
        plt.savefig(out_img, format='png')
        st.download_button(f"Download {adv} Pie Chart as PNG", out_img.getvalue(), file_name=f"{adv}_pie.png")
        plt.close()
else:
    st.info("Please upload at least one file to begin.")
