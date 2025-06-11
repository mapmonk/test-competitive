# Competitive Ad Spend Analysis Streamlit App

This app provides a step-by-step workflow for competitive ad spend analysis, enabling media planners to upload data, map advertiser/channel names, assign colors, set date ranges, and generate interactive dashboards with export options.

## Features

- **Step-by-step workflow** with custom progress indicator
- **Data upload** and preview (Excel files)
- **Bulk mapping** of advertisers and channels
- **Channel color assignment** with color picker
- **Date range selection**
- **Primary advertiser selection**
- **Interactive dashboard** with Plotly charts
- **Data export** (CSV, Excel)
- **Export dashboard to PDF** (requires `reportlab`)
- **Session safety**: Robust error handling to prevent crashes

## Requirements

- **Python 3.8+**
- [Streamlit](https://streamlit.io/)
- [plotly](https://plotly.com/python/)
- pandas
- openpyxl
- **reportlab** (for PDF export)

## Installation

Install all dependencies with:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install streamlit plotly pandas openpyxl reportlab
```

## Usage

```bash
streamlit run app.py
```

## Critical Notes

- The app **will not run** unless all required dependencies are installed. If a dependency is missing, the app will stop and provide installation instructions.
- Only Excel (`.xlsx`) files are supported for upload.
- On each step, input validation ensures critical fields are completed before you can proceed.
- All session state is managed defensively to prevent navigation or data errors.
- The progress bar is implemented using only native Streamlit components.

## Example Workflow

1. Upload your Excel ad spend files.
2. Map advertiser and channel names as needed.
3. Assign colors for each channel.
4. Select your date range.
5. Choose your primary advertiser.
6. View interactive charts and export your data (including to PDF).

## Troubleshooting

- If you see an error about a missing package, run the `pip install ...` command shown in the error message.
- If you encounter unexpected app behavior, refresh your browser or restart the app.

## License

MIT
