# Use the official lightweight Python image.
FROM python:3.10-slim

# Set a working directory inside the container
WORKDIR /app

# Copy requirements and app code into the container
COPY requirements.txt ./
COPY app.py ./
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
