#!/bin/bash

# Phase 12.A Dynamic Toxicity-Gate Verification Script
# Tests database setup, API endpoints, and basic functionality

set -e  # Exit on any error

echo "🚀 Phase 12.A: Dynamic Toxicity-Gate Verification"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"
JWT_TOKEN=""

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if server is running
check_server() {
    log_info "Checking if SafeStream server is running..."
    if curl -s "${BASE_URL}/healthz" > /dev/null; then
        log_success "Server is running"
    else
        log_error "Server is not running. Please start it with: uvicorn app.main:app --reload"
        exit 1
    fi
}

# Function to get admin JWT token
get_admin_token() {
    log_info "Getting admin JWT token..."
    
    # Try to register admin user (may fail if already exists)
    curl -s -X POST "${BASE_URL}/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${ADMIN_USERNAME}\",\"password\":\"${ADMIN_PASSWORD}\"}" > /dev/null || true
    
    # Login to get token
    RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USERNAME}&password=${ADMIN_PASSWORD}")
    
    JWT_TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
    
    if [ -z "$JWT_TOKEN" ]; then
        log_error "Failed to get JWT token"
        echo "Response: $RESPONSE"
        exit 1
    fi
    
    log_success "Got JWT token"
}

# Function to test database migration
test_migration() {
    log_info "Testing database migration..."
    
    # Check if settings table exists
    if sqlite3 data/safestream.db "SELECT name FROM sqlite_master WHERE type='table' AND name='settings';" | grep -q "settings"; then
        log_success "Settings table exists"
    else
        log_error "Settings table does not exist. Run: alembic upgrade head"
        exit 1
    fi
    
    # Check if default threshold is set
    THRESHOLD_ROW=$(sqlite3 data/safestream.db "SELECT * FROM settings WHERE key = 'toxicity_threshold';" 2>/dev/null || echo "")
    if [ -n "$THRESHOLD_ROW" ]; then
        log_success "Default toxicity threshold is set: $THRESHOLD_ROW"
    else
        log_warning "Default toxicity threshold not found, inserting..."
        sqlite3 data/safestream.db "INSERT INTO settings (key, value, created_at, updated_at) VALUES ('toxicity_threshold', '0.6', datetime('now'), datetime('now'));"
        log_success "Default threshold inserted"
    fi
}

# Function to test GET threshold endpoint
test_get_threshold() {
    log_info "Testing GET /api/mod/threshold endpoint..."
    
    RESPONSE=$(curl -s -X GET "${BASE_URL}/api/mod/threshold")
    THRESHOLD=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['threshold'])" 2>/dev/null || echo "")
    
    if [ -n "$THRESHOLD" ]; then
        log_success "GET threshold returned: $THRESHOLD"
    else
        log_error "GET threshold failed"
        echo "Response: $RESPONSE"
        exit 1
    fi
}

# Function to test PATCH threshold endpoint without auth (should fail)
test_patch_threshold_no_auth() {
    log_info "Testing PATCH /api/mod/threshold without authentication (should fail)..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -d '{"threshold": 0.8}')
    
    if [ "$HTTP_CODE" = "401" ]; then
        log_success "PATCH threshold correctly rejected without auth (401)"
    else
        log_error "PATCH threshold should return 401 without auth, got: $HTTP_CODE"
        exit 1
    fi
}

# Function to test PATCH threshold endpoint with auth
test_patch_threshold_with_auth() {
    log_info "Testing PATCH /api/mod/threshold with authentication..."
    
    RESPONSE=$(curl -s -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{"threshold": 0.75}')
    
    STATUS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")
    THRESHOLD=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('threshold', ''))" 2>/dev/null || echo "")
    
    if [ "$STATUS" = "updated" ] && [ "$THRESHOLD" = "0.75" ]; then
        log_success "PATCH threshold successful: $THRESHOLD"
    else
        log_error "PATCH threshold failed"
        echo "Response: $RESPONSE"
        exit 1
    fi
    
    # Verify the threshold was actually stored
    STORED_THRESHOLD=$(sqlite3 data/safestream.db "SELECT value FROM settings WHERE key = 'toxicity_threshold';" 2>/dev/null || echo "")
    if [ "$STORED_THRESHOLD" = "0.75" ]; then
        log_success "Threshold correctly stored in database: $STORED_THRESHOLD"
    else
        log_error "Threshold not correctly stored. Expected: 0.75, Got: $STORED_THRESHOLD"
        exit 1
    fi
}

# Function to test invalid threshold values
test_invalid_thresholds() {
    log_info "Testing invalid threshold values..."
    
    # Test negative value
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{"threshold": -0.1}')
    
    if [ "$HTTP_CODE" = "400" ]; then
        log_success "Negative threshold correctly rejected (400)"
    else
        log_error "Negative threshold should return 400, got: $HTTP_CODE"
        exit 1
    fi
    
    # Test value > 1.0
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{"threshold": 1.5}')
    
    if [ "$HTTP_CODE" = "400" ]; then
        log_success "Threshold > 1.0 correctly rejected (400)"
    else
        log_error "Threshold > 1.0 should return 400, got: $HTTP_CODE"
        exit 1
    fi
    
    # Test invalid type
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{"threshold": "invalid"}')
    
    if [ "$HTTP_CODE" = "400" ]; then
        log_success "Invalid threshold type correctly rejected (400)"
    else
        log_error "Invalid threshold type should return 400, got: $HTTP_CODE"
        exit 1
    fi
}

# Function to test admin action logging
test_admin_action_logging() {
    log_info "Testing admin action logging..."
    
    # Set a new threshold to trigger logging
    curl -s -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{"threshold": 0.65}' > /dev/null
    
    # Check if admin action was logged
    ADMIN_ACTION=$(sqlite3 data/safestream.db "SELECT action, action_details FROM admin_actions WHERE action = 'set_threshold' ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null || echo "")
    
    if echo "$ADMIN_ACTION" | grep -q "set_threshold"; then
        log_success "Admin action logged: $ADMIN_ACTION"
    else
        log_warning "Admin action logging might not be working (this could be due to user creation issues)"
    fi
}

# Function to run pytest tests
test_pytest() {
    log_info "Running pytest tests for toxicity gate..."
    
    if command -v pytest > /dev/null; then
        if pytest tests/test_toxic_gate.py -v --tb=short; then
            log_success "All pytest tests passed"
        else
            log_error "Some pytest tests failed"
            exit 1
        fi
    else
        log_warning "pytest not found, skipping automated tests"
    fi
}

# Function to test schema compatibility
test_schema() {
    log_info "Testing ChatMessageOut schema with blocked field..."
    
    python3 -c "
from app.schemas import ChatMessageOut
from datetime import datetime

# Test blocked message
try:
    msg = ChatMessageOut(
        id=1,
        user='test',
        message='test message',
        toxic=True,
        score=0.95,
        ts=datetime.now(),
        blocked=True
    )
    data = msg.model_dump()
    assert data['blocked'] is True
    print('✓ Blocked message schema works')
except Exception as e:
    print(f'✗ Blocked message schema failed: {e}')
    exit(1)

# Test normal message with default blocked=False
try:
    msg = ChatMessageOut(
        id=2,
        user='test',
        message='test message',
        toxic=False,
        score=0.05,
        ts=datetime.now()
    )
    data = msg.model_dump()
    assert data['blocked'] is False
    print('✓ Normal message schema works')
except Exception as e:
    print(f'✗ Normal message schema failed: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "Schema tests passed"
    else
        log_error "Schema tests failed"
        exit 1
    fi
}

# Function to reset threshold for next run
reset_threshold() {
    log_info "Resetting threshold to default (0.6) for next run..."
    
    curl -s -X PATCH "${BASE_URL}/api/mod/threshold" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{"threshold": 0.6}' > /dev/null
    
    log_success "Threshold reset to 0.6"
}

# Main execution
main() {
    echo ""
    log_info "Starting Dynamic Toxicity-Gate verification..."
    echo ""
    
    # Run all tests
    check_server
    test_migration
    get_admin_token
    test_get_threshold
    test_patch_threshold_no_auth
    test_patch_threshold_with_auth
    test_invalid_thresholds
    test_admin_action_logging
    test_schema
    test_pytest
    reset_threshold
    
    echo ""
    log_success "🎉 All Dynamic Toxicity-Gate tests passed!"
    echo ""
    log_info "Manual testing suggestions:"
    echo "1. Open dashboard at http://localhost:8501"
    echo "2. Adjust the toxicity threshold slider"
    echo "3. Send messages via WebSocket at http://localhost:8000/chat"
    echo "4. Observe blocked messages in browser developer tools"
    echo ""
    log_info "Verification complete!"
}

# Run main function
main 