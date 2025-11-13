from textual.app import App, ComposeResult
from textual.widgets import Input, Static
from textual.screen import Screen
from textual import events
from textual.containers import Vertical
from textual.reactive import reactive


# ------------------------------------------------------------
#  MENU SCREEN (arrow-key controlled)
# ------------------------------------------------------------
class MenuScreen(Screen):

    CSS = """
    Screen {
        align: center middle;
    }
    #option {
        width: 40;
        padding: 1;
        align: center middle;
    }
    """

    options = ["Local Network", "Open Internet (coming soon)"]
    selected = reactive(0)

    def compose(self) -> ComposeResult:
        self.menu_box = Static(id="option")
        yield self.menu_box

    def on_mount(self) -> None:
        self.update_menu()

    def update_menu(self):
        text = ""
        for i, opt in enumerate(self.options):
            if i == self.selected:
                text += f"[bold blue]> {opt}[/bold blue]\n"
            else:
                text += f"  {opt}\n"
        self.menu_box.update(text)

    async def on_key(self, event: events.Key):
        if event.key == "up":
            self.selected = (self.selected - 1) % len(self.options)
            self.update_menu()

        elif event.key == "down":
            self.selected = (self.selected + 1) % len(self.options)
            self.update_menu()

        elif event.key == "enter":
            choice = self.options[self.selected]

            if "Local" in choice:
                await self.app.push_screen(ConnectingScreen())

            elif "Open Internet" in choice:
                await self.app.exit("Open Internet mode coming soon!")


# ------------------------------------------------------------
#  CONNECTING SCREEN
# ------------------------------------------------------------
class ConnectingScreen(Screen):

    CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        self.label = Static("[yellow]Connecting to local network...[/yellow]")
        yield self.label

    def on_mount(self) -> None:
        # after 1 second, continue to chat
        self.set_timer(1, lambda: self.app.push_screen(ChatScreen()))


# ------------------------------------------------------------
#  CHAT SCREEN
# ------------------------------------------------------------
class ChatScreen(Screen):

    buffer = reactive("")

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
        yield Static("", id="chat")
        yield Input(placeholder="Type here...", id="inputbox")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.buffer += f"> {event.value}\n"
        chat = self.query_one("#chat", Static)
        chat.update(self.buffer)
        event.input.value = ""


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
class RvidiaApp(App):

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())


if __name__ == "__main__":
    RvidiaApp().run()
