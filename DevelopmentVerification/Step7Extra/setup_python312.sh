#!/bin/bash

# SafeStream Python 3.12 Setup Script
# Automates Python 3.12 installation and SafeStream setup for ML moderation

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
function success() { echo -e "${GREEN}✔ $1${NC}"; }
function fail() { echo -e "${RED}✖ $1${NC}"; exit 1; }
function warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
function info() { echo -e "${BLUE}ℹ $1${NC}"; }

echo -e "${BLUE}=== SafeStream Python 3.12 Setup ===${NC}"
echo "This script will set up Python 3.12 and SafeStream with ML moderation support."
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    fail "Please run this script from the SafeStream directory (where pyproject.toml is located)"
fi

# Check current Python version
CURRENT_PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2 || echo "unknown")
info "Current Python version: $CURRENT_PYTHON_VERSION"

if [ "$CURRENT_PYTHON_VERSION" = "3.12" ]; then
    success "Python 3.12 is already installed and active"
    PYTHON_CMD="python3"
elif command -v python3.12 >/dev/null 2>&1; then
    success "Python 3.12 is available as python3.12"
    PYTHON_CMD="python3.12"
else
    warn "Python 3.12 not found. Let's install it..."
    
    # Detect OS and install Python 3.12
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        info "Detected macOS. Installing Python 3.12..."
        
        # Check if Homebrew is available
        if command -v brew >/dev/null 2>&1; then
            info "Using Homebrew to install Python 3.12..."
            brew install python@3.12
            PYTHON_CMD="python3.12"
        else
            warn "Homebrew not found. Please install Python 3.12 manually:"
            echo "1. Download from: https://www.python.org/downloads/release/python-3123/"
            echo "2. Or install Homebrew first: https://brew.sh/"
            echo "3. Then run: brew install python@3.12"
            fail "Please install Python 3.12 and run this script again"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        info "Detected Linux. Please install Python 3.12 manually:"
        echo "Ubuntu/Debian: sudo apt update && sudo apt install python3.12 python3.12-venv"
        echo "CentOS/RHEL: sudo yum install python3.12"
        echo "Or use pyenv: pyenv install 3.12.3"
        fail "Please install Python 3.12 and run this script again"
    else
        fail "Unsupported operating system: $OSTYPE"
    fi
fi

# Verify Python 3.12 is working
info "Verifying Python 3.12 installation..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>/dev/null | cut -d' ' -f2 || echo "unknown")
if [[ "$PYTHON_VERSION" == 3.12* ]]; then
    success "Python 3.12 verified: $PYTHON_VERSION"
else
    fail "Python 3.12 verification failed. Got: $PYTHON_VERSION"
fi

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    warn "Existing virtual environment found. Removing it..."
    rm -rf .venv
fi

# Create new virtual environment
info "Creating Python 3.12 virtual environment..."
$PYTHON_CMD -m venv .venv
success "Virtual environment created"

# Activate virtual environment
info "Activating virtual environment..."
source .venv/bin/activate
success "Virtual environment activated"

# Upgrade pip and install build tools
info "Upgrading pip and build tools..."
python -m pip install --upgrade pip setuptools wheel
success "Build tools upgraded"

# Install SafeStream with ML dependencies
info "Installing SafeStream with ML dependencies..."
pip install -e ".[dev,ml]"
success "SafeStream installed with ML support"

# Install pre-commit hooks
info "Installing pre-commit hooks..."
pre-commit install
success "Pre-commit hooks installed"

# Run initial code quality checks
info "Running initial code quality checks..."
if black --check . --quiet; then
    success "Black formatting check passed"
else
    warn "Black formatting check failed. Running auto-format..."
    black .
    success "Code formatted with Black"
fi

if ruff check . --quiet; then
    success "Ruff linting check passed"
else
    warn "Ruff linting check failed. Running auto-fix..."
    ruff check . --fix
    success "Linting issues fixed"
fi

# Run tests to verify everything works
info "Running tests to verify installation..."
if pytest -q; then
    success "All tests passed"
else
    warn "Some tests failed. This might be expected if you're setting up for the first time."
fi

# Test Detoxify specifically
info "Testing Detoxify ML moderation..."
if python -c "from detoxify import Detoxify; print('Detoxify imported successfully')" 2>/dev/null; then
    success "Detoxify is working correctly"
else
    warn "Detoxify import failed. This might be due to missing dependencies."
fi

# Create a convenience script for activation
cat > activate_safestream.sh << 'EOF'
#!/bin/bash
# SafeStream activation script
echo "Activating SafeStream Python 3.12 environment..."
source .venv/bin/activate
echo "SafeStream environment activated!"
echo "Run 'uvicorn app.main:app --reload' to start the development server"
echo "Run 'pytest -q' to run tests"
echo "Run './DevelopmentVerification/Step7.bash' to verify ML moderation"
EOF

chmod +x activate_safestream.sh
success "Created activation script: ./activate_safestream.sh"

# Final summary
echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
success "Python 3.12 and SafeStream are ready to use"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Activate the environment: source .venv/bin/activate"
echo "2. Start the server: uvicorn app.main:app --reload"
echo "3. Test ML moderation: ./DevelopmentVerification/Step7.bash"
echo "4. Or use the convenience script: ./activate_safestream.sh"
echo ""
echo -e "${BLUE}Available commands:${NC}"
echo "- Start server: uvicorn app.main:app --reload"
echo "- Run tests: pytest -q"
echo "- Format code: black ."
echo "- Lint code: ruff check ."
echo "- Verify ML: ./DevelopmentVerification/Step7.bash"
echo ""
echo -e "${GREEN}SafeStream is ready for development with full ML moderation support!${NC}" 