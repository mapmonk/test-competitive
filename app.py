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
    if 'Advertiser' in df.columns:
        return df
    for col in df.columns:
        if str(col).strip().lower() == 'brand':
            df = df.rename(columns={col: 'Advertiser'})
            return df
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
                if any("spend" in cell for cell in row) and any("channel" in cell for cell in row):
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
    return df[df['Media Channel'].isin(selected_channels)].copy()

def apply_channel_grouping(df, grouping_dict):
    df = df.copy()
    df['Media Channel Grouped'] = df['Media Channel'].map(grouping_dict).fillna(df['Media Channel'])
    return df

def compute_pie_data(df, group_col='Media Channel'):
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
    df = df.rename(columns=lambda x: x.strip())

    # ----------- ADVERTISER MANUAL ENTRY IF MISSING -----------
    advertisers = get_advertisers(df)
    manual_advertisers = []
    if not advertisers:
        st.warning("No advertisers or brands found in the uploaded files. Please manually enter the advertiser/brand names separated by commas.")
        manual_input = st.text_input("Enter advertiser/brand names (comma separated):")
        if manual_input:
            manual_advertisers = [name.strip() for name in manual_input.split(",") if name.strip()]
            # Add new column to df if not present
            if 'Advertiser' not in df.columns:
                if df.shape[0] > 0:
                    df['Advertiser'] = np.nan
                else:
                    # Create a dummy DataFrame with only Advertiser column for UI continuity
                    df = pd.DataFrame({'Advertiser': manual_advertisers})
            # Fill missing advertisers in the data (if empty), otherwise just use these for selection
            df['Advertiser'] = df['Advertiser'].fillna('')
            for idx, val in enumerate(df['Advertiser']):
                if not val and idx < len(manual_advertisers):
                    df.at[idx, 'Advertiser'] = manual_advertisers[idx]
            advertisers = manual_advertisers

    if not advertisers:
        st.error("No advertisers/brands available for selection. Please check your files or enter advertiser names above.")
        st.stop()

    st.success(f"Loaded {len(df)} rows from {len(uploaded_files)} files.")

    # ----------- PRIMARY ADVERTISER SELECTION -----------
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
    if primary in total_spend.index:
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
