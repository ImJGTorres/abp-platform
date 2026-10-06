#!/usr/bin/env bash
set -euo pipefail

FRONTEND=frontend
BACKEND=backend

cd $FRONTEND
pnpm install --frozen-lockfile
pnpm build

cd ..

rm -rf $BACKEND/static/assets
cp -r $FRONTEND/dist/assets $BACKEND/static/

cp $FRONTEND/dist/index.html $BACKEND/templates/index.html