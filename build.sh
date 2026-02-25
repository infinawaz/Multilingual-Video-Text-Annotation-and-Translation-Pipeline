#!/usr/bin/env bash
# Build script for Render native Python runtime
# Installs Tesseract OCR + language packs and Python dependencies

set -o errexit

# Install Tesseract OCR and language packs
apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-ben \
    tesseract-ocr-tam \
    fonts-dejavu-core

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
