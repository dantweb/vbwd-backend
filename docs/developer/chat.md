# Plugin: chat

## Purpose

LLM-powered AI chat with token-gated access. Users spend platform tokens per message. Configurable LLM backend (default: DeepSeek). Tracks conversation history per session, enforces message length and history depth limits, and supports token-cost estimation before sending.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "chat", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. No Alembic migration required (uses core token tables).

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `llm_api_endpoint` | string | `"https://api.deepseek.com"` | LLM provider API base URL |
| `llm_api_key` | string | `""` | API key for LLM provider |
| `llm_model` | string | `"deepseek-reasoner"` | Model name to use |
| `counting_mode` | string | `"words"` | Token counting strategy |
| `words_per_token` | int | `10` | Words-per-token conversion ratio |
| `mb_per_token` | float | `0.001` | MB-per-token conversion ratio |
| `tokens_per_token` | int | `100` | Platform tokens consumed per LLM token |
| `system_prompt` | string | `""` | System message prepended to every request |
| `max_message_length` | int | `4000` | Max chars per user message |
| `max_history_messages` | int | `20` | Max prior messages sent to LLM |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/plugins/chat/send` | Bearer | Send a message (deducts tokens) |
| GET | `/api/v1/plugins/chat/config` | Bearer | Get public chat config |
| POST | `/api/v1/plugins/chat/estimate` | Bearer | Estimate token cost before sending |

## Events Emitted

None.

## Events Consumed

| Event | Handler | Effect |
|-------|---------|--------|
| `subscription.activated` | Internal | Reset per-period chat allowances |

## Architecture

```
plugins/chat/
├── __init__.py          # ChatPlugin class
├── src/
│   ├── routes.py        # Blueprint: /api/v1/plugins/chat/
│   ├── chat_service.py  # Message processing + token deduction
│   ├── llm_adapter.py   # LLM provider HTTP adapter
│   └── token_counting.py # Word/byte/token conversion
├── locale/
│   ├── en.json
│   └── de.json
└── tests/
```

## Extending

To add a new LLM provider: implement `llm_adapter.py` adapter interface and update `config.json` with the new endpoint. The `ChatService` is provider-agnostic via `LLMAdapter` protocol.
