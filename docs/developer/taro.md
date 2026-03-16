# Plugin: taro

## Purpose

AI-powered Tarot card reading with 3-card spreads (Past / Present / Future), LLM-generated interpretations via Claude, follow-up questions, contextual situation readings, daily session limits per subscription plan, and token-based consumption tracking. Conversation history is cleared on session expiry for privacy.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "taro", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Run migration: `flask db upgrade`
4. (Optional) Seed card data: `./plugins/taro/bin/populate-db.sh`

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `llm_api_endpoint` | string | Anthropic URL | Claude API endpoint |
| `llm_api_key` | string | `""` | Anthropic API key |
| `llm_model` | string | `"claude-haiku-4-5-20251001"` | Claude model name |
| `llm_temperature` | float | `0.8` | LLM temperature |
| `llm_max_tokens` | int | `1200` | Max response tokens |
| `session_duration_minutes` | int | `30` | Session lifetime |
| `session_expiry_warning_minutes` | int | `3` | Warning threshold before expiry |
| `base_session_tokens` | int | `10` | Platform tokens per session |
| `follow_up_base_tokens` | int | `5` | Platform tokens per follow-up |
| `card_interpretation_template` | string | — | Jinja2 prompt template |
| `situation_reading_template` | string | — | Jinja2 prompt template |
| `follow_up_question_template` | string | — | Jinja2 prompt template |
| `initial_greeting` | string | — | Initial oracle greeting |
| `system_prompt` | string | — | LLM system prompt |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/taro/session` | Bearer | Create session (3-card spread) |
| POST | `/api/v1/taro/session/<id>/follow-up` | Bearer | Ask follow-up question |
| POST | `/api/v1/taro/session/<id>/card-explanation` | Bearer | Get card detail interpretation |
| POST | `/api/v1/taro/session/<id>/situation` | Bearer | Get reading for user's situation |
| GET | `/api/v1/taro/history` | Bearer | Paginated session history |
| GET | `/api/v1/taro/limits` | Bearer | Daily limits and usage |
| GET | `/api/v1/taro/assets/arcana/<file>` | Public | Serve card SVG assets |
| GET | `/api/v1/taro/admin/users/<user_id>/sessions` | Admin | View user's sessions |
| POST | `/api/v1/taro/admin/users/<user_id>/reset-sessions` | Admin | Reset user's daily quota |
| GET | `/api/v1/taro/admin/prompts` | Admin | Get all prompt templates |
| GET | `/api/v1/taro/admin/prompts/defaults` | Admin | Get default prompts |
| PUT | `/api/v1/taro/admin/prompts/defaults` | Admin | Update default prompts |

## Events Emitted

| Domain event | When |
|-------------|------|
| `TaroSessionRequestedEvent` | Session creation requested |
| `TaroSessionCreatedEvent` | Session created with card spread |
| `TaroFollowUpRequestedEvent` | Follow-up question submitted |
| `TaroFollowUpGeneratedEvent` | Follow-up answer generated |
| `TaroInterpretationGeneratedEvent` | Card interpretation generated |
| `TaroSessionExpiredEvent` | Session expired |
| `TaroSessionClosedEvent` | Session closed by user |

## Events Consumed

None.

## Architecture

```
plugins/taro/
├── __init__.py
├── generate_cards.py          # One-time card data generator
├── src/
│   ├── routes.py
│   ├── handlers.py            # Domain event handlers
│   ├── events.py              # Taro domain events
│   ├── enums.py
│   ├── models/                # TaroSession, TaroCard, TaroReading
│   ├── repositories/
│   └── services/              # TaroService, LLMInterpreter
├── migrations/
├── locale/
│   └── en.json
└── tests/
```

## Extending

Prompt templates are editable at runtime via the admin API (`PUT /api/v1/taro/admin/prompts/defaults`) without restarting the server. To add new card spread types (5-card, Celtic Cross), extend `TaroService.create_session()` and add a new spread mode enum.
