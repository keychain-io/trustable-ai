"""
Setup configuration for Trustable AI.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="trustable-ai",
    version="2.0.6",
    author="Trustable AI Contributors",
    description="AI-assisted software lifecycle tools with multi-agent orchestration, state management, and work tracking integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/keychain-io/trustable-ai",
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
    },
    entry_points={
        "console_scripts": [
            "trustable-ai=cli.main:cli",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
