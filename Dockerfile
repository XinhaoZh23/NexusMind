# Stage 1: Builder
# Use an official Python runtime as a parent image
FROM python:3.11-slim as builder

# Set the working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy the dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
# --no-root: Don't install the project package itself
# --only main: Only install dependencies from the main group (production)
RUN poetry config virtualenvs.in-project true && poetry install --no-root --only main

# Stage 2: Runtime
# Use a slim version of Python for the runtime environment
FROM python:3.11-slim as runtime

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv/ .venv/

# Copy the application code
COPY core/ ./core
COPY main.py .

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 