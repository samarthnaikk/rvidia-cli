from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.prompt import Confirm

console = Console()

def show_header():
    console.print(Panel("[bold cyan]R V I D I A   C L I[/bold cyan]", expand=False))

def mode_selection():
    console.print("\n[bold]Select Mode:[/bold]")
    console.print("[green]1)[/green] Local shared compute")
    console.print("[yellow]2)[/yellow] Cross-network shared compute")
    mode = Prompt.ask("Enter 1 or 2", choices=["1", "2"], default="1")
    return mode

def show_room_table(users, admin):
    table = Table(title="Current Room", show_header=True, header_style="bold magenta")
    table.add_column("Username", style="dim")
    table.add_column("Role", style="bold")
    for user in users:
        role = "Admin" if user == admin else "Member"
        table.add_row(user, role)
    console.print(table)

def select_data_files(files):
    console.print("\n[bold]Select data files to include:[/bold]")
    selected = []
    for idx, fname in enumerate(files, 1):
        checked = Confirm.ask(f"Include {fname}?", default=(idx==1))
        if checked:
            selected.append(fname)
    return selected
