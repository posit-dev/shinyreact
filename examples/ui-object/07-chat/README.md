# Example 7 — Streaming chat with chatlas (shinyreact)

A chat UI backed by OpenAI's `gpt-4o-mini` (via [chatlas](https://github.com/posit-dev/chatlas)). Shows how to stream tokens from the server to the client through the message-passing primitive — no special chat protocol, just `send_message` calls dispatched by message type.

> **Note:** Uses `shinyreact`. The streaming pattern (server pushes message events, client appends them) ports directly to the `client-ui`-first model — `useShinyMessageHandler` works the same.

## Setup

You need an OpenAI API key:

```bash
echo 'OPENAI_API_KEY=sk-...' > examples/7-chat/.env
```

The `.env` file is loaded automatically when the app starts.

## What it shows

- A single `ChatApp` component subscribes to two message types: streamed tokens and a "done" signal.
- A `useShinyInput("chat_input")` ships the user's prompt to the server.
- Server-side: `chatlas.ChatOpenAI(...)` creates a model handle. Each user message triggers `chat.stream_async(...)`, and every chunk is pushed via `shinyreact.send_message(session, "chat_stream", ...)`.

## Layout

```
examples/7-chat/
├── app.py        # Server: chat input handler + streaming loop
├── chat.js       # JS bundle: ChatApp component
├── styles.css
└── .env          # YOU CREATE: OPENAI_API_KEY=...
```

## Run it

```bash
uv run shiny run examples/7-chat/app.py
```
