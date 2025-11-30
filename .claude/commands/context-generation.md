# Context Generation Workflow

Generate hierarchical CLAUDE.md documentation structure for Trusted AI Development Workbench.

## Purpose

This workflow analyzes the repository structure and creates CLAUDE.md files at key directories to provide optimal context for Claude Code sessions.

## Prerequisites

1. Repository should be initialized with `taid init`
2. Run `taid context generate --dry-run` first to see the plan

## Workflow Steps

### Step 1: Analyze Repository Structure

First, analyze the repository to understand its structure:

```bash
# Generate initial CLAUDE.md structure
taid context generate --dry-run
```

Review the output to see which directories will be documented.

### Step 2: Generate Base CLAUDE.md Files

Generate the initial CLAUDE.md templates:

```bash
taid context generate
```

This creates template CLAUDE.md files in key directories.

### Step 3: Enhance Root CLAUDE.md

The root CLAUDE.md should contain:

1. **Project Overview**: What this project does
2. **Architecture**: High-level architecture diagram/description
3. **Key Components**: Main modules and their responsibilities
4. **Development Setup**: How to set up the development environment
5. **Coding Standards**: Project-specific conventions
6. **Important Decisions**: Key architectural decisions and rationale

**Task for Claude:** Read the existing root CLAUDE.md and enhance it with project-specific details by analyzing:
- README.md
- Package configuration files (pyproject.toml, package.json, etc.)
- Main entry points
- Configuration files

### Step 4: Enhance Directory-Level CLAUDE.md Files

For each directory with a CLAUDE.md, enhance it with:

1. **Module Purpose**: What this directory/module is responsible for
2. **Key Files**: Important files and their roles
3. **Dependencies**: What this module depends on
4. **Dependents**: What depends on this module
5. **Patterns**: Coding patterns used in this module
6. **Testing**: How to test this module

**Task for Claude:** For each generated CLAUDE.md:
1. Read the template content
2. Analyze the actual code in that directory
3. Add specific documentation about the code's purpose and usage
4. Document any non-obvious patterns or conventions

### Step 5: Add Cross-References

Ensure CLAUDE.md files reference each other appropriately:
- Root should link to key subdirectories
- Subdirectories should reference parent context when relevant
- Related modules should cross-reference each other

### Step 6: Validate Context Hierarchy

```bash
# Build the context index
taid context index

# Verify all CLAUDE.md files are indexed
taid context show
```

### Step 7: Test Context Loading

Test that context is loaded correctly for different tasks:

```bash
# Test context lookup for various tasks
taid context lookup "implement new API endpoint"
taid context lookup "write tests for user service"
taid context lookup "deploy to production"
```

## Output Structure

After completion, your repository should have:

```
project/
├── CLAUDE.md                    # Root context (project overview)
├── src/
│   ├── CLAUDE.md               # Source code context
│   ├── api/
│   │   └── CLAUDE.md           # API-specific context
│   ├── services/
│   │   └── CLAUDE.md           # Services context
│   └── models/
│       └── CLAUDE.md           # Data models context
├── tests/
│   └── CLAUDE.md               # Testing context
├── terraform/
│   └── CLAUDE.md               # Infrastructure context
└── .claude/
    └── context-index.yaml      # Context index for fast lookup
```

## Best Practices for CLAUDE.md Content

1. **Be Specific**: Generic content doesn't help. Include actual file names, function names, patterns.

2. **Stay Current**: Update CLAUDE.md when making significant changes to a module.

3. **Focus on "Why"**: Code shows "what" and "how". CLAUDE.md should explain "why".

4. **Include Examples**: Show example usage, common patterns, typical workflows.

5. **Document Gotchas**: Known issues, workarounds, things that surprised you.

6. **Keep It Scannable**: Use headers, bullet points, code blocks. Claude needs to quickly find relevant info.

## Configuration Used

- **Project**: Trusted AI Development Workbench
- **Type**: library
- **Languages**: Python

## Success Criteria

- [ ] Root CLAUDE.md contains project-specific information (not just template)
- [ ] Each key directory has a CLAUDE.md with actual content about that code
- [ ] Context index is built and working
- [ ] Context lookup returns relevant files for common tasks