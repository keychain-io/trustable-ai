"""
Azure CLI Wrapper for Claude Code Agents
Simplifies Azure DevOps operations with battle-tested patterns
"""

import sys
from pathlib import Path

# Add this directory to path to allow direct imports
skill_dir = Path(__file__).parent
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from azure_cli import AzureCLI

# Singleton instance for convenience
azure_cli = AzureCLI()

__all__ = ['AzureCLI', 'azure_cli']
