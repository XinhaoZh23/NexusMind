# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set the PYTHONPATH environment variable
ENV PYTHONPATH "${PYTHONPATH}:/app/src"

# Install poetry
RUN pip install poetry

# Copy only the necessary files for dependency installation
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .

# Command to run the application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 