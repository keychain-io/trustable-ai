# Migration Guide: v2.0.3 → v2.0.4

**Sprint 5 Release - Verification Infrastructure**

This guide helps you upgrade from Trustable AI v2.0.3 to v2.0.4, which introduces verification gates across workflows and fixes critical bugs in the Azure DevOps skill.

---

## What's New in v2.0.4

### Features Added
- ✨ Verification gates in backlog-grooming workflow (catch childless features, story point mismatches)
- ✨ Verification gates in sprint-planning workflow (verify work items created, content quality)
- ✨ Verification gates in sprint-execution workflow (implementation verification)
- ✨ Verification gates in daily-standup workflow (progress tracking)
- ✨ New CLI command: `trustable-ai workflow verify` (programmatic verification)
- ✨ Enhanced qa-tester agent with test execution modes
- ✨ New sprint-review workflow for comprehensive sprint closure

### Bug Fixes
- 🐛 Fixed #1073: Added missing `parent_id`, `assigned_to`, `area` parameters to `AzureDevOpsSkill.create_work_item()`
  - Workflows can now create work items with parent links
  - Prevents error: `AzureCLI.create_work_item() got an unexpected keyword argument 'parent_id'`

### Breaking Changes
- ✅ **None** - This release is fully backward compatible with v2.0.3

---

## Quick Migration (5 minutes)

If you just want the bug fix and new features:

```bash
# Step 1: Upgrade package
pip install --upgrade trustable-ai  # or from git
# OR: pip install git+https://github.com/keychain-io/trustable-ai@v2.0.4

# Step 2: Re-render agents (get enhanced qa-tester)
cd your-project
trustable-ai agent render-all

# Step 3: Re-render workflows (get verification gates)
trustable-ai workflow render-all

# Step 4: Re-initialize skills (get bug fix)
trustable-ai skill init-all

# Step 5: Verify migration
trustable-ai doctor
```

Done! You now have v2.0.4 with all verification infrastructure.

---

## Detailed Migration Steps

### Prerequisites

- Existing Trustable AI v2.0.3 installation
- Project initialized with `.claude/config.yaml`
- Backup your `.claude/` directory (optional but recommended)

```bash
# Optional: Backup existing configuration
cp -r .claude .claude.backup-2.0.3
```

---

### Step 1: Upgrade the Package

Choose your installation method:

#### Option A: From PyPI (recommended)
```bash
pip install --upgrade trustable-ai
```

#### Option B: From Git Repository
```bash
pip install --upgrade git+https://github.com/keychain-io/trustable-ai@v2.0.4
```

#### Option C: From Local Source (development)
```bash
cd /path/to/trustable-ai
git pull
git checkout v2.0.4
pip install -e .
```

**Verify Installation:**
```bash
trustable-ai --version
# Should show: trustable-ai, version 2.0.4
```

---

### Step 2: Re-render Agents (Get Enhanced qa-tester)

The qa-tester agent was enhanced with test execution modes in this release.

```bash
# Re-render all agents
trustable-ai agent render-all

# Or render specific agents:
trustable-ai agent render qa-tester
```

**What's Updated:**
- `.claude/agents/qa-tester.md` - Enhanced with test execution modes, EPIC test plan generation

**Verification:**
```bash
# Check qa-tester was updated
grep -i "test execution mode" .claude/agents/qa-tester.md
# Should find: TEST EXECUTION MODES section
```

---

### Step 3: Re-render Workflows (Get Verification Gates)

Four workflows were enhanced with verification gates, and one new workflow was added.

```bash
# Re-render all workflows
trustable-ai workflow render-all

# Or render specific workflows:
trustable-ai workflow render backlog-grooming
trustable-ai workflow render sprint-planning
trustable-ai workflow render sprint-execution
trustable-ai workflow render daily-standup
trustable-ai workflow render sprint-review  # New workflow
```

**What's Updated:**
- `.claude/commands/backlog-grooming.md` - Added hierarchy verification, story point validation
- `.claude/commands/sprint-planning.md` - Added work item creation verification
- `.claude/commands/sprint-execution.md` - Added implementation verification
- `.claude/commands/daily-standup.md` - Added progress tracking verification
- `.claude/commands/sprint-review.md` - **NEW** - Comprehensive sprint closure workflow

**Verification:**
```bash
# Check verification gates were added
grep -i "verification" .claude/commands/backlog-grooming.md | head -5
# Should find: Step 4: Verify Work Item Hierarchy
```

---

### Step 4: Re-initialize Skills (Get Bug Fix)

The Azure DevOps skill was fixed to support parent_id parameter.

```bash
# Re-initialize all skills
trustable-ai skill init-all

# Or initialize specific skill:
trustable-ai skill init azure_devops
```

**What's Fixed:**
- `.claude/skills/azure_devops/__init__.py` - Now accepts `parent_id`, `assigned_to`, `area` parameters
- Workflows can now create work items with parent links without errors

**Verification:**
```bash
# Check bug fix was applied
grep -A 5 "def create_work_item" .claude/skills/azure_devops/__init__.py | grep "parent_id"
# Should find: parent_id: Optional[int] = None
```

---

### Step 5: Verify Migration

Run health checks to ensure everything is configured correctly.

```bash
# Run full health check
trustable-ai doctor

# Validate configuration
trustable-ai validate

# Test new workflow verification command
trustable-ai workflow verify backlog-grooming
trustable-ai workflow verify sprint-planning
```

**Expected Output:**
```
✅ Configuration file exists and valid
✅ Required directories present
✅ Agents available (9 agents)
✅ Workflows available (8 workflows) # 7 → 8 (new sprint-review)
✅ Skills initialized (5 skills)
✅ Work tracking configured
✅ All health checks passed
```

---

## Configuration Changes

### No Configuration Changes Required

**Good news:** Your existing `.claude/config.yaml` is fully compatible with v2.0.4.

No configuration schema changes were made in this release. All new features work with your existing configuration.

### Optional: Enable New Features

If you want to customize verification behavior, you can add these optional settings:

```yaml
# .claude/config.yaml (optional enhancements)

workflows:
  verification:
    # Enable strict verification (fails on warnings)
    strict_mode: false  # default: false

    # Skip verification in development mode
    skip_in_dev: false  # default: false

    # Verification timeout (seconds)
    timeout: 300  # default: 300

quality_standards:
  # Existing standards (no changes needed)
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
```

**Note:** These settings are entirely optional. The defaults work well for most projects.

---

## Testing the Migration

### Test 1: Verify Bug Fix (parent_id Support)

Test that work items can now be created with parent links:

```python
# test_migration.py
import sys
sys.path.insert(0, ".claude/skills")
from azure_devops import AzureDevOpsSkill

skill = AzureDevOpsSkill()

# This should now work without error (was broken in v2.0.3)
result = skill.create_work_item(
    work_item_type="Task",
    title="Test work item with parent",
    parent_id=1234,  # This parameter now works!
    verify=False
)

print(f"✅ Bug fix verified: parent_id parameter accepted")
```

### Test 2: Verify Verification Gates

Test that workflows now include verification steps:

```bash
# Test backlog-grooming verification
grep -A 10 "Step 4: Verify Work Item Hierarchy" .claude/commands/backlog-grooming.md
# Should show verification logic

# Test sprint-planning verification
grep -A 10 "Step 6: Verify Work Items Created" .claude/commands/sprint-planning.md
# Should show verification logic
```

### Test 3: New CLI Command

Test the new workflow verification command:

```bash
# Verify all workflows have verification gates
trustable-ai workflow verify --all

# Check specific workflow
trustable-ai workflow verify backlog-grooming
```

**Expected Output:**
```
✅ backlog-grooming: Verification gates implemented
   - Hierarchy verification: ✅ Present
   - Story point validation: ✅ Present
   - Verification checklist: ✅ Present
```

### Test 4: Run Full Test Suite (if applicable)

If you have tests in your project:

```bash
pytest tests/
```

All existing tests should continue passing (backward compatibility).

---

## Rollback Procedure

If you encounter issues and need to rollback to v2.0.3:

```bash
# Step 1: Uninstall v2.0.4
pip uninstall trustable-ai

# Step 2: Install v2.0.3
pip install trustable-ai==2.0.3
# OR: pip install git+https://github.com/keychain-io/trustable-ai@v2.0.3

# Step 3: Restore backup (if you made one)
rm -rf .claude
mv .claude.backup-2.0.3 .claude

# Step 4: Verify rollback
trustable-ai --version
# Should show: trustable-ai, version 2.0.3
```

**Rollback Risk:** Very low - v2.0.4 changes are backward compatible.

---

## Common Migration Issues

### Issue 1: "Command not found: trustable-ai workflow verify"

**Cause:** Package not upgraded or cache issue.

**Solution:**
```bash
# Clear pip cache and reinstall
pip cache purge
pip uninstall trustable-ai
pip install trustable-ai==2.0.4

# Verify command exists
trustable-ai workflow --help | grep verify
```

### Issue 2: "parent_id parameter still not recognized"

**Cause:** Skills not re-initialized.

**Solution:**
```bash
# Force re-initialize skills
rm -rf .claude/skills
trustable-ai skill init-all

# Verify fix applied
grep "parent_id" .claude/skills/azure_devops/__init__.py
```

### Issue 3: "Verification gates not in rendered workflows"

**Cause:** Workflows not re-rendered.

**Solution:**
```bash
# Force re-render workflows
trustable-ai workflow render-all

# Verify verification gates present
grep -i "verification" .claude/commands/backlog-grooming.md
```

### Issue 4: "trustable-ai doctor fails"

**Cause:** Configuration or directory structure issue.

**Solution:**
```bash
# Check what's failing
trustable-ai doctor --verbose

# Common fixes:
# - Ensure .claude/config.yaml exists
# - Run: trustable-ai validate
# - Check file permissions: chmod -R u+rw .claude/
```

---

## What You Get After Migration

### New Capabilities

1. **Verification Infrastructure** (External Source of Truth - VISION.md Pillar #2)
   - Workflows now query Azure DevOps to verify work items exist
   - Catch AI failures immediately (don't trust AI claims)
   - Story point validation prevents estimation drift
   - Hierarchy verification prevents orphaned work items

2. **Enhanced Testing**
   - qa-tester agent supports multiple test execution modes
   - EPIC acceptance test plan generation
   - Test report generation and attachment

3. **Better Sprint Management**
   - New sprint-review workflow for comprehensive closure
   - Acceptance testing, security review, deployment readiness
   - Automated sprint closure with verification

4. **Programmatic Verification**
   - CLI command to verify workflows: `trustable-ai workflow verify`
   - Integrate verification into CI/CD pipelines
   - Catch missing verification gates early

### Backward Compatibility

✅ **All v2.0.3 workflows continue to work**
- No breaking changes in workflow structure
- No configuration changes required
- Existing projects work without modification

✅ **Gradual adoption**
- Use new verification gates when you're ready
- Mix old and new workflow styles during transition
- No forced migration timeline

---

## Performance Impact

### Expected Changes

- **Workflow Execution Time**: +5-10 seconds per workflow (verification queries)
- **Test Coverage**: No change (unless you add new tests)
- **Memory Usage**: Negligible increase
- **Disk Space**: +3KB (verification checklist validators)

### Optimization Tips

If verification gates slow down your workflows:

```yaml
# .claude/config.yaml
workflows:
  verification:
    # Cache verification results (5 minutes)
    cache_duration: 300

    # Parallel verification queries
    parallel: true
```

---

## Getting Help

### Documentation
- **Release Notes**: Check CHANGELOG.md for v2.0.4 details
- **Verification Guide**: See workflows/CLAUDE.md for verification patterns
- **API Docs**: Updated for new parameters in skills/azure_devops/

### Support Channels
- **GitHub Issues**: Report bugs or migration issues
- **Documentation**: Read updated CLAUDE.md files in each module
- **Sprint Review Report**: `.claude/reports/sprint-reviews/sprint-5-review.md`

### Verification Checklist

After migration, verify these items:

- [ ] Package version shows 2.0.4: `trustable-ai --version`
- [ ] Health check passes: `trustable-ai doctor`
- [ ] Agents re-rendered: `ls -l .claude/agents/qa-tester.md`
- [ ] Workflows re-rendered: `ls -l .claude/commands/sprint-review.md`
- [ ] Skills re-initialized: `grep parent_id .claude/skills/azure_devops/__init__.py`
- [ ] New CLI command works: `trustable-ai workflow verify --help`
- [ ] Bug fix verified: Test work item creation with parent_id
- [ ] Existing workflows still work: Run a test workflow

---

## Migration Timeline Recommendation

### Immediate (Day 1)
- Upgrade package to v2.0.4
- Re-render agents, workflows, skills
- Run health checks

### Week 1
- Test new verification gates in backlog-grooming
- Try new sprint-review workflow
- Verify bug fix resolves parent_id issues

### Week 2
- Enable verification gates in sprint-planning
- Use `trustable-ai workflow verify` in CI/CD
- Train team on new verification patterns

### Month 1
- Adopt verification gates across all workflows
- Measure reduction in AI failure detection time
- Document team-specific verification patterns

---

## Summary

**Migration Complexity:** ⭐ Low (5 minutes, fully automated)

**Breaking Changes:** None (100% backward compatible)

**Required Actions:**
1. `pip install --upgrade trustable-ai`
2. `trustable-ai agent render-all`
3. `trustable-ai workflow render-all`
4. `trustable-ai skill init-all`
5. `trustable-ai doctor`

**Recommended Actions:**
- Test new verification gates in development first
- Review sprint-5-review.md for feature details
- Explore new sprint-review workflow

**Risk Level:** Very Low
- Rollback takes 2 minutes
- No data migration required
- No configuration changes needed

---

*For questions or issues during migration, please open a GitHub issue or consult the Sprint 5 review report at `.claude/reports/sprint-reviews/sprint-5-review.md`.*
