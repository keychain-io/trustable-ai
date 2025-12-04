"""
Documentation validation command.

Validates CLAUDE.md files for:
- Required front matter fields
- Problem-focused language (not feature-focused)
- Freshness (updated when code changes)
- VISION.md references where applicable
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
import yaml
from datetime import datetime


class ValidationResult:
    """Result of a documentation validation check."""

    def __init__(self, file_path: Path, passed: bool, errors: List[str], warnings: List[str]):
        self.file_path = file_path
        self.passed = passed
        self.errors = errors
        self.warnings = warnings


class DocumentationValidator:
    """Validates CLAUDE.md files against schema and problem-focused standards."""

    # Feature-focused phrases that should be avoided
    FEATURE_FOCUSED_PATTERNS = [
        (r"^Provides\s", "Start with the problem solved, not what it provides"),
        (r"^Implements\s", "Explain why it's needed, not just that it implements something"),
        (r"^Contains\s", "Describe the problem addressed, not just contents"),
        (r"^This module has\s", "Focus on problems solved, not features listed"),
        (r"See \[README\.md\].*for full documentation\.$", "Documentation should be self-contained, not just redirect to README"),
    ]

    # Required front matter fields
    REQUIRED_FIELDS = ["purpose", "problem_solved", "keywords", "task_types"]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[ValidationResult] = []

    def validate_all(self) -> List[ValidationResult]:
        """Validate all CLAUDE.md files in the project."""
        claude_files = list(self.project_root.glob("**/CLAUDE.md"))

        for claude_file in claude_files:
            result = self.validate_file(claude_file)
            self.results.append(result)

        return self.results

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single CLAUDE.md file."""
        errors = []
        warnings = []

        try:
            content = file_path.read_text()

            # Extract front matter and body
            front_matter, body = self._extract_front_matter(content)

            if front_matter is None:
                errors.append("Missing or malformed YAML front matter")
                return ValidationResult(file_path, False, errors, warnings)

            # Validate front matter fields
            field_errors, field_warnings = self._validate_front_matter(front_matter)
            errors.extend(field_errors)
            warnings.extend(field_warnings)

            # Validate body for feature-focused language
            language_errors = self._validate_language(body)
            errors.extend(language_errors)

            # Check for VISION.md references if solving known problems
            vision_warnings = self._check_vision_references(body, front_matter)
            warnings.extend(vision_warnings)

            # Check freshness (if related code files modified recently)
            freshness_warnings = self._check_freshness(file_path)
            warnings.extend(freshness_warnings)

        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")

        passed = len(errors) == 0
        return ValidationResult(file_path, passed, errors, warnings)

    def _extract_front_matter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML front matter and body from content."""
        # Front matter is between --- delimiters at start of file
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return None, content

        front_matter_text = match.group(1)
        body = match.group(2)

        try:
            front_matter = yaml.safe_load(front_matter_text)
            return front_matter, body
        except yaml.YAMLError:
            return None, body

    def _validate_front_matter(self, front_matter: Dict) -> Tuple[List[str], List[str]]:
        """Validate front matter has required fields and correct structure."""
        errors = []
        warnings = []

        # Check for context section
        if "context" not in front_matter:
            errors.append("Missing 'context' section in front matter")
            return errors, warnings

        context = front_matter["context"]

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in context:
                errors.append(f"Missing required field 'context.{field}'")

        # Validate field types
        if "keywords" in context and not isinstance(context["keywords"], list):
            errors.append("'context.keywords' must be a list")

        if "task_types" in context and not isinstance(context["task_types"], list):
            errors.append("'context.task_types' must be a list")

        # Check for empty values
        if "purpose" in context and not context["purpose"]:
            warnings.append("'context.purpose' should not be empty")

        if "problem_solved" in context and not context["problem_solved"]:
            warnings.append("'context.problem_solved' should not be empty")

        return errors, warnings

    def _validate_language(self, body: str) -> List[str]:
        """Check for feature-focused language patterns."""
        errors = []

        # Get first non-empty line after title (skip # heading)
        lines = [line.strip() for line in body.split("\n") if line.strip()]
        purpose_section_started = False

        for line in lines:
            # Look for Purpose section
            if line.startswith("## Purpose"):
                purpose_section_started = True
                continue

            # Check first paragraph after Purpose heading
            if purpose_section_started and line and not line.startswith("#"):
                for pattern, message in self.FEATURE_FOCUSED_PATTERNS:
                    if re.search(pattern, line):
                        errors.append(f"Feature-focused language detected: '{line[:50]}...' - {message}")
                break

        return errors

    def _check_vision_references(self, body: str, front_matter: Dict) -> List[str]:
        """Check if documentation references VISION.md for known problems."""
        warnings = []

        context = front_matter.get("context", {})
        problem_solved = context.get("problem_solved", "")

        # If problem_solved mentions framework problems but no VISION.md reference
        framework_problem_keywords = [
            "workflow fragility",
            "memory limitations",
            "context overload",
            "missing human intent",
            "tasks reported complete",
            "artifact pollution"
        ]

        mentions_problem = any(keyword in problem_solved.lower() for keyword in framework_problem_keywords)
        has_vision_ref = "VISION.md" in body or "vision.md" in body.lower()

        if mentions_problem and not has_vision_ref:
            warnings.append("Mentions framework problem but missing VISION.md reference")

        return warnings

    def _check_freshness(self, claude_file: Path) -> List[str]:
        """Check if CLAUDE.md is stale compared to related code files."""
        warnings = []

        # Get directory containing this CLAUDE.md
        directory = claude_file.parent

        # Find Python files in same directory
        py_files = list(directory.glob("*.py"))

        if not py_files:
            return warnings

        # Get modification times
        claude_mtime = claude_file.stat().st_mtime
        newest_py_mtime = max(f.stat().st_mtime for f in py_files)

        # If any Python file is newer than CLAUDE.md by more than 7 days, warn
        time_diff_days = (newest_py_mtime - claude_mtime) / (60 * 60 * 24)

        if time_diff_days > 7:
            newest_py_file = max(py_files, key=lambda f: f.stat().st_mtime)
            warnings.append(
                f"Potentially stale: {newest_py_file.name} modified {int(time_diff_days)} days after CLAUDE.md"
            )

        return warnings

    def print_report(self):
        """Print validation report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print("\n" + "=" * 80)
        print("DOCUMENTATION VALIDATION REPORT")
        print("=" * 80)
        print(f"\nTotal files: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")

        if failed > 0:
            print("\n" + "-" * 80)
            print("FAILURES:")
            print("-" * 80)

            for result in self.results:
                if not result.passed:
                    rel_path = result.file_path.relative_to(self.project_root)
                    print(f"\n📄 {rel_path}")

                    for error in result.errors:
                        print(f"   ❌ {error}")

                    if result.warnings:
                        for warning in result.warnings:
                            print(f"   ⚠️  {warning}")

        # Print warnings for passed files
        warnings_exist = any(r.warnings for r in self.results if r.passed)
        if warnings_exist:
            print("\n" + "-" * 80)
            print("WARNINGS (passed with warnings):")
            print("-" * 80)

            for result in self.results:
                if result.passed and result.warnings:
                    rel_path = result.file_path.relative_to(self.project_root)
                    print(f"\n📄 {rel_path}")
                    for warning in result.warnings:
                        print(f"   ⚠️  {warning}")

        print("\n" + "=" * 80)

        if failed == 0:
            print("✅ All documentation validates successfully!")
        else:
            print(f"❌ Fix {failed} file(s) and run 'trustable-ai validate --docs' again.")
        print("=" * 80 + "\n")


def validate_documentation(project_root: Path = None) -> int:
    """
    Validate all CLAUDE.md files in the project.

    Returns:
        int: Exit code (0 if all pass, 1 if any fail)
    """
    if project_root is None:
        project_root = Path.cwd()

    validator = DocumentationValidator(project_root)
    validator.validate_all()
    validator.print_report()

    # Exit code: 0 if all passed, 1 if any failed
    return 0 if all(r.passed for r in validator.results) else 1
