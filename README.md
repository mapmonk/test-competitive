# [Primary Advertiser Name] Competitor Ad Spend Analysis Dashboard

This web app enables robust competitive media mix analysis using Nielsen Ad Intel and Pathmatics data.  
It supports merging/normalizing advertiser and channel names, comparison of multiple competitors, and branded, multi-format exports.

## Features

- Upload Nielsen Ad Intel and Pathmatics files.
- Merge and standardize advertiser and media channel names (with persistent mappings).
- Set a primary advertiser; compare against competitors.
- Interactive dashboard with media mix pie charts, summary statistics, and automated insights.
- Export results to Excel, CSV, PDF (with charts and insights), and PNG (charts).
- Branding: Monks logo preset, with option to upload a client logo for report exports.
- All exports titled:  
  `[Primary Advertiser Name] Competitor Ad Spend Analysis - [start date] to [end date]`

## Setup

1. Clone this repository.
2. Place the Monks logo in `static/monks_logo.png`.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the app:
   ```
   python app.py
   ```
5. Open `http://127.0.0.1:5000` in your browser.

## Usage

1. Upload your Nielsen and Pathmatics files (Excel format).
2. Merge/rename advertisers and channels as needed.
3. Input the start & end date of your data set.
4. Choose your primary advertiser.
5. View the dashboard for comparisons, insights, and charts.
6. Export results in your preferred format and branding.

## Notes

- Advertiser/channel mapping is persisted for future sessions (in-memory for demo; use a DB for production).
- All outputs and exports are branded with the Monks logo and (optionally) your client’s logo.
- File and report titles are dynamically generated, e.g.:  
  `Shipt Competitor Ad Spend Analysis - 2025-01-01 to 2025-03-31.pdf`

## License

[Specify your license here]
