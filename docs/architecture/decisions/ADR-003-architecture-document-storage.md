# ADR-003: Architecture Document Storage Location

**Date**: 2025-12-07
**Status**: Proposed
**Deciders**: Project Architect Agent, Engineering Team
**Related Features**: #1027 (Enhance Artifact Flow: Embed Architecture Decisions in Work Items)

---

## Context

Architecture decisions from `/roadmap-planning` need to persist and flow through `/sprint-planning` to daily implementation. Currently, architectural decisions are not propagated, causing:
- Duplication: Architecture reviewed multiple times
- Inconsistency: Sprint decisions contradict roadmap architecture
- Lost context: Developers can't see original architecture during implementation

We need to decide **where to store** architecture documents so they:
1. Persist across workflow sessions
2. Are accessible to both humans and AI agents
3. Can be version controlled
4. Reference work items bidirectionally

---

## Decision

**Store architecture documents in the project repository under `docs/architecture/`.**

Architecture documents will be:
- Written to `docs/architecture/roadmap-{period}/`, `docs/architecture/sprint-{n}/`, `docs/architecture/decisions/`
- Committed to git after each workflow generates them
- Referenced from work items via comments containing file path + git commit SHA
- Loaded by downstream workflows from file system

---

## Options Considered

### Option 1: Work Item Attachments
**Description**: Upload architecture documents as attachments to Azure DevOps work items.

**Pros**:
- Close proximity to work items
- No git operations required
- Platform-managed storage

**Cons**:
- Large file size limits
- Azure-specific (not portable to Jira, GitHub)
- Difficult to version control
- No diff capability
- Requires platform-specific upload/download logic
- Not human-editable (locked in platform)

**Example**:
```python
adapter.upload_attachment(
    work_item_id=1001,
    file_path="epic-1001-architecture.md",
    file_content=architecture_doc
)
```

**Why not chosen**: Platform lock-in, no version control, poor diff/review experience. Architecture documents are too important to lock in a proprietary platform format.

---

### Option 2: State Files (`.claude/workflow-state/`)
**Description**: Save architecture documents alongside workflow state in `.claude/workflow-state/architecture/`.

**Pros**:
- Framework-managed location
- Already have state persistence infrastructure
- No git operations needed

**Cons**:
- Not human-readable location
- Lost during state cleanup (`trustable-ai state cleanup`)
- No version history
- Not accessible for PR reviews
- Hidden from developers (in .claude directory)
- Not part of code repository

**Example**:
```
.claude/workflow-state/
  architecture/
    roadmap-q1-2025/
      epic-1001-auth.md
```

**Why not chosen**: Architecture is too important to hide in state files. Needs to be version controlled, human-visible, and persistent.

---

### Option 3: Project Repo (`docs/architecture/`) - CHOSEN
**Description**: Store architecture documents in the project repository under standard `docs/` directory.

**Pros**:
- **Version controlled** with code (git history)
- **Human-readable** and editable (Markdown in docs/)
- **PR reviewable** (architecture changes reviewed with code)
- **Portable** (not tied to work tracking platform)
- **Standard location** (docs/ is conventional)
- **Persistent** (not deleted during cleanup)
- **Diffable** (git diff shows architecture evolution)

**Cons**:
- Requires git operations in workflows
- Increases repository size
- Commit discipline required (meaningful commit messages)

**Example**:
```
docs/architecture/
├── roadmap-q1-2025/
│   ├── epic-1001-auth-system.md
│   └── README.md
├── sprint-5/
│   ├── feature-oauth.md
│   └── README.md
└── decisions/
    └── ADR-001-auth-strategy.md
```

**Why chosen**: Architecture documents are first-class artifacts that should be version controlled alongside code. PR review process naturally includes architecture changes. Standard docs/ location is familiar to all developers.

---

### Option 4: Separate Documentation Repository
**Description**: Store architecture docs in a dedicated `architecture-docs` repository.

**Pros**:
- Clean separation of concerns
- Doesn't clutter code repository
- Can have different access control

**Cons**:
- Extra repository to manage
- Synchronization challenges (architecture versioning vs code versioning)
- Harder to ensure architecture-code consistency
- Additional clone/setup for developers
- Complexity for monorepo projects

**Why not chosen**: Architecture should evolve with code, not separately. Separate repo creates sync problems and adds management overhead.

---

## Consequences

### Positive

- **Version control**: Architecture evolution tracked in git history
- **PR review**: Architecture changes reviewed alongside code changes
- **Human accessible**: Developers read/edit Markdown files directly
- **Portable**: Not locked to Azure DevOps
- **Persistent**: Won't be deleted during workflow state cleanup
- **Standard**: `docs/` is conventional location for documentation
- **Diffable**: `git diff` shows architecture changes over time

### Negative

- **Repository size**: Large architecture documents increase repo size
- **Commit discipline**: Workflows must generate meaningful commit messages
- **Git operations**: Workflows must handle git add/commit correctly
- **Potential conflicts**: If architecture docs edited manually and by workflow simultaneously

### Risks

- **Risk**: Architecture documents drift from work item references
  - **Mitigation**: Store git commit SHA in work item comments, validation command checks integrity

- **Risk**: Large documents increase repo size significantly
  - **Mitigation**: Use concise Markdown, link to external diagrams if needed, monitor repo size

- **Risk**: Git merge conflicts on architecture documents
  - **Mitigation**: Workflows always create new files (epic-{id}-{slug}.md), rarely update existing docs

- **Risk**: Accidental deletion or modification of architecture docs
  - **Mitigation**: Git history preserves all versions, workflows never delete docs

---

## Implementation Notes

### Directory Structure

```
docs/architecture/
├── index.yaml                          # Machine-readable index
├── README.md                           # Human-readable overview
├── roadmap-q1-2025/                    # Roadmap period
│   ├── README.md                       # Roadmap overview
│   ├── epic-1001-auth-system.md        # Epic architecture
│   └── epic-1002-reporting.md
├── sprint-5/                           # Sprint elaborations
│   ├── README.md                       # Sprint architecture summary
│   ├── feature-oauth.md                # Feature implementation details
│   └── feature-reports.md
└── decisions/                          # Architecture Decision Records
    ├── ADR-001-auth-strategy.md
    ├── ADR-002-database-choice.md
    └── index.md                        # ADR index
```

### Document Format

```markdown
---
id: epic-auth-system
type: epic
work_item_id: 1001
created_at: 2025-01-15T10:00:00Z
git_commit: abc123
status: approved
---

# Epic: Authentication System Architecture

## Context
[Why this architecture is needed]

## Decision
[What was decided]

## Rationale
[Why this approach]

## Consequences
[Implications]
```

### Git Integration in Workflows

```python
# workflows/templates/roadmap-planning.j2
from pathlib import Path
import subprocess

# Generate architecture document
arch_dir = Path("docs/architecture/roadmap-{period}")
arch_dir.mkdir(parents=True, exist_ok=True)
arch_file = arch_dir / f"epic-{epic_id}-{slug}.md"
arch_file.write_text(architecture_content)

# Git commit
subprocess.run(["git", "add", str(arch_file)])
subprocess.run([
    "git", "commit", "-m",
    f"Add architecture for Epic #{epic_id}: {epic_title}"
])
commit_sha = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True, text=True
).stdout.strip()

# Add reference to work item
adapter.add_architecture_reference(
    work_item_id=epic_id,
    doc_path=str(arch_file),
    git_commit=commit_sha
)
```

### Work Item Comment Format

```markdown
## Architecture Reference

**Document**: `docs/architecture/roadmap-q1-2025/epic-1001-auth-system.md`
**Commit**: `abc123def456`
**Type**: epic-architecture
**Workflow**: /roadmap-planning
**Date**: 2025-01-15T10:00:00Z

---
*Auto-generated by Trustable AI Workbench*
```

### Loading Architecture from File System

```python
# Sprint planning workflow
from pathlib import Path
import re

# Find architecture reference in Epic comments
comments = adapter.get_comments(epic_id)
arch_refs = [
    c for c in comments
    if "Architecture Reference" in c.get("text", "")
]

if arch_refs:
    # Extract file path from comment
    match = re.search(r'docs/architecture/[^\s]+\.md', arch_refs[0]["text"])
    if match:
        arch_file = Path(match.group(0))
        if arch_file.exists():
            prior_architecture = arch_file.read_text()
            # Inject into architect agent context
```

---

## Related Decisions

- **ADR-001**: Learnings Injection Strategy (similar file-based storage pattern)
- Future: Architecture document retention policy
- Future: Architecture diff/conflict resolution strategy

---

## Approval

- [ ] Engineering Team Review
- [ ] Confirm git operations in workflows don't cause performance issues
- [ ] Test architecture flow: roadmap → sprint → implementation
