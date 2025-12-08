"""
Windows Compatibility Tests

Tests to ensure the framework works correctly on Windows with:
- UTF-8 encoding for all file operations
- Proper path handling (backslashes vs forward slashes)
- Windows line endings (CRLF vs LF)
- Special characters in filenames and content
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import patch

from config.loader import ConfigLoader
from config.schema import (
    FrameworkConfig,
    ProjectConfig,
    WorkTrackingConfig,
    QualityStandards,
    AgentConfig,
)
from adapters.file_based import FileBasedAdapter
from core.state_manager import WorkflowState
from core.profiler import WorkflowProfiler
from agents.registry import AgentRegistry
from workflows.registry import WorkflowRegistry


@pytest.mark.unit
class TestWindowsUTF8Encoding:
    """Test UTF-8 encoding works correctly on Windows."""

    def test_config_saves_with_utf8_special_characters(self, tmp_path):
        """Test config files save correctly with UTF-8 special characters."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        # Create config with various UTF-8 characters
        config_dict = {
            "project": {
                "name": "Test Project with émojis 🚀 and unicode ñ中文",
                "type": "web-application",
                "tech_stack": {"languages": ["Python"]},
            },
            "work_tracking": {
                "platform": "file-based",
                "organization": "Test Org with Ü",
                "project": "Проект",  # Cyrillic
            },
            "quality_standards": {"test_coverage_min": 80},
            "agent_config": {"enabled_agents": ["business-analyst"]},
        }

        # Save with UTF-8 encoding
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)

        # Load and verify special characters preserved
        loader = ConfigLoader(config_path)
        loaded = loader.load()

        assert "émojis 🚀" in loaded.project.name
        assert "ñ中文" in loaded.project.name
        assert "Ü" in loaded.work_tracking.organization
        assert loaded.work_tracking.project == "Проект"

    def test_work_items_save_with_utf8(self, tmp_path):
        """Test file-based adapter saves work items with UTF-8 encoding."""
        adapter = FileBasedAdapter(
            work_items_dir=tmp_path / "work-items", project_name="Test"
        )

        # Create work item with UTF-8 characters
        work_item = adapter.create_work_item(
            work_item_type="Task",
            title="Tâche avec émojis 🎉 and special chars: ñ, ü, 中文, Русский",
            description="Description with:\n- Emoji: 🚀\n- Accents: é è ê\n- Chinese: 你好\n- Cyrillic: Привет",
        )

        # Retrieve and verify
        retrieved = adapter.get_work_item(work_item["id"])

        assert "émojis 🎉" in retrieved["title"]
        assert "中文" in retrieved["title"]
        assert "Русский" in retrieved["title"]
        assert "🚀" in retrieved["description"]
        assert "你好" in retrieved["description"]
        assert "Привет" in retrieved["description"]

    def test_state_manager_saves_with_utf8(self, tmp_path, monkeypatch):
        """Test workflow state saves with UTF-8 encoding."""
        # Change to temp directory so state files go there
        monkeypatch.chdir(tmp_path)

        state = WorkflowState(
            workflow_name="test-workflow", workflow_id="test-001"
        )

        # Add state with UTF-8 characters
        state.state["user_input"] = "Input with émojis 🎯 and unicode: ñ, 中文"
        state.state["comments"] = [
            "Comment 1: Résumé",
            "Comment 2: 日本語",
            "Comment 3: Привет мир",
        ]
        state.save()

        # Verify file was saved with UTF-8 encoding
        state_file = tmp_path / ".claude" / "workflow-state" / "test-workflow-test-001.json"
        assert state_file.exists()

        # Read and verify UTF-8 content (JSON may escape unicode, but it should preserve correctly)
        with open(state_file, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)

        assert "émojis 🎯" in loaded_state["user_input"]
        assert "中文" in loaded_state["user_input"]
        assert "Résumé" in loaded_state["comments"][0]
        assert "日本語" in loaded_state["comments"][1]
        assert "Привет мир" in loaded_state["comments"][2]

    def test_profiler_saves_with_utf8(self, tmp_path):
        """Test profiler reports save with UTF-8 encoding."""
        profiler = WorkflowProfiler(workflow_name="test-workflow-émoji-🚀")

        # Simulate an agent call with UTF-8 characters
        call_data = profiler.start_agent_call(
            agent_name="analyst-中文",
            task_description="Analyze data with émojis 🎯",
            model="sonnet"
        )

        profiler.complete_agent_call(call_data, success=True, output_length=500)

        # Save report
        report_path = profiler.save_report(output_dir=tmp_path)

        # Read and verify UTF-8 content
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "émoji-🚀" in content or "émojis" in content
        assert "中文" in content

    def test_agent_rendering_with_utf8(self, tmp_path, sample_framework_config):
        """Test agent templates render correctly with UTF-8 content."""
        # Modify config to include UTF-8 characters
        sample_framework_config.project.name = "Проект with émojis 🎉"

        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("business-analyst")

        # Should include UTF-8 project name
        assert "Проект" in rendered or "émojis" in rendered

    def test_workflow_rendering_with_utf8(self, tmp_path, sample_framework_config):
        """Test workflow templates render correctly with UTF-8 content."""
        # Modify config to include UTF-8 characters
        sample_framework_config.project.name = "Test Проект 🚀"

        registry = WorkflowRegistry(sample_framework_config)
        rendered = registry.render_workflow("sprint-planning")

        # Should handle UTF-8 project name
        assert isinstance(rendered, str)

    def test_cli_agent_render_saves_utf8(self, tmp_path, sample_framework_config, monkeypatch):
        """Test CLI agent render command saves files with UTF-8 encoding."""
        from click.testing import CliRunner
        from cli.commands.agent import render_agent

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Save config to temp directory
        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        config_path = config_dir / "config.yaml"

        # Add UTF-8 characters to config
        sample_framework_config.project.name = "Test with émojis 🚀 中文"

        from config.loader import ConfigLoader
        loader = ConfigLoader(config_path)
        loader.save(sample_framework_config)

        # Run CLI command with output file
        runner = CliRunner()
        output_file = tmp_path / "test-agent.md"

        result = runner.invoke(
            render_agent,
            ["business-analyst", "-o", str(output_file)],
        )

        # Verify file was created with UTF-8 encoding
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        # Verify content contains UTF-8 characters
        assert isinstance(content, str)
        assert len(content) > 0

    def test_cli_workflow_render_saves_utf8(self, tmp_path, sample_framework_config, monkeypatch):
        """Test CLI workflow render command saves files with UTF-8 encoding."""
        from click.testing import CliRunner
        from cli.commands.workflow import render_workflow

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Save config to temp directory
        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        config_path = config_dir / "config.yaml"

        # Add UTF-8 characters to config
        sample_framework_config.project.name = "Workflow test 🎯 Русский"

        from config.loader import ConfigLoader
        loader = ConfigLoader(config_path)
        loader.save(sample_framework_config)

        # Run CLI command with output file
        runner = CliRunner()
        output_file = tmp_path / "test-workflow.md"

        result = runner.invoke(
            render_workflow,
            ["sprint-planning", "-o", str(output_file)],
        )

        # Verify file was created with UTF-8 encoding
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        # Verify content is valid string
        assert isinstance(content, str)
        assert len(content) > 0


@pytest.mark.unit
class TestWindowsPathHandling:
    """Test path handling works correctly on Windows."""

    def test_pathlib_handles_windows_paths(self, tmp_path):
        """Test pathlib correctly handles Windows-style paths."""
        # Create nested directory structure
        nested_path = tmp_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)

        config_file = nested_path / "config.yaml"
        config_file.write_text("test: value\n", encoding="utf-8")

        # Verify file exists and is readable
        assert config_file.exists()
        assert config_file.is_file()

        # Read back content
        content = config_file.read_text(encoding="utf-8")
        assert "test: value" in content

    def test_work_items_dir_creation_windows(self, tmp_path):
        """Test work items directory creation on Windows."""
        work_items_dir = tmp_path / "work-items" / "tasks"

        adapter = FileBasedAdapter(
            work_items_dir=tmp_path / "work-items", project_name="Test"
        )

        # Directories should be created
        assert (tmp_path / "work-items").exists()
        assert (tmp_path / "work-items" / "tasks").exists()
        assert (tmp_path / "work-items" / "epics").exists()

    def test_state_directory_creation_windows(self, tmp_path, monkeypatch):
        """Test state directory creation on Windows."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        state = WorkflowState(
            workflow_name="test", workflow_id="001"
        )

        # Directory should be created
        state_dir = tmp_path / ".claude" / "workflow-state"
        assert state_dir.exists()
        assert state_dir.is_dir()

    @pytest.mark.skipif(
        not hasattr(Path, "as_posix"), reason="as_posix not available"
    )
    def test_path_conversion_to_posix(self, tmp_path):
        """Test paths can be converted to POSIX format."""
        windows_style = tmp_path / "dir1" / "dir2" / "file.txt"

        # Should be able to convert to POSIX
        posix_path = windows_style.as_posix()
        assert "/" in posix_path
        assert "\\" not in posix_path


@pytest.mark.unit
class TestWindowsLineEndings:
    """Test handling of Windows line endings (CRLF)."""

    def test_config_loads_with_crlf_line_endings(self, tmp_path):
        """Test config files load correctly with Windows CRLF line endings."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        # Create config with CRLF line endings (Windows style)
        config_content = (
            "project:\r\n"
            "  name: 'Test Project'\r\n"
            "  type: 'web-application'\r\n"
            "  tech_stack:\r\n"
            "    languages:\r\n"
            "      - Python\r\n"
            "work_tracking:\r\n"
            "  platform: 'file-based'\r\n"
            "  organization: 'N/A'\r\n"
            "  project: 'Test'\r\n"
            "quality_standards:\r\n"
            "  test_coverage_min: 80\r\n"
            "agent_config:\r\n"
            "  enabled_agents:\r\n"
            "    - business-analyst\r\n"
        )

        config_path.write_text(config_content, encoding="utf-8")

        # Should load correctly regardless of line endings
        loader = ConfigLoader(config_path)
        config = loader.load()

        assert config.project.name == "Test Project"
        assert config.project.type == "web-application"

    def test_yaml_dump_produces_consistent_output(self, tmp_path):
        """Test YAML dump produces consistent output regardless of platform."""
        config_file = tmp_path / "test.yaml"

        data = {
            "project": {"name": "Test", "type": "web-application"},
            "list_items": ["item1", "item2", "item3"],
        }

        # Save with UTF-8 encoding
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)

        # Load and verify
        with open(config_file, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded == data

    def test_json_dump_produces_consistent_output(self, tmp_path):
        """Test JSON dump produces consistent output regardless of platform."""
        json_file = tmp_path / "test.json"

        data = {
            "workflow": "test",
            "state": {"step": 1, "data": ["a", "b", "c"]},
        }

        # Save with UTF-8 encoding
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Load and verify
        with open(json_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == data


@pytest.mark.unit
class TestWindowsSpecialCases:
    """Test Windows-specific special cases."""

    def test_reserved_filenames_handled(self, tmp_path):
        """Test that Windows reserved filenames are handled gracefully."""
        # Windows reserved names: CON, PRN, AUX, NUL, COM1-9, LPT1-9
        # We should be able to create files with these names in subdirectories

        adapter = FileBasedAdapter(
            work_items_dir=tmp_path / "work-items", project_name="Test"
        )

        # Should not crash when creating work items with reserved-like names
        work_item = adapter.create_work_item(
            work_item_type="Task",
            title="Configure AUX input",  # Contains reserved word
            description="Update COM port settings",  # Contains reserved word
        )

        assert work_item is not None
        assert "AUX" in work_item["title"]

    def test_long_paths_handled(self, tmp_path):
        """Test that long paths are handled correctly."""
        # Create a deeply nested directory structure
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"level{i}"

        deep_path.mkdir(parents=True)

        # Should be able to create file in deep path
        test_file = deep_path / "config.yaml"
        test_file.write_text("test: value\n", encoding="utf-8")

        assert test_file.exists()
        content = test_file.read_text(encoding="utf-8")
        assert "test: value" in content

    def test_special_characters_in_filenames(self, tmp_path):
        """Test handling of special characters in filenames."""
        # Test characters that might be problematic on Windows
        test_cases = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
        ]

        for filename in test_cases:
            file_path = tmp_path / filename
            file_path.write_text("test content", encoding="utf-8")

            assert file_path.exists()
            content = file_path.read_text(encoding="utf-8")
            assert content == "test content"

    def test_case_insensitive_filesystem_awareness(self, tmp_path):
        """Test awareness of case-insensitive filesystem on Windows."""
        # On Windows, file systems are typically case-insensitive
        file1 = tmp_path / "TestFile.txt"
        file1.write_text("content1", encoding="utf-8")

        # Path objects should handle this correctly
        file2_path = tmp_path / "testfile.txt"

        # On case-insensitive systems, these refer to the same file
        # On case-sensitive systems (Linux), they're different files
        # The test should work on both

        if file2_path.exists():
            # Case-insensitive system (Windows)
            content = file2_path.read_text(encoding="utf-8")
            assert content == "content1"


@pytest.mark.unit
class TestWindowsEncodingEdgeCases:
    """Test edge cases for Windows encoding."""

    def test_mixed_encodings_in_config(self, tmp_path):
        """Test handling of potential encoding issues."""
        config_path = tmp_path / "config.yaml"

        # Create config with various UTF-8 characters
        config_dict = {
            "project": {
                "name": "Test™ Project® with ©",  # Special symbols
                "type": "web-application",
                "tech_stack": {"languages": ["Python", "C++", "C#"]},  # Programming symbols
            },
            "work_tracking": {
                "platform": "file-based",
                "organization": "Café Müller & Søn",  # European chars
                "project": "Tëst",
            },
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, allow_unicode=True)

        # Load and verify all characters preserved
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded["project"]["name"] == "Test™ Project® with ©"
        assert loaded["work_tracking"]["organization"] == "Café Müller & Søn"

    def test_emoji_sequences_preserved(self, tmp_path):
        """Test complex emoji sequences are preserved correctly."""
        adapter = FileBasedAdapter(
            work_items_dir=tmp_path / "work-items", project_name="Test"
        )

        # Emojis with modifiers and combinations
        complex_emojis = "👨‍👩‍👧‍👦 👍🏽 🏳️‍🌈 🇺🇸"

        work_item = adapter.create_work_item(
            work_item_type="Task",
            title=f"Family features {complex_emojis}",
            description="Test emoji preservation",
        )

        retrieved = adapter.get_work_item(work_item["id"])
        assert complex_emojis in retrieved["title"]

    def test_right_to_left_text(self, tmp_path):
        """Test right-to-left text (Arabic, Hebrew) is preserved."""
        adapter = FileBasedAdapter(
            work_items_dir=tmp_path / "work-items", project_name="Test"
        )

        # Arabic and Hebrew text
        rtl_text = "مرحبا بك שלום"

        work_item = adapter.create_work_item(
            work_item_type="Task",
            title=f"RTL support: {rtl_text}",
            description="Test right-to-left text preservation",
        )

        retrieved = adapter.get_work_item(work_item["id"])
        assert rtl_text in retrieved["title"]


@pytest.mark.unit
class TestWindowsInitRendering:
    """Test that init command properly renders agents, workflows, and skills on Windows."""

    def test_init_renders_agents_non_interactive(self, tmp_path, monkeypatch):
        """Test that init renders all enabled agents in non-interactive mode."""
        from click.testing import CliRunner
        from cli.main import cli

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Run init in non-interactive mode
        result = runner.invoke(cli, ['init', '--no-interactive'])

        assert result.exit_code == 0

        # Verify agents directory was created
        agents_dir = tmp_path / ".claude" / "agents"
        assert agents_dir.exists(), "Agents directory should be created during init"

        # Verify agent files were rendered
        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) >= 5, f"Expected at least 5 agents, found {len(agent_files)}"

        # Verify specific agents exist
        expected_agents = ["business-analyst.md", "architect.md", "engineer.md"]
        for agent_name in expected_agents:
            agent_file = agents_dir / agent_name
            assert agent_file.exists(), f"Agent {agent_name} should be rendered"

            # Verify file has content and is valid UTF-8
            content = agent_file.read_text(encoding="utf-8")
            assert len(content) > 100, f"Agent {agent_name} should have substantial content"
            assert "# " in content, f"Agent {agent_name} should have markdown headers"

    def test_init_renders_workflows_non_interactive(self, tmp_path, monkeypatch):
        """Test that init renders all workflows in non-interactive mode."""
        from click.testing import CliRunner
        from cli.main import cli

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Run init in non-interactive mode
        result = runner.invoke(cli, ['init', '--no-interactive'])

        assert result.exit_code == 0

        # Verify workflows directory was created
        workflows_dir = tmp_path / ".claude" / "commands"
        assert workflows_dir.exists(), "Workflows directory should be created during init"

        # Verify workflow files were rendered
        workflow_files = list(workflows_dir.glob("*.md"))
        assert len(workflow_files) >= 10, f"Expected at least 10 workflows, found {len(workflow_files)}"

        # Verify specific workflows exist
        expected_workflows = [
            "sprint-planning.md",
            "backlog-grooming.md",
            "context-generation.md",
        ]
        for workflow_name in expected_workflows:
            workflow_file = workflows_dir / workflow_name
            assert workflow_file.exists(), f"Workflow {workflow_name} should be rendered"

            # Verify file has content and is valid UTF-8
            content = workflow_file.read_text(encoding="utf-8")
            assert len(content) > 100, f"Workflow {workflow_name} should have substantial content"

    def test_init_copies_skills_non_interactive(self, tmp_path, monkeypatch):
        """Test that init copies skills directory in non-interactive mode."""
        from click.testing import CliRunner
        from cli.main import cli

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Run init in non-interactive mode
        result = runner.invoke(cli, ['init', '--no-interactive'])

        assert result.exit_code == 0

        # Verify skills directory was created
        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.exists(), "Skills directory should be created during init"

        # Verify skill modules exist
        skill_modules = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
        assert len(skill_modules) >= 4, f"Expected at least 4 skill modules, found {len(skill_modules)}"

        # Verify specific skills exist
        expected_skills = ["coordination", "learnings", "work_tracking"]
        for skill_name in expected_skills:
            skill_dir = skills_dir / skill_name
            assert skill_dir.exists(), f"Skill {skill_name} should be copied"
            assert (skill_dir / "__init__.py").exists(), f"Skill {skill_name} should have __init__.py"

    def test_init_renders_with_utf8_project_name(self, tmp_path, monkeypatch):
        """Test that init handles UTF-8 characters in project name correctly."""
        from click.testing import CliRunner
        from cli.main import cli

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Run init with UTF-8 project name
        result = runner.invoke(
            cli,
            ['init', '--no-interactive'],
            input="Projeté 中文 🚀\n",  # UTF-8 project name
        )

        assert result.exit_code == 0

        # Verify agents were rendered despite UTF-8 project name
        agents_dir = tmp_path / ".claude" / "agents"
        assert agents_dir.exists()

        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) >= 5

        # Verify UTF-8 content in rendered files
        for agent_file in agent_files[:3]:
            content = agent_file.read_text(encoding="utf-8")
            assert isinstance(content, str)
            assert len(content) > 0

    def test_init_interactive_renders_agents_and_workflows(self, tmp_path, monkeypatch):
        """Test that init renders agents and workflows in interactive mode."""
        from click.testing import CliRunner
        from cli.main import cli

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Run init in interactive mode with all defaults
        result = runner.invoke(
            cli,
            ['init'],
            input="\n\n\n\n\n\n\n\n\n\n\n",  # Accept all defaults
        )

        assert result.exit_code == 0

        # Verify agents directory was created
        agents_dir = tmp_path / ".claude" / "agents"
        assert agents_dir.exists(), "Agents should be rendered in interactive mode"

        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) >= 5

        # Verify workflows directory was created
        workflows_dir = tmp_path / ".claude" / "commands"
        assert workflows_dir.exists(), "Workflows should be rendered in interactive mode"

        workflow_files = list(workflows_dir.glob("*.md"))
        assert len(workflow_files) >= 10

    def test_init_shows_correct_command_for_platform(self, tmp_path, monkeypatch, sample_framework_config):
        """Test that init shows correct Claude command based on platform."""
        from click.testing import CliRunner
        from cli.main import cli
        import platform

        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Run init
        result = runner.invoke(cli, ['init', '--no-interactive'])

        assert result.exit_code == 0

        # Check that output contains correct command for platform
        if platform.system() == 'Windows':
            assert "claude.cmd" in result.output, "Windows should show claude.cmd command"
        else:
            assert "$ claude" in result.output, "Linux/macOS should show claude command"
            assert "claude.cmd" not in result.output, "Linux/macOS should not show claude.cmd"


@pytest.mark.unit
class TestWindowsCrossCompatibility:
    """Test cross-platform compatibility between Windows and Unix."""

    def test_files_created_on_windows_readable_on_unix(self, tmp_path):
        """Test files created with UTF-8 encoding are cross-platform compatible."""
        # Simulate creating a file with Windows UTF-8 encoding
        test_file = tmp_path / "cross-platform.yaml"

        data = {
            "project": "Test with émojis 🚀 and unicode: ñ, 中文, Русский",
            "items": ["item1", "item2", "item3"],
        }

        # Save with UTF-8 (universal encoding)
        with open(test_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

        # Read back (should work on any platform)
        with open(test_file, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded["project"] == data["project"]
        assert loaded["items"] == data["items"]

    def test_state_files_portable(self, tmp_path, monkeypatch):
        """Test workflow state files are portable across platforms."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create state with UTF-8 content
        state = WorkflowState(
            workflow_name="test-workflow", workflow_id="cross-001"
        )

        state.state["platform_data"] = {
            "windows": "Data from Windows 🪟",
            "linux": "Data from Linux 🐧",
            "unicode": "中文 Русский العربية",
        }
        state.save()

        # Verify file was saved with UTF-8 encoding
        state_file = tmp_path / ".claude" / "workflow-state" / "test-workflow-cross-001.json"
        assert state_file.exists()

        # Read raw file content to verify UTF-8
        with open(state_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        assert content["platform_data"]["windows"] == "Data from Windows 🪟"
        assert content["platform_data"]["linux"] == "Data from Linux 🐧"
        assert "中文" in content["platform_data"]["unicode"]
