import os
import socket
import time

# rvidia-cli: Shared Computing CLI Tool

import argparse
import os
from ui import show_header, mode_selection, show_room_table
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

def main():
    show_header()
    parser = argparse.ArgumentParser(description="rvidia-cli: Shared Computing CLI Tool")
    parser.add_argument('--mode', choices=['local', 'cross-network'], default=None, help='Choose mode: local or cross-network')
    args = parser.parse_args()

    # Mode selection UI
    mode = args.mode
    if not mode:
        mode = mode_selection()
        mode = 'local' if mode == '1' else 'cross-network'

    console = Console()
    if mode == 'cross-network':
        console.print('[bold yellow]Cross network mode coming soon![/bold yellow]')
        return

    console.print('[bold green]Local mode selected.[/bold green]')
    username = Prompt.ask('Enter your username')
    room_file = 'local_room.txt'
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    user_entry = f'{username} ({ip})'

    # Register user in room
    with open(room_file, 'a+') as f:
        f.seek(0)
        users = [line.strip() for line in f.readlines()]
        if user_entry not in users:
            f.write(user_entry + '\n')
            users.append(user_entry)

    # Assign admin (first user in room)
    admin = users[0] if users else user_entry
    is_admin = (user_entry == admin)

    # Display room members and admin as table
    show_room_table(users, admin)

    # Persistent command loop
    while True:
        console.print(Panel("Enter a command: [bold cyan]select[/bold cyan], [bold cyan]generate[/bold cyan], [bold cyan]list[/bold cyan], [bold cyan]exit[/bold cyan]", expand=False))
        cmd = Prompt.ask("Command", choices=["select", "generate", "list", "exit"], default="list")

        if cmd == "exit":
            console.print("[bold red]Exiting RVIDIA CLI.[/bold red]")
            break
        elif cmd == "list":
            # List all files/folders in rvidia-data
            def list_tree(path, prefix=""):
                for item in os.listdir(path):
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        console.print(f"{prefix}[bold blue]{item}/[/bold blue]")
                        list_tree(full_path, prefix + "  ")
                    else:
                        console.print(f"{prefix}{item}")
            console.print(Panel("[bold]rvidia-data contents:[/bold]", expand=False))
            list_tree("rvidia-data")
        elif cmd == "select":
            # Arrow-key style selection (simulate with numbers)
            # List all files/folders in rvidia-data
            def gather_items(path, prefix=""):
                items = []
                for item in os.listdir(path):
                    full_path = os.path.join(path, item)
                    display_name = f"{prefix}{item}/" if os.path.isdir(full_path) else f"{prefix}{item}"
                    items.append((display_name, full_path, os.path.isdir(full_path)))
                return items
            def gather_all_files(selected_paths):
                all_files = []
                for path in selected_paths:
                    if os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            for f in files:
                                rel_path = os.path.relpath(os.path.join(root, f), "rvidia-data")
                                all_files.append(rel_path)
                    else:
                        rel_path = os.path.relpath(path, "rvidia-data")
                        all_files.append(rel_path)
                return all_files
            items = gather_items("rvidia-data")
            console.print(Panel("[bold]Select files/folders to include (enter numbers separated by comma):[/bold]", expand=False))
            for idx, (name, _, _) in enumerate(items, 1):
                console.print(f"[{idx}] {name}")
            sel = Prompt.ask("Enter selection", default="1")
            sel_idxs = [int(i.strip()) for i in sel.split(",") if i.strip().isdigit() and 1 <= int(i.strip()) <= len(items)]
            selected_paths = [items[i-1][1] for i in sel_idxs]
            selected_files = gather_all_files(selected_paths)
            # Store selection for later
            global _selected_files
            _selected_files = selected_files
            console.print(Panel(f"Selected: {', '.join(selected_files)}", expand=False))
        elif cmd == "generate":
            # Generate Dockerfile using selected files
            dockerfile_path = os.path.join('rvidia-data', 'Dockerfile')
            selected_files = globals().get('_selected_files', [])
            if not selected_files:
                console.print("[bold red]No files selected. Use 'select' first.[/bold red]")
                continue
            with open(dockerfile_path, 'w') as df:
                df.write('FROM python:3.9-slim\n')
                df.write('WORKDIR /app\n')
                df.write('COPY app.py ./\n')
                for rel_path in selected_files:
                    df.write(f'COPY {rel_path} ./{rel_path}\n')
                df.write('RUN pip install -r requirements.txt\n')
                df.write('CMD ["python", "app.py"]\n')
            console.print(f'[bold green]Dockerfile generated at {dockerfile_path}[/bold green]')

        # Display room members and admin
        console.print('[bold blue]Users in the room:[/bold blue]')
        for user in users:
            if user == admin:
                console.print(f'- {user} [bold red](admin)[/bold red]')
            else:
                console.print(f'- {user}')

        if is_admin:
            console.print('[bold green]You are the admin.[/bold green]')

if __name__ == '__main__':
    main()
