# .NET Web API Example - Trustable AI Workbench

This example demonstrates how to use the Trustable AI Workbench with a .NET Web API project.

## Project Overview

- **Project Type**: Web API
- **Language**: C# / .NET 8
- **Framework**: ASP.NET Core Web API
- **Work Tracking**: Azure DevOps (Agile template)
- **CI/CD**: Azure DevOps Pipelines
- **Deployment**: Azure App Service

## Setup

### 1. Install Trustable AI Workbench

Since the framework is Python-based, install it in your development environment:

```bash
pip install trustable-ai
```

> **Note**: The framework is used for workflow automation and doesn't need to be part of your .NET project dependencies.

### 2. Initialize in Your Project

```bash
cd your-dotnet-project
cwf init
```

Answer the prompts:
- Project name: `Customer Portal API`
- Project type: `api`
- Languages: `C#`
- Frameworks: `.NET 8,Entity Framework Core`
- Platforms: `Azure,Docker`

### 3. Configure Azure DevOps

```bash
cwf configure azure-devops
```

Provide your Azure DevOps details:
- Organization: `https://dev.azure.com/your-org`
- Project: `Customer Portal`
- Process Template: `Agile`

### 4. Configure Quality Standards

```bash
cwf configure quality-standards
```

Set your quality thresholds (recommended for .NET):
- Test coverage minimum: `80%`
- Critical vulnerabilities: `0`
- High vulnerabilities: `0`
- Code complexity: `10` (cyclomatic complexity)

## Configuration Example

The framework generates `.claude/config.yaml`:

```yaml
project:
  name: "Customer Portal API"
  type: "api"
  description: ".NET Web API for customer management system"
  source_directory: "src"
  test_directory: "tests"

  tech_stack:
    languages:
      - "C#"
    frameworks:
      - ".NET 8"
      - "ASP.NET Core"
      - "Entity Framework Core"
    platforms:
      - "Azure"
      - "Docker"
    databases:
      - "SQL Server"
    tools:
      - "xUnit"
      - "Moq"
      - "FluentAssertions"
      - "Coverlet"

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/your-org"
  project: "Customer Portal"
  process_template: "agile"  # Using Agile template
  credentials_source: "env:AZURE_DEVOPS_PAT"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"  # Agile uses "User Story" not "Product Backlog Item"
    task: "Task"
    bug: "Bug"

  custom_fields:
    business_value: "Microsoft.VSTS.Common.BusinessValue"  # Standard Agile field
    api_contract: "Custom.APIContract"
    breaking_change: "Custom.BreakingChange"

  sprint_naming: "Sprint {number}"
  iteration_format: "{project}\\Sprint {sprint}"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  medium_vulnerabilities_max: 5
  code_complexity_max: 10
  duplicate_code_max: 3
  build_time_max_minutes: 10
  test_time_max_minutes: 5

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
    analyst: "claude-sonnet-4.5"
    security: "claude-sonnet-4.5"
    scrum-master: "claude-sonnet-4.5"

  enabled_agents:
    - "business-analyst"
    - "project-architect"
    - "senior-engineer"
    - "security-specialist"
    - "scrum-master"

workflow_config:
  state_directory: ".claude/workflow-state"
  profiling_directory: ".claude/profiling"
  checkpoint_enabled: true
  verification_enabled: true
  max_retries: 3
  timeout_minutes: 60

deployment_config:
  environments:
    - "local"
    - "dev"
    - "staging"
    - "production"
  default_environment: "dev"
  deployment_tasks_enabled: true
  deployment_task_types:
    - "deployment-task"
    - "database-migration"
```

## Usage

### Enable Agents

```bash
cwf agent enable business-analyst project-architect senior-engineer security-specialist scrum-master
```

### Render Agent Definitions

```bash
# Render all agents with .NET-specific context
cwf agent render-all -o .claude/agents
```

This generates agents customized for .NET:

**Example: Senior Engineer Agent (.claude/agents/senior-engineer.md)**

```markdown
# Senior Engineer - .NET Specialist

## Tech Stack Context
**Project Type**: api
**Languages**: C#
**Frameworks**: .NET 8, ASP.NET Core, Entity Framework Core
**Platforms**: Azure, Docker
**Databases**: SQL Server

## Responsibilities for .NET Projects
- Break down features into implementation tasks
- Design RESTful API controllers and endpoints
- Plan Entity Framework migrations
- Structure dependency injection
- Implement repository pattern
- Design middleware and filters
- Plan unit and integration tests with xUnit
- Estimate story points (Fibonacci: 1, 2, 3, 5, 8, 13)

## Task Breakdown Guidelines for .NET
- **API Controller**: 2-3 story points
- **Entity Model + DbContext**: 1-2 story points
- **EF Migration**: 1 story point
- **Service Layer**: 2-3 story points
- **Unit Tests**: 1-2 story points per component
- **Integration Tests**: 3-5 story points
- **API Documentation (Swagger)**: 1 story point
```

### Render Workflows

```bash
# Render all workflows
cwf workflow render-all -o .claude/commands
```

### Run Sprint Planning

```bash
cwf workflow run sprint-planning --sprint "Sprint 12" --capacity 50
```

The workflow will:
1. Query Azure DevOps for backlog items
2. Analyze with Business Analyst (business value, priorities)
3. Review with Project Architect (C# patterns, EF Core design)
4. Security assessment (OWASP Top 10, SQL injection, etc.)
5. Break down with Senior Engineer (.NET task sizing)
6. Create work items in Azure DevOps
7. Generate deployment tasks (Azure App Service, SQL migrations)

## Integration with .NET Development

### Project Structure

```
CustomerPortalAPI/
├── .claude/
│   ├── config.yaml
│   ├── agents/
│   ├── commands/
│   ├── workflow-state/
│   └── profiling/
├── src/
│   ├── CustomerPortal.API/
│   │   ├── Controllers/
│   │   ├── Models/
│   │   ├── Services/
│   │   └── Program.cs
│   ├── CustomerPortal.Core/
│   │   ├── Entities/
│   │   ├── Interfaces/
│   │   └── Services/
│   └── CustomerPortal.Infrastructure/
│       ├── Data/
│       ├── Repositories/
│       └── Migrations/
├── tests/
│   ├── CustomerPortal.UnitTests/
│   └── CustomerPortal.IntegrationTests/
├── CustomerPortal.sln
└── azure-pipelines.yml
```

### Azure DevOps Pipeline Integration

Add to `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main
      - develop

schedules:
  - cron: "0 9 * * 1"  # Every Monday at 9 AM
    displayName: Weekly Sprint Planning
    branches:
      include:
        - main
    always: true

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: UseDotNet@2
            inputs:
              version: '8.x'

          - task: DotNetCoreCLI@2
            displayName: 'dotnet restore'
            inputs:
              command: 'restore'
              projects: '**/*.csproj'

          - task: DotNetCoreCLI@2
            displayName: 'dotnet build'
            inputs:
              command: 'build'
              projects: '**/*.csproj'

          - task: DotNetCoreCLI@2
            displayName: 'dotnet test with coverage'
            inputs:
              command: 'test'
              projects: '**/*Tests/*.csproj'
              arguments: '--collect:"XPlat Code Coverage"'

          - task: PublishCodeCoverageResults@1
            inputs:
              codeCoverageTool: 'Cobertura'
              summaryFileLocation: '$(Agent.TempDirectory)/**/coverage.cobertura.xml'

  - stage: SprintPlanning
    condition: and(succeeded(), eq(variables['Build.Reason'], 'Schedule'))
    jobs:
      - job: AutomatedSprintPlanning
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'

          - script: |
              pip install trustable-ai
            displayName: 'Install Trustable AI Workbench'

          - script: |
              export AZURE_DEVOPS_PAT=$(AZURE_DEVOPS_PAT)
              export ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY)
              cwf workflow run sprint-planning --sprint "Sprint $(Build.BuildNumber)"
            displayName: 'Run Sprint Planning'
```

### Custom Fields for .NET Projects

Add .NET-specific custom fields in Azure DevOps:

- `Custom.APIContract`: Link to API specification
- `Custom.BreakingChange`: Is this a breaking API change?
- `Custom.EFMigration`: Does this require EF migration?
- `Custom.NuGetPackage`: Which NuGet packages are affected?

Update `.claude/config.yaml`:

```yaml
work_tracking:
  custom_fields:
    business_value: "Microsoft.VSTS.Common.BusinessValue"
    api_contract: "Custom.APIContract"
    breaking_change: "Custom.BreakingChange"
    ef_migration: "Custom.EFMigration"
    nuget_package: "Custom.NuGetPackage"
```

### Quality Gates for .NET

Create `.claude/quality-gates.ps1`:

```powershell
# Run after dotnet test
$coverage = (Get-Content TestResults/*/coverage.cobertura.xml | Select-String -Pattern 'line-rate="([0-9.]+)"').Matches.Groups[1].Value
$coveragePercent = [math]::Round($coverage * 100, 2)

if ($coveragePercent -lt 80) {
    Write-Error "Code coverage $coveragePercent% is below minimum 80%"
    exit 1
}

Write-Host "✓ Code coverage: $coveragePercent%"

# Check for high/critical vulnerabilities
dotnet list package --vulnerable --include-transitive | Select-String -Pattern "Critical|High"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Critical or High vulnerabilities found"
    exit 1
}

Write-Host "✓ No critical/high vulnerabilities"
```

## Customizing Agents for .NET

Edit `.claude/agents/senior-engineer.md`:

```markdown
## .NET-Specific Task Breakdown Patterns

### RESTful API Endpoint
- Create controller class (1-2 SP)
- Implement service layer (2-3 SP)
- Add validation with FluentValidation (1 SP)
- Unit tests for service (1-2 SP)
- Integration tests for controller (2-3 SP)
- Update Swagger documentation (0.5 SP)

### Entity Framework Migration
- Design entity models (1-2 SP)
- Create migration (0.5 SP)
- Add seed data if needed (1 SP)
- Update DbContext (0.5 SP)
- Test migration up/down (1 SP)

### Authentication/Authorization Feature
- Implement JWT middleware (3-5 SP)
- Add role-based authorization (2-3 SP)
- Secure endpoints with [Authorize] (1-2 SP)
- Unit tests for auth logic (2-3 SP)
- Integration tests for secured endpoints (3-5 SP)

### Background Job/Service
- Create hosted service (2-3 SP)
- Implement business logic (3-5 SP)
- Add configuration (1 SP)
- Unit tests (2-3 SP)
- Monitoring/logging (1-2 SP)
```

## Workflow Examples

### 1. Sprint Planning for .NET API

```bash
cwf workflow run sprint-planning --sprint "Sprint 5" --capacity 50
```

**Output**:
```
═══════════════════════════════════════════════════════════════
🎯 Sprint Planning Workflow - Customer Portal API
═══════════════════════════════════════════════════════════════

Step 1: Business Analyst - Backlog Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analyzing 15 backlog items...

High Priority Items:
  ✓ Implement customer registration API (Business Value: 85)
  ✓ Add order history endpoint (Business Value: 75)
  ✓ Customer search with pagination (Business Value: 70)

Step 2: Project Architect - Architecture Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architecture Recommendations:
  - Use repository pattern for data access
  - Implement CQRS for complex queries
  - Add caching layer (Redis) for customer search
  - EF Core migrations for schema changes

Step 3: Security Specialist - Security Assessment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Security Considerations:
  ✓ Add input validation for customer registration
  ✓ Implement rate limiting on search endpoint
  ✓ Encrypt sensitive customer data at rest
  ✓ Use parameterized queries (EF Core handles this)

Step 4: Senior Engineer - Task Breakdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature: Customer Registration API (13 SP total)
  - Create Customer entity model (2 SP)
  - EF migration for Customer table (1 SP)
  - Implement ICustomerRepository (2 SP)
  - Create RegistrationController (2 SP)
  - Add validation with FluentValidation (1 SP)
  - Unit tests for repository (2 SP)
  - Integration tests for API (3 SP)

✓ Created 28 work items in Azure DevOps
✓ Sprint commitment: 48 story points (96% capacity)
```

### 2. Backlog Grooming

```bash
cwf workflow run backlog-grooming --limit 20
```

Updates backlog items with:
- Business value scores
- Technical complexity estimates
- .NET-specific notes (EF migrations needed, breaking changes, etc.)

### 3. Sprint Retrospective

```bash
cwf workflow run sprint-retrospective --sprint "Sprint 4"
```

Generates report with:
- Velocity analysis
- Code quality metrics (test coverage, complexity)
- Security scan results
- .NET-specific improvements (upgrade to .NET 9, refactor middleware, etc.)

## Best Practices for .NET Projects

### 1. Align with .NET Conventions

Update agent templates to follow Microsoft conventions:
- Use PascalCase for public members
- Async suffix for async methods
- Repository pattern for data access
- Dependency injection via constructor

### 2. Integrate with Visual Studio

Add `.claude/` folder to solution for easy access:

```xml
<!-- In .sln file -->
Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "Claude", "Claude", "{GUID}"
    ProjectSection(SolutionItems) = preProject
        .claude\config.yaml = .claude\config.yaml
        .claude\commands\sprint-planning.md = .claude\commands\sprint-planning.md
    EndProjectSection
EndProject
```

### 3. Quality Metrics Integration

Use tools .NET developers already know:
- **Code Coverage**: Coverlet + ReportGenerator
- **Security**: dotnet list package --vulnerable
- **Complexity**: dotnet-metrics or SonarQube
- **Style**: .editorconfig + StyleCop

### 4. Custom Workflows for .NET

Create `.NET-specific workflows`:
- **NuGet Package Update**: Analyze and update dependencies
- **API Versioning**: Plan breaking changes across versions
- **Performance Testing**: Load testing for critical endpoints

## Troubleshooting

### Issue: Work item types don't match

If using Agile template, ensure work item types are correct:

```yaml
work_item_types:
  story: "User Story"  # Not "Product Backlog Item"
  epic: "Epic"
  feature: "Feature"
  task: "Task"
  bug: "Bug"
```

### Issue: Can't access .NET-specific custom fields

Create custom fields in Azure DevOps:
1. Project Settings → Boards → Process
2. Customize your process template
3. Add custom fields
4. Update `.claude/config.yaml` with exact field names

### Issue: Framework doesn't understand C# patterns

Customize `.claude/agents/senior-engineer.md` with .NET examples:
- Show actual C# code snippets
- Reference .NET documentation
- Include common patterns (repository, middleware, filters)

## Next Steps

1. **Customize agents** for your .NET domain (fintech, healthcare, etc.)
2. **Create API specification workflow** for OpenAPI/Swagger
3. **Add database migration workflow** for Entity Framework
4. **Integrate with Azure DevOps Boards** for automatic updates
5. **Train team** on using AI-assisted sprint planning

## Resources

- [.NET Documentation](https://learn.microsoft.com/en-us/dotnet/)
- [Azure DevOps REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/)
- [Trustable AI Workbench](https://github.com/keychain/trustable-ai-workbench)

---

*Example project for Trustable AI Workbench with .NET*
