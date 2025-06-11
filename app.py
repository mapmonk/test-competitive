import streamlit as st
import datetime
import pandas as pd

# Absolutely critical: Dependency checks
try:
    import plotly.express as px
except ImportError:
    st.error("Please install plotly: pip install plotly")
    st.stop()

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
except ImportError:
    st.error("Please install reportlab: pip install reportlab")
    st.stop()

import random

# Helper for robust session state access
def get_state(key, default=None):
    return st.session_state.get(key, default)

def set_state(key, value):
    st.session_state[key] = value

# --- Step Progress Bar (Native Streamlit alternative) ---
def streamlit_step_bar(current_step, total_steps, steps_labels):
    cols = st.columns(total_steps)
    for idx, col in enumerate(cols):
        if idx < current_step:
            col.success(f"✓ {steps_labels[idx]}")
        elif idx == current_step:
            col.info(f"→ {steps_labels[idx]}")
        else:
            col.write(steps_labels[idx])

steps_labels = [
    "Upload", "Advertiser Map", "Channel Map", "Channel Colors",
    "Date Range", "Primary Adv", "Dashboard"
]
current_step = get_state("current_step", 0)
streamlit_step_bar(current_step, len(steps_labels), steps_labels)

# --- Step Navigation (Critical: prevents broken flow) ---
def go_to_step(step):
    set_state("current_step", step)
    st.experimental_rerun()

# Sample demo data for illustration
demo_advertisers = ["Adv1", "Adv2", "Adv3"]
demo_channels = ["TV", "Digital", "Print"]

# --- Step 1: Upload ---
if current_step == 0:
    st.header("Upload Data")
    uploaded_files = st.file_uploader("Upload Excel files", type=["xlsx"], accept_multiple_files=True)
    if uploaded_files:
        set_state("uploaded_files", uploaded_files)
        st.button("Continue", on_click=go_to_step, args=(1,))
    else:
        st.button("Continue", on_click=go_to_step, args=(1,), disabled=True)

# --- Step 2: Advertiser Map ---
elif current_step == 1:
    st.header("Map Advertisers")
    advertisers = get_state("demo_advertisers", demo_advertisers)
    adv_map_df = pd.DataFrame({"Original": advertisers, "Mapped": advertisers})
    adv_map_edit = st.data_editor(adv_map_df, num_rows="dynamic")
    if adv_map_edit["Mapped"].isnull().any() or adv_map_edit["Mapped"].eq("").any():
        st.warning("All advertisers must be mapped before continuing.")
        st.button("Continue", on_click=go_to_step, args=(2,), disabled=True)
    else:
        set_state("adv_map", dict(zip(adv_map_edit["Original"], adv_map_edit["Mapped"])))
        st.button("Continue", on_click=go_to_step, args=(2,))
    st.button("Back", on_click=go_to_step, args=(0,))

# --- Step 3: Channel Map ---
elif current_step == 2:
    st.header("Map Channels")
    channels = get_state("demo_channels", demo_channels)
    ch_map_df = pd.DataFrame({"Original": channels, "Mapped": channels})
    ch_map_edit = st.data_editor(ch_map_df, num_rows="dynamic")
    if ch_map_edit["Mapped"].isnull().any() or ch_map_edit["Mapped"].eq("").any():
        st.warning("All channels must be mapped before continuing.")
        st.button("Continue", on_click=go_to_step, args=(3,), disabled=True)
    else:
        set_state("ch_map", dict(zip(ch_map_edit["Original"], ch_map_edit["Mapped"])))
        st.button("Continue", on_click=go_to_step, args=(3,))
    st.button("Back", on_click=go_to_step, args=(1,))

# --- Step 4: Channel Colors ---
elif current_step == 3:
    st.header("Select Channel Colors")
    channels = list(set(get_state("ch_map", {}).values()))
    if not channels:
        st.error("No channels mapped. Please complete channel mapping.")
        st.stop()
    # Ensure color state exists for all channels (critical)
    default_palette = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"]
    channel_colors = get_state("channel_colors", {})
    for i, ch in enumerate(channels):
        if ch not in channel_colors:
            channel_colors[ch] = default_palette[i % len(default_palette)]
    for i, ch in enumerate(channels):
        val = st.color_picker(ch, channel_colors[ch], key=f"color_{ch}")
        channel_colors[ch] = val
    set_state("channel_colors", channel_colors)
    missing_colors = [ch for ch in channels if not channel_colors.get(ch)]
    if missing_colors:
        st.error("Please select a color for all channels before continuing.")
        st.button("Continue", on_click=go_to_step, args=(4,), disabled=True)
    else:
        st.button("Continue", on_click=go_to_step, args=(4,))
    st.button("Back", on_click=go_to_step, args=(2,))

# --- Step 5: Date Range ---
elif current_step == 4:
    st.header("Select Date Range")
    date_range = st.date_input("Date Range", value=(datetime.date(2024, 1, 1), datetime.date(2024, 12, 31)))
    if not date_range or len(date_range) != 2 or not all(date_range):
        st.warning("Please select both a start and end date before continuing.")
        st.button("Continue", on_click=go_to_step, args=(5,), disabled=True)
    else:
        set_state("date_range", date_range)
        st.button("Continue", on_click=go_to_step, args=(5,))
    st.button("Back", on_click=go_to_step, args=(3,))

# --- Step 6: Primary Advertiser ---
elif current_step == 5:
    st.header("Primary Advertiser")
    adv_map = get_state("adv_map", dict(zip(demo_advertisers, demo_advertisers)))
    adv_display = sorted(set(adv_map.values()))
    if not adv_display:
        st.error("No advertisers mapped. Please complete advertiser mapping.")
        st.stop()
    primary_adv = st.selectbox("Select primary advertiser", adv_display)
    set_state("primary_adv", primary_adv)
    st.button("Continue", on_click=go_to_step, args=(6,))
    st.button("Back", on_click=go_to_step, args=(4,))

# --- Step 7: Dashboard ---
elif current_step == 6:
    st.header("Dashboard")
    adv_map = get_state("adv_map")
    ch_map = get_state("ch_map")
    channel_colors = get_state("channel_colors")
    date_range = get_state("date_range")
    primary_adv = get_state("primary_adv")
    if not (adv_map and ch_map and channel_colors and date_range and primary_adv):
        st.error("Missing required data. Please complete all steps before viewing dashboard.")
        st.stop()
    # Simulated aggregate data for demonstration
    df = pd.DataFrame({
        "Advertiser": [primary_adv, "Adv2", "Adv3"],
        "TV": [60000, 30000, 20000],
        "Digital": [40000, 20000, 10000],
        "Print": [20000, 10000, 5000]
    })
    df = df.set_index("Advertiser")
    st.subheader("Media Mix Pie Chart (Plotly)")
    for adv in df.index:
        row = df.loc[adv]
        data = pd.DataFrame({"Channel": row.index, "Spend": row.values})
        fig = px.pie(
            data,
            names="Channel",
            values="Spend",
            color="Channel",
            color_discrete_map=channel_colors
        )
        fig.update_traces(textinfo='percent+label')
        st.markdown(f"**{adv}**")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Spend Summary Table")
    st.dataframe(df)

    # --- PDF Export ---
    def create_pdf(df, primary_adv, date_range):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 750, "Competitive Ad Spend Dashboard")
        c.setFont("Helvetica", 12)
        c.drawString(72, 730, f"Primary Advertiser: {primary_adv}")
        c.drawString(72, 715, f"Date Range: {date_range[0]} to {date_range[1]}")

        # Table header
        c.setFont("Helvetica-Bold", 12)
        y = 690
        x = 72
        for col in ["Advertiser"] + list(df.columns):
            c.drawString(x, y, col)
            x += 100
        # Table rows
        c.setFont("Helvetica", 12)
        y -= 18
        for adv, row in df.iterrows():
            x = 72
            c.drawString(x, y, str(adv))
            x += 100
            for val in row.values:
                c.drawString(x, y, str(val))
                x += 100
            y -= 18
            if y < 72:
                c.showPage()
                y = 750
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf(df, primary_adv, date_range)
    st.download_button("Export Dashboard as PDF", data=pdf_buffer, file_name="dashboard.pdf", mime="application/pdf")

    st.button("Back", on_click=go_to_step, args=(5,))
