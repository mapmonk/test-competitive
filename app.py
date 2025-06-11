import os
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_random_key"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory persistent mappings for advertisers and channels (replace with DB in prod)
advertiser_mappings = {}
channel_mappings = {}

# Persistent logo paths
MONKS_LOGO_PATH = "static/monks_logo.png"  # Place your logo as static/monks_logo.png

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

@app.route('/')
def index():
    return render_template('index.html', monks_logo=MONKS_LOGO_PATH)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return redirect(request.url)
    files = request.files.getlist('files[]')
    session['uploaded_files'] = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            session['uploaded_files'].append(path)
    return redirect(url_for('step1_mapping'))

@app.route('/step1-mapping', methods=['GET', 'POST'])
def step1_mapping():
    # TODO: Parse uploads, extract advertiser and channel names, present merge UI
    # Example: Load all advertisers/channels, show mapping interface
    # Save results to advertiser_mappings and channel_mappings
    return render_template('step1_mapping.html', monks_logo=MONKS_LOGO_PATH)

@app.route('/set-date-range', methods=['POST'])
def set_date_range():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    session['start_date'] = start_date
    session['end_date'] = end_date
    return redirect(url_for('choose_primary'))

@app.route('/choose-primary', methods=['GET', 'POST'])
def choose_primary():
    if request.method == 'POST':
        session['primary_advertiser'] = request.form.get('primary_advertiser')
        return redirect(url_for('dashboard'))
    # TODO: Present mapped advertiser list for primary selection
    return render_template('choose_primary.html', monks_logo=MONKS_LOGO_PATH)

@app.route('/dashboard')
def dashboard():
    # TODO: Aggregate, normalize, and display charts, stats, insights
    # Use session['primary_advertiser'], mappings, and uploaded files
    # Provide export options
    return render_template('dashboard.html', monks_logo=MONKS_LOGO_PATH)

@app.route('/export/<format>')
def export_report(format):
    # TODO: Generate and serve report in the requested format (xlsx, csv, pdf, png)
    # Use session data for mappings, date range, etc.
    # Compose filename as "[Primary Advertiser Name] Competitor Ad Spend Analysis - [start date] to [end date].ext"
    pass

@app.route('/upload-client-logo', methods=['POST'])
def upload_client_logo():
    file = request.files['client_logo']
    if file:
        filename = "client_logo.png"
        path = os.path.join("static", filename)
        file.save(path)
        session['client_logo'] = path
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
