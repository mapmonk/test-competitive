import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import matplotlib.pyplot as plt

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
    ("aggregated_data", None),
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

# ---- Simple Aggregation for Visualization ----
def aggregate_and_prepare(filepaths, advertiser_map, channel_map):
    all_rows = []
    for path in filepaths:
        try:
            xl = pd.ExcelFile(path)
            # Nielsen Ad Intel
            if "Report" in xl.sheet_names:
                df = xl.parse("Report", header=None)
                rows = df.iloc[4:, [0, 1, 2, 3]].dropna(how="any")  # Assume spend is in columns 2/3
                rows.columns = ["Advertiser", "Channel", "Spend", "Date"]
                for _, row in rows.iterrows():
                    mapped_adv = advertiser_map.get(str(row["Advertiser"]), str(row["Advertiser"]))
                    mapped_chan = channel_map.get(str(row["Channel"]), str(row["Channel"]))
                    spend = pd.to_numeric(row["Spend"], errors="coerce")
                    date = row["Date"]
                    all_rows.append({"Advertiser": mapped_adv, "Channel": mapped_chan, "Spend": spend, "Date": date})
            # Pathmatics (assume Daily Spend is a pivot table: dates as rows, channels as columns, spend as values)
            if "Cover" in xl.sheet_names and "Daily Spend" in xl.sheet_names:
                cover = xl.parse("Cover", header=None)
                adv_val = advertiser_map.get(str(cover.iloc[3, 1]), str(cover.iloc[3, 1])) if pd.notnull(cover.iloc[3, 1]) else None  # B4
                spend = xl.parse("Daily Spend", header=None)
                if spend.shape[0] > 1 and spend.shape[1] > 1:
                    for i in range(1, spend.shape[0]):  # Skip header row
                        date = spend.iloc[i, 0]
                        for j in range(1, spend.shape[1]):
                            chan = spend.iloc[0, j]
                            mapped_chan = channel_map.get(str(chan), str(chan))
                            val = pd.to_numeric(spend.iloc[i, j], errors="coerce")
                            all_rows.append({"Advertiser": adv_val, "Channel": mapped_chan, "Spend": val, "Date": date})
        except Exception:
            continue
    agg_df = pd.DataFrame(all_rows)
    agg_df = agg_df.dropna(subset=["Spend"])
    agg_df["Spend"] = agg_df["Spend"].astype(float)
    return agg_df

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

# ---- Step 5: Dashboard and export with aggregation/visualization ----
if st.session_state.get("primary_advertiser"):
    st.header("Dashboard")
    st.success(f"Primary Advertiser: {st.session_state['primary_advertiser']}")
    st.write("Date Range:", st.session_state.get("start_date"), "to", st.session_state.get("end_date"))
    st.write("Advertiser Mappings:", st.session_state.get("advertiser_mappings"))
    st.write("Channel Mappings:", st.session_state.get("channel_mappings"))

    # --- AGGREGATION & VISUALIZATION ---
    with st.spinner("Aggregating and visualizing..."):
        agg_df = aggregate_and_prepare(
            st.session_state.get("uploaded_files", []),
            st.session_state.get("advertiser_mappings", {}),
            st.session_state.get("channel_mappings", {})
        )
        st.session_state["aggregated_data"] = agg_df

    if agg_df is not None and not agg_df.empty:
        st.subheader("Key Stats")
        total_spend = agg_df["Spend"].sum()
        st.metric("Total Spend (All Advertisers)", f"${total_spend:,.2f}")

        spend_by_adv = agg_df.groupby("Advertiser")["Spend"].sum().sort_values(ascending=False)
        spend_by_chan = agg_df.groupby("Channel")["Spend"].sum().sort_values(ascending=False)

        st.subheader("Spend by Advertiser")
        st.bar_chart(spend_by_adv)

        st.subheader("Spend by Channel")
        st.bar_chart(spend_by_chan)

        st.subheader("Top 10 Advertiser-Channel Pairs")
        pivot = agg_df.groupby(["Advertiser", "Channel"])["Spend"].sum().reset_index()
        top_pairs = pivot.sort_values("Spend", ascending=False).head(10)
        st.dataframe(top_pairs, use_container_width=True)

        # Time-series if Date column is good
        if "Date" in agg_df.columns:
            try:
                temp = agg_df.copy()
                temp["Date"] = pd.to_datetime(temp["Date"], errors="coerce")
                temp = temp.dropna(subset=["Date"])
                ts = temp.groupby(["Date", "Advertiser"])["Spend"].sum().reset_index()
                st.subheader("Spend Over Time (Primary Advertiser)")
                ts_primary = ts[ts["Advertiser"] == st.session_state["primary_advertiser"]]
                fig, ax = plt.subplots()
                ax.plot(ts_primary["Date"], ts_primary["Spend"], marker="o")
                ax.set_xlabel("Date")
                ax.set_ylabel("Spend")
                ax.set_title(f"Spend Over Time: {st.session_state['primary_advertiser']}")
                st.pyplot(fig)
            except Exception:
                pass

        st.subheader("Aggregated Data Table")
        st.dataframe(agg_df, use_container_width=True)
    else:
        st.info("No data available for aggregation/visualization. Please check your uploads and mappings.")

    # Export option
    export_format = st.selectbox("Export report as:", ["xlsx", "csv"])
    if st.button("Export"):
        if agg_df is not None and not agg_df.empty:
            if export_format == "csv":
                st.download_button(
                    label="Download CSV",
                    data=agg_df.to_csv(index=False),
                    file_name="aggregated_report.csv",
                    mime="text/csv"
                )
            elif export_format == "xlsx":
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    agg_df.to_excel(writer, index=False, sheet_name="Aggregated Data")
                output.seek(0)
                st.download_button(
                    label="Download Excel",
                    data=output,
                    file_name="aggregated_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("Nothing to export!")
