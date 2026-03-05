"""CLI - Click commands for convert, batch, build-site."""

from pathlib import Path

import click

from spina.config import SpinaConfig
from spina.engines.base import ConversionEngine
from spina.engines.marker_engine import MarkerEngine
from spina.intermediate import read_intermediate
from spina.outputs.site_builder import build_html, build_site
from spina.pipeline import batch_convert, convert_pdf


def _create_engine(*, gpu: bool, force_ocr: bool) -> ConversionEngine:
    return MarkerEngine(gpu=gpu, force_ocr=force_ocr)


def build_site_from_intermediate(output_dir: Path, *, site_name: str) -> None:
    """Rebuild site from existing intermediate files."""
    book_dirs = [
        d for d in output_dir.iterdir() if d.is_dir() and (d / "metadata.yaml").exists()
    ]
    books = [read_intermediate(d) for d in sorted(book_dirs)]
    site_dir = output_dir / "site"
    build_site(books, site_dir, site_name=site_name, library_dir=output_dir)
    build_html(site_dir, output_dir=output_dir / "html")


@click.group()
def main() -> None:
    """spina - PDF to web-friendly HTML/EPUB converter."""


@main.command()
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", "output_dir", type=click.Path(path_type=Path), default="library")
@click.option("--force-ocr", is_flag=True, default=False)
@click.option("--enable-gpu", "gpu", is_flag=True, default=False)
@click.option("--no-epub", is_flag=True, default=False)
@click.option("--clean-pdf", is_flag=True, default=False)
@click.option("--page-threshold", type=int, default=30)
def convert(
    pdf_path: Path,
    output_dir: Path,
    force_ocr: bool,
    gpu: bool,
    no_epub: bool,
    clean_pdf: bool,
    page_threshold: int,
) -> None:
    """Convert a single PDF to web-friendly formats."""
    config = SpinaConfig(
        force_ocr=force_ocr,
        gpu=gpu,
        generate_epub=not no_epub,
        generate_clean_pdf=clean_pdf,
        page_threshold=page_threshold,
    )
    engine = _create_engine(gpu=gpu, force_ocr=force_ocr)

    click.echo(f"Converting {pdf_path.name}...")
    convert_pdf(pdf_path, engine=engine, config=config, output_dir=output_dir)
    click.echo(f"Done. Output in {output_dir}")


@main.command()
@click.argument("pdf_dir", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", "output_dir", type=click.Path(path_type=Path), default="library")
@click.option("--force-ocr", is_flag=True, default=False)
@click.option("--enable-gpu", "gpu", is_flag=True, default=False)
@click.option("--no-epub", is_flag=True, default=False)
@click.option("--clean-pdf", is_flag=True, default=False)
@click.option("--page-threshold", type=int, default=30)
@click.option("--site-name", type=str, default="spina")
def batch(
    pdf_dir: Path,
    output_dir: Path,
    force_ocr: bool,
    gpu: bool,
    no_epub: bool,
    clean_pdf: bool,
    page_threshold: int,
    site_name: str,
) -> None:
    """Convert all PDFs in a directory and build an index site."""
    config = SpinaConfig(
        force_ocr=force_ocr,
        gpu=gpu,
        generate_epub=not no_epub,
        generate_clean_pdf=clean_pdf,
        page_threshold=page_threshold,
        site_name=site_name,
    )
    engine = _create_engine(gpu=gpu, force_ocr=force_ocr)

    click.echo(f"Batch converting PDFs from {pdf_dir}...")
    books = batch_convert(
        pdf_dir, engine=engine, config=config, output_dir=output_dir
    )
    click.echo(f"Converted {len(books)} PDFs. Site in {output_dir}/site")


@main.command(name="build-site")
@click.argument("output_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--site-name", type=str, default="spina")
def build_site_cmd(output_dir: Path, site_name: str) -> None:
    """Rebuild site from existing intermediate files."""
    click.echo(f"Building site from {output_dir}...")
    build_site_from_intermediate(output_dir, site_name=site_name)
    click.echo("Done.")
