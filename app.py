import os
import socket
import time

# rvidia-cli: Shared Computing CLI Tool

import argparse
from ui import show_header, mode_selection, show_room_table, select_data_files

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

    if mode == 'cross-network':
        from rich.console import Console
        Console().print('[bold yellow]Cross network mode coming soon![/bold yellow]')
        return
    else:
        from rich.prompt import Prompt
        from rich.console import Console
        console = Console()
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

        if is_admin:
            # If admin, prompt to select data files to share and generate Dockerfile
            data_dir = os.path.join('rvidia-data', 'data')
            files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
            selected_files = select_data_files(files)

            # Generate Dockerfile
            dockerfile_path = os.path.join('rvidia-data', 'Dockerfile')
            with open(dockerfile_path, 'w') as df:
                df.write('FROM python:3.9-slim\n')
                df.write('WORKDIR /app\n')
                df.write('COPY app.py ./\n')
                for fname in selected_files:
                    df.write(f'COPY data/{fname} ./data/{fname}\n')
                df.write('RUN pip install -r requirements.txt\n')
                df.write('CMD ["python", "app.py"]\n')
            console.print(f'[bold green]Dockerfile generated at {dockerfile_path}[/bold green]')
            console.print('[bold green]You are the admin.[/bold green]')

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
