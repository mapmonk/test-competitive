# Competitive Ad Spend Analysis Dashboard

This Streamlit app enables robust competitive media mix analysis using Nielsen Ad Intel and Pathmatics data.  
It supports uploading and parsing multiple Excel files, mapping advertiser and channel names, selecting a primary advertiser, and setting analysis date ranges. The app also supports branded, multi-format exports.

## Features

- Upload one or more Nielsen Ad Intel and Pathmatics Excel files (`.xls` or `.xlsx`).
- Automatic extraction and mapping of advertiser and media channel names.
- Interactive UI for renaming advertisers and channels.
- Set a primary advertiser and select an analysis date range.
- Dashboard view with context (charts and aggregation: TODO).
- Export options for Excel, CSV, PDF, and PNG (charts and reports: TODO).
- Monks logo preset in sidebar; upload your own client logo for custom branding.
- All exports titled:  
  `[Primary Advertiser Name] Competitor Ad Spend Analysis - [start date] to [end date]`

## Setup

1. Clone this repository.
2. Place the Monks logo in `static/monks_logo.png`.
3. (Optional) Prepare a placeholder client logo as `static/client_logo.png`.
4. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
5. Run the app:
    ```
    streamlit run app.py
    ```
6. Open the provided local URL in your browser.

## Usage

1. **Upload Files:** Upload one or more Excel files containing your data.
2. **Advertiser & Channel Mapping:** Map extracted advertisers and channels to your preferred names.
3. **Set Date Range:** Choose the start and end date for your analysis.
4. **Select Primary Advertiser:** Identify your main brand for focused analysis.
5. **Dashboard:** View summary information and (future) insights, charts, and comparisons.
6. **Export:** Select your preferred export format and brand with your client logo (export logic: TODO).

## Notes

- The app expects Excel files with columns named `Advertiser` and `Channel`.
- File, advertiser, and channel mapping is session-based (will reset on app restart).
- All outputs and exports are branded with the Monks logo and, if uploaded, the client’s logo.
- Export and dashboard visualizations are currently placeholders (see TODOs in app.py).

## License

[Specify your license here]
