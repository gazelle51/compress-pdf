```bash
uv sync
uv run compress-pdf <pdf_path>
uv run compress-pdf --help
```

By default, the compressor downsamples and recompresses images, deflates PDF
streams, and removes duplicate or unreferenced objects. To discard visible page
image content instead, use `--remove-images`; PyMuPDF replaces images with tiny
transparent placeholders. This is destructive to the image content but keeps
the rest of the page content.

See the [pypdf file-size guide](https://pypdf.readthedocs.io/en/latest/user/file-size.html)
for more about these compression techniques and their tradeoffs.
