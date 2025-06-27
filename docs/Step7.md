# Stage 7: Detoxify ML Moderation Integration

## Overview

Stage 7 integrates Detoxify, a pre-trained toxicity detection model from HuggingFace, into SafeStream's moderation pipeline. This provides real-time toxicity detection for chat messages with configurable sensitivity and fallback stub mode.

## Key Features

- **Real-time toxicity detection** using Detoxify "original-small" model
- **Lazy model loading** - only loads when first needed
- **Environment-based configuration** - disable for testing/CI
- **Configurable threshold** - adjust sensitivity via `TOXIC_THRESHOLD`
- **Stub mode fallback** - always returns non-toxic when disabled
- **Async interface** - non-blocking predictions

## Implementation Details

### Dependencies

Added to `pyproject.toml`:
```toml
[project.optional-dependencies]
ml = ["detoxify~=0.5", "torch>=2.0,<3.0"]
dev = [
    # ... existing dev deps ...
    "detoxify~=0.5",  # ML moderation
    "torch>=2.0,<3.0",  # Required by detoxify
]
```

### Core Moderation Module

`app/moderation.py`:
- Lazy loading with `@lru_cache` decorator
- Environment variable support (`DISABLE_DETOXIFY`, `TOXIC_THRESHOLD`)
- Async `predict(text: str) -> tuple[bool, float]` interface
- Comprehensive error handling and documentation

### Testing Strategy

`tests/test_moderation.py`:
- Tests for both stub and real modes
- Environment variable patching
- Custom threshold testing
- Async interface validation
- Conditional tests based on Detoxify availability

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DISABLE_DETOXIFY` | `"0"` | Set to `"1"` to use stub mode |
| `TOXIC_THRESHOLD` | `0.6` | Threshold for toxic classification |

## Usage Examples

### Production Setup
```bash
# Install with ML dependencies
pip install -e ".[dev,ml]"

# Run with real toxicity detection
uvicorn app.main:app --reload
```

### Development/CI Setup
```bash
# Install without ML dependencies
pip install -e ".[dev]"

# Disable Detoxify (uses stub)
export DISABLE_DETOXIFY=1
uvicorn app.main:app --reload
```

### Custom Threshold
```bash
# More sensitive (lower threshold)
export TOXIC_THRESHOLD=0.3

# Less sensitive (higher threshold)
export TOXIC_THRESHOLD=0.8
```

## Performance Characteristics

- **First run**: Downloads ~60MB model, slow inference
- **Subsequent runs**: ~10ms inference on CPU
- **Memory usage**: ~200MB RAM
- **Model**: Detoxify "original-small" (HuggingFace)

## Testing

### Run All Tests
```bash
# With stub mode (fast)
export DISABLE_DETOXIFY=1
pytest tests/test_moderation.py -q

# With real model (requires Detoxify)
export DISABLE_DETOXIFY=0
pytest tests/test_moderation.py -q
```

### Verification Script
```bash
# Run comprehensive verification
./scripts/Step7.bash
```

## CI/CD Integration

Updated `.github/workflows/ci.yml`:
```yaml
env:
  DISABLE_DETOXIFY: "1"  # Use stub mode in CI
```

This ensures:
- Fast CI runs without model downloads
- No ML dependencies required for basic tests
- Consistent test behavior across environments

## API Integration

The moderation pipeline integrates seamlessly with existing WebSocket chat:

```python
# In app/main.py WebSocket handler
is_toxic, score = await predict(message)
response = {
    "type": "chat",
    "user": username,
    "message": message,
    "toxic": is_toxic,
    "score": score,
    "ts": timestamp
}
```

## Error Handling

- **Model loading failures**: Falls back to stub mode
- **Prediction errors**: Returns `(False, 0.0)` as safe default
- **Environment issues**: Graceful degradation with logging

## Future Enhancements

- **Model caching**: Persistent model storage
- **Batch processing**: Multiple messages at once
- **Custom models**: Support for fine-tuned models
- **Multi-language**: Language detection and translation
- **Performance optimization**: GPU acceleration, model quantization

## Troubleshooting

### Common Issues

1. **Slow first inference**
   - Normal behavior - model is loading
   - Subsequent calls will be fast

2. **Memory usage high**
   - Model requires ~200MB RAM
   - Consider stub mode for development

3. **Import errors**
   - Install ML dependencies: `pip install -e ".[dev,ml]"`
   - Or use stub mode: `export DISABLE_DETOXIFY=1`

4. **CI failures**
   - Ensure `DISABLE_DETOXIFY=1` in CI environment
   - Tests should run without ML dependencies

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import asyncio
from app.moderation import predict

async def debug():
    result = await predict('test message')
    print(f'Result: {result}')

asyncio.run(debug())
"
```

## Migration from Stage 6

No breaking changes - existing code continues to work:
- WebSocket protocol unchanged
- API endpoints unchanged
- Configuration backward compatible
- Tests continue to pass

The only change is the addition of real toxicity detection when Detoxify is available and enabled. 