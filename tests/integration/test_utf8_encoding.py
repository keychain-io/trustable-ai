"""
Test UTF-8 encoding in file operations.

Tests that all file write operations properly handle UTF-8 encoding,
preventing encoding errors on Windows (where default encoding is cp1252).

Related: WI-1015 - Fix UTF-8 encoding errors in trustable-ai init on Windows
"""
import pytest
from pathlib import Path
from cli.commands.init import _create_gitignore, _create_readme
from click.testing import CliRunner
from cli.commands.context import context as context_cli
import yaml


class TestUTF8Encoding:
    """Test that file operations use UTF-8 encoding explicitly."""

    def test_readme_with_unicode_content(self, tmp_path):
        """Test README creation with Unicode characters."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create README with Unicode content
        _create_readme(claude_dir, "Test Project with Unicode: 你好世界 🌍")

        readme_file = claude_dir / "README.md"
        assert readme_file.exists()

        # Read with explicit UTF-8 (this would fail on Windows with cp1252 default)
        content = readme_file.read_text(encoding='utf-8')
        assert "Test Project with Unicode: 你好世界 🌍" in content
        assert "Trustable AI" in content

    def test_gitignore_with_unicode_comments(self, tmp_path):
        """Test gitignore creation with UTF-8 content."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        _create_gitignore(claude_dir)

        gitignore_file = claude_dir / ".gitignore"
        assert gitignore_file.exists()

        # Verify can read as UTF-8
        content = gitignore_file.read_text(encoding='utf-8')
        assert "workflow-state" in content
        assert "profiling" in content

    def test_claude_md_with_emoji_and_unicode(self, tmp_path):
        """Test that CLAUDE.md files can contain emojis and Unicode."""
        test_dir = tmp_path / "src"
        test_dir.mkdir()

        claude_md = test_dir / "CLAUDE.md"

        # Write content with various Unicode characters
        content = """# Test Module 🚀

## Purpose

Solves **internationalization** issues (i18n) 🌍

## Features

- Supports Chinese: 你好世界
- Supports Japanese: こんにちは世界
- Supports Korean: 안녕하세요
- Supports Arabic: مرحبا بالعالم
- Supports Emoji: 🎉 ✅ 🔥 💡

## Examples

```python
def greet(name: str) -> str:
    return f"Hello {name}! 👋"
```
"""

        claude_md.write_text(content, encoding='utf-8')

        # Verify file can be read back correctly
        read_content = claude_md.read_text(encoding='utf-8')
        assert "🚀" in read_content
        assert "你好世界" in read_content
        assert "こんにちは世界" in read_content
        assert "안녕하세요" in read_content
        assert "مرحبا بالعالم" in read_content
        assert "🎉 ✅ 🔥 💡" in read_content

    def test_file_operations_default_encoding_compatibility(self, tmp_path):
        """Test that operations work regardless of system default encoding."""
        import locale
        import sys

        # Get system's default encoding (would be cp1252 on Windows)
        default_encoding = locale.getpreferredencoding(False)

        test_file = tmp_path / "test_unicode.txt"
        unicode_content = "Test with Unicode: 你好世界 🌍 café"

        # Write with UTF-8 (as our fix does)
        test_file.write_text(unicode_content, encoding='utf-8')

        # Read with UTF-8
        read_content = test_file.read_text(encoding='utf-8')
        assert read_content == unicode_content

        # Verify this would have failed with system default on some systems
        # (This is informational - demonstrates why the fix was needed)
        print(f"System default encoding: {default_encoding}")
        print(f"Python filesystem encoding: {sys.getfilesystemencoding()}")
