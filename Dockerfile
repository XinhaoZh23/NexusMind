# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set the PYTHONPATH environment variable to include the src directory
ENV PYTHONPATH "${PYTHONPATH}:/app/src"

# Install poetry
RUN pip install poetry

# Copy only the necessary files for dependency installation
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]