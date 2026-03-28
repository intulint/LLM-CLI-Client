# llama.cpp Server API Endpoints

## Overview

This document lists all HTTP API endpoints exposed by the llama-server component of llama.cpp.

---

## Public Endpoints (No API Key Required)

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint |
| GET | `/v1/health` | Health check endpoint (v1 format) |

### Models
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models` | Get list of loaded models |
| GET | `/v1/models` | Get list of loaded models (v1 format) |
| GET | `/api/tags` | Ollama-specific endpoint for model tags |

### Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics` | Prometheus-style metrics endpoint (proxies to current model or child server) |

---

## Protected Endpoints (Require API Key)

### Completion
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/completion` | Legacy completion endpoint |
| POST | `/completions` | Completion endpoint |
| POST | `/v1/completions` | Completion endpoint (v1 format) |

### Chat Completions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/completions` | Chat completion endpoint |
| POST | `/v1/chat/completions` | Chat completion endpoint (v1 format) |
| POST | `/api/chat` | Ollama-specific chat endpoint |

### Responses (OpenAI-like)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/responses` | Responses endpoint (v1 format) |
| POST | `/responses` | Responses endpoint |

### Anthropic Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/messages` | Anthropic messages API |
| POST | `/v1/messages/count_tokens` | Anthropic token counting |

### Advanced Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/infill` | Text infilling |
| POST | `/embedding` | Legacy embedding endpoint |
| POST | `/embeddings` | Embedding endpoint |
| POST | `/v1/embeddings` | Embedding endpoint (v1 format) |
| POST | `/rerank` | Reranking endpoint |
| POST | `/reranking` | Reranking endpoint (variant) |
| POST | `/v1/rerank` | Reranking endpoint (v1 format) |
| POST | `/v1/reranking` | Reranking endpoint (v1 format variant) |
| POST | `/tokenize` | Tokenize text to IDs |
| POST | `/detokenize` | Detokenize IDs to text |
| POST | `/apply-template` | Apply custom template |

---

## LoRA Adapters Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/lora-adapters` | List loaded LoRA adapters |
| POST | `/lora-adapters` | Load/swap LoRA adapter |

---

## Slots Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/slots` | List loaded slots |
| POST | `/slots/:id_slot` | Save/load slot by ID |

---

## CORS Proxy (Experimental)

> ⚠️ **Warning**: CORS proxy is EXPERIMENTAL and should only be used with trusted environments.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cors-proxy` | CORS proxy GET handler |
| POST | `/cors-proxy` | CORS proxy POST handler |

---

## Router Server Endpoints (Multiple Model Support)

When running in router mode (no model loaded in memory), the following endpoints are available:

### Router-Specific
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/props` | Get server properties |
| GET | `/api/show` | Show API information |
| POST | `/models/load` | Load a model |
| POST | `/models/unload` | Unload a model |

### Proxy Endpoints (Forward to Child Servers)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics` | Proxy to child server metrics (router mode only) |
| POST | `/props` | Proxy to child server properties |
| GET | `/api/show` | Proxy to child server API info |
| POST | `/completions` | Proxy to child server completions |
| POST | `/v1/completions` | Proxy to child server completions (v1) |
| POST | `/chat/completions` | Proxy to child server chat completions |
| POST | `/v1/chat/completions` | Proxy to child server chat completions (v1) |
| POST | `/api/chat` | Proxy to child server chat |
| POST | `/v1/responses` | Proxy to child server responses (v1) |
| POST | `/responses` | Proxy to child server responses |
| POST | `/v1/messages` | Proxy to child server messages |
| POST | `/v1/messages/count_tokens` | Proxy to child server token count |
| POST | `/infill` | Proxy to child server infill |
| POST | `/embedding` | Proxy to child server embedding |
| POST | `/embeddings` | Proxy to child server embeddings |
| POST | `/v1/embeddings` | Proxy to child server embeddings (v1) |
| POST | `/rerank` | Proxy to child server rerank |
| POST | `/reranking` | Proxy to child server rerank |
| POST | `/v1/rerank` | Proxy to child server rerank (v1) |
| POST | `/v1/reranking` | Proxy to child server rerank (v1 variant) |
| POST | `/tokenize` | Proxy to child server tokenize |
| POST | `/detokenize` | Proxy to child server detokenize |
| POST | `/apply-template` | Proxy to child server apply-template |
| GET | `/lora-adapters` | Proxy to child server LoRA adapters |
| POST | `/lora-adapters` | Proxy to child server LoRA adapters |
| GET | `/slots` | Proxy to child server slots |
| POST | `/slots/:id_slot` | Proxy to child server slots |

---

## Error Response Format

All error responses follow this JSON format:

```json
{
  "error": {
    "message": "Error message here",
    "type": "error_type",
    "code": 400
  }
}
```

### Error Types
- `not_found_error` - 404
- `authentication_error` - 401
- `unavailable_error` - 503
- `invalid_request` - 400
- `server` - 500

---

## API Authentication

When API keys are configured, requests must include:
- Authorization header: `Bearer <api_key>`
- Or X-Api-Key header: `<api_key>`

---

## Notes

1. **Router mode**: When `model.path` is empty, the server runs in router mode, managing multiple child servers
2. **CORS proxy**: Experimental feature, only enabled when `webui_mcp_proxy` is set
3. **Streaming**: Some endpoints support streaming responses via SSE (Server-Sent Events)
4. **Web UI**: When `webui` is enabled, static files are served from `/` or configured path

---

## Sources

This API documentation was extracted from the following source files in the llama.cpp repository:

| Source File | Description |
|-------------|-------------|
| `./tools/server/server.cpp` | Main server file with registered HTTP endpoints |
| `./tools/server/server-http.h` | HTTP server header with request/response structures |
| `./tools/server/server-http.cpp` | HTTP server implementation with middleware and routes |
| `./tools/server/server-models.h` | Router server models header |
| `./tools/server/server-models.cpp` | Router server models implementation |
| `./tools/server/server-context.h` | Server context header |
| `./tools/server/server-context.cpp` | Server context implementation |
| `./tools/server/server-task.h` | Task queue header |
| `./tools/server/server-task.cpp` | Task queue implementation |

**Repository**: https://github.com/ggml-org/llama.cpp
**Directory**: `./tools/server/`

**Last updated**: 2026-03-19
**Extraction method**: Manual analysis of HTTP endpoint registrations in server.cpp
