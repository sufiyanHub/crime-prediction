FROM python:3.9

# Install system packages required for TensorFlow and Flask app
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Ensure gunicorn is installed (important)
RUN pip install gunicorn

# Copy app code
COPY . .

# Expose the port Flask app runs on
EXPOSE 5000

# Final command to run the app using gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
