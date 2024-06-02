# Use the official Playwright image with all dependencies
FROM mcr.microsoft.com/playwright:focal

# Set the working directory
WORKDIR /app

# Copy your application files to the working directory
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Set the entry point to your application
CMD ["python", "api/oai_agent.py"]
