import os
import socket
import time

# rvidia-cli: Shared Computing CLI Tool
import argparse
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def main():
    parser = argparse.ArgumentParser(description="rvidia-cli: Shared Computing CLI Tool")
    parser.add_argument('--mode', choices=['local', 'cross-network'], default='local', help='Choose mode: local or cross-network')
    args = parser.parse_args()

    if args.mode == 'cross-network':
        console.print('[bold yellow]Cross network mode coming soon![/bold yellow]')
        return
    else:
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

        # Display room members and admin
        console.print('[bold blue]Users in the room:[/bold blue]')
        for user in users:
            if user == admin:
                console.print(f'- {user} [bold red](admin)[/bold red]')
            else:
                console.print(f'- {user}')

        if is_admin:
            # If admin, prompt to select data files to share and generate Dockerfile
            data_dir = os.path.join('rvidia-data', 'data')
            files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
            console.print("\nSelect data files to share (comma separated, e.g. 1,2):")
            for idx, fname in enumerate(files, 1):
                console.print(f"[{idx}] {fname}")
            selected = Prompt.ask("Enter file numbers", default="1")
            selected_idxs = [int(i.strip()) for i in selected.split(',') if i.strip().isdigit() and 1 <= int(i.strip()) <= len(files)]
            selected_files = [files[i-1] for i in selected_idxs]

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
        elif is_admin:
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
