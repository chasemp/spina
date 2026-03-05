"""Tests for intermediate format I/O - write/read round-trip."""

from pathlib import Path

from spina.intermediate import read_intermediate, write_intermediate
from spina.models import BookMetadata, Chapter, IntermediateBook
from tests.conftest import make_chapter, make_intermediate_book, make_metadata


class TestWriteIntermediate:
    def test_creates_output_directory(self, tmp_path: Path) -> None:
        book = make_intermediate_book()
        output_dir = tmp_path / "output"

        write_intermediate(book, output_dir)

        assert output_dir.exists()

    def test_writes_metadata_yaml(self, tmp_path: Path) -> None:
        book = make_intermediate_book(
            metadata=make_metadata(title="My Book", author="Author")
        )

        write_intermediate(book, tmp_path)

        meta_file = tmp_path / "metadata.yaml"
        assert meta_file.exists()
        content = meta_file.read_text()
        assert "My Book" in content
        assert "Author" in content

    def test_writes_chapter_markdown_files(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(title="Ch 1", content="Content 1", order=0),
            make_chapter(title="Ch 2", content="Content 2", order=1),
        )
        book = make_intermediate_book(chapters=chapters)

        write_intermediate(book, tmp_path)

        chapters_dir = tmp_path / "chapters"
        assert chapters_dir.exists()
        md_files = sorted(chapters_dir.glob("*.md"))
        assert len(md_files) == 2

    def test_writes_images(self, tmp_path: Path) -> None:
        book = make_intermediate_book(image_dir=tmp_path / "src_images")
        # Create a source image
        src_dir = tmp_path / "src_images"
        src_dir.mkdir()
        (src_dir / "fig1.png").write_bytes(b"\x89PNG fake image")

        write_intermediate(book, tmp_path / "output", images={"fig1.png": b"\x89PNG fake image"})

        img_dir = tmp_path / "output" / "images"
        assert img_dir.exists()
        assert (img_dir / "fig1.png").exists()


class TestReadIntermediate:
    def test_round_trip_preserves_metadata(self, tmp_path: Path) -> None:
        original = make_intermediate_book(
            metadata=make_metadata(
                title="Round Trip",
                author="Tester",
                source_filename="test.pdf",
                page_count=25,
            ),
        )

        write_intermediate(original, tmp_path)
        restored = read_intermediate(tmp_path)

        assert restored.metadata.title == "Round Trip"
        assert restored.metadata.author == "Tester"
        assert restored.metadata.source_filename == "test.pdf"
        assert restored.metadata.page_count == 25

    def test_round_trip_preserves_chapters(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(title="First", content="Content A", order=0),
            make_chapter(title="Second", content="Content B", order=1),
        )
        original = make_intermediate_book(chapters=chapters)

        write_intermediate(original, tmp_path)
        restored = read_intermediate(tmp_path)

        assert len(restored.chapters) == 2
        assert restored.chapters[0].title == "First"
        assert restored.chapters[1].title == "Second"
        assert "Content A" in restored.chapters[0].content
        assert "Content B" in restored.chapters[1].content

    def test_round_trip_preserves_chapter_order(self, tmp_path: Path) -> None:
        chapters = (
            make_chapter(title="A", content="a", order=0),
            make_chapter(title="B", content="b", order=1),
            make_chapter(title="C", content="c", order=2),
        )
        original = make_intermediate_book(chapters=chapters)

        write_intermediate(original, tmp_path)
        restored = read_intermediate(tmp_path)

        titles = [ch.title for ch in restored.chapters]
        assert titles == ["A", "B", "C"]

    def test_round_trip_preserves_images(self, tmp_path: Path) -> None:
        original = make_intermediate_book()

        write_intermediate(
            original, tmp_path, images={"test.png": b"\x89PNG data"}
        )
        restored = read_intermediate(tmp_path)

        assert restored.image_dir is not None
        assert (restored.image_dir / "test.png").exists()
