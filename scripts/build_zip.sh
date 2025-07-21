#!/bin/bash

set -euo pipefail

LAMBDA_DIR="./lambdas"
DIST_DIR="./dist"

echo "🧹 Cleaning output directory..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

for lambda_path in "$LAMBDA_DIR"/*/; do
    lambda_name=$(basename "$lambda_path")
    build_dir="./build/$lambda_name"
    zip_file="$(pwd)/$DIST_DIR/$lambda_name.zip"

    echo "📦 Building Lambda: $lambda_name"

    # Clean and prepare build directory
    rm -rf "$build_dir"
    mkdir -p "$build_dir"

    # Copy source files
    cp -r "$lambda_path"*.py "$build_dir"/

    # Install dependencies if requirements.txt exists
    if [ -f "$lambda_path/requirements.txt" ]; then
        echo "📦 Installing dependencies for $lambda_name"
        pip install -r "$lambda_path/requirements.txt" --target "$build_dir"
    fi

    # Zip the contents
    echo "🗜️  Zipping $lambda_name into $zip_file"
    (
        cd "$build_dir"
        zip -r "$zip_file" .
    )

    echo "✅ Finished: $lambda_name"
done

echo "🎉 All Lambda functions zipped in $DIST_DIR/"
