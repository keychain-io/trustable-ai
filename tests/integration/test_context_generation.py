"""
Integration tests for context generation.

Tests the hierarchical CLAUDE.md generation and context indexing functionality.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner
import yaml

from cli.main import cli


@pytest.mark.integration
class TestContextGenerate:
    """Test suite for trustable-ai context generate command."""

    def test_context_generate_dry_run(self):
        """Test context generation dry-run shows plan without creating files."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a simple project structure
            Path("src").mkdir()
            Path("src/main.py").write_text("# Main module")
            Path("src/utils.py").write_text("# Utils module")
            Path("tests").mkdir()
            Path("tests/test_main.py").write_text("# Tests")
            Path("pyproject.toml").write_text("[project]\nname = 'test'")

            result = runner.invoke(cli, ['context', 'generate', '--dry-run'])

            assert result.exit_code == 0
            assert 'Analyzing repository' in result.output
            assert 'Dry run' in result.output
            # Should not create any files
            assert not Path("CLAUDE.md").exists()
            assert not Path("src/CLAUDE.md").exists()

    def test_context_generate_creates_files(self):
        """Test context generation creates CLAUDE.md files."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a project structure
            Path("src").mkdir()
            Path("src/app.py").write_text("# App module")
            Path("src/models.py").write_text("# Models")
            Path("tests").mkdir()
            Path("tests/test_app.py").write_text("# Tests")
            Path("pyproject.toml").write_text("[project]\nname = 'test'")

            result = runner.invoke(cli, ['context', 'generate'])

            assert result.exit_code == 0
            assert 'Generation complete' in result.output

            # Verify files created
            assert Path("CLAUDE.md").exists()
            assert Path("src/CLAUDE.md").exists()
            assert Path("tests/CLAUDE.md").exists()

    def test_context_generate_skips_existing(self):
        """Test context generation with --no-merge skips existing CLAUDE.md files."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create structure with existing CLAUDE.md
            Path("src").mkdir()
            Path("src/app.py").write_text("# App")
            existing_content = "# Existing Content\nDo not overwrite"
            Path("CLAUDE.md").write_text(existing_content)

            # Use --no-merge to skip existing files (merge is now default)
            result = runner.invoke(cli, ['context', 'generate', '--no-merge'])

            assert result.exit_code == 0
            assert 'exists' in result.output.lower()

            # Verify existing file not overwritten
            assert Path("CLAUDE.md").read_text() == existing_content

    def test_context_generate_force_overwrites(self):
        """Test context generation with --force overwrites existing files."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create structure with existing CLAUDE.md
            Path("src").mkdir()
            Path("src/app.py").write_text("# App")
            Path("CLAUDE.md").write_text("# Old Content")

            result = runner.invoke(cli, ['context', 'generate', '--force'])

            assert result.exit_code == 0

            # Verify file was overwritten
            content = Path("CLAUDE.md").read_text()
            assert "Old Content" not in content
            # New format references README.md and contains context directive
            assert "README.md" in content or "context" in content.lower()

    def test_context_generate_respects_depth(self):
        """Test context generation respects depth limit."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create deep structure with named directories
            Path("src/api/routes/handlers").mkdir(parents=True)
            Path("src/api/auth.py").write_text("# Auth")
            Path("src/api/users.py").write_text("# Users")
            Path("src/api/routes/main.py").write_text("# Routes")
            Path("src/api/routes/admin.py").write_text("# Admin")
            Path("src/api/routes/handlers/base.py").write_text("# Base handler")

            # Generate with depth 2
            result = runner.invoke(cli, ['context', 'generate', '-d', '2'])

            assert result.exit_code == 0

            # Should create up to depth 2
            assert Path("CLAUDE.md").exists()
            assert Path("src/CLAUDE.md").exists()
            assert Path("src/api/CLAUDE.md").exists()
            # Depth 3 (routes) might be created if it's a named pattern
            # Depth 4 (handlers) should NOT be created
            assert not Path("src/api/routes/handlers/CLAUDE.md").exists()


@pytest.mark.integration
class TestContextIndex:
    """Test suite for trustable-ai context index command."""

    def test_context_index_creates_index(self):
        """Test context indexing creates index file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create CLAUDE.md files
            Path(".claude").mkdir()
            Path("CLAUDE.md").write_text("# Project\nThis is a Python project")
            Path("src").mkdir()
            Path("src/CLAUDE.md").write_text("# Source\nContains API code")

            result = runner.invoke(cli, ['context', 'index'])

            assert result.exit_code == 0
            assert 'Context index saved' in result.output

            # Verify index file
            index_path = Path(".claude/context-index.yaml")
            assert index_path.exists()

            with open(index_path) as f:
                index = yaml.safe_load(f)

            assert "context_files" in index
            assert len(index["context_files"]) >= 2
            assert "keywords" in index

    def test_context_index_extracts_keywords(self):
        """Test context indexing extracts keywords properly."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            Path(".claude").mkdir()
            Path("CLAUDE.md").write_text("""
# Authentication Module

This module handles user authentication and authorization.
Uses JWT tokens for session management.
Integrates with OAuth providers.
""")

            result = runner.invoke(cli, ['context', 'index'])

            assert result.exit_code == 0

            with open(".claude/context-index.yaml") as f:
                index = yaml.safe_load(f)

            # Check keywords were extracted
            keywords = index.get("keywords", {})
            # Should have relevant keywords
            keyword_list = list(keywords.keys())
            assert any("auth" in k for k in keyword_list)


@pytest.mark.integration
class TestContextLookup:
    """Test suite for trustable-ai context lookup command."""

    def test_context_lookup_finds_relevant_files(self):
        """Test context lookup finds relevant files based on task."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create indexed structure
            Path(".claude").mkdir()
            Path("CLAUDE.md").write_text("# Project Overview")
            Path("src").mkdir()
            Path("src/CLAUDE.md").write_text("# Source - API endpoints and handlers")
            Path("tests").mkdir()
            Path("tests/CLAUDE.md").write_text("# Tests - Unit and integration tests")

            # Build index first
            runner.invoke(cli, ['context', 'index'])

            # Lookup
            result = runner.invoke(cli, ['context', 'lookup', 'write unit tests'])

            assert result.exit_code == 0
            assert 'tests' in result.output.lower()


@pytest.mark.integration
class TestHierarchicalContext:
    """Test suite for hierarchical context loading."""

    def test_hierarchical_context_structure(self):
        """Test that hierarchical CLAUDE.md structure is properly created."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a realistic project structure
            dirs = [
                "src",
                "src/api",
                "src/api/routes",
                "src/models",
                "src/services",
                "tests",
                "tests/unit",
                "tests/integration",
                "docs",
            ]
            for d in dirs:
                Path(d).mkdir(parents=True, exist_ok=True)

            # Add some Python files
            Path("src/api/__init__.py").write_text("")
            Path("src/api/routes/users.py").write_text("# User routes")
            Path("src/api/routes/auth.py").write_text("# Auth routes")
            Path("src/models/user.py").write_text("# User model")
            Path("src/services/auth_service.py").write_text("# Auth service")
            Path("tests/unit/test_user.py").write_text("# User tests")
            Path("pyproject.toml").write_text("[project]\nname = 'test'")

            # Generate context
            result = runner.invoke(cli, ['context', 'generate'])

            assert result.exit_code == 0

            # Verify hierarchical structure
            assert Path("CLAUDE.md").exists(), "Root CLAUDE.md should exist"
            assert Path("src/CLAUDE.md").exists(), "src/CLAUDE.md should exist"
            assert Path("tests/CLAUDE.md").exists(), "tests/CLAUDE.md should exist"

            # Verify content is appropriate for each level
            # New format has YAML front matter and references README.md
            root_content = Path("CLAUDE.md").read_text()
            assert "README.md" in root_content or "context" in root_content.lower()

            src_content = Path("src/CLAUDE.md").read_text()
            assert "src" in src_content.lower() or "source" in src_content.lower() or "README.md" in src_content

            tests_content = Path("tests/CLAUDE.md").read_text()
            assert "test" in tests_content.lower() or "README.md" in tests_content

    def test_context_index_after_generation(self):
        """Test that context index works with generated CLAUDE.md files."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create and generate
            Path("src").mkdir()
            Path("src/main.py").write_text("# Main")
            Path("tests").mkdir()
            Path("tests/test_main.py").write_text("# Tests")

            runner.invoke(cli, ['context', 'generate'])

            # Now index
            Path(".claude").mkdir(exist_ok=True)
            result = runner.invoke(cli, ['context', 'index'])

            assert result.exit_code == 0

            # Verify index contains generated files
            with open(".claude/context-index.yaml") as f:
                index = yaml.safe_load(f)

            paths = [f["path"] for f in index["context_files"]]
            assert "CLAUDE.md" in paths
            assert any("src" in p for p in paths)
            assert any("tests" in p for p in paths)

    def test_full_workflow_init_generates_context(self, sample_config_yaml):
        """Test that init workflow properly generates context when requested."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create project structure
            Path("src").mkdir()
            Path("src/app.py").write_text("# App")
            Path("tests").mkdir()
            Path("tests/test_app.py").write_text("# Tests")

            # Run init with all prompts answered
            result = runner.invoke(cli, ['init'], input='\n'.join([
                'y',                      # Use detected settings as defaults
                'Test Project',           # Project name
                'api',                    # Project type
                'Python',                 # Languages
                'FastAPI',                # Frameworks
                'Docker',                 # Platforms
                '',                       # Databases
                'file-based',             # Platform
                'default',                # Agent selection
                'y',                      # Render agents/workflows
                'y',                      # Generate context
            ]))

            # Should complete successfully
            assert result.exit_code == 0
            assert 'Initialization complete' in result.output

            # Context files should be created
            assert Path("CLAUDE.md").exists() or 'CLAUDE.md' in result.output

            # Context index should exist
            assert Path(".claude/context-index.yaml").exists()


@pytest.fixture
def sample_config_yaml():
    """Sample configuration YAML for testing."""
    return """
project:
  name: Test Project
  type: api
  tech_stack:
    languages:
      - Python
    frameworks:
      - FastAPI
work_tracking:
  platform: file-based
quality_standards:
  test_coverage_min: 80
agent_config:
  enabled_agents:
    - senior-engineer
"""
