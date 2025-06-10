# Advertiser Media Mix Dashboard

A web-based dashboard (built with [Streamlit](https://streamlit.io/)) that allows users to upload multiple media spend reports (from Nielsen, Pathmatics, SEM Rush, etc.), aggregate and visualize advertiser media mixes, and compare spend patterns between a primary advertiser and its competitors.

## Features

- **Multi-file Upload:** Upload multiple Excel files at once from different sources (Nielsen, Pathmatics, SEM Rush).
- **Automatic Data Aggregation:** All files are merged and standardized for analysis.
- **Advertiser and Competitor Analysis:** Select a primary advertiser; others are treated as competitors for benchmarking.
- **Visualizations:** One pie chart per advertiser, showing media mix by channel (with custom channel grouping/filtering).
- **Dynamic Filtering:** Filter by media channel and create custom channel groupings directly in the UI.
- **Summary Statistics:** Bulleted summary highlights similarities and differences in media mix between your primary advertiser and competitors, and ranks the primary advertiser by total spend.
- **Export:** Download filtered/grouped data as Excel, and pie charts as PNG images.

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_NAME>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

### 4. Using the Dashboard

- **Upload Files:** Click the file uploader and select your Excel files from Nielsen, Pathmatics, SEM Rush, etc.
- **Select Primary Advertiser:** Choose your main brand for comparison.
- **Filter/Group Media Channels:** Use the sidebar options to filter channels or group them into custom categories.
- **Review Visualizations:** Explore side-by-side pie charts for each advertiser.
- **Read the Summary:** See bulleted insights on similarities, differences, and rankings.
- **Download Data or Charts:** Use the download buttons to export your current view as an Excel file or PNG image.

## File Format Requirements

- **Nielsen/Pathmatics:** Excel files should include at least columns for `Advertiser`, `Media Channel`, and `Spend`.
- **SEM Rush or Custom:** Files with different column names may require minor adaptation in the code (see `app.py`).
- All spend should be numeric and in the same currency.

## Customization

To adapt for additional file types or new data formats, update the placeholder functions in `app.py`:
- `parse_nielsen()`
- `parse_pathmatics()`
- `parse_semrush()`

Each should return a DataFrame with standardized columns: `Advertiser`, `Media Channel`, `Spend`, etc.

## Dependencies

See [requirements.txt](./requirements.txt).

- streamlit
- pandas
- numpy
- matplotlib
- openpyxl
- xlsxwriter

## License

MIT

---

For questions or feature requests, please open an issue or contact the maintainer.
