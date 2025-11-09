"""
Setup configuration for Claude Workflow Framework.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="claude-workflow-framework",
    version="0.1.0",
    author="Keychain Team",
    description="A reusable workflow automation framework for Claude Code with multi-agent orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/keychain/claude-workflow-framework",
    packages=find_packages(),
    package_data={
        "": ["*.j2", "*.yaml", "*.yml", "*.md"],
    },
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "azure": [
            "azure-cli-core>=2.50.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cwf=cli.main:cli",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
