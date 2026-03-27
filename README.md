# LLM CLI Client (Educational Project)

LLM CLI Client is an educational project created to deeply understand the principles of interacting with Large Language Model (LLM) APIs. The development goal was to independently learn the mechanisms of token streaming, Function Calling, and Reasoning Content handling in the OpenAI-like API format, without using ready-made SDKs for neural networks.

## Project Goal

This project was written to independently learn how exactly calls to neural networks work at the HTTP request level. The main task is to implement a chat interface functionality, relying on basic protocols and standard libraries, to understand the internal logic of LLMs.

## Technical Details

- **Language:** Python 3.8+
- **Dependencies:**
  - `requests` (for HTTP requests)
  - `json` (Python standard library)
- **Architecture:** Pure Python without using third-party libraries directly related to neural networks (e.g., langchain, llama-index, or official OpenAI SDKs were not used).
- **API:** Compatibility with OpenAI-like API (uses the `/chat/completions` endpoint).

## Functional Features

- **Streaming:** Support for `stream=True` to output tokens as they are generated.
- **Reasoning Content:** Processing and output of hidden "thoughts" from the model, if the server supports the `reasoning_content` field.
- **Function Calling (Tools):** Implementation of external function calls within the conversation (using the `fetch` function as an example for retrieving web pages).
- **CLI Interface:** A managing console with commands to control chat history.

## CLI Commands

- `/q` — Exit the program
- `/n` — New chat (clear history)
- `/d` — Delete the last message from history
- `/r` — Regenerate the last assistant response

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

Ensure that a local neural network server (e.g., Ollama, LM Studio) is running and accessible at `http://localhost:8080` (or change the URL in the code).

## Code Architecture

- `chat_form`: A list of messages storing the conversation history.
- `generate_api_request`: Main logic for sending requests to the API, including streaming and error handling.
- `tool_message`: Processing tool call results and adding them to the context.
- `fetch_tool`: Function to implement the `fetch` tool.

## Note

This project is educational. It demonstrates the basic principle of working with LLM APIs "out of the box", but is not intended for production use. It lacks advanced security features, asynchronous operations, and complex modular architecture.

## License

This project is distributed under the [The Unlicense](https://unlicense.org/) license.