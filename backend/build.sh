#!/bin/bash
set -e

echo "=== Starting build process ==="

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build frontend
echo "Building frontend..."
cd ../frontend

# Limpiar node_modules previo de npm en cache si existe
if [ -d "node_modules" ] && [ ! -d "node_modules/.pnpm" ]; then
    echo "Eliminando node_modules previo de npm para evitar conflictos..."
    rm -rf node_modules
fi

# Habilitar pnpm nativo vía Corepack (incluido en Node.js 22)
corepack enable 2>/dev/null || true
corepack prepare pnpm@12.6.0 --activate 2>/dev/null || true

if command -v pnpm &> /dev/null; then
    pnpm install
    pnpm run build
else
    echo "pnpm no detectado en PATH, usando npx pnpm..."
    npx -y pnpm install
    npx -y pnpm run build
fi

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
