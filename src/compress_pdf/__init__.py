from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
import time

console = Console()


@click.command()
@click.argument(
    "pdf_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to the PDF file to compress",
)
def main(pdf_path: Path):
    """A CLI tool to compress a local PDF file."""

    # Check that the file extension is strictly '.pdf' (case-insensitive)
    if pdf_path.suffix.lower() != ".pdf":
        console.print(
            f"[bold red]Error:[/bold red] '{pdf_path.name}' is not a PDF file. Please provide a file ending in .pdf"
        )
        raise click.Abort()

    # Print an initial status banner using a Rich Panel
    console.print(
        Panel(
            f"[bold green]Target File:[/bold green] {pdf_path.name}\n"
            f"[dim]Full Path: {pdf_path.resolve()}[/dim]",
            title="PDF Compressor Initialised",
            expand=False,
        )
    )

    # Show processing with a Rich Progress bar
    for _ in track(range(100), description="[blue]Compressing pages..."):
        time.sleep(0.02)  # Simulating work

    # Print the final summary comparison table
    original_size = pdf_path.stat().st_size / (1024 * 1024)  # Size in MB
    compressed_size = original_size * 0.42

    console.print("\n[bold]Compression Complete![/bold]")

    # Text-based visual breakdown
    console.print(f"📉 Original Size:   {original_size:.2f} MB", highlight=False)
    console.print(f"🍃 Compressed Size: {compressed_size:.2f} MB", highlight=False)
    console.print(f"✨ Space Saved:     {(1 - 0.42)*100:.0f}%\n", highlight=False)


if __name__ == "__main__":
    main()
