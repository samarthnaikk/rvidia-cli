#!/usr/bin/env python3
"""
rvidia-cli: Option A - Simple LAN chat (single-file)

Features:
- Textual UI (menu -> connecting -> chat)
- UDP broadcast on port 50505
- JOIN heartbeat messages and MSG messages
- Admin detection: user with smallest join_time is Admin (A)
- Everyone sees messages and the live user list
"""

import asyncio
import json
import socket
import time
import argparse
from typing import Dict

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Static
from textual.reactive import reactive
from textual import events
from textual.containers import Vertical

# Networking constants
PORT = 50505
BROADCAST_ADDR = "<broadcast>"
HEARTBEAT_INTERVAL = 3.0  # seconds


# --------------------------
# UDP Protocol to push messages into an asyncio.Queue
# --------------------------
class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr):
        try:
            msg = json.loads(data.decode("utf-8"))
        except Exception:
            return
        # Put message into queue for the app to handle
        asyncio.get_event_loop().create_task(self.queue.put((msg, addr)))

    def error_received(self, exc):
        # ignore for now
        pass


# --------------------------
# Menu screen (arrow keys + enter)
# --------------------------
class MenuScreen(Screen):
    options = ["Local Network", "Open Internet (coming soon)"]
    selected = reactive(0)

    def compose(self) -> ComposeResult:
        self.box = Static("", id="menu_box")
        yield self.box

    def on_mount(self) -> None:
        self.update_menu()

    def update_menu(self):
        text = "\n\n[bold cyan]RVIDIA CLI[/bold cyan]\n\n"
        for i, opt in enumerate(self.options):
            if i == self.selected:
                text += f"[bold blue]> {opt}[/bold blue]\n"
            else:
                text += f"  {opt}\n"
        self.box.update(text)

    async def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            self.selected = (self.selected - 1) % len(self.options)
            self.update_menu()
        elif event.key == "down":
            self.selected = (self.selected + 1) % len(self.options)
            self.update_menu()
        elif event.key == "enter":
            if "Local" in self.options[self.selected]:
                await self.app.push_screen(ConnectingScreen())
            else:
                await self.app.exit("Open Internet coming soon!")


# --------------------------
# Connecting screen
# --------------------------
class ConnectingScreen(Screen):
    def compose(self) -> ComposeResult:
        self.label = Static("[yellow]Connecting to local network...[/yellow]\n")
        yield self.label

    def on_mount(self) -> None:
        # after a short delay, go to chat screen
        self.set_timer(0.8, lambda: self.app.push_screen(ChatScreen()))


# --------------------------
# Chat screen with networking
# --------------------------
class ChatScreen(Screen):
    # internal chat buffer
    buffer = reactive("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # networking queue where UDPProtocol will push received messages
        self.net_queue: asyncio.Queue = asyncio.Queue()
        self.transport = None
        self.protocol = None

        # users dict keyed by id (username|ip)
        self.users: Dict[str, Dict] = {}
        self.admin_id: str | None = None

        # set on entering chat
        self.username = None
        self.my_id = None
        self.join_time = None

        # keep track of tasks to cancel on unmount
        self._tasks = []

    def compose(self) -> ComposeResult:
        # top: users list, middle: chat box, bottom: input
        self.users_widget = Static("", id="users")
        self.chat_widget = Static("", id="chat")
        self.input_widget = Input(placeholder="Type here...", id="inputbox")
        yield Vertical(self.users_widget, self.chat_widget)
        yield self.input_widget

    async def on_mount(self) -> None:
        # get username (ask user via blocking prompt)
        # Textual does not provide a built-in blocking console prompt; use simple asyncio-friendly input
        # But to keep UI smooth we use an argument prompt via terminal input before app run.
        # The app sets username at creation-time (passed via App attribute).
        app = self.app
        self.username = getattr(app, "username", None) or "anon"
        # determine local ip
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "0.0.0.0"
        self.join_time = time.time()
        self.my_id = f"{self.username}|{local_ip}"

        # setup UDP socket with broadcast enabled and bind to PORT
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Some systems require SO_REUSEPORT as well; ignore if unavailable
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception:
            pass
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", PORT))

        self.protocol = UDPProtocol(self.net_queue)
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.protocol, sock=sock
        )
        self.transport = transport

        # Immediately send a JOIN so others know we're here
        await self.send_join()

        # Start tasks:
        # 1) process incoming network messages
        t1 = asyncio.create_task(self._network_reader())
        # 2) periodic heartbeat/join
        t2 = asyncio.create_task(self._heartbeat_loop())
        self._tasks.extend([t1, t2])

        # initial UI refresh
        self._refresh_users()
        self._refresh_chat()

    async def _heartbeat_loop(self):
        # send JOIN/heartbeat periodically so others see us alive
        while True:
            try:
                await self.send_join()
                await asyncio.sleep(HEARTBEAT_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def send_join(self):
        # Broadcast a join message with join_time
        msg = {
            "type": "join",
            "username": self.username,
            "ip": socket.gethostbyname(socket.gethostname()),
            "join_time": self.join_time,
            "timestamp": time.time(),
        }
        data = json.dumps(msg).encode("utf-8")
        # Send to broadcast address
        try:
            self.transport.sendto(data, (BROADCAST_ADDR, PORT))
        except Exception:
            # fallback: send to 255.255.255.255
            self.transport.sendto(data, ("255.255.255.255", PORT))

    async def send_msg(self, text: str):
        msg = {
            "type": "msg",
            "username": self.username,
            "ip": socket.gethostbyname(socket.gethostname()),
            "text": text,
            "timestamp": time.time(),
        }
        data = json.dumps(msg).encode("utf-8")
        try:
            self.transport.sendto(data, (BROADCAST_ADDR, PORT))
        except Exception:
            self.transport.sendto(data, ("255.255.255.255", PORT))

    async def _network_reader(self):
        # process messages from UDPProtocol via queue
        while True:
            try:
                msg, addr = await self.net_queue.get()
            except asyncio.CancelledError:
                break
            try:
                mtype = msg.get("type")
                username = msg.get("username", "anon")
                ip = msg.get("ip", addr[0] if addr else "0.0.0.0")
                id_key = f"{username}|{ip}"

                if mtype == "join":
                    join_time = float(msg.get("join_time", time.time()))
                    # update users dict
                    self.users[id_key] = {
                        "username": username,
                        "ip": ip,
                        "join_time": join_time,
                        "last_seen": time.time(),
                    }
                    # recompute admin
                    self._recompute_admin()
                    # refresh users list UI
                    self._refresh_users()

                    # Optionally, don't add a system message for joins - but we can:
                    self._append_system(f"{username} joined")

                elif mtype == "msg":
                    text = msg.get("text", "")
                    # append to chat buffer and update UI
                    self._append_message(username, text)

                # other message types can be added later
            except Exception:
                continue

    def _recompute_admin(self):
        # Find user with smallest join_time
        if not self.users:
            self.admin_id = None
            return
        min_id = min(self.users.items(), key=lambda kv: kv[1].get("join_time", float("inf")))[0]
        self.admin_id = min_id

    def _refresh_users(self):
        # build users string; mark admin with (A) else (U)
        lines = ["[bold]Users on LAN:[/bold]"]
        # sort by join_time for stable ordering
        sorted_users = sorted(self.users.items(), key=lambda kv: kv[1].get("join_time", 0))
        for uid, info in sorted_users:
            uname = info.get("username")
            tag = "(A)" if uid == self.admin_id else "(U)"
            me = " <you>" if uid == self.my_id else ""
            lines.append(f"- {uname} {tag}{me}")
        # make sure local user is included even if no one else replied yet
        if self.my_id not in self.users:
            # add self
            tag = "(A)" if (self.admin_id == self.my_id) else "(U)"
            lines.append(f"- {self.username} {tag} <you>")
        self.users_widget.update("\n".join(lines))

    def _refresh_chat(self):
        self.chat_widget.update(self.buffer)

    def _append_system(self, text: str):
        self.buffer += f"[italic]{text}[/italic]\n"
        self._refresh_chat()

    def _append_message(self, username: str, text: str):
        # simple formatting
        self.buffer += f"{username}: {text}\n"
        self._refresh_chat()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            event.input.value = ""
            return
        # append locally
        self._append_message(self.username, text)
        # broadcast
        await self.send_msg(text)
        event.input.value = ""

    async def on_unmount(self) -> None:
        # cancel background tasks and close transport
        for t in self._tasks:
            t.cancel()
        try:
            if self.transport:
                self.transport.close()
        except Exception:
            pass


# --------------------------
# Main App
# --------------------------
class RvidiaApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    #menu_box {
        padding: 2;
    }
    #users {
        height: 6;
        width: 100%;
        border: round green;
        padding: 1;
    }
    #chat {
        height: 1fr;
        width: 100%;
        border: round white;
        padding: 1;
        overflow: auto;
    }
    #inputbox {
        dock: bottom;
        height: 3;
        border: round blue;
    }
    """

    def __init__(self, username: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.username = username or None

    async def on_mount(self) -> None:
        await self.push_screen(MenuScreen())

    # allow passing username via CLI before running textual loop
    # (we will set it from argparse in main below)


# --------------------------
# Entrypoint
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="rvidia-cli LAN chat")
    parser.add_argument("--username", "-u", help="Your username (optional)", default=None)
    args = parser.parse_args()

    app = RvidiaApp(username=args.username)
    app.run()


if __name__ == "__main__":
    main()
