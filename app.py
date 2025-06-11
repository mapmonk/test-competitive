import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl

# Set Streamlit page configuration
st.set_page_config(
    page_title="Media Spend Pie Charts",
    layout="wide",
)

st.title("Media Spend Comparison by Advertiser (Pie Charts)")

st.markdown("""
Upload a media spend file (`.xlsx` or `.csv`) containing columns:  
- **Advertiser**  
- **Channel**  
- **Spend**  

Each advertiser will be shown as a pie chart, with each channel’s % of total spend and consistent colors across advertisers.
""")

uploaded_file = st.file_uploader(
    "Upload an Excel (.xlsx) or CSV (.csv) file", 
    type=["xlsx", "csv"]
)

# Helper function for color mapping
def get_color_map(channels):
    COLORS = plt.cm.tab20.colors  # Up to 20 distinct colors
    color_map = {channel: COLORS[i % len(COLORS)] for i, channel in enumerate(sorted(channels))}
    return color_map

if uploaded_file is not None:
    # Load the data
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    # Validate required columns
    required_cols = {"Advertiser", "Channel", "Spend"}
    if not required_cols.issubset(set(df.columns)):
        st.error(
            f"Missing required columns. Required: {', '.join(required_cols)}. "
            f"Found: {', '.join(df.columns)}"
        )
        st.stop()

    # Remove rows with missing or zero spend
    df = df.dropna(subset=["Advertiser", "Channel", "Spend"])
    df["Spend"] = pd.to_numeric(df["Spend"], errors="coerce").fillna(0)
    df = df[df["Spend"] > 0]

    if df.empty:
        st.warning("No valid spend data found in your file.")
        st.stop()

    all_channels = sorted(df["Channel"].unique())
    color_map = get_color_map(all_channels)

    # Pie chart for each advertiser
    for advertiser in sorted(df["Advertiser"].unique()):
        adf = df[df["Advertiser"] == advertiser]
        spend_by_channel = adf.groupby("Channel")["Spend"].sum()
        spend_by_channel = spend_by_channel.reindex(all_channels, fill_value=0)
        colors = [color_map[ch] for ch in spend_by_channel.index]
        fig, ax = plt.subplots(figsize=(5, 5))
        wedges, texts, autotexts = ax.pie(
            spend_by_channel,
            labels=spend_by_channel.index,
            autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
            startangle=90,
            colors=colors,
            wedgeprops=dict(edgecolor="white"),
            textprops=dict(color="black", fontsize=12)
        )
        ax.set_title(advertiser, fontsize=16, pad=20)
        ax.axis("equal")
        st.pyplot(fig)

    # Color legend
    st.markdown("### Channel Color Legend")
    legend_cols = st.columns(min(len(all_channels), 6))
    for idx, channel in enumerate(all_channels):
        rgb = tuple(int(255 * x) for x in color_map[channel][:3])
        hex_color = '#%02x%02x%02x' % rgb
        legend_cols[idx % len(legend_cols)].markdown(
            f"<span style='font-size:2em;color:{hex_color}'>⬤</span><br/>{channel}",
            unsafe_allow_html=True
        )
else:
    st.info("Please upload a file to begin.")

st.markdown("---")
st.markdown(
    "Built for competitive media spend analysis. "
    "For questions or help, see the README or contact the project maintainers."
)
