# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory into the container
COPY . /app

# Upgrade pip and install the required dependencies
RUN pip install --upgrade pip && \
    pip install Flask Flask-Bootstrap

# Expose port 5000 for the Flask application
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "app.py"]
