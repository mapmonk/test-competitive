# Competitive Ad Spend Analysis Dashboard

This Streamlit app enables robust competitive media mix analysis using Nielsen Ad Intel and Pathmatics data.  
It supports uploading and parsing multiple Excel files, mapping advertiser and channel names, selecting a primary advertiser, and setting analysis date ranges. The app also supports branded, multi-step workflows, and exports.

## Features

- Loading progress bar at the start of the app for improved UX.
- Upload one or more Nielsen Ad Intel and Pathmatics Excel files (`.xls` or `.xlsx`).
- Automatic extraction and mapping of advertiser and media channel names.
- Interactive UI for renaming advertisers and channels.
- Set a primary advertiser and select an analysis date range.
- **Dashboard view with aggregation, charts, and insights (NEW!).**
- Export options for Excel and CSV.
- Monks logo preset in sidebar.

## Supported Excel File Formats

The app automatically detects and extracts advertisers and channels from two supported file types:

1. **Nielsen Ad Intel**:
    - Should have a sheet named **"Report"**.
    - Advertisers: Extracted from column A, starting at cell A5 (row 5).
    - Channels: Extracted from column B, starting at cell B5 (row 5).

2. **Pathmatics**:
    - Should have sheets named **"Cover"** and **"Daily Spend"**.
    - Advertiser: Extracted from cell B4 on the "Cover" sheet.
    - Channels: Extracted from the header row (row 1, columns B and onward) on the "Daily Spend" sheet.

If a file does not match these formats, an error will be shown and that file will not be processed.

## Setup

1. Clone this repository.
2. Place the Monks logo in `static/monks_logo.png`.
3. (Optional/Future) Client logo upload is not yet implemented – the current sidebar only supports the Monks logo.
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

1. **Upload Files:** Upload one or more Excel files in the supported formats above.
2. **Advertiser & Channel Mapping:** Map extracted advertisers and channels to your preferred names.
3. **Set Date Range:** Choose the start and end date for your analysis.
4. **Select Primary Advertiser:** Identify your main brand for focused analysis.
5. **Dashboard:** View summary information, insights, charts, and comparisons.
6. **Export:** Download aggregated data as Excel or CSV.

## Notes

- The app expects Excel files in the formats detailed above for correct processing.
- If a file is not in the supported format, an error will be displayed and it will not be included in the analysis.
- Uploaded files are saved to the `uploaded_files/` directory during your session.
- File, advertiser, and channel mapping is session-based (will reset on app restart).
- All outputs and exports are branded with the Monks logo (no client logo upload yet).
- Aggregation, charts, and dashboard visualizations are now implemented!

## License

[Specify your license here]
