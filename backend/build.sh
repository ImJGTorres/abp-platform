#!/bin/bash
set -e

echo "=== Starting build process ==="

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build frontend
echo "Building frontend..."
cd ../frontend
# pnpm (versión fijada en package.json → packageManager); si no está instalado,
# se activa con corepack (incluido en Node) o, en último caso, vía npx.
if ! command -v pnpm >/dev/null 2>&1; then
    corepack enable pnpm 2>/dev/null || true
fi
if command -v pnpm >/dev/null 2>&1; then
    PNPM="pnpm"
else
    PNPM="npx --yes pnpm@12.6.0"
fi
$PNPM install --frozen-lockfile
$PNPM build

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
