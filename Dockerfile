# Dockerfile
FROM python:3.10

WORKDIR /app

# Copy the requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN python -m venv .venv
RUN . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire project
COPY . .

# Run the main.py script
CMD ["venv/bin/python", "main.py"]
