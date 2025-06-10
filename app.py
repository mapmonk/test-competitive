import streamlit as st
import pandas as pd
import numpy as np
import io
from collections import defaultdict
import matplotlib.pyplot as plt

# ------------------- DATA UPLOAD AND PARSING -------------------

@st.cache_data(show_spinner=False)
def standardize_columns(df):
    # If 'Brand' is present, rename to 'Advertiser'
    if 'Brand' in df.columns and 'Advertiser' not in df.columns:
        df = df.rename(columns={'Brand': 'Advertiser'})
    elif 'brand' in df.columns and 'Advertiser' not in df.columns:
        df = df.rename(columns={'brand': 'Advertiser'})
    return df

@st.cache_data(show_spinner=False)
def parse_nielsen(file):
    # Detect if this is a Nielsen Ad Intel report with the special "Report" tab format
    xls = pd.ExcelFile(file)
    if "Report" in xls.sheet_names:
        # Read the "Report" sheet without treating any row as header
        df_raw = pd.read_excel(xls, sheet_name="Report", header=None)
        # Search for "Brand" in cell A4
        if df_raw.shape[0] >= 4 and str(df_raw.iloc[3, 0]).strip().lower() == "brand":
            # Find the first fully empty row after the "Brand" header, or end of file
            brand_col = df_raw.iloc[4:, 0].dropna().reset_index(drop=True)
            # We'll treat the column below A4 as 'Advertiser' names (could be brands)
            advertisers = brand_col.tolist()
            # For demonstration, we'll prompt the user to map these brands to the rest of the data if needed.
            # We'll also try to extract the actual data (assuming typical Ad Intel structure)
            # Find the first row after A4 that looks like the column headers (often row 5 or 6)
            data_start_row = 3
            # Find actual data table: search for a header row containing "Spend" or "Media Channel"
            possible_headers = None
            for i in range(4, min(df_raw.shape[0], 15)):
                row = df_raw.iloc[i].astype(str).str.lower().tolist()
                if any("spend" in cell for cell in row) and any("channel" in cell for cell in row):
                    possible_headers = i
                    break
            if possible_headers is not None:
                nielsen_data = pd.read_excel(
                    xls, sheet_name="Report", header=possible_headers)
                nielsen_data = standardize_columns(nielsen_data)
                # If there's a "Brand" column, treat it as "Advertiser"
                nielsen_data = nielsen_data.rename(
                    columns={"Brand": "Advertiser", "brand": "Advertiser"}
                )
                return nielsen_data
            else:
                # Fallback: just try to read with headers at row 5 (A6)
                nielsen_data = pd.read_excel(
                    xls, sheet_name="Report", header=5)
                nielsen_data = standardize_columns(nielsen_data)
                return nielsen_data
        else:
            # Not the expected Ad Intel format, try normal parsing
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
    return sorted(df['Advertiser'].dropna().unique())

def get_media_channels(df):
    return sorted(df['Media Channel'].dropna().unique())

def filter_by_channel(df, selected_channels):
    return df[df['Media Channel'].isin(selected_channels)].copy()

def apply_channel_grouping(df, grouping_dict):
    df = df.copy()
    df['Media Channel Grouped'] = df['Media Channel'].map(grouping_dict).fillna(df['Media Channel'])
    return df

def compute_pie_data(df, group_col='Media Channel'):
    # Returns a dict: advertiser -> {channel: spend%}
    pie_data = defaultdict(dict)
    for adv, subdf in df.groupby('Advertiser'):
        total = subdf['Spend'].sum()
        if total == 0: continue
        channel_sums = subdf.groupby(group_col)['Spend'].sum()
        for channel, spend in channel_sums.items():
            pie_data[adv][channel] = spend / total * 100
    return pie_data

def compute_total_spend(df):
    return df.groupby('Advertiser')['Spend'].sum().sort_values(ascending=False)

def get_top_channels(pie, threshold=0.5):
    # pie: dict channel->percent
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
    # Gather all channels appearing in any pie
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
    df = df.rename(columns=lambda x: x.strip())
    st.success(f"Loaded {len(df)} rows from {len(uploaded_files)} files.")

    # ----------- PRIMARY ADVERTISER SELECTION -----------
    advertisers = get_advertisers(df)
    if not advertisers:
        st.warning("No advertisers or brands found in the uploaded files. Please check your files and try again.")
        st.stop()
    primary = st.selectbox("Select your primary advertiser (brand):", advertisers)
    competitors = [a for a in advertisers if a != primary]

    # ----------- FILTER BY MEDIA CHANNEL -----------
    all_channels = get_media_channels(df)
    selected_channels = st.multiselect(
        "Filter by media channel (leave blank for all):",
        all_channels,
        default=all_channels
    )
    if selected_channels:
        df = filter_by_channel(df, selected_channels)

    # ----------- CUSTOM CHANNEL GROUPING -----------
    st.markdown("**Custom Group Media Channels** (optional):")
    grouping_dict = {}
    for ch in all_channels:
        group = st.text_input(f"Group for '{ch}'", value=ch, key=f"group_{ch}")
        grouping_dict[ch] = group
    df = apply_channel_grouping(df, grouping_dict)
    group_col = "Media Channel Grouped" if any(grouping_dict[ch] != ch for ch in all_channels) else "Media Channel"

    # ----------- PIE CHART DATA -----------
    pie_data = compute_pie_data(df, group_col=group_col)
    total_spend = compute_total_spend(df)
    primary_pie = pie_data.get(primary, {})
    competitor_pies = {a: pie_data[a] for a in competitors if a in pie_data}

    # ----------- SUMMARY STATISTICS -----------
    st.subheader("Summary Statistics")
    summary = []
    pattern_lines = compare_pie(primary_pie, competitor_pies, threshold_similar=5, threshold_diff=20)
    if pattern_lines:
        summary.extend(pattern_lines)
    rank = list(total_spend.index).index(primary) + 1
    n_adv = len(total_spend)
    summary.append(f"- Primary Advertiser ranks {rank} out of {n_adv} in total ad spend.")
    top_channel_lines = highlight_top_channels(primary_pie, competitor_pies)
    if top_channel_lines:
        summary.extend(top_channel_lines)
    if summary:
        st.markdown("\n".join(summary))
    else:
        st.markdown("No notable similarities or differences in spend patterns detected.")

    # ----------- PIE CHARTS -----------
    st.subheader("Media Mix Pie Charts (each advertiser/brand)")
    pie_imgs = {}
    ncols = min(3, len(advertisers))
    cols = st.columns(ncols)
    for idx, adv in enumerate(advertisers):
        pie = pie_data.get(adv, {})
        if not pie: continue
        with cols[idx % ncols]:
            fig, ax = plt.subplots()
            wedges, texts, autotexts = ax.pie(
                pie.values(),
                labels=pie.keys(),
                autopct='%1.1f%%',
                startangle=140,
                textprops=dict(color="w"),
                wedgeprops=dict(width=0.5 if adv == primary else 0.3)
            )
            # Highlight primary advertiser
            ax.set_title(adv + (" (Primary)" if adv == primary else " (Competitor)"), color=("red" if adv == primary else "black"))
            st.pyplot(fig)
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            pie_imgs[adv] = buf
            plt.close(fig)

    # ----------- DOWNLOAD DATA (EXCEL) -----------
    st.subheader("Download Options")
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df['Advertiser'].isin(advertisers)]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, sheet_name='Filtered Media Mix', index=False)
    st.download_button(
        "Download Filtered Data as Excel",
        data=output.getvalue(),
        file_name="media_mix_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ----------- DOWNLOAD PIE CHARTS (IMAGES) -----------
    for adv, buf in pie_imgs.items():
        st.download_button(
            f"Download Pie Chart for {adv}",
            data=buf.getvalue(),
            file_name=f"media_mix_{adv}.png",
            mime="image/png"
        )
else:
    st.info("Please upload at least one Excel file to begin.")

# ------------------- END OF APP -------------------
