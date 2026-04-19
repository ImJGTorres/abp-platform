#!/bin/bash
set -e

echo "=== Starting build process ==="

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build frontend
echo "Building frontend..."
cd ../frontend
npm install
npm run build

# Copy frontend files to backend
echo "Copying frontend build to backend..."
cd ../backend
rm -rf static/assets
mkdir -p static/assets
cp -r ../frontend/dist/assets/* static/assets/
cp ../frontend/dist/index.html templates/index.html

# Django collectstatic
echo "Running Django collectstatic..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

echo "=== Build complete ==="
