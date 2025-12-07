# Safe Action Permissions

## Overview

### What are Safe Action Permissions?

Safe Action Permissions is a platform-aware permission configuration system that automatically approves safe operations while requiring manual approval for destructive ones. This prevents AI agents from performing dangerous operations without user consent while maintaining development velocity.

**Example**: Git status and git commit are auto-approved (safe). Git push requires approval (could affect remote). Git push --force is denied (destructive).

### Why Do We Need This?

The Trustable AI framework orchestrates multiple AI agents that execute bash commands to complete SDLC tasks. Without permission controls, agents could:

- **Push to production branches** without review
- **Delete files recursively** (rm -rf)
- **Run privileged operations** (sudo)
- **Access external networks** without consent
- **Delete work items** or cloud resources

**Problem**: Approve every single command → constant interruptions, slow workflows
**Solution**: Auto-approve safe operations → only interrupt for risky commands

### What Problems Does It Solve?

**Without safe action permissions:**

1. **Constant approval prompts slow development**
   - Agent runs git status → approval prompt
   - Agent runs pytest → approval prompt
   - Agent runs git diff → approval prompt
   - Every command requires manual approval, breaking flow

2. **Risk of destructive operations**
   - No guardrails against git push --force
   - No protection against rm -rf /
   - No validation before production deployment

3. **Platform-specific command patterns not considered**
   - Windows PowerShell vs Linux bash different
   - WSL detection needed for cross-platform support
   - Command patterns must match OS shell

4. **No security policy enforcement**
   - Can't enforce "never auto-approve sudo"
   - Can't require approval for network access
   - Can't prevent work item deletion

**With safe action permissions:**

```bash
# Auto-approved (safe, read-only operations)
Bash(git status:*)       → executed immediately
Bash(git diff:*)         → executed immediately
Bash(pytest:*)           → executed immediately

# Require approval (could affect remote/external systems)
Bash(git push:*)         → asks for approval
Bash(curl:*)             → asks for approval
Bash(kubectl apply:*)    → asks for approval

# Denied (destructive operations)
Bash(git push --force:*) → denied without asking
Bash(rm -rf /:*)         → denied without asking
Bash(az boards work-item delete:*) → denied without asking
```

Every bash command is categorized as **allow** (auto-approve), **ask** (require approval), or **deny** (always block), enabling safe automation with security guardrails.

---

## Quick Start

### Initialize Permissions

When you run `trustable-ai init`, permissions are automatically generated based on your platform:

```bash
# Initialize project (generates permissions automatically)
trustable-ai init
```

This creates `.claude/settings.local.json` with platform-specific permissions:

- **Linux/macOS**: Bash command patterns
- **Windows**: PowerShell/cmd patterns
- **WSL**: Detects WSL and generates appropriate patterns

### Validate Permissions

After initialization or manual edits, validate your permissions configuration:

```bash
# Validate permissions structure and content
trustable-ai permissions validate
```

Output:

```
🔍 Validating permissions configuration...

✅ Permissions file found: .claude/settings.local.json
✅ Valid JSON structure
✅ All required fields present

📊 Validation Results:
   - Auto-approved (allow): 45 commands
   - Require approval (ask): 28 commands
   - Denied: 8 commands

✅ No issues found!
```

### Where Permissions are Stored

Permissions are stored in `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(pytest:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(curl:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf /:*)"
    ]
  }
}
```

**Important**: `.claude/settings.local.json` is local to your machine (gitignored). Each developer can customize their own permissions.

---

## Platform-Specific Behavior

The framework detects your platform automatically and generates appropriate permission patterns.

### Linux

**Shell**: bash (default)

**Safe Operations** (auto-approved):

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(pytest:*)",
      "Bash(python3 -m pytest:*)",
      "Bash(az boards work-item show:*)",
      "Bash(az boards work-item create:*)",
      "Bash(az boards work-item update:*)"
    ]
  }
}
```

**Require Approval** (ask):

```json
{
  "permissions": {
    "ask": [
      "Bash(git push:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(ssh:*)",
      "Bash(kubectl apply:*)",
      "Bash(docker push:*)",
      "Bash(sudo:*)"
    ]
  }
}
```

**Denied** (always blocked):

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(rm -rf:*)",
      "Bash(az boards work-item delete:*)",
      "Bash(git clean -fd:*)"
    ]
  }
}
```

### Windows

**Shell**: PowerShell (default)

**Safe Operations** (auto-approved):

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(dir:*)",
      "Bash(type:*)",
      "Bash(findstr:*)",
      "Bash(pytest:*)",
      "Bash(python -m pytest:*)",
      "Bash(az boards work-item show:*)",
      "Bash(az boards work-item create:*)",
      "Bash(az boards work-item update:*)",
      "Bash(msbuild:*)"
    ]
  }
}
```

**Require Approval** (ask):

```json
{
  "permissions": {
    "ask": [
      "Bash(git push:*)",
      "Bash(Set-ExecutionPolicy:*)",
      "Bash(runas:*)",
      "Bash(kubectl apply:*)",
      "Bash(docker push:*)"
    ]
  }
}
```

**Denied** (always blocked):

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(Remove-Item -Recurse -Force:*)",
      "Bash(del /s /q:*)",
      "Bash(rmdir /s /q:*)",
      "Bash(az boards work-item delete:*)"
    ]
  }
}
```

### macOS

**Shell**: zsh (default since macOS Catalina)

**Safe Operations** (auto-approved):

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(pytest:*)",
      "Bash(python3 -m pytest:*)",
      "Bash(az boards work-item show:*)",
      "Bash(az boards work-item create:*)",
      "Bash(az boards work-item update:*)"
    ]
  }
}
```

**Require Approval** (ask):

```json
{
  "permissions": {
    "ask": [
      "Bash(git push:*)",
      "Bash(curl:*)",
      "Bash(ssh:*)",
      "Bash(sudo:*)",
      "Bash(kubectl apply:*)",
      "Bash(docker push:*)"
    ]
  }
}
```

**Denied** (always blocked):

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(rm -rf:*)",
      "Bash(az boards work-item delete:*)",
      "Bash(git clean -fd:*)"
    ]
  }
}
```

### WSL (Windows Subsystem for Linux)

**Detection**: Automatically detects WSL by checking `/proc/version` for "microsoft" or "WSL"

**Shell**: bash (Linux shell in WSL)

**Permissions**: Same as Linux (bash patterns)

**WSL Interop**: The framework detects if WSL interop is enabled (can run Windows executables from WSL). If enabled, generates patterns for both Linux and Windows commands.

**Example WSL Configuration**:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(pytest:*)",
      "Bash(python3 -m pytest:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(curl:*)",
      "Bash(sudo:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

---

## Permission Categories

Permissions are organized into three categories based on risk level.

### Allow List (Auto-Approve)

**Purpose**: Safe operations that don't modify remote systems or delete data

**Operations**:

#### Git (Read-Only and Local Writes)
```json
"Bash(git status:*)",
"Bash(git diff:*)",
"Bash(git log:*)",
"Bash(git show:*)",
"Bash(git branch:*)",
"Bash(git remote -v:*)",
"Bash(git fetch:*)",
"Bash(git add:*)",        // Local staging
"Bash(git commit:*)",     // Local commit
"Bash(git stash:*)"       // Local stash
```

**Rationale**: These commands only affect local repository. No risk to remote/production.

#### File Operations (Read-Only)
```json
"Bash(ls:*)",
"Bash(cat:*)",
"Bash(head:*)",
"Bash(tail:*)",
"Bash(grep:*)",
"Bash(find:*)",
"Bash(tree:*)"
```

**Rationale**: Read operations can't corrupt data. Safe to auto-approve.

#### Work Tracking (CRUD, No Delete)
```json
"Bash(az boards work-item show:*)",
"Bash(az boards work-item create:*)",
"Bash(az boards work-item update:*)",
"Bash(az boards query:*)",
"Bash(az boards iteration:*)",
"Bash(az boards area:*)"
```

**Rationale**: Creating and updating work items is part of normal workflow. No deletion allowed.

#### Test Execution
```json
"Bash(pytest:*)",
"Bash(python -m pytest:*)",
"Bash(python3 -m pytest:*)",
"Bash(npm test:*)",
"Bash(npm run test:*)",
"Bash(mvn test:*)",
"Bash(gradle test:*)",
"Bash(go test:*)",
"Bash(cargo test:*)"
```

**Rationale**: Running tests is safe, doesn't modify code or deploy anything.

#### Build Operations
```json
"Bash(npm install:*)",
"Bash(npm run build:*)",
"Bash(pip install:*)",
"Bash(mvn compile:*)",
"Bash(gradle build:*)",
"Bash(make:*)",
"Bash(cargo build:*)",
"Bash(go build:*)"
```

**Rationale**: Building locally is safe. Doesn't publish or deploy.

#### Code Inspection
```json
"Bash(pylint:*)",
"Bash(flake8:*)",
"Bash(mypy:*)",
"Bash(black --check:*)",
"Bash(ruff:*)",
"Bash(eslint:*)",
"Bash(tsc --noEmit:*)"
```

**Rationale**: Static analysis is read-only, safe to run automatically.

#### Utility Commands
```json
"Bash(pwd:*)",
"Bash(whoami:*)",
"Bash(date:*)",
"Bash(echo:*)",
"Bash(which:*)"
```

**Rationale**: Basic system info commands, completely safe.

### Ask List (Require Approval)

**Purpose**: Operations that affect remote systems, access network, or require privileged permissions

**Operations**:

#### Git Push (Remote Updates)
```json
"Bash(git push:*)"
```

**Rationale**: Pushes to remote repository. User should approve which branch and when. (Force push is in deny list.)

#### Production Deployments
```json
"Bash(git push origin main:*)",
"Bash(git push origin master:*)",
"Bash(npm publish:*)",
"Bash(az webapp:*)",
"Bash(az container:*)",
"Bash(az aks:*)",
"Bash(kubectl apply:*)",
"Bash(docker push:*)",
"Bash(terraform apply:*)"
```

**Rationale**: These commands deploy to production or production-like environments. Always require explicit user approval.

#### Network Access
```json
"Bash(curl:*)",
"Bash(wget:*)",
"Bash(ping:*)",
"Bash(ssh:*)",
"Bash(scp:*)",
"Bash(rsync:*)"
```

**Rationale**: Network access could exfiltrate data or download malicious content. Require approval to review URL/target.

#### Privileged Operations (Linux/macOS)
```json
"Bash(sudo:*)",
"Bash(su:*)",
"Bash(chmod:*)",
"Bash(chown:*)"
```

**Rationale**: System-level operations that modify permissions or run as root. Always require approval.

#### Privileged Operations (Windows)
```json
"Bash(runas:*)",
"Bash(Set-ExecutionPolicy:*)"
```

**Rationale**: Elevate privileges or modify security policies. Always require approval.

### Deny List (Always Block)

**Purpose**: Destructive operations that should NEVER be auto-approved, even with user approval

**Operations**:

#### Destructive Git Operations
```json
"Bash(git push --force:*)",
"Bash(git reset --hard:*)",
"Bash(git clean -fd:*)"
```

**Rationale**: These commands can lose work permanently. Force push overwrites remote history. Hard reset loses uncommitted changes. Clean deletes untracked files.

#### Destructive File Operations (Linux/macOS)
```json
"Bash(rm -rf:*)"
```

**Rationale**: Recursive force delete can delete entire directories, including system files. Extremely dangerous.

#### Destructive File Operations (Windows)
```json
"Bash(del /s /q:*)",
"Bash(rmdir /s /q:*)",
"Bash(Remove-Item -Recurse -Force:*)"
```

**Rationale**: Windows equivalents of rm -rf. Recursive deletion without prompts.

#### Work Item Deletion
```json
"Bash(az boards work-item delete:*)"
```

**Rationale**: Deleting work items loses project history. Should be done manually through web UI after careful consideration.

#### Resource Deletion (Azure)
```json
"Bash(az group delete:*)"
```

**Rationale**: Deleting resource groups destroys entire environments. Catastrophic if executed accidentally.

---

## Customization Guide

You can customize permissions to match your team's workflows and risk tolerance.

### Pattern Format

Permissions use Claude Code's safe-action pattern format:

```
Bash(command:arguments)
```

**Examples**:

```json
"Bash(git status:*)",           // git status with any arguments
"Bash(git diff:*)",             // git diff with any arguments
"Bash(pytest:*)",               // pytest with any arguments
"Bash(git push:origin main)"    // git push ONLY to origin main (exact match)
```

**Wildcards**:
- `*` matches any arguments
- Specific arguments match exactly

### Adding New Patterns

**Use Case**: Allow a new safe command (e.g., `docker-compose up`)

1. Open `.claude/settings.local.json`
2. Add pattern to appropriate list:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      // ... existing patterns ...
      "Bash(docker-compose up:*)"  // Add new pattern
    ]
  }
}
```

3. Validate:

```bash
trustable-ai permissions validate
```

### Moving Patterns Between Lists

**Use Case**: git push is in "ask" list, but you want to auto-approve pushes to your feature branch

**Option 1: Specific Pattern (Recommended)**

Add specific pattern to allow list, keep general pattern in ask list:

```json
{
  "permissions": {
    "allow": [
      "Bash(git push:origin feature/my-feature)"  // Auto-approve this specific push
    ],
    "ask": [
      "Bash(git push:*)"  // Still ask for all other pushes
    ]
  }
}
```

**Option 2: Move to Allow List (Less Safe)**

Remove from ask, add to allow (not recommended - pushes affect remote):

```json
{
  "permissions": {
    "allow": [
      "Bash(git push:*)"  // ⚠️ Auto-approve ALL pushes (risky!)
    ],
    "ask": [
      // Remove "Bash(git push:*)" from here
    ]
  }
}
```

**Validation Warning**: The validator will warn if you auto-approve risky operations:

```
⚠️  Warnings:
   - Overly permissive pattern in allow list: 'Bash(git push:*)' (consider moving to ask list for approval)
```

### Common Customization Scenarios

#### Scenario 1: Auto-Approve Azure DevOps Work Item Creation

**Default**: Work item creation in allow list (already auto-approved)

**No change needed** - this is safe and already configured.

#### Scenario 2: Allow Docker Commands

**Add Docker patterns to allow list**:

```json
{
  "permissions": {
    "allow": [
      "Bash(docker build:*)",
      "Bash(docker run:*)",
      "Bash(docker ps:*)",
      "Bash(docker logs:*)",
      "Bash(docker-compose up:*)"
    ],
    "ask": [
      "Bash(docker push:*)"  // Still require approval for pushing images
    ]
  }
}
```

#### Scenario 3: Auto-Approve Specific Git Push Target

**Allow pushes to your feature branch only**:

```json
{
  "permissions": {
    "allow": [
      "Bash(git push:origin feature/WI-1234-my-feature)"
    ],
    "ask": [
      "Bash(git push:*)"  // Ask for all other pushes
    ]
  }
}
```

**Note**: More specific patterns match first. If exact match exists in allow, won't check ask list.

#### Scenario 4: Deny Terraform Destroy

**Add terraform destroy to deny list**:

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)",
      "Bash(terraform destroy:*)"  // Never auto-approve
    ],
    "ask": [
      "Bash(terraform apply:*)"  // Require approval for apply
    ]
  }
}
```

#### Scenario 5: Development vs Production Modes

**Development Mode** (generated by `trustable-ai init` with `mode="development"`):

- Auto-approves git add, git commit, work item CRUD, tests, builds
- Asks for git push, network access, deployments
- Denies destructive operations

**Production Mode** (more conservative):

- Asks for git add, git commit (review every change)
- Asks for work item creation/update (prevent accidental work item spam)
- Denies destructive operations

To switch modes, re-run init or manually edit `.claude/settings.local.json`.

---

## Validation Workflow

The validation command helps catch permission configuration errors before they cause problems.

### Running Validation

```bash
trustable-ai permissions validate
```

### Understanding Validation Output

#### Success (No Issues)

```
🔍 Validating permissions configuration...

✅ Permissions file found: .claude/settings.local.json
✅ Valid JSON structure
✅ All required fields present

📊 Validation Results:
   - Auto-approved (allow): 45 commands
   - Require approval (ask): 28 commands
   - Denied: 8 commands

✅ No issues found!
```

**Exit Code**: 0 (success)

#### Errors Found

```
🔍 Validating permissions configuration...

✅ Permissions file found: .claude/settings.local.json
❌ Invalid permissions structure

❌ Errors:
   - Conflict: 'Bash(git push:*)' appears in both allow and ask lists
   - Conflict: 'Bash(sudo:*)' appears in both ask and deny lists

💡 Recommendations:
   - Fix errors before using permissions configuration
   - Remove conflicting patterns from one of the lists
```

**Exit Code**: 2 (errors - must fix)

#### Warnings Found

```
🔍 Validating permissions configuration...

✅ Permissions file found: .claude/settings.local.json
✅ Valid JSON structure
✅ All required fields present

📊 Validation Results:
   - Auto-approved (allow): 48 commands
   - Require approval (ask): 25 commands
   - Denied: 8 commands

⚠️  Warnings:
   - Duplicate pattern in allow list: 'Bash(git status:*)'
   - Unsafe pattern in allow list: 'Bash(git push:*)' (contains dangerous command: 'git push')
   - Overly permissive pattern in allow list: 'Bash(curl:*)' (consider moving to ask list for approval)

💡 Recommendations:
   - Remove duplicate patterns to clean up configuration
   - Move unsafe patterns from 'allow' to 'ask' for approval
   - Review permissive patterns and consider requiring approval
```

**Exit Code**: 1 (warnings - should fix, but not critical)

### Validation Checks

The validator performs these checks:

#### 1. File Existence
```
❌ Permissions file not found: .claude/settings.local.json

💡 Run 'trustable-ai init' to generate permissions configuration.
```

#### 2. Valid JSON Structure
```
❌ Invalid JSON in permissions file: Expecting ',' delimiter: line 10 column 5 (char 234)
```

**Fix**: Correct JSON syntax errors (missing commas, quotes, brackets).

#### 3. Required Fields Present
```
❌ Errors:
   - Missing required field: permissions.allow
   - Missing required field: permissions.deny
   - Missing required field: permissions.ask
```

**Fix**: Add missing fields to settings.local.json.

#### 4. Pattern Format Validation
```
⚠️  Warnings:
   - Pattern in allow list may be invalid format: 'git status' (expected format: 'Bash(command:*)')
```

**Fix**: Use Claude Code format: `Bash(command:*)` not just `command`.

#### 5. Duplicate Detection
```
⚠️  Warnings:
   - Duplicate pattern in allow list: 'Bash(git status:*)'
```

**Fix**: Remove duplicate pattern from allow list.

#### 6. Conflict Detection (Same Pattern in Multiple Lists)
```
❌ Errors:
   - Conflict: 'Bash(git push:*)' appears in both allow and ask lists
```

**Fix**: Pattern can only be in ONE list. Remove from one of them.

**Common Conflicts**:
- `allow` + `ask` → Conflict (auto-approve or ask, pick one)
- `allow` + `deny` → Conflict (auto-approve or deny, pick one)
- `ask` + `deny` → Conflict (ask or deny, pick one)

#### 7. Unsafe Pattern Detection
```
⚠️  Warnings:
   - Unsafe pattern in allow list: 'Bash(rm -rf:*)' (contains dangerous command: 'rm -rf')
```

**Fix**: Move dangerous pattern to ask or deny list.

**Dangerous Patterns Detected**:
- `rm -rf`, `git push --force`, `git reset --hard`
- `sudo`, `chmod 777`, `chown`
- `az boards work-item delete`, `az group delete`
- Windows: `del /s /q`, `rmdir /s /q`, `Remove-Item -Recurse -Force`

#### 8. Overly Permissive Pattern Detection
```
⚠️  Warnings:
   - Overly permissive pattern in allow list: 'Bash(curl:*)' (consider moving to ask list for approval)
```

**Fix**: Consider moving to ask list for more control.

**Risky Patterns Flagged**:
- `git push`, `npm publish`, `docker push`
- `curl`, `wget`, `ssh`
- `kubectl apply`, `terraform apply`
- `az webapp`, `az container`, `az aks`

### Fixing Common Issues

#### Issue: Duplicate Patterns

**Error**:
```
⚠️  Warnings:
   - Duplicate pattern in allow list: 'Bash(git status:*)'
```

**Fix**: Remove duplicate entry

**Before**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git status:*)"  // Duplicate
    ]
  }
}
```

**After**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)"
    ]
  }
}
```

#### Issue: Conflicting Patterns

**Error**:
```
❌ Errors:
   - Conflict: 'Bash(git push:*)' appears in both allow and ask lists
```

**Fix**: Remove from one list

**Before**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git push:*)"  // In allow...
    ],
    "ask": [
      "Bash(git push:*)"  // ...and also in ask (conflict!)
    ]
  }
}
```

**After**:
```json
{
  "permissions": {
    "allow": [
      // Removed from allow
    ],
    "ask": [
      "Bash(git push:*)"  // Keep in ask (safer)
    ]
  }
}
```

#### Issue: Unsafe Pattern in Allow List

**Warning**:
```
⚠️  Warnings:
   - Unsafe pattern in allow list: 'Bash(git push --force:*)' (contains dangerous command: 'git push --force')
```

**Fix**: Move to deny list

**Before**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git push --force:*)"  // Dangerous in allow!
    ]
  }
}
```

**After**:
```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)"  // Move to deny
    ]
  }
}
```

#### Issue: Corrupted JSON

**Error**:
```
❌ Invalid JSON in permissions file: Expecting ',' delimiter: line 10 column 5 (char 234)
```

**Fix**: Validate JSON syntax

Use a JSON validator or IDE to find syntax errors:
- Missing commas between array elements
- Missing quotes around strings
- Unclosed brackets/braces
- Trailing commas (not allowed in JSON)

**Before** (invalid):
```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)"
      "Bash(git diff:*)"  // Missing comma!
    ]
  }
}
```

**After** (valid):
```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",  // Added comma
      "Bash(git diff:*)"
    ]
  }
}
```

### Re-Validation After Fixes

After fixing issues, re-run validation:

```bash
trustable-ai permissions validate
```

**Success**:
```
✅ No issues found!
```

**Remaining Issues**:
```
❌ Errors:
   - (any remaining errors)
```

Fix remaining issues and validate again until clean.

---

## Security Best Practices

### 1. Principle of Least Privilege

**DO**: Only auto-approve commands that are truly safe

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",    // Read-only - safe
      "Bash(git diff:*)",      // Read-only - safe
      "Bash(pytest:*)"         // Test execution - safe
    ]
  }
}
```

**DON'T**: Auto-approve commands that could affect production

```json
{
  "permissions": {
    "allow": [
      "Bash(git push:*)",           // ❌ Affects remote - not safe
      "Bash(kubectl apply:*)",      // ❌ Deploys to cluster - not safe
      "Bash(az webapp restart:*)"   // ❌ Affects production - not safe
    ]
  }
}
```

**Rationale**: If uncertain whether command is safe, put in ask list (require approval) not allow list.

### 2. Review Permissions Regularly

**Schedule**: Review permissions quarterly or when:
- New team members join
- New tools added to workflow
- Security incident occurs
- Workflow patterns change

**Review Checklist**:
- [ ] Are all allow patterns still safe?
- [ ] Should any ask patterns move to allow (team trust increased)?
- [ ] Should any allow patterns move to ask (new risks identified)?
- [ ] Are deny patterns still comprehensive?
- [ ] Are there new destructive operations to add to deny list?

**Commands**:
```bash
# Validate current permissions
trustable-ai permissions validate

# Review settings.local.json
cat .claude/settings.local.json | jq '.permissions'
```

### 3. Avoid Overly Permissive Wildcards

**DO**: Use specific patterns when possible

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ]
  }
}
```

**DON'T**: Use wildcards that match too broadly

```json
{
  "permissions": {
    "allow": [
      "Bash(git:*)"  // ❌ Matches ALL git commands including git push --force!
    ]
  }
}
```

**Rationale**: Overly broad wildcards can inadvertently auto-approve dangerous commands.

**Wildcard Guidelines**:
- Wildcard in arguments (`git status:*`) → OK (matches git status with any args)
- Wildcard in command (`git:*`) → DANGEROUS (matches all git subcommands)
- Wildcard in both (`*:*`) → EXTREMELY DANGEROUS (matches everything!)

### 4. Team Collaboration Considerations

**Individual Permissions**: Each developer has their own `.claude/settings.local.json` (gitignored)

**Team Standardization**:

1. **Create template**: `.claude/settings.local.json.template` (committed to repo)

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(pytest:*)"
    ],
    "ask": [
      "Bash(git push:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

2. **Document customization policy**: `docs/PERMISSIONS.md`

```markdown
# Permissions Policy

## Team Standard Permissions

Copy `.claude/settings.local.json.template` to `.claude/settings.local.json`:

\`\`\`bash
cp .claude/settings.local.json.template .claude/settings.local.json
\`\`\`

## Customization Rules

- **Allow List**: Only add read-only commands or safe local operations
- **Ask List**: Add commands that need case-by-case approval
- **Deny List**: Never remove entries (team safety standard)

## Approval Process

- New allow patterns → discuss in team standup
- New deny patterns → PR to update template
```

3. **Onboarding checklist**:

```markdown
## New Developer Setup

- [ ] Clone repository
- [ ] Run `trustable-ai init` (generates permissions)
- [ ] Review `.claude/settings.local.json`
- [ ] Run `trustable-ai permissions validate`
- [ ] Read `docs/PERMISSIONS.md`
```

### 5. Deny List is Non-Negotiable

**Rule**: Never remove patterns from deny list

**Rationale**: Deny list protects against catastrophic operations:
- `rm -rf /` → Deletes entire filesystem
- `git push --force` → Overwrites remote history
- `az group delete` → Destroys entire cloud environment

**If pattern is too restrictive**:
- DON'T remove from deny list
- DO add more specific pattern to ask list

**Example**: Want to allow force push to personal feature branch

**DON'T**:
```json
{
  "permissions": {
    "deny": [
      // ❌ Don't remove git push --force from deny
    ]
  }
}
```

**DO**:
```json
{
  "permissions": {
    "ask": [
      "Bash(git push --force:origin feature/my-temp-branch)"  // Specific branch only
    ],
    "deny": [
      "Bash(git push --force:*)"  // Keep general deny
    ]
  }
}
```

**Note**: More specific patterns match first, so ask pattern for specific branch overrides general deny.

### 6. Audit Permissions Before Production Deployment

**Pre-Deployment Checklist**:

```bash
# 1. Validate permissions
trustable-ai permissions validate

# 2. Review allow list for production-affecting commands
cat .claude/settings.local.json | jq '.permissions.allow' | grep -E '(push|deploy|publish|apply)'

# 3. Ensure deny list includes destructive operations
cat .claude/settings.local.json | jq '.permissions.deny' | grep -E '(--force|delete|destroy|rm -rf)'

# 4. Verify no overly permissive wildcards
cat .claude/settings.local.json | jq '.permissions.allow' | grep 'Bash(\*:'
```

**Red Flags**:
- `Bash(git push:*)` in allow list → Should be in ask
- `Bash(kubectl:*)` in allow list → Too broad, should be specific
- `Bash(*:*)` anywhere → Matches everything, EXTREMELY DANGEROUS

### 7. Document Security Exceptions

If you deviate from defaults, document why:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      // Exception: Auto-approve push to personal feature branch
      // Rationale: Experimental branch, no production impact
      // Approved by: Security Team, 2025-12-01
      "Bash(git push:origin feature/experimental/*)"
    ]
  }
}
```

---

## Troubleshooting

### Common Error Messages and Fixes

#### Error: Permissions file not found

**Message**:
```
❌ Permissions file not found: .claude/settings.local.json

💡 Run 'trustable-ai init' to generate permissions configuration.
```

**Fix**:
```bash
trustable-ai init
```

**Root Cause**: Project not initialized or settings.local.json deleted

---

#### Error: Invalid JSON

**Message**:
```
❌ Invalid JSON in permissions file: Expecting ',' delimiter: line 10 column 5 (char 234)
```

**Fix**: Validate JSON syntax using JSON validator or IDE

**Common Issues**:
- Missing commas between array elements
- Trailing commas (not allowed in JSON)
- Unclosed brackets/braces
- Missing quotes around strings

**Tools**:
```bash
# Validate JSON syntax
cat .claude/settings.local.json | jq '.'

# Pretty-print JSON (fixes formatting)
cat .claude/settings.local.json | jq '.' > .claude/settings.local.json.tmp
mv .claude/settings.local.json.tmp .claude/settings.local.json
```

---

#### Error: Missing required field

**Message**:
```
❌ Errors:
   - Missing required field: permissions.allow
   - Missing required field: permissions.deny
```

**Fix**: Add missing fields

**Template**:
```json
{
  "permissions": {
    "allow": [],
    "deny": [],
    "ask": []
  }
}
```

**Root Cause**: Manually edited file, forgot required fields

---

#### Error: Conflict - pattern in multiple lists

**Message**:
```
❌ Errors:
   - Conflict: 'Bash(git push:*)' appears in both allow and ask lists
```

**Fix**: Remove pattern from one list

**Rule**: Pattern can only be in ONE list (allow, deny, or ask)

**Decision Guide**:
- Safe operation → allow
- Risky but sometimes needed → ask
- Destructive/never auto-approve → deny

---

#### Warning: Unsafe pattern in allow list

**Message**:
```
⚠️  Warnings:
   - Unsafe pattern in allow list: 'Bash(git push --force:*)' (contains dangerous command: 'git push --force')
```

**Fix**: Move to deny list

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force:*)"
    ]
  }
}
```

**Why**: Force push can overwrite remote history, losing work permanently

---

#### Warning: Overly permissive pattern

**Message**:
```
⚠️  Warnings:
   - Overly permissive pattern in allow list: 'Bash(curl:*)' (consider moving to ask list for approval)
```

**Fix**: Move to ask list (or keep in allow if confident)

```json
{
  "permissions": {
    "ask": [
      "Bash(curl:*)"  // Require approval to review URL
    ]
  }
}
```

**Why**: curl accesses network, could exfiltrate data or download malicious content

---

### Corrupted settings.local.json Recovery

**Symptoms**:
- JSON parse errors
- Missing fields
- Invalid structure

**Recovery Steps**:

1. **Backup corrupted file**:
```bash
mv .claude/settings.local.json .claude/settings.local.json.backup
```

2. **Regenerate from template** (if exists):
```bash
cp .claude/settings.local.json.template .claude/settings.local.json
```

3. **Or regenerate with init**:
```bash
trustable-ai init
# Choose to overwrite when prompted
```

4. **Validate new file**:
```bash
trustable-ai permissions validate
```

5. **Restore customizations** (from backup):
```bash
# Review backup
cat .claude/settings.local.json.backup

# Manually copy custom patterns to new file
vim .claude/settings.local.json
```

---

### Platform Detection Issues

**Symptoms**:
- Wrong command patterns generated
- Linux patterns on Windows
- Windows patterns on Linux

**Diagnosis**:

1. **Check platform detection**:
```bash
python3 -c "from cli.platform_detector import PlatformDetector; import json; print(json.dumps(PlatformDetector().detect_platform(), indent=2))"
```

**Expected Output (Linux)**:
```json
{
  "os": "Linux",
  "is_wsl": false,
  "shell": "bash",
  "platform_specific": {
    "architecture": "x86_64",
    "release": "5.15.0-1028-azure",
    "command_extensions": [""]
  }
}
```

**Expected Output (WSL)**:
```json
{
  "os": "Linux",
  "is_wsl": true,
  "shell": "bash",
  "platform_specific": {
    "architecture": "x86_64",
    "release": "5.15.90.4-microsoft-standard-WSL2",
    "command_extensions": [""],
    "wsl_interop": true
  }
}
```

2. **If platform misdetected, regenerate**:
```bash
# Backup existing
mv .claude/settings.local.json .claude/settings.local.json.backup

# Regenerate
trustable-ai init

# Validate
trustable-ai permissions validate
```

3. **Manual override** (if detection fails):

Edit `.claude/settings.local.json` directly and replace with platform-specific patterns from examples above.

---

### Conflicts Between Allow/Deny/Ask Lists

**Diagnosis**:

```bash
# Find conflicts
trustable-ai permissions validate
```

**Fix**:

1. **Identify conflicting pattern**:
```
❌ Errors:
   - Conflict: 'Bash(git push:*)' appears in both allow and ask lists
```

2. **Decide which list should have the pattern**:
   - **allow**: Auto-approve (safe, no review needed)
   - **ask**: Require approval (case-by-case decision)
   - **deny**: Always block (destructive, never auto-approve)

3. **Remove from inappropriate list**:

**Before**:
```json
{
  "permissions": {
    "allow": [
      "Bash(git push:*)"
    ],
    "ask": [
      "Bash(git push:*)"
    ]
  }
}
```

**After**:
```json
{
  "permissions": {
    "ask": [
      "Bash(git push:*)"  // Keep in ask (safer)
    ]
  }
}
```

4. **Validate**:
```bash
trustable-ai permissions validate
```

---

## Complete Configuration Example

### Example: Full settings.local.json (Linux/macOS)

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git show:*)",
      "Bash(git branch:*)",
      "Bash(git remote -v:*)",
      "Bash(git fetch:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git stash:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(tree:*)",
      "Bash(az boards work-item show:*)",
      "Bash(az boards work-item create:*)",
      "Bash(az boards work-item update:*)",
      "Bash(az boards query:*)",
      "Bash(az boards iteration:*)",
      "Bash(az boards area:*)",
      "Bash(pytest:*)",
      "Bash(python -m pytest:*)",
      "Bash(python3 -m pytest:*)",
      "Bash(npm test:*)",
      "Bash(npm run test:*)",
      "Bash(mvn test:*)",
      "Bash(gradle test:*)",
      "Bash(go test:*)",
      "Bash(cargo test:*)",
      "Bash(npm install:*)",
      "Bash(npm run build:*)",
      "Bash(pip install:*)",
      "Bash(mvn compile:*)",
      "Bash(gradle build:*)",
      "Bash(make:*)",
      "Bash(cargo build:*)",
      "Bash(go build:*)",
      "Bash(pylint:*)",
      "Bash(flake8:*)",
      "Bash(mypy:*)",
      "Bash(black --check:*)",
      "Bash(ruff:*)",
      "Bash(eslint:*)",
      "Bash(tsc --noEmit:*)",
      "Bash(pwd:*)",
      "Bash(whoami:*)",
      "Bash(date:*)",
      "Bash(echo:*)",
      "Bash(which:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(git push origin main:*)",
      "Bash(git push origin master:*)",
      "Bash(npm publish:*)",
      "Bash(az webapp:*)",
      "Bash(az container:*)",
      "Bash(az aks:*)",
      "Bash(kubectl apply:*)",
      "Bash(docker push:*)",
      "Bash(terraform apply:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(ping:*)",
      "Bash(ssh:*)",
      "Bash(scp:*)",
      "Bash(rsync:*)",
      "Bash(sudo:*)",
      "Bash(su:*)",
      "Bash(chmod:*)",
      "Bash(chown:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(git clean -fd:*)",
      "Bash(rm -rf:*)",
      "Bash(az boards work-item delete:*)",
      "Bash(az group delete:*)"
    ]
  }
}
```

### Example: Full settings.local.json (Windows)

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git show:*)",
      "Bash(git branch:*)",
      "Bash(git remote -v:*)",
      "Bash(git fetch:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git stash:*)",
      "Bash(dir:*)",
      "Bash(type:*)",
      "Bash(findstr:*)",
      "Bash(az boards work-item show:*)",
      "Bash(az boards work-item create:*)",
      "Bash(az boards work-item update:*)",
      "Bash(az boards query:*)",
      "Bash(az boards iteration:*)",
      "Bash(az boards area:*)",
      "Bash(pytest:*)",
      "Bash(python -m pytest:*)",
      "Bash(npm test:*)",
      "Bash(npm run test:*)",
      "Bash(mvn test:*)",
      "Bash(gradle test:*)",
      "Bash(npm install:*)",
      "Bash(npm run build:*)",
      "Bash(pip install:*)",
      "Bash(mvn compile:*)",
      "Bash(gradle build:*)",
      "Bash(msbuild:*)",
      "Bash(pylint:*)",
      "Bash(flake8:*)",
      "Bash(mypy:*)",
      "Bash(black --check:*)",
      "Bash(ruff:*)",
      "Bash(eslint:*)",
      "Bash(tsc --noEmit:*)",
      "Bash(pwd:*)",
      "Bash(whoami:*)",
      "Bash(date:*)",
      "Bash(echo:*)",
      "Bash(which:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(git push origin main:*)",
      "Bash(git push origin master:*)",
      "Bash(npm publish:*)",
      "Bash(az webapp:*)",
      "Bash(az container:*)",
      "Bash(az aks:*)",
      "Bash(kubectl apply:*)",
      "Bash(docker push:*)",
      "Bash(terraform apply:*)",
      "Bash(Set-ExecutionPolicy:*)",
      "Bash(runas:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(git clean -fd:*)",
      "Bash(Remove-Item -Recurse -Force:*)",
      "Bash(del /s /q:*)",
      "Bash(rmdir /s /q:*)",
      "Bash(az boards work-item delete:*)",
      "Bash(az group delete:*)"
    ]
  }
}
```

---

## Integration with Claude Code

### How Permissions Affect Claude Code Behavior

When Claude Code (the AI agent) executes bash commands:

1. **Check allow list first**
   - If pattern matches → execute immediately, no prompt
   - Example: `git status` matches `Bash(git status:*)` → auto-approved

2. **Check deny list next**
   - If pattern matches → deny without asking
   - Example: `rm -rf /` matches `Bash(rm -rf:*)` → denied
   - Claude Code shows error: "Command denied by permissions"

3. **Check ask list**
   - If pattern matches → prompt user for approval
   - Example: `git push` matches `Bash(git push:*)` → asks user

4. **Default behavior** (no match)
   - If no pattern matches → ask user (conservative default)

### When Approval is Requested

**Approval Prompt Example**:

```
Claude Code wants to execute:

  git push origin feature/WI-1234

This command matches pattern: Bash(git push:*)

Allow this command?
  [A] Allow once
  [R] Reject
  [S] Allow for this session
  [N] Never allow (add to deny list)
```

**User Options**:
- **Allow once**: Execute this command, ask again next time
- **Reject**: Don't execute, agent continues without running command
- **Allow for session**: Execute this command, auto-approve same command for rest of session
- **Never allow**: Add to deny list in settings.local.json, never auto-approve

### How to Respond to Permission Requests

**Scenario 1: Safe operation, should be auto-approved**

```
Claude Code wants to execute: pytest -m unit
```

**Response**: Allow for session, then add to allow list

```bash
# After session, add to settings.local.json
vim .claude/settings.local.json
# Add "Bash(pytest:*)" to allow list
trustable-ai permissions validate
```

**Scenario 2: Risky operation, case-by-case approval needed**

```
Claude Code wants to execute: git push origin feature/WI-1234
```

**Response**:
- Review command (correct branch?)
- Allow once (or reject if wrong branch)
- Keep in ask list (don't move to allow)

**Scenario 3: Destructive operation, should never auto-approve**

```
Claude Code wants to execute: git push --force origin main
```

**Response**:
- **Reject** (pushing force to main is destructive)
- **Never allow** (add to deny list)
- Investigate why agent tried this command

---

## Architecture Reference

This permissions system implements the architecture defined in:

- **[ADR-002: Permission Pattern Syntax](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/architecture/decisions/ADR-002-permission-pattern-syntax.md)**
  - Design rationale for glob patterns
  - Platform variant handling
  - Pattern matching semantics

- **[cli/platform_detector.py](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/cli/platform_detector.py)**
  - Platform detection logic (Windows, Linux, macOS, WSL)
  - Command pattern generation per platform
  - Dangerous pattern identification

- **[cli/permissions_generator.py](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/cli/permissions_generator.py)**
  - Safe pattern template generation
  - Development vs production modes
  - Permission categorization logic

- **[cli/commands/permissions.py](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/cli/commands/permissions.py)**
  - Validation logic (structure, format, conflicts, unsafe patterns)
  - Permission count reporting
  - Actionable error messages

- **[docs/architecture/qol-improvements-design.md](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/architecture/qol-improvements-design.md)**
  - Feature #1026 architecture design
  - Three-tier permission model (allow/deny/ask)
  - Platform abstraction strategy

---

## Related Documentation

- **[Quick Start Guide](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/QUICKSTART.md)**: Getting started with the framework
- **[Architecture Decision Records](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/architecture/decisions/)**: Design decisions and rationale
- **[CLI Commands](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/cli/CLAUDE.md)**: CLI command reference

---

## Summary

Safe Action Permissions provides a three-tier permission model for AI agent bash command execution:

1. **Allow List**: Auto-approve safe operations (git status, pytest, file reads, work item CRUD)
2. **Ask List**: Require approval for risky operations (git push, network access, deployments, privileged commands)
3. **Deny List**: Always block destructive operations (force push, rm -rf, resource deletion)

**Platform-Aware**: Automatically detects OS (Windows, Linux, macOS, WSL) and generates appropriate command patterns.

**Customizable**: Edit `.claude/settings.local.json` to match your team's workflows and risk tolerance.

**Validated**: Use `trustable-ai permissions validate` to catch configuration errors (duplicates, conflicts, unsafe patterns).

**Security**: Follows principle of least privilege, prevents destructive operations, provides approval checkpoints for risky commands.

**Result**: Safe AI automation with security guardrails. Agents can execute safe operations without interruption while requiring human approval for risky commands and blocking destructive operations entirely.
