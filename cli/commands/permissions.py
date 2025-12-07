"""
Permissions command - validates Claude Code permissions configuration.

Validates .claude/settings.local.json permissions structure and content.
"""
import click
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any

from cli.platform_detector import PlatformDetector


class PermissionsValidator:
    """
    Validate Claude Code permissions configuration.

    Responsibilities:
    - Load and validate permissions file structure
    - Check for invalid command patterns
    - Detect duplicates across allow/deny/ask lists
    - Warn about unsafe or overly permissive patterns
    - Provide actionable recommendations for fixes
    """

    def __init__(self):
        """Initialize validator with platform detector."""
        self._detector = PlatformDetector()
        self._platform_info = self._detector.detect_platform()

    def validate_file(self, settings_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate permissions configuration file.

        Args:
            settings_path: Path to .claude/settings.local.json

        Returns:
            Tuple of (is_valid, errors, warnings):
                - is_valid: True if no critical errors found
                - errors: List of error messages
                - warnings: List of warning messages

        Examples:
            >>> validator = PermissionsValidator()
            >>> is_valid, errors, warnings = validator.validate_file(Path(".claude/settings.local.json"))
            >>> if not is_valid:
            ...     print(f"Errors: {errors}")
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check if file exists
        if not settings_path.exists():
            errors.append(f"Permissions file not found: {settings_path}")
            return False, errors, warnings

        # Load and parse JSON
        try:
            with settings_path.open("r") as f:
                settings = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in permissions file: {e}")
            return False, errors, warnings
        except (IOError, OSError) as e:
            errors.append(f"Failed to read permissions file: {e}")
            return False, errors, warnings

        # Validate structure
        structure_valid, structure_errors = self._validate_structure(settings)
        errors.extend(structure_errors)

        if not structure_valid:
            # Can't continue without valid structure
            return False, errors, warnings

        permissions = settings["permissions"]

        # Validate pattern formats
        format_errors, format_warnings = self._validate_pattern_formats(permissions)
        errors.extend(format_errors)
        warnings.extend(format_warnings)

        # Check for duplicates
        duplicate_warnings = self._check_duplicates(permissions)
        warnings.extend(duplicate_warnings)

        # Check for conflicts (same pattern in multiple lists)
        conflict_errors = self._check_conflicts(permissions)
        errors.extend(conflict_errors)

        # Check for unsafe patterns
        unsafe_warnings = self._check_unsafe_patterns(permissions)
        warnings.extend(unsafe_warnings)

        # Check for overly permissive patterns
        permissive_warnings = self._check_overly_permissive(permissions)
        warnings.extend(permissive_warnings)

        # Overall validation result
        is_valid = len(errors) == 0

        return is_valid, errors, warnings

    def _validate_structure(self, settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate permissions file structure.

        Args:
            settings: Loaded settings dict

        Returns:
            Tuple of (is_valid, errors)
        """
        errors: List[str] = []

        # Check for permissions key
        if "permissions" not in settings:
            errors.append("Missing 'permissions' key in settings file")
            return False, errors

        permissions = settings["permissions"]

        # Check for required fields
        required_fields = ["allow", "deny", "ask"]
        for field in required_fields:
            if field not in permissions:
                errors.append(f"Missing required field: permissions.{field}")

        if errors:
            return False, errors

        # Validate field types
        for field in required_fields:
            if not isinstance(permissions[field], list):
                errors.append(
                    f"Field permissions.{field} must be a list, got {type(permissions[field]).__name__}"
                )

        is_valid = len(errors) == 0
        return is_valid, errors

    def _validate_pattern_formats(
        self, permissions: Dict[str, List[str]]
    ) -> Tuple[List[str], List[str]]:
        """
        Validate that patterns use correct Claude Code format.

        Args:
            permissions: Permissions dict with allow/deny/ask lists

        Returns:
            Tuple of (errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []

        for list_name in ["allow", "deny", "ask"]:
            for i, pattern in enumerate(permissions[list_name]):
                if not isinstance(pattern, str):
                    errors.append(
                        f"Invalid pattern in {list_name} list at index {i}: {repr(pattern)} (must be string)"
                    )
                    continue

                # Check Claude Code format: Bash(command:*)
                if not pattern.startswith("Bash("):
                    warnings.append(
                        f"Pattern in {list_name} list may be invalid format: '{pattern}' "
                        f"(expected format: 'Bash(command:*)')"
                    )
                elif not pattern.endswith(":*)"):
                    warnings.append(
                        f"Pattern in {list_name} list may be invalid format: '{pattern}' "
                        f"(expected format: 'Bash(command:*)')"
                    )

        return errors, warnings

    def _check_duplicates(self, permissions: Dict[str, List[str]]) -> List[str]:
        """
        Check for duplicate patterns within each list.

        Args:
            permissions: Permissions dict with allow/deny/ask lists

        Returns:
            List of warning messages
        """
        warnings: List[str] = []

        for list_name in ["allow", "deny", "ask"]:
            patterns = permissions[list_name]
            seen: Set[str] = set()
            duplicates: Set[str] = set()

            for pattern in patterns:
                if pattern in seen:
                    duplicates.add(pattern)
                seen.add(pattern)

            for dup in sorted(duplicates):
                warnings.append(f"Duplicate pattern in {list_name} list: '{dup}'")

        return warnings

    def _check_conflicts(self, permissions: Dict[str, List[str]]) -> List[str]:
        """
        Check for patterns that appear in multiple lists (conflicts).

        Args:
            permissions: Permissions dict with allow/deny/ask lists

        Returns:
            List of error messages
        """
        errors: List[str] = []

        allow_set = set(permissions["allow"])
        deny_set = set(permissions["deny"])
        ask_set = set(permissions["ask"])

        # Check allow vs deny
        allow_deny_conflicts = allow_set & deny_set
        for pattern in sorted(allow_deny_conflicts):
            errors.append(
                f"Conflict: '{pattern}' appears in both allow and deny lists"
            )

        # Check allow vs ask
        allow_ask_conflicts = allow_set & ask_set
        for pattern in sorted(allow_ask_conflicts):
            errors.append(
                f"Conflict: '{pattern}' appears in both allow and ask lists"
            )

        # Check deny vs ask
        deny_ask_conflicts = deny_set & ask_set
        for pattern in sorted(deny_ask_conflicts):
            errors.append(
                f"Conflict: '{pattern}' appears in both deny and ask lists"
            )

        return errors

    def _check_unsafe_patterns(self, permissions: Dict[str, List[str]]) -> List[str]:
        """
        Check for unsafe patterns in allow list.

        Args:
            permissions: Permissions dict with allow/deny/ask lists

        Returns:
            List of warning messages
        """
        warnings: List[str] = []

        # Get dangerous patterns from platform detector
        dangerous_patterns = self._detector.get_dangerous_patterns()

        # Flatten all dangerous patterns
        all_dangerous: List[str] = []
        for category in dangerous_patterns.values():
            all_dangerous.extend(category)

        # Check if any dangerous patterns are in allow list
        for allowed_pattern in permissions["allow"]:
            # Skip non-string patterns (already reported as errors)
            if not isinstance(allowed_pattern, str):
                continue

            for dangerous_cmd in all_dangerous:
                if dangerous_cmd in allowed_pattern:
                    warnings.append(
                        f"Unsafe pattern in allow list: '{allowed_pattern}' "
                        f"(contains dangerous command: '{dangerous_cmd}')"
                    )
                    break

        return warnings

    def _check_overly_permissive(
        self, permissions: Dict[str, List[str]]
    ) -> List[str]:
        """
        Check for overly permissive patterns (wildcards, etc.).

        Args:
            permissions: Permissions dict with allow/deny/ask lists

        Returns:
            List of warning messages
        """
        warnings: List[str] = []

        # Patterns that should probably require approval
        should_ask = [
            "git push",
            "npm publish",
            "docker push",
            "kubectl apply",
            "terraform apply",
            "az webapp",
            "curl",
            "wget",
            "ssh",
        ]

        for pattern in permissions["allow"]:
            # Skip non-string patterns (already reported as errors)
            if not isinstance(pattern, str):
                continue

            for risky_cmd in should_ask:
                if risky_cmd in pattern:
                    warnings.append(
                        f"Overly permissive pattern in allow list: '{pattern}' "
                        f"(consider moving to ask list for approval)"
                    )
                    break

        return warnings

    def get_permission_counts(self, settings_path: Path) -> Dict[str, int]:
        """
        Get counts of permissions in each category.

        Args:
            settings_path: Path to settings.local.json

        Returns:
            Dict with counts: {"allow": N, "deny": M, "ask": K}
        """
        counts = {"allow": 0, "deny": 0, "ask": 0}

        if not settings_path.exists():
            return counts

        try:
            with settings_path.open("r") as f:
                settings = json.load(f)

            if "permissions" in settings:
                permissions = settings["permissions"]
                counts["allow"] = len(permissions.get("allow", []))
                counts["deny"] = len(permissions.get("deny", []))
                counts["ask"] = len(permissions.get("ask", []))
        except (json.JSONDecodeError, IOError, KeyError):
            # Return zeros on error
            pass

        return counts


@click.command(name="validate")
@click.option(
    "--settings-path",
    type=click.Path(exists=False, path_type=Path),
    default=None,
    help="Path to settings.local.json (default: .claude/settings.local.json)",
)
def validate_permissions(settings_path: Path = None):
    """
    Validate Claude Code permissions configuration.

    Checks .claude/settings.local.json for:
    - Valid JSON structure
    - Required fields (allow, deny, ask)
    - Invalid command patterns
    - Duplicate patterns
    - Conflicts (pattern in multiple lists)
    - Unsafe or overly permissive patterns

    Returns exit code 0 if valid, 1 if warnings found, 2 if errors found.

    Examples:
        trustable-ai permissions validate
        trustable-ai permissions validate --settings-path custom/settings.json
    """
    import sys

    # Determine settings path
    if settings_path is None:
        settings_path = Path.cwd() / ".claude" / "settings.local.json"

    click.echo("\n🔍 Validating permissions configuration...\n")

    # Check if file exists
    if not settings_path.exists():
        click.echo(f"❌ Permissions file not found: {settings_path}")
        click.echo("\n💡 Run 'trustable-ai init' to generate permissions configuration.\n")
        sys.exit(2)

    click.echo(f"✅ Permissions file found: {settings_path}")

    # Validate
    validator = PermissionsValidator()
    is_valid, errors, warnings = validator.validate_file(settings_path)

    # Get permission counts
    counts = validator.get_permission_counts(settings_path)

    # Display results
    if is_valid and not warnings:
        click.echo("✅ Valid JSON structure")
        click.echo("✅ All required fields present")
        click.echo("")
        click.echo("📊 Validation Results:")
        click.echo(f"   - Auto-approved (allow): {counts['allow']} commands")
        click.echo(f"   - Require approval (ask): {counts['ask']} commands")
        click.echo(f"   - Denied: {counts['deny']} commands")
        click.echo("")
        click.echo("✅ No issues found!")
        click.echo("")
        sys.exit(0)

    # Display structure validation
    if is_valid:
        click.echo("✅ Valid JSON structure")
        click.echo("✅ All required fields present")
    else:
        click.echo("❌ Invalid permissions structure")

    # Display counts if structure is valid
    if is_valid:
        click.echo("")
        click.echo("📊 Validation Results:")
        click.echo(f"   - Auto-approved (allow): {counts['allow']} commands")
        click.echo(f"   - Require approval (ask): {counts['ask']} commands")
        click.echo(f"   - Denied: {counts['deny']} commands")

    # Display errors
    if errors:
        click.echo("")
        click.echo("❌ Errors:")
        for error in errors:
            click.echo(f"   - {error}")

    # Display warnings
    if warnings:
        click.echo("")
        click.echo("⚠️  Warnings:")
        for warning in warnings:
            click.echo(f"   - {warning}")

    # Provide recommendations
    if errors or warnings:
        click.echo("")
        click.echo("💡 Recommendations:")
        if errors:
            click.echo("   - Fix errors before using permissions configuration")
            if any("Conflict" in e for e in errors):
                click.echo("   - Remove conflicting patterns from one of the lists")
            if any("Missing" in e for e in errors):
                click.echo("   - Add missing required fields to permissions configuration")

        if warnings:
            if any("Duplicate" in w for w in warnings):
                click.echo("   - Remove duplicate patterns to clean up configuration")
            if any("Unsafe" in w for w in warnings):
                click.echo(
                    "   - Move unsafe patterns from 'allow' to 'ask' for approval"
                )
            if any("permissive" in w for w in warnings):
                click.echo(
                    "   - Review permissive patterns and consider requiring approval"
                )

        click.echo("")

    # Return appropriate exit code
    if errors:
        click.echo("Exit code: 2 (errors found)\n")
        sys.exit(2)
    elif warnings:
        click.echo("Exit code: 1 (warnings found)\n")
        sys.exit(1)
    else:
        click.echo("Exit code: 0 (valid)\n")
        sys.exit(0)


# Create permissions command group
@click.group(name="permissions")
def permissions_command():
    """
    Manage Claude Code permissions configuration.

    Permissions control which bash commands Claude Code can auto-approve vs require
    manual approval. This helps prevent destructive operations while allowing safe
    development workflows.
    """
    pass


# Register validate subcommand
permissions_command.add_command(validate_permissions)
