# Phase 12.A: Dynamic Toxicity-Gate Implementation

This document describes the implementation of the Dynamic Toxicity-Gate feature, which allows moderators to set a global toxicity threshold that dynamically blocks messages in real-time.

## Overview

The Dynamic Toxicity-Gate provides runtime control over message moderation by:
1. Allowing moderators to set a global toxicity threshold (0.0-1.0)
2. Blocking messages with scores above the threshold for all users except the sender
3. Providing real-time threshold updates via the Streamlit dashboard
4. Persisting threshold settings in the database across restarts

## Database Schema

### Settings Table

A new `settings` table stores key-value configuration pairs:

```sql
CREATE TABLE settings (
    "key" VARCHAR(100) NOT NULL PRIMARY KEY,
    value TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

**Default Values:**
- `toxicity_threshold`: `"0.6"` (60% toxicity threshold)

## API Endpoints

### GET /api/mod/threshold

Returns the current toxicity threshold.

**Response:**
```json
{
    "threshold": 0.6
}
```

### PATCH /api/mod/threshold

Updates the toxicity threshold (admin authentication required).

**Request:**
```json
{
    "threshold": 0.75
}
```

**Response:**
```json
{
    "threshold": 0.75,
    "status": "updated"
}
```

**Validation:**
- Threshold must be a number between 0.0 and 1.0
- Requires valid JWT authentication
- Logs the action to admin_actions table

## Message Processing Pipeline

### Conditional Broadcast Logic

When a message is processed:

1. **Toxicity Detection**: Detoxify library scores the message (0.0-1.0)
2. **Threshold Check**: Compare score against current database threshold
3. **Conditional Routing**:
   - **Score ≥ Threshold**: Send only to sender with `blocked: true`
   - **Score < Threshold**: Broadcast to all clients with `blocked: false`

### Message Schema Extension

The `ChatMessageOut` schema now includes an optional `blocked` field:

```json
{
    "type": "chat",
    "id": 123,
    "user": "alice",
    "message": "hello world",
    "toxic": false,
    "score": 0.02,
    "ts": "2025-06-30T12:34:56Z",
    "blocked": false
}
```

## Client-Side Implementation

### JavaScript Message Handling

The client now processes the `blocked` field:

```javascript
function renderMessage(msg) {
    const div = document.createElement('div');
    div.className = 'chat-message';
    
    // Handle blocked messages
    if (msg.blocked) {
        div.classList.add('blocked');
        div.setAttribute('data-blocked', `Message blocked (score: ${(msg.score * 100).toFixed(1)}%)`);
    }
    
    // ... rest of rendering logic
}
```

### CSS Styling

Blocked messages are styled with:
- Red border and background
- Reduced opacity (30%)
- Tooltip showing block reason on hover

```css
.chat-message.blocked {
    background: rgba(255, 77, 77, 0.25);
    border: 2px solid #FF4D4D;
    border-radius: 18px;
    opacity: 0.3;
}
```

## Dashboard Controls

### Streamlit Threshold Slider

The moderator dashboard includes a threshold control section:

```python
new_threshold = st.slider(
    "Toxicity Threshold",
    min_value=0.0,
    max_value=1.0,
    value=current_threshold,
    step=0.05,
    format="%.2f",
    help="Messages with toxicity scores above this threshold will be blocked"
)
```

**Features:**
- Real-time threshold updates
- Visual feedback on changes
- Current threshold display
- Error handling for API failures

## Database Service Layer

### Settings Management Functions

```python
async def get_setting(session: AsyncSession, key: str, default: str | None = None) -> str | None
async def set_setting(session: AsyncSession, key: str, value: str) -> Setting
async def get_toxicity_threshold(session: AsyncSession) -> float
async def set_toxicity_threshold(session: AsyncSession, threshold: float) -> Setting
```

**Key Features:**
- Type-safe threshold handling
- Validation of threshold range (0.0-1.0)
- Fallback to default values on invalid data
- Atomic database operations

## Migration

### Alembic Revision

File: `alembic/versions/2ced2aeb79df_add_settings_table_for_toxicity_.py`

**Upgrade:**
- Creates `settings` table
- Inserts default `toxicity_threshold` = `"0.6"`

**Downgrade:**
- Drops `settings` table

## Testing

### Test Coverage

The implementation includes comprehensive tests in `tests/test_toxic_gate.py`:

1. **Settings Service Tests** (8 tests)
   - CRUD operations for settings
   - Threshold validation
   - Default value handling
   - Invalid data handling

2. **API Endpoint Tests** (6 tests)
   - GET/PATCH threshold endpoints
   - Authentication requirements
   - Input validation
   - Error handling

3. **Integration Tests** (3 tests)
   - Message schema validation
   - End-to-end blocking logic (infrastructure)

### Running Tests

```bash
pytest tests/test_toxic_gate.py -v
```

## Configuration

### Environment Variables

The system respects the existing `TOXIC_THRESHOLD` environment variable as a fallback, but database settings take precedence.

### Default Values

- **Initial Threshold**: 0.6 (60%)
- **Slider Step**: 0.05 (5%)
- **Range**: 0.0 - 1.0 (0% - 100%)

## Performance Considerations

### Database Queries

- Threshold lookup is performed once per message (cached in session)
- Settings are small key-value pairs (minimal storage overhead)
- Atomic updates prevent race conditions

### Client Performance

- Blocked messages still rendered (maintain UI consistency)
- CSS opacity reduces visual prominence
- No additional network requests for blocked messages

## Security

### Authentication

- Threshold changes require valid JWT authentication
- All admin actions are logged with user attribution
- Read-only threshold endpoint (GET) is public

### Validation

- Server-side validation of threshold range
- Type checking for numeric values
- SQL injection prevention via parameterized queries

## Monitoring

### Admin Action Logging

All threshold changes are recorded in the `admin_actions` table:

```json
{
    "action": "set_threshold",
    "action_details": "Set toxicity threshold to: 0.75",
    "admin_user_id": 123,
    "timestamp": "2025-06-30T12:34:56Z"
}
```

### Dashboard Feedback

- Success/error messages for threshold updates
- Current threshold display
- Real-time sync with database state

## Future Enhancements

### Potential Improvements

1. **User-Specific Thresholds**: Different thresholds per user role
2. **Time-Based Thresholds**: Automatic threshold adjustment by time of day
3. **Channel-Specific Thresholds**: Different thresholds for different chat rooms
4. **Threshold History**: Audit trail of threshold changes over time
5. **Gradual Enforcement**: Soft warnings before full blocking

### API Extensions

- `GET /api/mod/threshold/history` - Threshold change history
- `POST /api/mod/threshold/schedule` - Scheduled threshold changes
- `GET /api/mod/threshold/stats` - Blocking statistics by threshold

## Troubleshooting

### Common Issues

1. **Migration Failure**: Table already exists
   - Solution: `alembic stamp head` to mark migration as applied

2. **Default Threshold Not Set**: Missing database record
   - Solution: Manual insert or re-run migration

3. **Dashboard Not Updating**: API connection issues
   - Check SafeStream server is running on localhost:8000
   - Verify JWT authentication for PATCH requests

4. **Messages Not Blocking**: Threshold logic not applied
   - Verify database has correct threshold value
   - Check server logs for moderation pipeline errors

### Debug Commands

```bash
# Check current threshold in database
sqlite3 data/safestream.db "SELECT * FROM settings WHERE key = 'toxicity_threshold';"

# Test API endpoints
curl -X GET http://localhost:8000/api/mod/threshold
curl -X PATCH http://localhost:8000/api/mod/threshold -H "Authorization: Bearer TOKEN" -d '{"threshold": 0.8}'

# Run specific test
pytest tests/test_toxic_gate.py::TestSettingsService::test_get_toxicity_threshold_default -v
``` 