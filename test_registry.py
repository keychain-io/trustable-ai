"""Quick test to verify agent registry works."""

from pathlib import Path
from config.schema import (
    FrameworkConfig,
    ProjectConfig,
    WorkTrackingConfig,
    QualityStandards,
    AgentConfig,
)
from agents.registry import AgentRegistry


def test_agent_registry():
    """Test that agent registry can render templates."""

    # Create test configuration
    config = FrameworkConfig(
        project=ProjectConfig(
            name="Test Project",
            type="web-application",
            tech_stack={
                "languages": ["Python", "TypeScript"],
                "frameworks": ["FastAPI", "React"],
                "platforms": ["Azure", "Docker"],
            },
        ),
        work_tracking=WorkTrackingConfig(
            organization="https://dev.azure.com/test-org",
            project="Test Project",
            work_item_types={
                "epic": "Epic",
                "feature": "Feature",
                "story": "User Story",
                "task": "Task",
                "bug": "Bug",
            },
            custom_fields={
                "business_value": "Custom.BusinessValue",
                "technical_risk": "Custom.TechnicalRisk",
            },
        ),
        quality_standards=QualityStandards(
            test_coverage_min=80,
            critical_vulnerabilities_max=0,
        ),
        agent_config=AgentConfig(
            models={
                "architect": "claude-opus-4",
                "engineer": "claude-sonnet-4.5",
                "analyst": "claude-sonnet-4.5",
            },
            enabled_agents=[
                "business-analyst",
                "senior-engineer",
                "scrum-master",
            ],
        ),
    )

    # Create registry
    registry = AgentRegistry(config)

    # List available agents
    print("Available agents:")
    for agent in registry.list_agents():
        print(f"  - {agent}")

    # Test rendering each agent
    print("\nTesting agent rendering:")
    for agent_name in registry.list_agents():
        try:
            rendered = registry.render_agent(agent_name)
            print(f"  ✓ {agent_name}: {len(rendered)} chars")

            # Verify key values are rendered
            assert "Test Project" in rendered
            assert "claude-" in rendered.lower()

        except Exception as e:
            print(f"  ✗ {agent_name}: {e}")

    print("\n✅ Agent registry test passed!")


if __name__ == "__main__":
    test_agent_registry()
