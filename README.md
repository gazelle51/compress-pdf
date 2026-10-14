# compress-pdf

A command-line tool for reducing the size of local PDF files. It is most useful for PDFs with large raster images, such as scanned documents and photos.

The tool rewrites images using lossy compression, downsamples images above the selected resolution, deflates uncompressed PDF streams, and removes duplicate and unreferenced PDF objects. The original file is left unchanged; by default, the output is saved beside it with `_compressed` added to the filename.

## Security: trusted inputs only

Use this CLI only with trusted local PDFs. It passes the input directly to PyMuPDF and does not enforce input-size, memory, or execution-time limits. Very large or specially crafted PDFs can exhaust CPU or memory during parsing or rewriting. This is a resource-exhaustion concern, not a claim of a verified PyMuPDF parser vulnerability.

Processing untrusted PDFs, including user uploads, is not a supported workflow for this CLI on its own. Before using it in an upload-processing service, run compression in an isolated worker or subprocess with an enforced input-file-size cap, memory limit, and execution timeout that terminates the worker. Enforce these controls outside the PDF-processing process and add tests or operational checks that verify oversized inputs are rejected and workers exceeding memory or time limits are terminated. A file-size cap alone does not bound the resources needed to parse or rewrite a PDF.

## Requirements

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)

## Install

Clone this repository, open a terminal in the project directory, then run:

```bash
uv sync
```

`uv run` uses the project environment and does not require a separate global installation of the CLI.

## Usage

Compress a PDF with the default settings:

```bash
uv run compress-pdf "C:\path\to\document.pdf"
```

This creates `document_compressed.pdf` in the same directory. Choose an output path explicitly with `-o` or `--output`:

```bash
uv run compress-pdf "C:\path\to\document.pdf" -o "C:\path\to\smaller-document.pdf"
```

Use lower resolution and JPEG quality for more aggressive image compression:

```bash
uv run compress-pdf "C:\path\to\scan.pdf" --dpi 100 --quality 40 -o "C:\path\to\scan-smaller.pdf"
```

Lower DPI and quality can reduce image detail. Check the output before deleting or sharing the original.

## Options

| Option                    | Default                  | Description                                                                                  |
| ------------------------- | ------------------------ | -------------------------------------------------------------------------------------------- |
| `PDF_PATH`                | Required                 | Input PDF file.                                                                              |
| `-o`, `--output PATH`     | `<input>_compressed.pdf` | Output file path. It must differ from the input path.                                        |
| `--dpi INTEGER`           | `150`                    | Target resolution for downsampling images whose effective DPI is above the target threshold. |
| `-q`, `--quality INTEGER` | `60`                     | JPEG quality from 1 (smaller, lower quality) to 100 (higher quality).                        |
| `--remove-images`         | Off                      | Replace page images with tiny transparent placeholders instead of compressing them.          |
| `--help`                  |                          | Show the command help.                                                                       |

> [!IMPORTANT]
> `--remove-images` is destructive to visible image content. A scanned PDF may consist almost entirely of page images, so this option can leave its pages blank. Do not use it when you need to preserve the scanned pages.

## Tests

Run the test suite with:

```bash
uv run pytest
```

## Compression Results

The amount saved depends on the PDF. Already optimized images, low-resolution scans, text, and vector graphics may not shrink much. Re-encoding can also produce an output that is the same size or larger than the original; compare the reported sizes and inspect the output.
