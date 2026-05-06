# Example 4 — Custom messages (shinyreact)

Demonstrates the **server → client push** path: the server sends one-off messages (not output values) that the client consumes through a custom message handler.

> **Note:** Uses `shinyreact`. The same `useShinyMessageHandler` API is available in the SPA-first model — only the UI-rendering surface differs.

## What it shows

- A `ToastCard` that subscribes to a custom message type via `useShinyMessageHandler("toast", handler)`.
- A server-side `reactive.effect` that fires every few seconds, picks a random log entry, and calls `shinyreact.send_message(session, "toast", payload)` to push it to the client.
- Toasts stack and auto-dismiss client-side; the server has no idea they exist after sending.

This is the contract for any pattern where the server needs to *notify* the client (alerts, progress milestones, streaming events) without that data showing up in a reactive output.

## Layout

```
examples/4-messages/
├── app.py        # Server: timed reactive.effect calling send_message
├── messages.js   # JS bundle: AppLayout / ToastCard
└── styles.css
```

## Run it

```bash
uv run shiny run examples/4-messages/app.py
```
