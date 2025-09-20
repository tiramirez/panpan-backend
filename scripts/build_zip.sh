#!/bin/bash

set -euo pipefail

# Global cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "🧹 Cleaning up build directories due to failure..."
        rm -rf "$BUILD_DIR"
    fi
    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT

# Function to display usage
usage() {
    echo "Usage: $0 [LAMBDA_NAME]"
    echo "  LAMBDA_NAME: Specific lambda to build (optional, builds all if not provided)"
    echo "  Examples:"
    echo "    $0                    # Build all lambdas"
    echo "    $0 lambda_test        # Build only lambda_test"
    exit 1
}

# Function to build a single lambda
build_lambda() {
    local lambda_name="$1"
    local lambda_path="$2"
    local build_dir="$BUILD_DIR/$lambda_name"
    local zip_file="$(pwd)/$DIST_DIR/$lambda_name.zip"

    echo "🧹 Cleaning build directory for $lambda_name..."
    rm -rf "$build_dir"
    mkdir -p "$build_dir"

    echo "📋 Copying source files for $lambda_name..."
    
    # Method 1: Try copying all contents with proper path handling
    if [ -d "$lambda_path" ]; then
        # Copy all files and subdirectories
        if ! cp -r "$lambda_path"/* "$build_dir"/ 2>/dev/null; then
            echo "⚠️  Primary copy method failed, trying alternative..."
            # Method 2: Copy individual items
            for item in "$lambda_path"/*; do
                if [ -e "$item" ]; then
                    item_name=$(basename "$item")
                    echo "   Copying: $item_name"
                    cp -r "$item" "$build_dir"/
                fi
            done
        fi
    else
        echo "❌ Lambda directory $lambda_path does not exist"
        exit 1
    fi
    
    # Verify essential files were copied
    if [ ! -f "$build_dir/handler.py" ]; then
        echo "❌ handler.py not found in build directory after copy"
        echo "💡 Files in build directory:"
        ls -la "$build_dir" || echo "   (build directory is empty)"
        exit 1
    fi
    
    echo "✅ Source files copied successfully"

    # Install dependencies if requirements.txt exists
    if [ -f "$lambda_path/requirements.txt" ]; then
        echo "📦 Installing dependencies for $lambda_name..."
        
        # Check if requirements.txt is not empty
        if [ ! -s "$lambda_path/requirements.txt" ]; then
            echo "⚠️  Warning: requirements.txt is empty, skipping dependency installation"
        else
            # Install dependencies with better error handling
            if ! pip install -r "$lambda_path/requirements.txt" --target "$build_dir" --no-deps --quiet --disable-pip-version-check; then
                echo "❌ Failed to install dependencies for $lambda_name"
                echo "💡 Try running: pip install -r $lambda_path/requirements.txt --target $build_dir"
                exit 1
            fi
            
            # Verify dependencies were installed
            echo "🔍 Verifying installed dependencies..."
            if ! python -c "import sys; sys.path.insert(0, '$build_dir'); import pkg_resources; pkg_resources.require(open('$lambda_path/requirements.txt').read().splitlines())" 2>/dev/null; then
                echo "⚠️  Warning: Could not verify all dependencies, but continuing..."
            else
                echo "✅ Dependencies verified successfully"
            fi
        fi
    else
        echo "ℹ️  No requirements.txt found, skipping dependency installation"
    fi

    # Zip the contents
    echo "🗜️  Zipping $lambda_name into $zip_file"
    if ! (cd "$build_dir" && zip -r "$zip_file" . -q); then
        echo "❌ Failed to create zip file for $lambda_name"
        exit 1
    fi

    # Verify zip file was created and has content
    if [ ! -f "$zip_file" ] || [ ! -s "$zip_file" ]; then
        echo "❌ Zip file for $lambda_name is empty or missing"
        exit 1
    fi
    
    # Additional validation: check zip file integrity
    if ! unzip -t "$zip_file" >/dev/null 2>&1; then
        echo "❌ Zip file for $lambda_name is corrupted"
        exit 1
    fi
    
    # Check if handler.py is in the zip
    if ! unzip -l "$zip_file" | grep -q "handler\.py"; then
        echo "❌ handler.py not found in zip file for $lambda_name"
        echo "💡 Zip contents:"
        unzip -l "$zip_file" | head -10
        exit 1
    fi
    
    # Get file size for reporting
    local file_size=$(du -h "$zip_file" | cut -f1)
    local file_count=$(unzip -l "$zip_file" | tail -1 | awk '{print $2}')
    
    echo "✅ Successfully built: $lambda_name"
    echo "   📦 Size: $file_size"
    echo "   📁 Files: $file_count"
}

LAMBDA_DIR="./lambdas"
DIST_DIR="./dist"
BUILD_DIR="./build"

# Ensure dist directory exists
mkdir -p "$DIST_DIR"

# If lambda name provided, build only that lambda
if [ $# -eq 1 ]; then
    LAMBDA_NAME="$1"
    LAMBDA_PATH="$LAMBDA_DIR/$LAMBDA_NAME"
    
    # Validate lambda directory exists
    if [ ! -d "$LAMBDA_PATH" ]; then
        echo "❌ Error: Lambda directory '$LAMBDA_PATH' not found"
        echo "💡 Available lambdas:"
        ls -1 "$LAMBDA_DIR" 2>/dev/null | sed 's/^/   - /' || echo "   (none found)"
        exit 1
    fi
    
    # Validate handler.py exists
    if [ ! -f "$LAMBDA_PATH/handler.py" ]; then
        echo "❌ Error: handler.py not found in '$LAMBDA_PATH'"
        echo "💡 Files in $LAMBDA_PATH:"
        ls -la "$LAMBDA_PATH" 2>/dev/null | sed 's/^/   /' || echo "   (directory is empty)"
        exit 1
    fi
    
    echo "📦 Building Lambda: $LAMBDA_NAME"
    build_lambda "$LAMBDA_NAME" "$LAMBDA_PATH"
    
elif [ $# -eq 0 ]; then
    echo "📦 Building all Lambda functions..."
    for lambda_path in "$LAMBDA_DIR"/*/; do
        if [ -d "$lambda_path" ]; then
            lambda_name=$(basename "$lambda_path")
            build_lambda "$lambda_name" "$lambda_path"
        fi
    done
    echo "🎉 All Lambda functions zipped in $DIST_DIR/"
else
    usage
fi
