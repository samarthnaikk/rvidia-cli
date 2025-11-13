from textual.app import App, ComposeResult
from textual.widgets import Input, Static
from textual.containers import Vertical

class ChatApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }
    #chat {
        height: 100%;
        width: 100%;
        border: solid green;
        padding: 1 2;
        overflow: auto;
    }
    #inputbox {
        dock: bottom;
        height: 3;
        border: solid blue;
    }
    """

    def compose(self) -> ComposeResult:
        self.buffer = ""   # <- internal safe text buffer

        yield Static("", id="chat")
        yield Input(placeholder="Type here...", id="inputbox")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Append new line to buffer
        self.buffer += f"> {event.value}\n"

        chat = self.query_one("#chat", Static)
        chat.update(self.buffer)   # update display safely

        event.input.value = ""  # clear input


if __name__ == "__main__":
    ChatApp().run()
