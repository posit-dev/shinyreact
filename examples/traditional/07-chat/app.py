from pathlib import Path

import dotenv
import shinyjsonold as shinyjson
from chatlas import ChatOpenAI, content_image_url
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

# Load .env file in this directory for OPENAI_API_KEY
app_dir = Path(__file__).parent
env_file = app_dir / ".env"
dotenv.load_dotenv(env_file)

# Initialize chat with OpenAI GPT-4o-mini by default
chat = ChatOpenAI(
    model="gpt-4o-mini",
    system_prompt=(
        "You are a helpful AI assistant. Be concise but informative in your responses."
    ),
)

_chat_dep = HTMLDependency(
    name="chat-example",
    version=str(int((app_dir / "chat.js").stat().st_mtime)),
    source={"subdir": str(app_dir)},
    script={"src": "chat.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui_output("main", extra_deps=[_chat_dep])


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------
def chat_app(input_id: str, stream_handler: str) -> shinyjson.Node:
    return shinyjson.Node(
        type="ChatApp",
        props={"input_id": input_id, "stream_handler": stream_handler},
    )


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def main():
        return chat_app("chat_input", "chat_stream")

    @reactive.effect
    @reactive.event(input.chat_input)
    async def handle_chat_input():
        message_data = input.chat_input()
        if not message_data or not message_data["text"]:
            return

        try:
            # Parse structured input (dict with text and attachments)
            if isinstance(message_data, str):
                user_text = message_data.strip()
                attachments = []
            elif isinstance(message_data, dict):
                user_text = message_data.get("text", "").strip()
                attachments = message_data.get("attachments", [])
            else:
                user_text = ""
                attachments = []

            # Build chat arguments
            chat_args = []

            if user_text:
                chat_args.append(user_text)

            # Add image attachments as content_image_url objects
            if attachments:
                for attachment in attachments:
                    if attachment.get("content") and attachment.get("type"):
                        data_url = (
                            f"data:{attachment['type']};base64,{attachment['content']}"
                        )
                        chat_args.append(content_image_url(data_url))

            if not chat_args:
                chat_args = ["Please provide some content to analyze."]

            # Create async streaming with all arguments
            stream = await chat.stream_async(*chat_args)
            async for chunk in stream:
                await send_chunk(chunk)

            await send_chunk("", done=True)

        except Exception as e:
            print(f"Error getting AI response: {e}")
            await send_chunk(
                "Sorry, I encountered an error. Please try again.",
                done=True,
            )

    async def send_chunk(chunk: str, done: bool = False):
        await shinyjson.post_message(
            session, "chat_stream", {"chunk": chunk, "done": done}
        )


app = App(app_ui, server)
