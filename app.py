import streamlit as st
import pandas as pd
import os
from datetime import datetime

# App config
st.set_page_config(page_title="Competitive Ad Spend Analysis", layout="wide")

# Paths and folders
UPLOAD_FOLDER = "uploads"
MONKS_LOGO_PATH = "static/monks_logo.png"
CLIENT_LOGO_PATH = "static/client_logo.png"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Session state initialization
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

# Utility functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

def save_upload(uploadedfile):
    filename = uploadedfile.name
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(uploadedfile.getbuffer())
    return filepath

def extract_advertisers_and_channels(filepaths):
    advertisers = set()
    channels = set()
    errors = []
    for path in filepaths:
        try:
            df = pd.read_excel(path)
            # Adjust these column names if your actual files differ
            if 'Advertiser' in df.columns:
                advertisers.update(df['Advertiser'].dropna().astype(str).unique())
            else:
                errors.append(f"File '{os.path.basename(path)}' is missing 'Advertiser' column.")
            if 'Channel' in df.columns:
                channels.update(df['Channel'].dropna().astype(str).unique())
            else:
                errors.append(f"File '{os.path.basename(path)}' is missing 'Channel' column.")
        except Exception as e:
            errors.append(f"Error reading '{os.path.basename(path)}': {e}")
    return sorted(advertisers), sorted(channels), errors

# Sidebar branding and logo
st.sidebar.image(MONKS_LOGO_PATH, use_column_width=True)

# Step 1: File upload
st.title("Competitive Ad Spend Analysis Dashboard")
st.header("Step 1: Upload Excel Files")
uploaded_files = st.file_uploader(
    "Upload one or more Excel files", type=['xlsx', 'xls'], accept_multiple_files=True
)
if uploaded_files:
    filepaths = []
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

# Step 2: Mapping (dynamic UI)
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

# Step 3: Date range
if st.session_state.get("advertiser_mappings") and len(st.session_state["advertiser_mappings"]) > 0:
    st.header("Step 3: Set Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.today())
    with col2:
        end_date = st.date_input("End Date", value=datetime.today())
    st.session_state["start_date"] = str(start_date)
    st.session_state["end_date"] = str(end_date)

# Step 4: Primary advertiser
if st.session_state.get("advertiser_mappings") and len(st.session_state["advertiser_mappings"]) > 0:
    st.header("Step 4: Choose Primary Advertiser")
    mapped_advertisers = list(st.session_state["advertiser_mappings"].values())
    if mapped_advertisers:
        primary = st.selectbox("Select the primary advertiser", mapped_advertisers)
        st.session_state["primary_advertiser"] = primary

# Step 5: Dashboard and export stub
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

# Client logo upload in sidebar
st.sidebar.header("Upload Client Logo")
client_logo = st.sidebar.file_uploader("Client Logo (PNG)", type=['png'])
if client_logo is not None:
    client_logo_path = os.path.join("static", "client_logo.png")
    with open(client_logo_path, "wb") as f:
        f.write(client_logo.getbuffer())
    st.session_state["client_logo"] = client_logo_path
    st.sidebar.image(client_logo_path, width=100)
elif os.path.exists(CLIENT_LOGO_PATH):
    st.sidebar.image(CLIENT_LOGO_PATH, width=100)
