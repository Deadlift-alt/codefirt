# codefirt/display.py

from rich.console import Console
from rich.table import Table
from rich.text import Text
from datetime import datetime

def create_nifty_table(data):
    """Creates the NIFTY display table."""
    table = Table(title=f"NIFTY Index Analysis (Last Updated: {datetime.now().strftime('%H:%M:%S')})", title_style="bold magenta", show_header=True, header_style="bold blue")

    table.add_column("Metric", justify="center")
    table.add_column("Value", justify="center")
    table.add_column("3 min", justify="center")
    table.add_column("5 min", justify="center")
    table.add_column("10 min", justify="center")
    table.add_column("15 min", justify="center")
    table.add_column("30 min", justify="center")
    table.add_column("3 hr", justify="center")

    table.add_row(
        Text("NIFTY Price", style="cyan"),
        Text(str(data.get("price", "N/A")), style="bold green"),
        data.get("change_3m", "N/A"),
        data.get("change_5m", "N/A"),
        data.get("change_10m", "N/A"),
        data.get("change_15m", "N/A"),
        data.get("change_30m", "N/A"),
        data.get("change_3hr", "N/A"),
    )

    return table

def create_options_table(title, data, color_rules):
    """Creates the options (Call/Put) display table and counts red cells."""
    table = Table(title=title, title_style="bold cyan" if "Call" in title else "bold yellow", show_header=True, header_style="bold blue")

    columns = ["Strike", "Current OI", "3 min", "5 min", "10 min", "15 min", "30 min", "3 hr"]
    for col in columns:
        table.add_column(col, justify="center")

    red_cell_count = 0
    for strike, strike_data in sorted(data.items()):
        row_data = [
            Text(str(strike), style="cyan"),
            Text(str(strike_data.get("oi", "N/A")), style="white")
        ]

        for key, threshold in color_rules.items():
            change_key = f"change_{key}"
            change_tuple = strike_data.get(change_key)

            if change_tuple and isinstance(change_tuple, tuple) and len(change_tuple) == 2:
                formatted_string, percentage = change_tuple
                style = "white"
                # Check if the percentage change (which can be positive or negative)
                # exceeds the threshold in magnitude. The user's request implies
                # they are interested in large increases.
                if percentage > threshold:
                    style = "bold red"
                    red_cell_count += 1
                row_data.append(Text(formatted_string, style=style))
            else:
                row_data.append("N/A")

        table.add_row(*row_data)

    return table, red_cell_count

def render_tables(nifty_data, call_data, put_data, color_rules={}):
    """Renders all tables to the console and returns red cell counts."""
    console = Console()
    console.clear()

    nifty_table = create_nifty_table(nifty_data)
    call_table, call_red_cells = create_options_table("Call Options OI Analysis", call_data, color_rules)
    put_table, put_red_cells = create_options_table("Put Options OI Analysis", put_data, color_rules)

    console.print(nifty_table)
    console.print(call_table)
    console.print(put_table)

    return call_red_cells, put_red_cells
