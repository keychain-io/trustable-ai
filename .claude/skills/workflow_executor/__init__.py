"""
Workflow Executor - External Enforcement Engine

This module provides external enforcement for critical SDLC workflows.

The Problem:
    AI agents are unreliable - they skip steps, bypass gates, claim completion
    without verification. More explicit instructions don't help because AI
    optimizes for goals rather than following procedures.

The Solution:
    External enforcement scripts that control execution flow, verify each step
    externally, and use blocking approval gates that AI cannot bypass.

Key Workflows:
    - sprint_review_enforced: Sprint review with guaranteed compliance
    - (Future) deployment_enforced: Deployment with security gates
    - (Future) release_enforced: Release with quality verification

Usage:
    # Via slash command in Claude Code
    /sprint-review-enforced Sprint 7

    # Or directly
    python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7"

Architecture:
    1. Script controls flow (not AI)
    2. Each step verified externally before proceeding
    3. Approval gates are truly blocking (Python input())
    4. Claude API used for analysis only
    5. Full audit trail of all steps
    6. Cannot skip steps or bypass gates

This demonstrates the breakthrough design: Combining Claude's reasoning
with external enforcement creates reliable, trustworthy AI-assisted development.
"""

__version__ = "1.0.0"
__all__ = ["SprintReviewEnforcer"]

from .sprint_review_enforced import SprintReviewEnforcer
