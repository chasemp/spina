# spina

PDF to web-friendly EPUB, HTML, and PDF converter using ML-based extraction.

spina takes PDF files (including scanned documents) and converts them to clean, readable output formats: EPUB for e-readers, a static HTML site with search and navigation, and optionally a cleaned-up PDF. It uses [marker-pdf](https://github.com/VikParuchuri/marker) for ML-powered text and layout extraction, then builds outputs from the intermediate markdown representation.

## Installation

```bash
pip install .
```

### System dependencies

- **pandoc** - required for EPUB generation. Install via your package manager (`brew install pandoc`, `apt install pandoc`, etc.)
- **pdflatex** - optional, only needed for `--clean-pdf` output. Part of most TeX distributions (`brew install --cask mactex`, `apt install texlive`, etc.)

## Quick start

Convert a single PDF:

```bash
spina convert book.pdf -o library
```

Convert all PDFs in a directory and build a browsable site:

```bash
spina batch pdfs/ -o library
```

Rebuild the site from existing intermediate files:

```bash
spina build-site library
```

## Commands

### `spina convert`

Convert a single PDF to web-friendly formats.

```
spina convert <pdf_path> [OPTIONS]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output directory | `library` |
| `--force-ocr` | Force OCR even on text-based PDFs | off |
| `--enable-gpu` | Use GPU acceleration for extraction | off |
| `--no-epub` | Skip EPUB generation | off |
| `--clean-pdf` | Generate a clean PDF (requires pdflatex) | off |
| `--page-threshold` | Minimum pages before splitting into parts | `30` |

### `spina batch`

Convert all PDFs in a directory and build an index site.

```
spina batch <pdf_dir> [OPTIONS]
```

Accepts all `convert` flags plus:

| Flag | Description | Default |
|------|-------------|---------|
| `--site-name` | Name for the generated site | `spina` |

### `spina build-site`

Rebuild the static site from existing intermediate files without re-running extraction.

```
spina build-site <output_dir> [OPTIONS]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--site-name` | Name for the generated site | `spina` |

## Output formats

Each converted book produces an intermediate directory containing:

- **Markdown** - extracted text with structure preserved
- **metadata.yaml** - title, author, page count, and other book metadata
- **Images** - extracted figures and diagrams

From the intermediate representation, spina generates:

- **EPUB** - e-reader-compatible book (via pandoc)
- **Static HTML site** - browsable site with search, built on MkDocs Material
- **Clean PDF** - re-typeset PDF from the extracted markdown (optional, requires pdflatex)
- **Markdown zip** - packaged intermediate markdown and images

## Pipeline overview

```
PDF
 |
 v
marker-pdf (ML extraction)
 |
 v
Intermediate (markdown + images + metadata)
 |
 +---> EPUB (pandoc)
 +---> Static HTML site (MkDocs Material)
 +---> Clean PDF (pdflatex, optional)
 +---> Markdown zip
```

## Math handling

spina handles mathematical notation differently depending on the output format:

- **EPUB / Clean PDF**: Math is rendered as images via pandoc's `--webtex` flag, using an external rendering service. This produces universally compatible output across e-readers and PDF viewers.
- **Static HTML site**: Math is rendered client-side using MathJax via the MkDocs arithmatex extension. This gives full-fidelity rendering in the browser.

The guiding principle is consumable output over perfect output: a math formula rendered as an image is more useful than a broken LaTeX string that a reader can't parse.

## Development

```bash
pip install -e ".[dev]"
pytest
```

spina follows test-driven development. See `.claude/CLAUDE.md` for development guidelines.

## License

See [LICENSE](LICENSE) for details.
