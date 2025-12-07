# Architecture Planning Summary - QoL Improvements

**Date**: 2025-12-07
**Initiative**: QoL Improvements
**Features**: 4 (#1025, #1026, #1027, #1030)
**Architect**: Project Architect Agent (claude-opus-4)
**Workflow**: /architecture-planning

---

## Executive Summary

Successfully completed architecture planning for four Quality-of-Life improvement features targeting key usability and reliability gaps in the Trustable AI Development Workbench. The architecture integrates with existing infrastructure (state_manager, profiler, context loaders, skills system) without requiring fundamental changes to core components.

---

## Architecture Artifacts Created

### Main Design Document
- **File**: `docs/architecture/qol-improvements-design.md`
- **Commit**: `24b8de9224daf2b2716d1095732a9a0ad1d68191`
- **Sections**:
  - Executive Summary
  - System Architecture (mermaid diagrams)
  - Component Design (4 features)
  - Data Models & Schemas
  - API Specifications
  - Implementation Sequence
  - Technical Risk Assessment

### Architecture Decision Records (ADRs)
Four ADRs created in `docs/architecture/decisions/`:

1. **ADR-001: Learnings Injection Strategy**
   - Decision: Per-agent injection with category filtering and caching
   - Rationale: Balance relevance, performance, and flexibility
   - File: `docs/architecture/decisions/ADR-001-learnings-injection-strategy.md`

2. **ADR-002: Permission Pattern Syntax**
   - Decision: Glob patterns with platform-specific variants
   - Rationale: Standard, familiar, safe (consistent with Claude Code)
   - File: `docs/architecture/decisions/ADR-002-permission-pattern-syntax.md`

3. **ADR-003: Architecture Document Storage Location**
   - Decision: Project repo under `docs/architecture/`
   - Rationale: Version controlled, human-readable, PR reviewable
   - File: `docs/architecture/decisions/ADR-003-architecture-document-storage.md`

4. **ADR-004: Test Marker Taxonomy**
   - Decision: pytest.mark.* with standardized registry
   - Rationale: Standard pytest, IDE support, workflow integration
   - File: `docs/architecture/decisions/ADR-004-test-marker-taxonomy.md`

---

## Features Architected

### Feature #1025: Integrate Active Learnings Feedback Loop
**Problem**: Tool failures recur across sessions because learnings aren't automatically injected.

**Architecture**:
- **ErrorFailureDetector** (`core/error_detector.py`): Parse stderr, classify errors, detect learning-worthy patterns
- **LearningsContextInjector** (`core/learnings_injector.py`): Fetch category-filtered learnings, inject into agent contexts
- **Integration**: Extends AgentRegistry, StateManager, Profiler
- **Config**: Agent-category mapping in `.claude/config.yaml`

**Key Design**: Per-agent injection with 5-minute cache, max 1000 tokens per agent

---

### Feature #1026: Default Safe-Action Permissions Configuration
**Problem**: Excessive permission prompts for safe operations during workflows.

**Architecture**:
- **PlatformDetector** (`cli/platform_detector.py`): Detect OS, generate platform-specific patterns
- **PermissionsTemplateGenerator** (`cli/permissions_generator.py`): Generate `.claude/settings.local.json`
- **Integration**: CLI init command, validation command
- **Safe operations**: git read/local-commits, work item CRUD, file reads, test execution
- **Require approval**: git push, destructive ops, production deployments

**Key Design**: Glob patterns with platform variants (Windows/Linux/macOS)

---

### Feature #1027: Enhance Artifact Flow - Architecture Decisions
**Problem**: Architecture decisions from planning not propagated to implementation, causing duplication and inconsistency.

**Architecture**:
- **Document Storage**: `docs/architecture/roadmap-{period}/`, `docs/architecture/sprint-{n}/`, `docs/architecture/decisions/`
- **ArchitectureLoader** (`core/architecture_loader.py`): Load documents from file system, traverse work item hierarchy
- **Adapter Methods**: `add_comment()`, `get_comments()`, `get_parent_work_item()`, `add_architecture_reference()`
- **Workflow Integration**: Roadmap planning generates docs, sprint planning loads prior architecture, implementation loads full context

**Key Design**: Documents in git repo (version controlled), work items reference via comments with commit SHA

---

### Feature #1030: Test Classification Tags
**Problem**: Tests created without consistent classification, making targeted execution impossible.

**Architecture**:
- **TestMarkerRegistry** (`testing/markers.py`): Standard markers (test levels + test types)
- **pytest.ini**: Marker definitions for IDE support and validation
- **Agent Templates**: Updated to apply markers (tester, engineer agents)
- **CLI Command**: `trustable-ai test --type=security --level=unit`
- **Workflow Integration**: Workflow presets (sprint-execution runs unit+integration, release runs all)

**Key Design**: pytest.mark.* with registry, two dimensions (level: unit/integration/system, type: functional/security/performance)

---

## Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Learnings injection | Per-agent with caching | Relevance + performance balance |
| Permission patterns | Glob with platform variants | Standard, familiar, safe |
| Architecture storage | Project repo (`docs/architecture/`) | Version controlled, PR reviewable |
| Test markers | pytest.mark.* with registry | Standard pytest, IDE support |

---

## Technical Risks Identified

### High Severity
1. **Architecture Document Sync** (Feature #1027)
   - Risk: Documents drift from work item references
   - Mitigation: Store git SHA, validation command, clear errors

### Medium Severity
2. **Learnings Injection Performance** (Feature #1025)
   - Risk: Loading/filtering learnings adds latency
   - Mitigation: 5-minute cache, hard token limit, profiling metrics

3. **Permission Pattern Compatibility** (Feature #1026)
   - Risk: Platform-specific patterns incorrect
   - Mitigation: Extensive testing, conservative defaults, validation

4. **Azure CLI Error Pattern Changes** (Feature #1025)
   - Risk: Error patterns change with CLI updates
   - Mitigation: Pattern versioning, fallback to "general", quarterly review

### Low Severity
5. **Test Marker Enforcement Friction** (Feature #1030)
   - Risk: Marker requirements slow development
   - Mitigation: Start with warnings, auto-suggestion, escape hatch

---

## Security Requirements

1. **Permission System** (Feature #1026):
   - Deny list takes precedence over allow list
   - No wildcard patterns matching sensitive operations
   - Audit logging for all permission decisions

2. **Architecture Documents** (Feature #1027):
   - Documents in git (version controlled)
   - No executable code in architecture docs
   - References include commit SHA for verification

3. **Learnings Data** (Feature #1025):
   - Sanitize learnings before capture (remove tokens, paths, IDs)
   - Category-based access control for learnings

---

## Technology Stack Changes

**New Dependencies**: None (uses existing tech stack)

**New Components**:
- `core/error_detector.py`
- `core/learnings_injector.py`
- `core/architecture_loader.py`
- `cli/platform_detector.py`
- `cli/permissions_generator.py`
- `testing/markers.py`
- `pytest.ini` (generated during init)

**Modified Components**:
- `agents/registry.py` (learnings injection)
- `adapters/azure_devops/` (comment methods)
- `adapters/file_based/` (comment methods)
- `workflows/templates/roadmap-planning.j2` (architecture generation)
- `workflows/templates/sprint-planning.j2` (architecture loading)

---

## Implementation Readiness

- ✅ Architecture approved (self-approved in workflow)
- ✅ Security considerations documented
- ✅ Risks identified and mitigation strategies defined
- ✅ Work items updated with architecture references
- ✅ Architecture documents committed to git
- ⏸️ Human stakeholder approval pending
- ⏸️ Security review pending (low priority for internal QoL features)

---

## Implementation Sequence

### Phase 1: Foundation (Week 1-2)
1. **#1030: Test Classification Tags**
   - Self-contained, immediately useful
   - No dependencies
   - Provides foundation for testing other features

2. **#1026: Safe-Action Permissions**
   - Immediate UX improvement
   - No architectural changes
   - Independent of other features

### Phase 2: Core Enhancements (Week 3-4)
3. **#1025: Learnings Feedback Loop**
   - Most complex feature
   - Builds on existing LearningsSkill
   - Needs careful testing

### Phase 3: Integration (Week 5-6)
4. **#1027: Architecture Document Flow**
   - Most invasive (adapter extensions, workflow modifications)
   - Should be last to avoid blocking other work
   - Requires git operations in workflows

---

## Next Steps

1. **Review & Approval**:
   - [ ] Present architecture to stakeholders
   - [ ] Security review (if required for Features #1025, #1026)
   - [ ] Obtain approval to proceed

2. **Backlog Grooming**:
   - [ ] Run `/backlog-grooming` to break Features into Tasks
   - [ ] Create implementation tasks with architecture context
   - [ ] Estimate story points based on architecture complexity

3. **Sprint Planning**:
   - [ ] Assign Features to sprints per implementation sequence
   - [ ] Sprint 1: #1030 + #1026 (Foundation)
   - [ ] Sprint 2: #1025 (Core Enhancements)
   - [ ] Sprint 3: #1027 (Integration)

4. **Pre-Implementation**:
   - [ ] Review architecture docs before implementation
   - [ ] Set up test infrastructure for marker validation
   - [ ] Prepare platform detection test environment

---

## Metrics & Success Criteria

### Feature #1025: Learnings Feedback Loop
- **Metric**: Retry count reduction
- **Target**: 50% reduction in tool invocation retries
- **Measurement**: Profiler efficiency metrics

### Feature #1026: Safe-Action Permissions
- **Metric**: Permission prompt reduction
- **Target**: 80% reduction in unnecessary prompts
- **Measurement**: User experience survey

### Feature #1027: Architecture Document Flow
- **Metric**: Architecture review duplication
- **Target**: Zero duplicate architecture reviews
- **Measurement**: Workflow profiling (architect agent calls)

### Feature #1030: Test Classification Tags
- **Metric**: Workflow test execution time
- **Target**: 30% faster sprint-execution (run only unit+integration)
- **Measurement**: pytest execution time

---

## Conclusion

Architecture planning completed successfully for QoL Improvements initiative. All four features have clear architectural designs, documented risks, and implementation sequences. The architecture maintains backward compatibility while progressively enhancing framework reliability and developer experience.

**Recommendation**: Proceed to `/backlog-grooming` to create implementation tasks with architecture context.

---

*Generated by Trustable AI Workbench - /architecture-planning workflow*
*Architect: Project Architect Agent (claude-opus-4)*
*Date: 2025-12-07*
