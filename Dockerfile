# Use official Python base image
FROM python:3.13-slim

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

# Create a working directory and give ownership to the non-root user
WORKDIR /app
RUN chown appuser:appuser /app

# Copy your Python program files into the container
COPY --chown=appuser:appuser server.py /app

# Install dependencies if you have requirements.txt
# (optional, remove if not needed)
COPY --chown=appuser:appuser requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-root user
USER appuser

ENV HOME=/home/appuser
ENV PYTHONUNBUFFERED=1

# Run your Python script
CMD ["./wait-for-port.sh", "python", "server.py"]