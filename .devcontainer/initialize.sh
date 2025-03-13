#!/bin/bash

# Update apt-get and install necessary packages
sudo apt-get update
sudo apt-get install -y python3-dev

# Check if running on Windows (WSL)
if grep -q "microsoft" /proc/version; then
    echo "Running on WSL"
    # Add any Windows-specific initialization commands here if needed
else
    echo "Not running on WSL"
    # Add any Linux-specific initialization commands here if needed
fi