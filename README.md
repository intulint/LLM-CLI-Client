# LLM CLI Client (Educational Project)

LLM CLI Client is an educational project created to deeply understand the principles of interacting with Large Language Model (LLM) APIs. The development goal was to independently learn the mechanisms of token streaming, Function Calling, and Reasoning Content handling in the OpenAI-like API format, without using ready-made SDKs for LLM.

## Project Goal

This project was written to independently learn how exactly calls to LLM work at the HTTP request level. The main task is to implement a chat interface functionality, relying on basic protocols and standard libraries, to understand the internal logic of LLMs.

## Technical Details

- **Language:** Python 3.8+
- **Dependencies:**
  - `requests` (for HTTP requests)
  - `json` (Python standard library)
- **Architecture:** Pure Python without using third-party libraries directly related to neural networks (e.g., langchain, llama-index, or official OpenAI SDKs were not used).
- **API:** Compatibility with OpenAI-like API (uses the `/v1/chat/completions` endpoint).

## Functional Features

- **Streaming:** Support for `stream=True` to output tokens as they are generated in real-time.
- **Reasoning Content:** Processing and output of hidden model reasoning (`reasoning_content`) with visual markers (`=========Thinking=========` / `=========Thinking=========`).
- **Function Calling (Tools):** Implementation of external function calls within the conversation. The example tool `fetch` downloads URL content into context.
- **CLI Interface:** Console commands for managing chat history and session control.
- **Temperature & Sampling Control:** Configurable `temperature` (0.6), `top_p` (0.95), `top_k` (20) parameters.
- **Max Tokens:** Configurable `max_tokens` limit (default 4000).
- **HTTP Timeout:** Request timeout protection (30 seconds for tool fetch).

## CLI Commands

| Command | Description |
|---------|-------------|
| `/h` | Show help (list of commands) |
| `/q` | Exit the program |
| `/n` | New chat session (clears conversation history) |
| `/d` | Delete the last user message and assistant response from history |
| `/r` | Regenerate the last assistant response |
| `/p` | Print current chat context |
| `/s` | Toggle streaming mode (on/off) |
| `/t` | Toggle reasoning content display (on/off) |

## Installation

The project depends on the `requests` library.

```bash
pip install requests
```

## Usage

Run the script from the terminal:

```bash
python main.py
```

Ensure that a local LLM server (e.g., llama.cpp, Ollama, LM Studio) is running and accessible at `http://localhost:8080` (or change the URL in the code).

## Code Architecture

- **chat_form:** Message history list storing system prompt, assistant first message, and conversation turns.
- **generate_api_request:** Core request generator supporting both streaming and non-streaming modes with reasoning_content and tool_calls handling.
- **tool_message:** Processes tool call results and recursively generates follow-up responses.
- **fetch_tool:** Tool implementation for downloading URL content with error handling.
- **model_api_request:** Fetches available models from the server via `/models` endpoint.
- **message_print:** Helper function for displaying chat messages.
- **main:** Main loop handling user input and CLI commands.

## Configuration

- **Stream:** Toggle streaming mode with `/s` command (default: `True`).
- **Print_thinking:** Toggle reasoning content display with `/t` command (default: `True`).
- **server_url:** Configure server address (default: `http://localhost:8080`).
- **Authorization:** API authorization header (default: `Bearer no-key`).
- **tools:** Tool definitions for function calling (default: `fetch` tool).

## Notes

- The client expects an OpenAI-compatible API endpoint at `/v1/chat/completions`.
- Tool calling uses the standard OpenAI `tool_calls` format with function definitions.
- Reasoning content is displayed inline with visual separators when enabled (`Print_thinking = True`).
- The fetch tool returns plain text content or error messages if the request fails.
- This project is educational and demonstrates core LLM API interaction principles without relying on high-level SDKs.

## License

This project is distributed under the [The Unlicense](https://unlicense.org/) license.
