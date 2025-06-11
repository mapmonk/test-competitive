import streamlit as st
import pandas as pd
import numpy as np
import io
from collections import defaultdict
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional

# ------------------- CONSTANTS -------------------
COL_ADVERTISER = "Advertiser"
COL_MEDIA_CHANNEL = "Media Channel"
COL_SPEND = "Spend"
COL_GROUPED = "Media Channel Grouped"
REQUIRED_COLS = [COL_ADVERTISER, COL_MEDIA_CHANNEL, COL_SPEND]

# ------------------- DATA UPLOAD AND PARSING -------------------

@st.cache_data(show_spinner=False)
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names for consistency across different sources."""
    col_map = {col.lower().strip(): col for col in df.columns}
    if COL_ADVERTISER not in df.columns:
        for col in df.columns:
            if str(col).strip().lower() == "brand":
                df = df.rename(columns={col: COL_ADVERTISER})
                break
    if COL_MEDIA_CHANNEL not in df.columns:
        for col in df.columns:
            if str(col).strip().lower() == "media type":
                df = df.rename(columns={col: COL_MEDIA_CHANNEL})
                break
    return df

@st.cache_data(show_spinner=False)
def parse_nielsen(file) -> pd.DataFrame:
    """Parses Nielsen-formatted Excel files."""
    try:
        xls = pd.ExcelFile(file)
        if "Report" in xls.sheet_names:
            df_raw = pd.read_excel(xls, sheet_name="Report", header=None)
            if df_raw.shape[0] >= 4 and str(df_raw.iloc[3, 0]).strip().lower() == "brand":
                # Try to find header row
                for i in range(4, min(df_raw.shape[0], 15)):
                    row = df_raw.iloc[i].astype(str).str.lower().tolist()
                    if any("spend" in cell for cell in row) and (any("channel" in cell for cell in row) or any("media type" in cell for cell in row)):
                        nielsen_data = pd.read_excel(xls, sheet_name="Report", header=i)
                        nielsen_data = standardize_columns(nielsen_data)
                        return nielsen_data
                # Fallback: header at row 5
                nielsen_data = pd.read_excel(xls, sheet_name="Report", header=5)
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
    except Exception as e:
        st.error(f"Error parsing Nielsen file: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def parse_pathmatics(file) -> pd.DataFrame:
    """Parses Pathmatics-formatted Excel files."""
    try:
        df = pd.read_excel(file)
        df = standardize_columns(df)
        return df
    except Exception as e:
        st.error(f"Error parsing Pathmatics file: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def parse_semrush(file) -> pd.DataFrame:
    """Parses SEMrush-formatted Excel files."""
    try:
        df = pd.read_excel(file)
        df = standardize_columns(df)
        return df
    except Exception as e:
        st.error(f"Error parsing SEMrush file: {e}")
        return pd.DataFrame()

def parse_files(files) -> pd.DataFrame:
    """Parses and merges multiple uploaded files."""
    data = []
    for file in files:
        name = file.name.lower()
        if "nielsen" in name:
            df = parse_nielsen(file)
        elif "pathmatics" in name:
            df = parse_pathmatics(file)
        elif "semrush" in name:
            df = parse_semrush(file)
        else:
            try:
                df = pd.read_excel(file)
                df = standardize_columns(df)
            except Exception as e:
                st.error(f"Error parsing file {file.name}: {e}")
                continue
        if not df.empty:
            data.append(df)
    if data:
        return pd.concat(data, ignore_index=True)
    else:
        return pd.DataFrame()

# ------------------- DATA VALIDATION -------------------

def validate_df(df: pd.DataFrame) -> bool:
    """Validates dataframe for required columns."""
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing:
        st.warning(f"Missing columns: {', '.join(missing)}")
        return False
    return True

# ------------------- HELPER FUNCTIONS -------------------

def get_advertisers(df: pd.DataFrame) -> List[str]:
    """Returns sorted list of unique advertisers."""
    if COL_ADVERTISER not in df.columns:
        return []
    return sorted(df[COL_ADVERTISER].dropna().unique())

def get_media_channels(df: pd.DataFrame) -> List[str]:
    """Returns sorted list of unique media channels."""
    if COL_MEDIA_CHANNEL not in df.columns:
        return []
    return sorted(df[COL_MEDIA_CHANNEL].dropna().unique())

def filter_by_channel(df: pd.DataFrame, selected_channels: List[str]) -> pd.DataFrame:
    """Returns dataframe filtered by selected media channels."""
    if COL_MEDIA_CHANNEL not in df.columns or not selected_channels:
        return df.copy()
    return df[df[COL_MEDIA_CHANNEL].isin(selected_channels)].copy()

def apply_channel_grouping(df: pd.DataFrame, grouping_dict: Dict[str, str]) -> pd.DataFrame:
    """Adds a grouped channel column based on user mapping."""
    if COL_MEDIA_CHANNEL not in df.columns:
        st.error(f"The uploaded data does not have a '{COL_MEDIA_CHANNEL}' column.")
        return df
    df = df.copy()
    df[COL_GROUPED] = df[COL_MEDIA_CHANNEL].map(grouping_dict).fillna(df[COL_MEDIA_CHANNEL])
    return df

def compute_pie_data(df: pd.DataFrame, group_col: str = COL_MEDIA_CHANNEL) -> Dict[str, Dict[str, float]]:
    """Computes pie chart data as % share by advertiser and channel."""
    pie_data = defaultdict(dict)
    if COL_ADVERTISER not in df.columns or group_col not in df.columns or COL_SPEND not in df.columns:
        return pie_data
    for adv, subdf in df.groupby(COL_ADVERTISER):
        total = subdf[COL_SPEND].sum()
        if total == 0:
            continue
        channel_sums = subdf.groupby(group_col)[COL_SPEND].sum()
        for channel, spend in channel_sums.items():
            pie_data[adv][channel] = spend / total * 100
    return pie_data

def compute_total_spend(df: pd.DataFrame) -> pd.Series:
    """Computes total spend by advertiser."""
    if COL_ADVERTISER not in df.columns or COL_SPEND not in df.columns:
        return pd.Series(dtype=float)
    return df.groupby(COL_ADVERTISER)[COL_SPEND].sum().sort_values(ascending=False)

def get_top_channels(pie: Dict[str, float], threshold: float = 0.5) -> List[str]:
    """Returns top channels covering a threshold % of spend."""
    sorted_channels = sorted(pie.items(), key=lambda x: x[1], reverse=True)
    total = 0
    top_channels = []
    for ch, pct in sorted_channels:
        total += pct / 100
        top_channels.append(ch)
        if total >= threshold:
            break
    return top_channels

def compare_pie(primary_pie: Dict[str, float], competitor_pies: Dict[str, Dict[str, float]], threshold_similar: int = 5, threshold_diff: int = 20) -> List[str]:
    """Compares media mix between primary and competitors."""
    summary = []
    channels = set(primary_pie.keys())
    for comp in competitor_pies.values():
        channels.update(comp.keys())
    for channel in channels:
        p_val = primary_pie.get(channel, 0)
        for comp_name, comp_pie in competitor_pies.items():
            c_val = comp_pie.get(channel, 0)
            diff = abs(p_val - c_val)
            if diff < threshold_similar:
                summary.append(f"- Similar spend on {channel} (within {threshold_similar}%) between Primary and {comp_name}.")
            elif diff > threshold_diff:
                direction = "more" if p_val > c_val else "less"
                summary.append(f"- Primary spends >{threshold_diff}% {direction} on {channel} than {comp_name}.")
    return summary

def highlight_top_channels(primary_pie: Dict[str, float], competitor_pies: Dict[str, Dict[str, float]]) -> List[str]:
    """Finds shared top channels between primary and competitors."""
    lines = []
    primary_top = get_top_channels(primary_pie)
    for comp_name, comp_pie in competitor_pies.items():
        comp_top = get_top_channels(comp_pie)
        shared = set(primary_top) & set(comp_top)
        if shared:
            lines.append(f"- Top channels shared with {comp_name}: {', '.join(shared)}.")
    return lines

# ------------------- UI LAYOUT -------------------

st.set_page_config(page_title="Advertiser Media Mix Dashboard", layout="wide")
st.title("Advertiser (Brand) Media Mix Dashboard")

with st.sidebar:
    st.header("Controls")
    uploaded_files = st.file_uploader(
        "Upload Nielsen, Pathmatics, SEM Rush Excel files (multiple allowed):",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="file_uploader"
    )

if uploaded_files:
    progress = st.progress(0, "Parsing and validating files...")
    df = parse_files(uploaded_files)
    progress.progress(20, "Validating data...")
    if df.empty or not validate_df(df):
        st.stop()
    advertisers = get_advertisers(df)
    if not advertisers:
        st.warning("No advertisers found in the uploaded data.")
        st.stop()
    media_channels = get_media_channels(df)
    # Session state for selections
    if "primary_adv" not in st.session_state:
        st.session_state.primary_adv = advertisers[0]
    primary_adv = st.sidebar.selectbox("Select Primary Advertiser", advertisers, key="primary_adv")
    selected_channels = st.sidebar.multiselect("Filter Media Channels", media_channels, default=media_channels)
    # Collapsible for grouping
    with st.sidebar.expander("Custom Channel Grouping", expanded=False):
        channel_grouping = {}
        for channel in media_channels:
            group = st.text_input(f"Group for {channel}", value=channel, key=f"group_{channel}")
            # Basic validation: prevent code injection
            if not isinstance(group, str) or len(group) > 50:
                st.warning(f"Invalid group name for {channel}; using default.")
                group = channel
            channel_grouping[channel] = group
    progress.progress(40, "Applying filters and grouping...")
    df_filtered = filter_by_channel(df, selected_channels)
    df_grouped = apply_channel_grouping(df_filtered, channel_grouping)
    group_col = COL_GROUPED if COL_GROUPED in df_grouped.columns else COL_MEDIA_CHANNEL
    progress.progress(55, "Computing summary data...")
    pie_data = compute_pie_data(df_grouped, group_col=group_col)
    if primary_adv not in pie_data:
        st.warning(f"No data for primary advertiser: {primary_adv}")
        st.stop()
    competitor_pies = {adv: pie for adv, pie in pie_data.items() if adv != primary_adv}
    progress.progress(70, "Rendering dashboard...")

    # TABS for UI organization
    tab1, tab2, tab3 = st.tabs(["Pie Charts", "Summary", "Ranking/Export"])
    with tab1:
        st.subheader("Media Mix Pie Charts")
        cols = st.columns(len(pie_data))
        for idx, (adv, pie) in enumerate(pie_data.items()):
            with cols[idx]:
                fig, ax = plt.subplots(figsize=(4, 4))
                wedges, texts, autotexts = ax.pie(pie.values(), labels=pie.keys(), autopct='%1.1f%%', startangle=140)
                ax.set_title(adv)
                ax.legend(wedges, pie.keys(), title=group_col, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                st.pyplot(fig)
                plt.close(fig)

    with tab2:
        st.subheader("Summary Statistics")
        summary = compare_pie(pie_data[primary_adv], competitor_pies)
        shared_top = highlight_top_channels(pie_data[primary_adv], competitor_pies)
        st.markdown("#### Similarities/Differences")
        st.markdown("\n".join(summary) if summary else "No major similarities or differences found.")
        st.markdown("#### Shared Top Channels")
        st.markdown("\n".join(shared_top) if shared_top else "No top channels shared.")

    with tab3:
        st.subheader("Advertiser Ranking by Total Spend")
        total_spend = compute_total_spend(df_grouped)
        st.dataframe(total_spend)
        st.subheader("Export")
        out_excel = io.BytesIO()
        # Add metadata to the output
        with pd.ExcelWriter(out_excel, engine='xlsxwriter') as writer:
            df_grouped.to_excel(writer, index=False, sheet_name="Data")
            metadata = pd.DataFrame({
                "Description": [
                    "Exported by Media Mix Dashboard",
                    f"Primary Advertiser: {primary_adv}",
                    f"Selected Channels: {', '.join(selected_channels)}",
                    f"Timestamp: {pd.Timestamp.now()}",
                ]
            })
            metadata.to_excel(writer, index=False, sheet_name="Metadata")
        st.download_button("Download Data as Excel", out_excel.getvalue(), file_name="media_mix.xlsx")
        for adv, pie in pie_data.items():
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie(pie.values(), labels=pie.keys(), autopct='%1.1f%%', startangle=140)
            ax.set_title(adv)
            out_img = io.BytesIO()
            plt.savefig(out_img, format='png')
            st.download_button(f"Download {adv} Pie Chart as PNG", out_img.getvalue(), file_name=f"{adv}_pie.png")
            plt.close(fig)
    progress.progress(100, "Done!")
else:
    st.info("Please upload at least one file to begin.")
