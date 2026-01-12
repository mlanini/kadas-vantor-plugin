#!/bin/bash
# Package the KADAS Vantor Open Data plugin for distribution
#
# This script creates a zip file suitable for QGIS/KADAS plugin installation
#
# Usage:
#   ./package_plugin.sh                          # Default packaging
#   ./package_plugin.sh --output /path/to/out    # Custom output path
#   ./package_plugin.sh --no-version             # Don't include version in filename
#
# Requirements:
#   - zip command

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
PLUGIN_NAME="kadas_maxar"
SOURCE_DIR="${SCRIPT_DIR}/kadas_maxar"
OUTPUT_DIR="${SCRIPT_DIR}"
INCLUDE_VERSION=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source|-s)
            SOURCE_DIR="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --no-version)
            INCLUDE_VERSION=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --source, -s PATH     Source plugin directory (default: kadas_maxar)"
            echo "  --output, -o PATH     Output directory for zip file (default: current dir)"
            echo "  --no-version          Don't include version in filename"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if source directory exists
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "Error: Source directory not found: $SOURCE_DIR"
    exit 1
fi

# Get version from metadata.txt
VERSION=$(grep "^version=" "${SOURCE_DIR}/metadata.txt" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')
if [[ -z "$VERSION" ]]; then
    VERSION="unknown"
fi

# Create output filename
if [[ "$INCLUDE_VERSION" == true ]]; then
    ZIP_NAME="kadas-vantor-plugin-${VERSION}.zip"
else
    ZIP_NAME="kadas-vantor-plugin.zip"
fi

OUTPUT_PATH="${OUTPUT_DIR}/${ZIP_NAME}"

echo "Packaging KADAS Vantor Open Data Plugin"
echo "========================================"
echo "Source directory: $SOURCE_DIR"
echo "Plugin name: $PLUGIN_NAME"
echo "Version: $VERSION"
echo "Output: $OUTPUT_PATH"
echo ""

# Create temp directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/${PLUGIN_NAME}"

# Copy plugin files
echo "Copying plugin files..."
mkdir -p "$PACKAGE_DIR"
cp -r "${SOURCE_DIR}/"* "$PACKAGE_DIR/"

# Remove unwanted files and directories
echo "Cleaning up..."
find "$PACKAGE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".svn" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".idea" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".vscode" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name "__MACOSX" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.bak" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*~" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name ".DS_Store" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "ui_*.py" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "resources_rc.py" -delete 2>/dev/null || true

# Remove development/documentation files
rm -f "$PACKAGE_DIR/debug_ui.py" 2>/dev/null || true
rm -f "$PACKAGE_DIR/pytest.ini" 2>/dev/null || true
rm -f "$PACKAGE_DIR/CHANGELOG.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/COMPLETION_REPORT.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/DEPLOYMENT_CHECKLIST.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/IMPLEMENTATION_NOTES.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/IMPLEMENTATION_SUMMARY.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/README_IMPLEMENTATION.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/UNLOAD_TESTING.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/QUICK_REFERENCE.md" 2>/dev/null || true
rm -f "$PACKAGE_DIR/implementation_metadata.json" 2>/dev/null || true
rm -f "$PACKAGE_DIR/dialogs/maxar_dock_old.py" 2>/dev/null || true

# Remove existing zip if it exists
if [[ -f "$OUTPUT_PATH" ]]; then
    rm "$OUTPUT_PATH"
fi

# Create zip file
echo "Creating zip archive..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_PATH" "$PLUGIN_NAME" -x "*.pyc" -x "*__pycache__*" -x "*.git*" >/dev/null

# Cleanup
rm -rf "$TEMP_DIR"

# Display results
ZIP_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
echo ""
echo "=================================================="
echo "Plugin packaged successfully!"
echo "=================================================="
echo "Output: $OUTPUT_PATH"
echo "Size: $ZIP_SIZE"
echo ""
echo "To install in KADAS:"
echo "  1. Plugins → Manage and Install Plugins"
echo "  2. Click 'Install from ZIP'"
echo "  3. Select: $OUTPUT_PATH"
echo ""
echo "To upload to QGIS Plugin Repository:"
echo "  https://plugins.qgis.org/plugins/"
echo "=================================================="

# Verify zip contents (first 50 files)
echo ""
echo "Zip contents (first 50 files):"
echo "-------------------------------"
unzip -l "$OUTPUT_PATH" | head -53
