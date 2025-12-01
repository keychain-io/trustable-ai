"""
Trustable AI - Skills System

Skills provide reusable capabilities for common development tasks.
Each skill includes Python implementations and documentation.

Available Skills:
- azure_devops: Azure DevOps operations (CLI wrapper, bulk operations)
- workflow: Workflow management (state, profiling)
- context: Context loading and optimization
- learnings: Knowledge capture and management
- coordination: Cross-repo coordination
"""

from .registry import SkillRegistry, get_skill, list_skills

__all__ = [
    "SkillRegistry",
    "get_skill",
    "list_skills",
]
