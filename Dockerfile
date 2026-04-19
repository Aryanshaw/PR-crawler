# Use the official Playwright image which includes all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY . .

# Install dependencies using uv
# Use absolute path to uv just in case
RUN uv pip install --system -r requirements.txt

# Install chromium only (to keep image size smaller)
RUN playwright install chromium

# Expose port if running in SSE mode (optional)
EXPOSE 8000

# Set the entrypoint to run the server
ENTRYPOINT ["python", "server.py"]
