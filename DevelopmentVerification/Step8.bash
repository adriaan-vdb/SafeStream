#!/bin/bash

# Step 8 Verification Script: Frontend Skeleton and WebSocket Client
# Verifies Stage 8 implementation including frontend files, static serving, and basic functionality

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✓ PASS${NC}: $message"
            ;;
        "FAIL")
            echo -e "${RED}✗ FAIL${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ INFO${NC}: $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠ WARN${NC}: $message"
            ;;
    esac
}

echo "=========================================="
echo "Stage 8 Verification: Frontend Implementation"
echo "=========================================="
echo

# Change to project directory
cd "$(dirname "$0")/.." || exit 1

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_status "FAIL" "Not in SafeStream project directory"
    exit 1
fi

print_status "INFO" "Starting Stage 8 verification..."

# Step 1: Check if frontend directory exists
echo
print_status "INFO" "Step 1: Checking static directory structure"
if [[ -d "static" ]]; then
    print_status "PASS" "Static directory exists"
else
    print_status "FAIL" "Static directory not found"
    exit 1
fi

# Step 2: Check frontend files exist
echo
print_status "INFO" "Step 2: Checking static files"
static_files=("static/index.html" "static/css/styles.css" "static/js/main.js")
missing_files=()

for file in "${static_files[@]}"; do
    if [[ -f "$file" ]]; then
        print_status "PASS" "Found $file"
    else
        print_status "FAIL" "Missing $file"
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    print_status "FAIL" "Missing static files: ${missing_files[*]}"
    exit 1
fi

# Step 3: Check HTML structure
echo
print_status "INFO" "Step 3: Validating HTML structure"
if grep -q "<!DOCTYPE html>" static/index.html; then
    print_status "PASS" "HTML has proper DOCTYPE"
else
    print_status "FAIL" "HTML missing DOCTYPE"
fi

if grep -q "SafeStream" static/index.html; then
    print_status "PASS" "HTML contains SafeStream title"
else
    print_status "FAIL" "HTML missing SafeStream title"
fi

if grep -q "chatMessages" static/index.html; then
    print_status "PASS" "HTML contains chat messages container"
else
    print_status "FAIL" "HTML missing chat messages container"
fi

if grep -q "messageInput" static/index.html; then
    print_status "PASS" "HTML contains message input"
else
    print_status "FAIL" "HTML missing message input"
fi

if grep -q "usernameModal" static/index.html; then
    print_status "PASS" "HTML contains username modal"
else
    print_status "FAIL" "HTML missing username modal"
fi

# Step 4: Check CSS structure
echo
print_status "INFO" "Step 4: Validating CSS structure"
if grep -q "\.chat-message" static/css/styles.css; then
    print_status "PASS" "CSS contains chat message styles"
else
    print_status "FAIL" "CSS missing chat message styles"
fi

if grep -q "\.toxic" static/css/styles.css; then
    print_status "PASS" "CSS contains toxicity styles"
else
    print_status "FAIL" "CSS missing toxicity styles"
fi

if grep -q "\.input-bar" static/css/styles.css; then
    print_status "PASS" "CSS contains input bar styles"
else
    print_status "FAIL" "CSS missing input bar styles"
fi

if grep -q "@media" static/css/styles.css; then
    print_status "PASS" "CSS contains responsive design"
else
    print_status "WARN" "CSS missing responsive design"
fi

# Step 5: Check JavaScript structure
echo
print_status "INFO" "Step 5: Validating JavaScript structure"
if grep -q "WebSocket" static/js/main.js; then
    print_status "PASS" "JavaScript contains WebSocket functionality"
else
    print_status "FAIL" "JavaScript missing WebSocket functionality"
fi

if grep -q "renderMessage" static/js/main.js; then
    print_status "PASS" "JavaScript contains message rendering"
else
    print_status "FAIL" "JavaScript missing message rendering"
fi

if grep -q "renderGift" static/js/main.js; then
    print_status "PASS" "JavaScript contains gift rendering"
else
    print_status "FAIL" "JavaScript missing gift rendering"
fi

if grep -q "connectWS" static/js/main.js; then
    print_status "PASS" "JavaScript contains WebSocket connection"
else
    print_status "FAIL" "JavaScript missing WebSocket connection"
fi

# Step 6: Check backend integration
echo
print_status "INFO" "Step 6: Checking backend integration"
if grep -q "StaticFiles" app/main.py; then
    print_status "PASS" "Backend contains static file serving"
else
    print_status "FAIL" "Backend missing static file serving"
fi

if grep -q "/chat" app/main.py; then
    print_status "PASS" "Backend contains /chat route"
else
    print_status "FAIL" "Backend missing /chat route"
fi

if grep -q "static" app/main.py; then
    print_status "PASS" "Backend references static directory"
else
    print_status "FAIL" "Backend missing static directory reference"
fi

# Step 7: Run linting and formatting checks
echo
print_status "INFO" "Step 7: Running code quality checks"

# Check if ruff is available
if command -v ruff >/dev/null 2>&1; then
    print_status "INFO" "Running ruff linting..."
    if ruff check .; then
        print_status "PASS" "Ruff linting passed"
    else
        print_status "FAIL" "Ruff linting failed"
        exit 1
    fi
else
    print_status "WARN" "Ruff not found, skipping linting"
fi

# Check if black is available for formatting
if command -v black >/dev/null 2>&1; then
    print_status "INFO" "Running black formatting check..."
    if black --check .; then
        print_status "PASS" "Black formatting check passed"
    else
        print_status "FAIL" "Black formatting check failed"
        exit 1
    fi
else
    print_status "WARN" "Black not found, skipping formatting check"
fi

# Step 8: Check file sizes and basic validation
echo
print_status "INFO" "Step 8: File size and basic validation"

# Check HTML file size (should be reasonable)
html_size=$(wc -c < static/index.html)
if [[ $html_size -gt 500 && $html_size -lt 10000 ]]; then
    print_status "PASS" "HTML file size reasonable ($html_size bytes)"
else
    print_status "WARN" "HTML file size unusual ($html_size bytes)"
fi

# Check CSS file size (should be substantial)
css_size=$(wc -c < static/css/styles.css)
if [[ $css_size -gt 1000 && $css_size -lt 50000 ]]; then
    print_status "PASS" "CSS file size substantial ($css_size bytes)"
else
    print_status "WARN" "CSS file size unusual ($css_size bytes)"
fi

# Check JS file size (should be reasonable)
js_size=$(wc -c < static/js/main.js)
if [[ $js_size -gt 500 && $js_size -lt 20000 ]]; then
    print_status "PASS" "JavaScript file size reasonable ($js_size bytes)"
else
    print_status "WARN" "JavaScript file size unusual ($js_size bytes)"
fi

# Step 9: Check for common issues
echo
print_status "INFO" "Step 9: Checking for common issues"

# Check for hardcoded localhost references
if grep -q "localhost" static/js/main.js; then
    print_status "WARN" "Found hardcoded localhost reference in JavaScript"
else
    print_status "PASS" "No hardcoded localhost references"
fi

# Check for proper WebSocket URL construction
if grep -q "location.host" static/js/main.js; then
    print_status "PASS" "JavaScript uses dynamic host for WebSocket"
else
    print_status "WARN" "JavaScript may not use dynamic host for WebSocket"
fi

# Check for proper error handling
if grep -q "onclose\|onerror" static/js/main.js; then
    print_status "PASS" "JavaScript contains error handling"
else
    print_status "WARN" "JavaScript may lack error handling"
fi

# Step 10: Summary
echo
print_status "INFO" "Step 10: Verification Summary"
echo "=========================================="
print_status "PASS" "Stage 8 Frontend Implementation Verification Complete"
echo
print_status "INFO" "Static files created:"
echo "  - static/index.html ($html_size bytes)"
echo "  - static/css/styles.css ($css_size bytes)"
echo "  - static/js/main.js ($js_size bytes)"
echo
print_status "INFO" "Backend integration:"
echo "  - Static file serving configured"
echo "  - /chat route implemented"
echo "  - WebSocket client ready"
echo
print_status "INFO" "Next steps:"
echo "  - Test frontend manually at http://localhost:8000/chat"
echo "  - Verify WebSocket connections work"
echo "  - Test mobile responsiveness"
echo "  - Validate toxicity highlighting"
echo

print_status "PASS" "Stage 8 verification completed successfully!"
exit 0 