---
context:
  purpose: "Provides human-friendly interface to framework operations, preventing manual workflow errors and configuration mistakes"
  problem_solved: "Manually invoking framework operations is error-prone - wrong paths, missing dependencies, invalid config values, forgotten initialization steps. Without a CLI, users must remember dozens of commands and flags, leading to setup failures and workflow inconsistencies."
  keywords: [cli, command-line, interface, trustable-ai, initialization, validation]
  task_types: [implementation, cli, tooling]
  priority: medium
  max_tokens: 600
  children: [commands]
  dependencies: [core, config, agents, workflows]
---
# CLI (Command Line Interface)

## Purpose

Solves **manual workflow invocation errors** and **configuration validation gaps**.

Without a CLI, users must:
- Remember exact paths for config files, agent templates, workflow templates
- Know correct sequence of initialization steps
- Manually validate configuration before running workflows
- Invoke Python modules directly with correct parameters
- Debug cryptic errors when setup is incomplete

**Manual invocation is error-prone.** Users forget steps, typo paths, miss validation, and workflows fail mysteriously.

The CLI provides a **single, validated entry point** for all framework operations with helpful error messages, validation, and guided setup.

## Key Commands

### `trustable-ai init`
**Problem Solved**: Manual project initialization forgets critical steps

Guides user through project setup: creates `.claude/` directory, generates `config.yaml` with prompts, sets up default agent/workflow templates.

**Real Failure Prevented**: User manually creates `.claude/config.yaml`, forgets required `work_tracking.organization` field. Workflows fail with "KeyError: organization". With `init`: prompts for all required fields, validates before writing, guaranteed valid config.

### `trustable-ai validate`
**Problem Solved**: Invalid configuration discovered during workflow execution (late failure)

Validates configuration against schema **before** workflows run. Catches missing fields, invalid values, incompatible combinations with actionable error messages.

**Real Failure Prevented**: User sets `test_coverage_min: "80"` (string, should be int). Sprint planning starts, runs for 20 minutes, crashes when comparing coverage. With `validate`: error caught in 2 seconds, fix immediately.

### `trustable-ai agent render-all`
**Problem Solved**: Agent templates not rendered with project-specific configuration

Renders all agent templates from `agents/templates/*.j2` to `.claude/agents/*.md` with project config (tech stack, quality standards) injected.

**Real Failure Prevented**: User enables business-analyst agent, forgets to render. Workflow tries to spawn `/business-analyst`, slash command doesn't exist. With `render-all`: renders all enabled agents, ensures slash commands available.

### `trustable-ai workflow render-all`
**Problem Solved**: Workflow templates not rendered with project-specific configuration

Renders all workflow templates from `workflows/templates/*.j2` to `.claude/commands/*.md` with project config injected.

**Real Failure Prevented**: User updates `config.yaml` with new quality standards, forgets to re-render workflows. Workflows use old standards, tests pass with 60% coverage (should be 80%). With `render-all`: re-render workflows, new standards enforced.

### `trustable-ai doctor`
**Problem Solved**: Framework dependencies or configuration issues hard to diagnose

Runs health check: verifies CLI installation, checks Azure CLI auth, validates config, confirms agents/workflows rendered, reports issues.

**Real Failure Prevented**: Workflows fail with "Azure CLI not found". User debugs for hour. With `doctor`: "❌ Azure CLI not installed or not in PATH. Install: pip install azure-cli".

## CLI to SDLC Workflow Mapping

The CLI exposes framework operations that map directly to SDLC workflows:

| CLI Command | SDLC Workflow | Purpose |
|-------------|---------------|---------|
| `trustable-ai init` | Project Setup | Initialize framework in project |
| `trustable-ai validate` | Configuration Validation | Check config before workflows |
| `trustable-ai agent render-all` | Agent Provisioning | Make agents available in Claude Code |
| `trustable-ai workflow render-all` | Workflow Provisioning | Make workflows available as slash commands |
| `trustable-ai configure azure-devops` | Work Tracking Setup | Connect to Azure DevOps |
| `trustable-ai configure file-based` | Work Tracking Setup | Use local file-based tracking |

**Workflow in Claude Code** (runs after CLI setup):
- `/sprint-planning` - Plan sprint with agent orchestration
- `/backlog-grooming` - Break Features into User Stories
- `/daily-standup` - Generate daily progress report
- `/sprint-execution` - Monitor sprint progress

## Design Principle: Assume Failure

The CLI embodies **Design Principle #1: Assume Failure** from VISION.md.

Users will:
- Typo configuration values
- Forget required fields
- Run commands in wrong order
- Use outdated templates
- Have missing dependencies

**CLI assumes these failures happen** and catches them:

```bash
$ trustable-ai validate

❌ Configuration validation failed:
   - work_tracking.organization: Required field missing
   - quality_standards.test_coverage_min: Must be integer, got string "80"
   - agent_config.enabled_agents: Unknown agent "business-analystt" (did you mean "business-analyst"?)

Fix these errors and run 'trustable-ai validate' again.
```

**Fail-fast principle**: Catch errors in seconds during validation, not minutes/hours during workflow execution.

## Command Structure

All commands follow consistent structure:

```bash
trustable-ai <command> [subcommand] [options] [arguments]
```

**Examples:**
```bash
# Top-level commands
trustable-ai init
trustable-ai validate
trustable-ai doctor

# Subcommands with options
trustable-ai agent render business-analyst --show
trustable-ai agent render-all
trustable-ai agent list

trustable-ai workflow render sprint-planning --output sprint.md
trustable-ai workflow render-all

trustable-ai configure azure-devops
trustable-ai configure file-based

trustable-ai state list
trustable-ai state resume <workflow-id>
```

## Help and Error Messages

CLI provides actionable help:

```bash
$ trustable-ai agent render business-analyst

Error: Agent template not found: business-analyst.j2

Possible causes:
  1. Agent name typo (check with: trustable-ai agent list)
  2. Agent template missing in agents/templates/
  3. Agent not enabled in .claude/config.yaml

Enable agent:
  1. Edit .claude/config.yaml
  2. Add 'business-analyst' to agent_config.enabled_agents
  3. Run: trustable-ai agent render business-analyst
```

**No cryptic errors.** CLI translates technical failures into user-actionable steps.

## Usage

### Initial Setup

```bash
# 1. Initialize project
trustable-ai init

# 2. Configure work tracking
trustable-ai configure azure-devops  # or file-based

# 3. Validate configuration
trustable-ai validate

# 4. Render agents and workflows
trustable-ai agent render-all
trustable-ai workflow render-all

# 5. Health check
trustable-ai doctor
```

### Iterative Development

```bash
# Update config
vim .claude/config.yaml

# Validate changes
trustable-ai validate

# Re-render (pick up config changes)
trustable-ai agent render-all
trustable-ai workflow render-all
```

### Workflow Management

```bash
# List incomplete workflows
trustable-ai state list

# Resume interrupted workflow
trustable-ai state resume sprint-planning-001
```

## Important Notes

- **All commands validate before executing**: Prevents invalid operations
- **Exit codes**: 0 = success, non-zero = failure (script-friendly)
- **Colored output**: Errors in red, success in green, warnings in yellow (TTY-aware)
- **Progress indicators**: Long operations show progress, not silent
- **Dry-run mode**: Many commands support `--dry-run` to preview without changes

## Real Failure Scenarios Prevented

### Scenario 1: User Forgets Initialization Step
**Without CLI**: User creates `.claude/` directory manually, forgets to create `config.yaml`. Workflows fail: "FileNotFoundError: .claude/config.yaml". User confused, doesn't know what's required.

**With CLI**: `trustable-ai init` guides through all steps, creates all required files, validates setup. Can't forget steps because CLI enforces sequence.

### Scenario 2: Configuration Invalid But Not Caught Until Workflow
**Without CLI**: User sets `test_coverage_min: 105` (>100, invalid). Sprint planning runs for 25 minutes (multiple agents), crashes when checking coverage. 25 minutes wasted.

**With CLI**: `trustable-ai validate` catches invalid value in 2 seconds: "test_coverage_min must be 0-100, got 105". Fix immediately, re-validate, proceed.

### Scenario 3: Templates Not Rendered After Config Change
**Without CLI**: User updates quality standards in config, forgets to re-render agents. Agents use old standards (cached from previous render). Tests pass with 60% coverage, should fail at 80%.

**With CLI**: After config change, `trustable-ai validate` warns: "⚠️  Config changed since last render. Run 'trustable-ai agent render-all'". User re-renders, new standards enforced.

## Related

- **VISION.md**: Design Principle #1 (Assume Failure)
- **cli/commands/**: Individual command implementations
- **config/CLAUDE.md**: Configuration that CLI validates
- **agents/**: Agents that CLI renders
- **workflows/**: Workflows that CLI renders
