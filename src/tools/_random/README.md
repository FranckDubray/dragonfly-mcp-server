# True Random Number Generator

Generate cryptographically secure true random numbers using **physical sources** (atmospheric noise, quantum phenomena).

## 🎲 Physical Sources

### 1. Cisco Outshift QRNG (Quantum)
- **Source**: Quantum hardware (quantum phenomena)
- **Speed**: Very fast (~100ms)
- **Limit**: 100,000 bits/day (free tier)
- **Requires**: `CISCO_QRNG_API_KEY` environment variable

### 2. RANDOM.ORG (Atmospheric)
- **Source**: Atmospheric radio noise
- **Speed**: Fast (~200ms)
- **Limit**: ~1,000,000 bits/day (no key required)
- **Certification**: Gaming Labs International certified

### 3. Fallback (CSPRNG)
- **Source**: Python's `secrets` module (cryptographically secure pseudo-random)
- **Speed**: Instant
- **Limit**: Unlimited
- **Note**: Not true random, but cryptographically secure

## 🔧 Operations

### generate_integers
Generate random integers in a range.

```json
{
  "operation": "generate_integers",
  "min": 1,
  "max": 100,
  "count": 10,
  "unique": false,
  "source": "auto"
}
```

### generate_floats
Generate random floating-point numbers.

```json
{
  "operation": "generate_floats",
  "min": 0.0,
  "max": 1.0,
  "count": 5,
  "decimals": 4,
  "source": "quantum"
}
```

### generate_bytes
Generate random bytes (cryptographic use).

```json
{
  "operation": "generate_bytes",
  "length": 32,
  "format": "hex",
  "source": "atmospheric"
}
```

**Formats**: `hex`, `base64`, `decimal`

### coin_flip
Flip a coin (heads/tails).

```json
{
  "operation": "coin_flip",
  "count": 10,
  "source": "auto"
}
```

### dice_roll
Roll dice with N sides.

```json
{
  "operation": "dice_roll",
  "sides": 20,
  "count": 5,
  "source": "quantum"
}
```

### shuffle
Shuffle a list using Fisher-Yates with true randomness.

```json
{
  "operation": "shuffle",
  "items": ["apple", "banana", "cherry", "date"],
  "source": "atmospheric"
}
```

### pick_random
Pick random items from a list (no duplicates).

```json
{
  "operation": "pick_random",
  "items": ["red", "green", "blue", "yellow"],
  "count": 2,
  "source": "auto"
}
```

## 📊 Source Selection

### auto (recommended)
Tries sources in order:
1. Cisco QRNG (quantum) - fastest
2. RANDOM.ORG (atmospheric) - fallback
3. Python secrets (CSPRNG) - final fallback

### atmospheric
Forces RANDOM.ORG (atmospheric noise).

### quantum
Forces Cisco QRNG (quantum hardware).

## ⚙️ Configuration

### Environment Variables

```bash
# Optional: Cisco QRNG API key (100k bits/day free)
CISCO_QRNG_API_KEY=your_cisco_api_key_here
```

**Get a key**: https://developer.cisco.com/

**Note**: RANDOM.ORG works without API key (public HTTP interface).

## 🎯 Use Cases

### Cryptography
```json
{
  "operation": "generate_bytes",
  "length": 32,
  "format": "hex",
  "source": "quantum"
}
```

### Gaming / Lotteries
```json
{
  "operation": "dice_roll",
  "sides": 6,
  "count": 3,
  "source": "atmospheric"
}
```

### Random Selection
```json
{
  "operation": "pick_random",
  "items": ["Alice", "Bob", "Charlie", "Diana"],
  "count": 1,
  "source": "auto"
}
```

### A/B Testing
```json
{
  "operation": "generate_integers",
  "min": 0,
  "max": 1,
  "count": 1000,
  "source": "quantum"
}
```

## 🛡️ Security

- **True Random**: Physical sources (not algorithmic)
- **Fallback Safety**: Always returns valid data
- **Source Tracking**: Know which source was used
- **CSPRNG Fallback**: Cryptographically secure if physical sources fail

## 📈 Performance

| Operation | Quantum | Atmospheric | Fallback |
|-----------|---------|-------------|----------|
| 10 integers | ~100ms | ~200ms | <1ms |
| 100 integers | ~150ms | ~300ms | <1ms |
| 32 bytes | ~100ms | ~200ms | <1ms |

## 🔍 Example Output

```json
{
  "success": true,
  "operation": "generate_integers",
  "numbers": [42, 17, 89, 3, 56],
  "count": 5,
  "min": 1,
  "max": 100,
  "unique": false,
  "source_used": "quantum"
}
```

## 🚨 Error Handling

All operations return structured errors:

```json
{
  "error": "Failed to generate random integers from all sources",
  "note": "All physical sources failed. Check API keys and connectivity."
}
```

## 🏗️ Architecture

```
_random/
├── __init__.py         # Spec loader
├── api.py              # Router
├── core.py             # Operation handlers
├── validators.py       # Input validation
├── sources.py          # Physical sources (RANDOM.ORG, Cisco QRNG)
└── README.md           # This file
```

## 📚 References

- RANDOM.ORG: https://www.random.org/
- Cisco QRNG: https://developer.cisco.com/
- Fisher-Yates Shuffle: https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle
