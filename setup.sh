#!/bin/bash

# Quick setup script for Mac/Linux

echo "========================================"
echo "Connectly Project - Quick Setup"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ -d "env" ]; then
    echo "Virtual environment already exists."
else
    echo "Creating virtual environment..."
    python3 -m venv env
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

echo ""
echo "Activating virtual environment..."
source env/bin/activate

echo ""
echo "Installing dependencies..."
cd connectly_project
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Running database migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to run migrations"
    exit 1
fi

echo ""
echo "Generating authentication token..."
python create_token.py

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Import Connectly_API.postman_collection.json into Postman"
echo "2. Disable SSL verification in Postman (Settings -> General)"
echo "3. Run: python manage.py runserver_plus --cert-file cert.pem --key-file key.pem"
echo ""
echo "The server will be available at: https://127.0.0.1:8000"
echo ""
