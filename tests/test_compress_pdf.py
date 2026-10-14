from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
import pymupdf
from click.testing import CliRunner

from compress_pdf import compress_image_heavy_pdf, main


def test_compress_image_heavy_pdf_writes_a_valid_pdf(tmp_path: Path) -> None:
    input_path = tmp_path / "input.pdf"
    output_path = tmp_path / "output.pdf"
    document = pymupdf.open()
    page = document.new_page(width=72, height=72)
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 288, 288), 0)
    image.clear_with(96)
    page.insert_image(page.rect, stream=image.tobytes("png"))
    document.save(input_path)
    document.close()

    compress_image_heavy_pdf(input_path, output_path, target_dpi=72)

    with pymupdf.open(output_path) as compressed_document:
        assert len(compressed_document) == 1
        assert compressed_document[0].get_images(full=True)


def test_compress_image_heavy_pdf_rewrites_images_and_closes_document(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.pdf"
    output_path = tmp_path / "output.pdf"
    document = MagicMock()
    open_pdf = MagicMock(return_value=document)
    monkeypatch.setattr("compress_pdf.pymupdf.open", open_pdf)

    compress_image_heavy_pdf(input_path, output_path, target_dpi=120, jpeg_quality=45)

    open_pdf.assert_called_once_with(str(input_path))
    document.rewrite_images.assert_called_once_with(
        dpi_threshold=121,
        dpi_target=120,
        quality=45,
        lossy=True,
    )
    document.save.assert_called_once_with(str(output_path), garbage=4, deflate=True)
    document.close.assert_called_once_with()


def test_compress_image_heavy_pdf_removes_each_unique_positive_image_xref(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.pdf"
    output_path = tmp_path / "output.pdf"
    page = MagicMock()
    page.get_images.return_value = [(12,), (0,), (12,), (23,)]
    document = MagicMock()
    document.__iter__.return_value = iter([page])
    monkeypatch.setattr("compress_pdf.pymupdf.open", MagicMock(return_value=document))

    compress_image_heavy_pdf(input_path, output_path, remove_images=True)

    page.delete_image.assert_has_calls([call(12), call(23)])
    document.rewrite_images.assert_not_called()
    document.save.assert_called_once_with(str(output_path), garbage=4, deflate=True)
    document.close.assert_called_once_with()


def test_compress_image_heavy_pdf_closes_document_when_save_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    document = MagicMock()
    document.save.side_effect = OSError("write failed")
    monkeypatch.setattr("compress_pdf.pymupdf.open", MagicMock(return_value=document))

    with pytest.raises(OSError, match="write failed"):
        compress_image_heavy_pdf(tmp_path / "input.pdf", tmp_path / "output.pdf")

    document.close.assert_called_once_with()


def test_main_uses_default_output_and_forwards_options(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.pdf"
    input_path.write_bytes(b"pdf")
    output_path = tmp_path / "input_compressed.pdf"

    def compress(**kwargs: object) -> None:
        output_path.write_bytes(b"compressed")

    compress_pdf = MagicMock(side_effect=compress)
    monkeypatch.setattr("compress_pdf.compress_image_heavy_pdf", compress_pdf)

    result = CliRunner().invoke(
        main,
        [str(input_path), "--dpi", "110", "--quality", "35", "--remove-images"],
    )

    assert result.exit_code == 0, result.output
    assert output_path.read_bytes() == b"compressed"
    compress_pdf.assert_called_once_with(
        input_path=input_path,
        output_path=output_path,
        target_dpi=110,
        jpeg_quality=35,
        remove_images=True,
    )
    assert "Compression Complete!" in result.output


@pytest.mark.parametrize(
    ("quality", "is_valid"), [(0, False), (1, True), (100, True), (101, False)]
)
def test_main_validates_quality_range(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    quality: int,
    is_valid: bool,
) -> None:
    input_path = tmp_path / "document.pdf"
    input_path.write_bytes(b"pdf")
    output_path = tmp_path / "document_compressed.pdf"

    def create_output(**kwargs: object) -> None:
        output_path.write_bytes(b"compressed")

    compress_pdf = MagicMock(side_effect=create_output)
    monkeypatch.setattr("compress_pdf.compress_image_heavy_pdf", compress_pdf)

    result = CliRunner().invoke(main, [str(input_path), "--quality", str(quality)])

    if is_valid:
        assert result.exit_code == 0, result.output
        compress_pdf.assert_called_once()
    else:
        assert result.exit_code != 0
        compress_pdf.assert_not_called()


@pytest.mark.parametrize(
    ("input_data", "output_data", "expected"),
    [
        (b"x" * 100, b"x" * 40, "60.0%"),
        (b"x" * 100, b"x" * 100, "0.0%"),
        (b"x" * 100, b"x" * 120, "-20.0% (file size increased)"),
    ],
)
def test_main_reports_space_saved_or_size_increase(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    input_data: bytes,
    output_data: bytes,
    expected: str,
) -> None:
    input_path = tmp_path / "document.pdf"
    output_path = tmp_path / "compressed.pdf"
    input_path.write_bytes(input_data)
    monkeypatch.setattr(
        "compress_pdf.compress_image_heavy_pdf",
        lambda **kwargs: output_path.write_bytes(output_data),
    )

    result = CliRunner().invoke(main, [str(input_path), "--output", str(output_path)])

    assert result.exit_code == 0, result.output
    assert expected in result.output


@pytest.mark.parametrize("input_name", ["document.txt", "document.Pdfx"])
def test_main_rejects_non_pdf_input(tmp_path: Path, input_name: str) -> None:
    input_path = tmp_path / input_name
    input_path.touch()

    result = CliRunner().invoke(main, [str(input_path)])

    assert result.exit_code != 0
    assert "is not a PDF file" in result.output


def test_main_rejects_output_path_equal_to_input(tmp_path: Path) -> None:
    input_path = tmp_path / "document.pdf"
    input_path.write_bytes(b"pdf")

    result = CliRunner().invoke(main, [str(input_path), "--output", str(input_path)])

    assert result.exit_code != 0
    assert "cannot be the same as the input" in result.output


def test_main_removes_empty_output_when_compression_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "document.pdf"
    output_path = tmp_path / "compressed.pdf"
    input_path.write_bytes(b"pdf")

    def fail_after_creating_output(**kwargs: object) -> None:
        output_path.touch()
        raise OSError("write failed")

    monkeypatch.setattr(
        "compress_pdf.compress_image_heavy_pdf", fail_after_creating_output
    )

    result = CliRunner().invoke(main, [str(input_path), "--output", str(output_path)])

    assert result.exit_code != 0
    assert "Compression failed: write failed" in result.output
    assert not output_path.exists()
