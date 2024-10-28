#!/bin/bash

# Function to set up the virtual environment on Windows
setup_venv_windows() {
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    python s3_file_uploader.py
}

# Function to set up the virtual environment on macOS
setup_venv_macos() {
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python s3_file_uploader.py
}

# Prompt the user to choose the operating system
echo "Select your operating system:"
echo "1. Windows"
echo "2. macOS"
read -p "Enter your choice (1 or 2): " choice

# Set up the virtual environment based on the user's choice
case $choice in
    1)
        setup_venv_windows
        ;;
    2)
        setup_venv_macos
        ;;
    *)
        echo "Invalid choice. Please try again."
        exit 1
        ;;
esac
