# Media Spend Competitive Analysis (Pie Charts)

This Streamlit app generates one pie chart **per advertiser**, showing each channel's % of total media spend. Channel colors are consistent across all advertisers.

---

## Features

- **Upload**: Excel (.xlsx) or CSV (.csv) files from Nielsen Ad Intel, Pathmatics, or similar.
- **Visualization**: One pie chart per advertiser, showing each channel's % of spend.
- **Color Legend**: Consistent, distinct colors for each channel across all charts.
- **Automatic Handling**: Ignores missing/zero spend rows, automatic type conversion.

---

## Data Format

Your file must have these columns (capitalization/spacing must match):

| Advertiser | Channel | Spend |
|------------|---------|-------|
| AdvA       | TV      | 1000  |
| AdvA       | Digital | 500   |
| AdvB       | TV      | 2000  |
| AdvB       | Digital | 800   |

- **Advertiser**: Name of the advertiser.
- **Channel**: Marketing channel (e.g., TV, Digital, Radio, Social).
- **Spend**: Numeric (no $ or %, just numbers).

---

## How to Run

1. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

2. Start the app:

    ```
    streamlit run app.py
    ```

3. Upload your `.xlsx` or `.csv` file using the uploader.

---

## Example Files

- Nielsen Ad Intel or Pathmatics exports are supported.
- If your file uses different column names, edit in Excel so the first row matches: `Advertiser`, `Channel`, `Spend`.

---

## Troubleshooting

- **Missing columns**: Check that your file includes the required headers.
- **Empty chart**: Check for blank/zero spend rows or wrong column names.
- **Colors**: Up to 20 unique channels are supported per chart.

---

## License

MIT

---

Built for media and marketing analysts by [mapmonk/test-competitive](https://github.com/mapmonk/test-competitive).
