#!/bin/bash

# Product Organizer - Setup Script

echo "=========================================="
echo "Product Organizer - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.7 or higher."
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install boto3

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Create directories
echo "Creating directories..."
mkdir -p raw_assets
mkdir -p organized_products

echo "✓ Directories created:"
echo "  - raw_assets/          (put your product files here)"
echo "  - organized_products/  (organized output will go here)"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "✓ AWS credentials configured"
    echo ""
    echo "Would you like to enable S3 upload? (y/n)"
    read -r enable_s3
    
    if [ "$enable_s3" = "y" ]; then
        echo "Enter your S3 bucket name:"
        read -r bucket_name
        
        # Update the script with S3 bucket
        sed -i.bak "s/S3_BUCKET = None/S3_BUCKET = \"$bucket_name\"/" product_organizer_final.py
        echo "✓ S3 upload enabled with bucket: $bucket_name"
    fi
else
    echo "⚠ AWS credentials not configured (S3 upload will be disabled)"
    echo "  To configure AWS: aws configure"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Place your product files in: raw_assets/"
echo "2. Run the organizer: python3 product_organizer_final.py"
echo ""
echo "Test with sample data:"
echo "  python3 create_test_data.py"
echo "  python3 product_organizer_final.py"
echo ""
