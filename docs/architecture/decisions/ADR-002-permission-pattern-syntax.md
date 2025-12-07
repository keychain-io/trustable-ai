# ADR-002: Permission Pattern Syntax

**Date**: 2025-12-07
**Status**: Proposed
**Deciders**: Project Architect Agent, Engineering Team
**Related Features**: #1026 (Default safe-action permissions configuration)

---

## Context

The framework needs to define permission patterns in `.claude/settings.local.json` that auto-approve safe operations while requiring approval for destructive ones. These patterns must:
1. Work across platforms (Windows, Linux, macOS)
2. Be easy for users to understand and customize
3. Integrate with Claude Code's permission system
4. Support platform-specific command variations

We need to choose a pattern syntax that balances expressiveness, simplicity, and cross-platform compatibility.

---

## Decision

**Glob patterns with platform-specific variants.**

Permission patterns will use glob-style wildcards (`*`) for matching, with platform-specific pattern registries to handle cross-platform differences (e.g., `python` vs `python3`, path separators).

Example:
```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(python* -m pytest:*)",  // Matches python, python3, python3.9, etc.
      "Bash(az boards work-item create:*)"
    ]
  }
}
```

---

## Options Considered

### Option 1: Exact string match
**Description**: Permissions match commands exactly (no wildcards).

**Pros**:
- Simple, predictable
- No ambiguity
- Easy to debug

**Cons**:
- Too rigid (can't match variations like `python` vs `python3`)
- Requires many permission entries for similar commands
- Doesn't handle command arguments
- Poor user experience

**Example**:
```json
"allow": [
  "Bash(git status)",
  "Bash(git status -sb)",
  "Bash(git status --short)"  // Need separate entry for each variant
]
```

**Why not chosen**: Too inflexible. Users would need dozens of entries for common command variations.

---

### Option 2: Regular expressions
**Description**: Permissions use regex for pattern matching.

**Pros**:
- Very flexible and powerful
- Can express complex patterns
- Standard regex syntax

**Cons**:
- Complex, error-prone
- High learning curve for users
- Easy to create overly permissive patterns
- Difficult to validate correctness
- Performance overhead

**Example**:
```json
"allow": [
  "Bash(git (status|diff|log):.*)",
  "Bash(python[0-9.]* -m pytest:.*)"
]
```

**Why not chosen**: Too complex for typical users. Risk of creating insecure patterns (e.g., `Bash(git .*:.*)`  accidentally allows `git push --force`).

---

### Option 3: Glob patterns (current Claude Code convention) - CHOSEN
**Description**: Use glob-style wildcards (`*`, `?`) similar to shell patterns.

**Pros**:
- Consistent with Claude Code's existing permission system
- Familiar to developers (shell wildcards)
- Simple enough for non-experts
- Covers 90% of use cases
- Lower risk of overly permissive patterns

**Cons**:
- Limited expressiveness (can't do alternation like `(a|b)`)
- May need multiple entries for complex patterns
- Platform differences require variant handling

**Example**:
```json
"allow": [
  "Bash(git status:*)",
  "Bash(python* -m pytest:*)",
  "Bash(az boards work-item create:*)"
]
```

**Why chosen**: Best balance of simplicity, familiarity, and safety. Consistent with Claude Code conventions. Platform variants handle cross-platform differences without regex complexity.

---

### Option 4: Custom DSL
**Description**: Create framework-specific permission language.

**Pros**:
- Tailored exactly to needs
- Can add domain-specific features
- Full control over syntax

**Cons**:
- Learning curve (new syntax)
- Maintenance burden
- Documentation overhead
- Reinventing the wheel

**Example**:
```
allow git.read_operations
allow work_tracking.crud except work_tracking.delete
```

**Why not chosen**: Unnecessary complexity. Glob patterns + platform variants solve the problem without inventing new syntax.

---

## Consequences

### Positive

- **Consistency**: Follows Claude Code's existing permission pattern syntax
- **Low learning curve**: Developers already know glob patterns from shell usage
- **Safety**: Harder to accidentally create overly permissive patterns
- **Platform support**: Variant system handles cross-platform differences cleanly
- **Extensibility**: Can add regex escape hatch later if needed for edge cases

### Negative

- **Limited expressiveness**: Can't do complex alternation without multiple entries
- **Platform variants**: Requires maintaining platform-specific pattern sets
- **Validation complexity**: Glob patterns can still be overly broad (e.g., `Bash(*:*)`)

### Risks

- **Risk**: Users create overly broad patterns (e.g., `Bash(az *:*)` allows all Azure CLI commands)
  - **Mitigation**: Validation command warns about promiscuous patterns, deny rules take precedence

- **Risk**: Platform detection incorrect → wrong patterns generated
  - **Mitigation**: Manual override option, validation command checks patterns match platform

- **Risk**: Glob patterns insufficient for complex use case
  - **Mitigation**: Future enhancement: regex escape hatch for advanced users

---

## Implementation Notes

### Platform-Specific Pattern Variants

```python
# cli/permissions_generator.py
COMMAND_PATTERNS = {
    "windows": {
        "python_test": "Bash(python -m pytest:*)",
        "git_status": "Bash(git status:*)",
    },
    "linux": {
        "python_test": "Bash(python3 -m pytest:*)",  // python3 on Linux
        "git_status": "Bash(git status:*)",
    },
    "macos": {
        "python_test": "Bash(python3 -m pytest:*)",
        "git_status": "Bash(git status:*)",
    }
}
```

### Validation Rules

```python
# cli/commands/validate.py
class PermissionsValidator:
    PROMISCUOUS_PATTERNS = [
        r"Bash\(\*:\*\)",  // Matches everything
        r"Bash\(az \*:\*\)",  // Matches all Azure CLI
        r"Bash\(git \*:\*\)",  // Matches all git (including push --force)
    ]

    def validate(self, patterns: List[str]) -> List[ValidationIssue]:
        issues = []
        for pattern in patterns:
            for promiscuous in self.PROMISCUOUS_PATTERNS:
                if re.match(promiscuous, pattern):
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        message=f"Overly broad pattern: {pattern}",
                        suggestion="Narrow to specific commands"
                    ))
        return issues
```

### Escape Hatch for Complex Patterns (Future)

```json
// If glob patterns prove insufficient, add regex support:
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",  // Glob (default)
      {"pattern": "Bash(python[0-9.]+ -m pytest:.*)", "type": "regex"}  // Regex escape hatch
    ]
  }
}
```

---

## Related Decisions

- Future: Permission deny rules precedence order
- Future: Permission validation strictness levels (warn vs error)

---

## Approval

- [ ] Engineering Team Review
- [ ] Test on Windows, Linux, macOS
- [ ] Security Review (promiscuous pattern detection)
