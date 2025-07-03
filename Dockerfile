FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only the files needed for dependency installation
COPY poetry.lock pyproject.toml ./

# Install project dependencies
# --no-root means do not install the project itself, only its dependencies
RUN poetry install --no-root

# Copy the entire project source code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 