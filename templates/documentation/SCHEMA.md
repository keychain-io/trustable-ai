# CLAUDE.md Documentation Schema

## Purpose

This schema defines the structure and requirements for CLAUDE.md files throughout the Trustable AI Workbench codebase. These files provide context to AI agents working on the project.

## Front Matter Schema

Every CLAUDE.md file must include YAML front matter with the following structure:

```yaml
---
context:
  # Brief description of what problems this module/component solves (REQUIRED)
  # Should be problem-focused, not feature-focused
  # Example: "Solves workflow fragility and memory limitations"
  purpose: string

  # What specific problem(s) does this component solve? (REQUIRED)
  # Reference problems from VISION.md where applicable
  # Example: "Prevents AI agents from skipping tasks by enforcing verification"
  problem_solved: string

  # Search keywords for context loading (REQUIRED)
  # Used by context loaders to find relevant documentation
  # Example: [state, checkpoint, recovery, workflow]
  keywords: [string, ...]

  # Types of tasks this context is relevant for (REQUIRED)
  # Example: [implementation, debugging, architecture]
  task_types: [string, ...]

  # Priority level for context loading: high, medium, low (OPTIONAL, default: medium)
  priority: string

  # Maximum tokens to allocate when loading this context (OPTIONAL, default: 600)
  max_tokens: integer

  # Child modules/components (OPTIONAL)
  # Example: [state_manager, profiler, context_loader]
  children: [string, ...]

  # Dependencies this component relies on (OPTIONAL)
  # Example: [core, config]
  dependencies: [string, ...]
---
```

### Required Fields

1. **purpose** (string): Brief description of what problems this module solves
   - Must be problem-focused (what pain does it address?)
   - Should reference VISION.md problems when applicable
   - 1-2 sentences maximum

2. **problem_solved** (string): Detailed explanation of the specific problem(s) solved
   - Why does this component exist?
   - What would break or fail without it?
   - Link to VISION.md problem pillars when relevant

3. **keywords** (array of strings): Search terms for context loading
   - Include technical terms, domain concepts, and functionality keywords
   - Used by `core/context_loader.py` to match tasks to relevant context
   - 3-10 keywords recommended

4. **task_types** (array of strings): Types of tasks this context helps with
   - Common values: `implementation`, `debugging`, `testing`, `architecture`, `documentation`, `refactoring`
   - Used to load context only when relevant to the current task type

### Optional Fields

5. **priority** (string): Context loading priority
   - Values: `high`, `medium`, `low`
   - Default: `medium`
   - High-priority contexts load first when token budget is limited

6. **max_tokens** (integer): Token budget for this context
   - Default: 600
   - Larger modules may need more tokens (800-1000)
   - Leaf nodes may need fewer (400-600)

7. **children** (array of strings): Sub-components or sub-modules
   - Used to understand module hierarchy
   - Example: `core` has children `[state_manager, profiler, context_loader]`

8. **dependencies** (array of strings): Other modules this depends on
   - Helps AI understand what needs to be loaded together
   - Example: `agents` depends on `[core, config]`

## Document Body Structure

After the front matter, the document body should follow this structure:

### 1. Title (H1)
The module/component name

### 2. Purpose Section (H2)
**Problem-Focused Format:**
- Start with the problem this solves
- Then explain how it solves it
- Reference VISION.md problems where applicable

**Example:**
```markdown
## Purpose

Solves **workflow fragility** and **memory limitations** (VISION.md Problems #3, #4) by persisting workflow state to disk, enabling checkpointing and recovery.

Without state management, long-running workflows fail unpredictably when sessions timeout or context windows overflow. State persistence makes workflow progress recoverable and verifiable.
```

### 3. Key Components Section (H2) (Optional)
List major sub-components with brief descriptions

### 4. Architecture Section (H2) (Optional)
How the component fits into the larger system

### 5. Usage Section (H2)
How to use this component, with code examples

### 6. Important Notes Section (H2) (Optional)
Critical information, gotchas, or best practices

## Problem-Focused vs Feature-Focused Documentation

### ❌ Feature-Focused (What it does)
```markdown
## Purpose

Provides state management for workflows. Saves workflow state to JSON files in `.claude/workflow-state/`. Supports resume functionality.
```

**Problem**: Doesn't explain WHY state management exists or what problem it solves.

### ✅ Problem-Focused (Why it exists)
```markdown
## Purpose

Solves **workflow fragility** (VISION.md Problem #5) - long-running workflows fail unpredictably when sessions timeout or token limits are hit, losing all progress.

State management persists workflow progress to `.claude/workflow-state/` after each step, enabling recovery from any checkpoint. This makes multi-step workflows reliable even when context windows overflow or sessions crash.
```

**Better**: Explains the problem (workflow fragility), the consequence (lost progress), and how this component solves it (checkpointing).

## Template Types

The following template types should be created in `templates/documentation/`:

1. **core-module.j2**: For core framework modules (state_manager, profiler, etc.)
2. **agent.j2**: For agent definitions
3. **workflow.j2**: For workflow definitions
4. **adapter.j2**: For platform adapters (Azure DevOps, Jira, etc.)
5. **config.j2**: For configuration modules
6. **skill.j2**: For reusable skills
7. **cli.j2**: For CLI command modules

Each template should:
- Include front matter schema
- Provide problem-focused structure
- Include placeholders for module-specific content
- Reference VISION.md problems where applicable

## Validation

Schema validation should detect:

1. **Missing Required Fields**: `purpose`, `problem_solved`, `keywords`, `task_types`
2. **Feature-Focused Language**: Detection of phrases like "provides", "implements", "has" without explaining why
3. **Missing VISION.md References**: When a component solves a known problem but doesn't reference VISION.md
4. **Empty Sections**: Required sections that exist but have no content beyond "See README.md"

Validation implementation should be added to CLI: `trustable-ai validate documentation`

## Examples

See existing CLAUDE.md files for examples:
- `.claude/CLAUDE.md` - High-level framework context
- `core/CLAUDE.md` - Core module context (needs enhancement per Task 1005)
- `agents/CLAUDE.md` - Agent system context

## Related

- **VISION.md**: Defines the problems the framework solves (foundation document)
- **Task 1005**: Enhance core module documentation using this schema
- **Task 1008**: Build validation tooling to enforce this schema
