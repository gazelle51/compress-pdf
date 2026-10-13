from pathlib import Path
from typing import Optional

import click
import pymupdf
from rich.console import Console
from rich.panel import Panel

console = Console()


def compress_image_heavy_pdf(
    input_path: Path,
    output_path: Path,
    target_dpi: int = 150,
    jpeg_quality: int = 60,
    remove_images: bool = False,
) -> None:
    """Rewrite and compress images and streams in a PDF."""
    doc = pymupdf.open(str(input_path))
    try:
        if remove_images:
            for page in doc:
                for xref in {image[0] for image in page.get_images(full=True)}:
                    if xref > 0:
                        page.delete_image(xref)
        else:
            # Rewrite images to reduce pixel dimensions and apply lossy compression
            doc.rewrite_images(
                dpi_threshold=target_dpi + 1,
                dpi_target=target_dpi,
                quality=jpeg_quality,
                lossy=True,
            )

        # Save with maximum cleanup and stream deflation
        doc.save(
            str(output_path),
            garbage=4,
            deflate=True,
        )
    finally:
        doc.close()


@click.command()
@click.argument(
    "pdf_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to the PDF file to compress",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Output path for the compressed PDF (defaults to '<name>_compressed.pdf').",
)
@click.option(
    "--dpi",
    type=int,
    default=150,
    show_default=True,
    help="Target DPI for image downsampling.",
)
@click.option(
    "-q",
    "--quality",
    type=click.IntRange(1, 100),
    default=60,
    show_default=True,
    help="JPEG compression quality (1-100).",
)
@click.option(
    "--remove-images",
    is_flag=True,
    help="Replace page images with transparent placeholders instead of compressing them.",
)
def main(
    pdf_path: Path,
    output_path: Optional[Path],
    dpi: int,
    quality: int,
    remove_images: bool,
) -> None:
    """A CLI tool to compress a local PDF file and save as a new file."""

    # Check that the file extension is strictly '.pdf' (case-insensitive)
    if pdf_path.suffix.lower() != ".pdf":
        console.print(
            f"[bold red]Error:[/bold red] '{pdf_path.name}' is not a PDF file. Please provide a file ending in .pdf"
        )
        raise click.Abort()

    # Determine output path if not specified
    if output_path is None:
        output_path = pdf_path.with_name(f"{pdf_path.stem}_compressed.pdf")

    if output_path.resolve() == pdf_path.resolve():
        console.print(
            "[bold red]Error:[/bold red] Output file path cannot be the same as the input file path."
        )
        raise click.Abort()

    # Print an initial status banner using a Rich Panel
    console.print(
        Panel(
            f"[bold green]Input File:[/bold green]  {pdf_path.name}\n"
            f"[dim]Input Path:  {pdf_path.resolve()}[/dim]\n"
            f"[bold green]Output File:[/bold green] {output_path.name}\n"
            f"[dim]Output Path: {output_path.resolve()}[/dim]\n"
            f"[bold cyan]Settings:[/bold cyan]    Target DPI: {dpi} | Quality: {quality}%",
            title="PDF Compressor Initialised",
            expand=False,
        )
    )

    original_size = pdf_path.stat().st_size

    try:
        with console.status("[bold blue]Compressing PDF images and streams..."):
            compress_image_heavy_pdf(
                input_path=pdf_path,
                output_path=output_path,
                target_dpi=dpi,
                jpeg_quality=quality,
                remove_images=remove_images,
            )
    except Exception as exc:
        console.print(f"[bold red]Compression failed:[/bold red] {exc}")
        if output_path.exists() and output_path.stat().st_size == 0:
            output_path.unlink()
        raise click.Abort()

    compressed_size = output_path.stat().st_size
    orig_mb = original_size / (1024 * 1024)
    comp_mb = compressed_size / (1024 * 1024)
    saved_bytes = original_size - compressed_size
    saved_pct = (saved_bytes / original_size * 100) if original_size > 0 else 0.0

    console.print("\n[bold]Compression Complete![/bold]")
    console.print(
        f"📉 Original Size:   {orig_mb:.2f} MB ({original_size:,} bytes)",
        highlight=False,
    )
    console.print(
        f"🍃 Compressed Size: {comp_mb:.2f} MB ({compressed_size:,} bytes)",
        highlight=False,
    )
    if saved_bytes >= 0:
        console.print(f"✨ Space Saved:     {saved_pct:.1f}%\n", highlight=False)
    else:
        console.print(
            f"⚠️  Space Saved:     {saved_pct:.1f}% (file size increased)\n",
            highlight=False,
        )
    console.print(
        f"📁 Saved to:        [bold]{output_path.resolve()}[/bold]\n", highlight=False
    )


if __name__ == "__main__":
    main()
