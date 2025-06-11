import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# ---- Config ----
st.set_page_config(page_title="Competitive Ad Spend Analysis", layout="wide")

# ---- Constants ----
UPLOAD_FOLDER = "uploaded_files"
MONKS_LOGO_PATH = "static/monks_logo.png"

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Progress Bar at Startup ----
progress_text = "Initializing session, please wait..."
progress_bar = st.progress(0, text=progress_text)
for percent_complete in range(60):
    time.sleep(0.005)
    progress_bar.progress(percent_complete + 1, text=progress_text)
progress_bar.empty()

# ---- Session State Initialization ----
for key, default in [
    ("uploaded_files", []),
    ("advertiser_mappings", {}),
    ("channel_mappings", {}),
    ("start_date", None),
    ("end_date", None),
    ("primary_advertiser", ""),
    ("advertisers", []),
    ("channels", []),
    ("file_read_error", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---- Utility Functions ----
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

@st.cache_data(show_spinner=False)
def save_upload(uploadedfile):
    filename = uploadedfile.name
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(uploadedfile.getbuffer())
    return filepath

@st.cache_data(show_spinner=False)
def extract_advertisers_and_channels(filepaths):
    advertisers = set()
    channels = set()
    errors = []
    for path in filepaths:
        try:
            xl = pd.ExcelFile(path)
            found = False
            # 1. Try Nielsen Ad Intel (Report tab, A5 down for Advertiser, B5 down for Channel)
            if "Report" in xl.sheet_names:
                df = xl.parse("Report", header=None)
                advs = df.iloc[4:, 0].dropna().astype(str).unique()  # A5 down
                chans = df.iloc[4:, 1].dropna().astype(str).unique() # B5 down
                if len(advs) > 0:
                    advertisers.update(advs)
                    found = True
                if len(chans) > 0:
                    channels.update(chans)
                    found = True
            # 2. Try Pathmatics (Cover tab cell B4, Daily Spend row 1 for channels)
            if "Cover" in xl.sheet_names and "Daily Spend" in xl.sheet_names:
                cover = xl.parse("Cover", header=None)
                adv_val = str(cover.iloc[3, 1]) if pd.notnull(cover.iloc[3, 1]) else None  # B4 = row 3, col 1
                if adv_val:
                    advertisers.add(adv_val)
                    found = True
                spend = xl.parse("Daily Spend", header=None)
                chans = spend.iloc[0, 1:].dropna().astype(str).unique()  # Row 1, B1 and right
                if len(chans) > 0:
                    channels.update(chans)
                    found = True
            if not found:
                errors.append(f"File '{os.path.basename(path)}' does not match expected format or lacks data.")
        except Exception as e:
            errors.append(f"Error reading '{os.path.basename(path)}': {e}")
    return sorted(advertisers), sorted(channels), errors

# ---- Sidebar Branding and Logo ----
if os.path.exists(MONKS_LOGO_PATH):
    st.sidebar.image(MONKS_LOGO_PATH, use_container_width=True)

# ---- Step 1: File upload ----
st.title("Competitive Ad Spend Analysis Dashboard")
st.header("Step 1: Upload Excel Files")
uploaded_files = st.file_uploader(
    "Upload one or more Excel files", type=['xlsx', 'xls'], accept_multiple_files=True
)
if uploaded_files:
    filepaths = []
    with st.spinner("Saving uploaded files..."):
        for f in uploaded_files:
            if allowed_file(f.name):
                try:
                    path = save_upload(f)
                    filepaths.append(path)
                except Exception as e:
                    st.error(f"Failed to save {f.name}: {e}")
            else:
                st.error(f"File '{f.name}' is not a supported Excel file.")
    st.session_state.uploaded_files = filepaths

    # Extract advertisers and channels
    if filepaths:
        with st.spinner("Parsing uploaded files..."):
            advertisers, channels, errors = extract_advertisers_and_channels(filepaths)
        st.session_state.advertisers = advertisers
        st.session_state.channels = channels
        st.session_state.file_read_error = errors
        if errors:
            for err in errors:
                st.error(err)
        elif not (advertisers and channels):
            st.warning("No advertisers or channels found in the uploaded files.")
        else:
            st.success("Files uploaded and parsed successfully!")

# ---- Step 2: Mapping (dynamic UI) ----
if st.session_state.get("uploaded_files") and st.session_state.get("advertisers") and st.session_state.get("channels"):
    st.header("Step 2: Advertiser and Channel Mapping")
    st.info("Map each advertiser and channel to your preferred names.")

    adv_map = {}
    chan_map = {}
    for adv in st.session_state.advertisers:
        adv_map[adv] = st.text_input(f"Map advertiser '{adv}' to:", value=adv)
    for chan in st.session_state.channels:
        chan_map[chan] = st.text_input(f"Map channel '{chan}' to:", value=chan)

    st.session_state["advertiser_mappings"] = adv_map
    st.session_state["channel_mappings"] = chan_map

elif st.session_state.file_read_error:
    st.warning("Please fix the file issues above before proceeding.")

# ---- Step 3: Date range ----
if st.session_state.get("advertiser_mappings") and len(st.session_state["advertiser_mappings"]) > 0:
    st.header("Step 3: Set Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.today())
    with col2:
        end_date = st.date_input("End Date", value=datetime.today())
    st.session_state["start_date"] = str(start_date)
    st.session_state["end_date"] = str(end_date)

# ---- Step 4: Primary advertiser ----
if st.session_state.get("advertiser_mappings") and len(st.session_state["advertiser_mappings"]) > 0:
    st.header("Step 4: Choose Primary Advertiser")
    mapped_advertisers = list(st.session_state["advertiser_mappings"].values())
    if mapped_advertisers:
        primary = st.selectbox("Select the primary advertiser", mapped_advertisers)
        st.session_state["primary_advertiser"] = primary

# ---- Step 5: Dashboard and export stub ----
if st.session_state.get("primary_advertiser"):
    st.header("Dashboard")
    st.success(f"Primary Advertiser: {st.session_state['primary_advertiser']}")
    st.write("Date Range:", st.session_state.get("start_date"), "to", st.session_state.get("end_date"))
    st.write("Advertiser Mappings:", st.session_state.get("advertiser_mappings"))
    st.write("Channel Mappings:", st.session_state.get("channel_mappings"))
    st.info("Charts, stats, and insights would appear here. [TODO: Implement aggregation and visualization]")

    # Export option (stub)
    export_format = st.selectbox("Export report as:", ["xlsx", "csv", "pdf", "png"])
    if st.button("Export"):
        st.info(f"Exporting as {export_format}... [TODO: Implement export logic]")
