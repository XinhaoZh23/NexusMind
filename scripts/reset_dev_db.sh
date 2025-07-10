#!/bin/bash

# This script resets the development database to a clean state.
# It drops the entire 'public' schema, recreates it, and then
# applies all database migrations from scratch.
# WARNING: This will permanently delete all data in the public schema.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Get the directory of the script to robustly find the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

CONTAINER_NAME="nexusmind_postgres"
DB_NAME="nexusmind_db"

# --- Main Logic ---

echo "--- Resetting Development Database ---"

# 1. Check if the Docker container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: Docker container '$CONTAINER_NAME' is not running."
    echo "Please start the services with 'docker-compose up -d'."
    exit 1
fi
echo "✅ Docker container '$CONTAINER_NAME' is running."

# 2. Drop and recreate the public schema. This is a powerful and clean way to wipe the DB.
# We connect as the superuser defined in docker-compose.yml to perform this.
echo "⏳ Dropping and recreating the 'public' schema..."
docker exec "$CONTAINER_NAME" psql -U nexusmind_user -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
echo "✅ 'public' schema has been reset."

# 3. Apply all migrations to bring the schema to the latest version
echo "⏳ Applying all database migrations..."
poetry run alembic upgrade head
echo "✅ All migrations have been applied."

echo "--- Database reset complete! ---" 