#!/usr/bin/env python
"""Environment setup script for Deep Agent AGI.

This script automates the initial environment setup by:
- Validating Python 3.10+ and Node.js 18+ are installed
- Creating necessary directories (db/data/, build/, .cache/)
- Creating .env file from .env.example template

Usage:
    python scripts/setup_env.py

Requirements:
    - Python 3.10+
    - Node.js 18+

Examples:
    # First-time setup
    python scripts/setup_env.py

    # Check Python version
    python --version

Exit Codes:
    0 - Setup completed successfully
    1 - Python version too old, Node.js missing, or .env.example not found
"""

import sys
from pathlib import Path


def create_env_file() -> None:
    """Create .env file from .env.example if it doesn't exist."""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if env_file.exists():
        print("✅ .env file already exists")
        return

    if not env_example.exists():
        print("❌ .env.example not found")
        sys.exit(1)

    # Copy .env.example to .env
    env_file.write_text(env_example.read_text())
    print("✅ Created .env file from .env.example")
    print("⚠️  Please edit .env file with your actual API keys")


def check_python_version() -> None:
    """Check if Python version is 3.10+."""
    if sys.version_info < (3, 10):  # noqa: UP036 - intentional runtime check for user-facing validation
        print(f"❌ Python 3.10+ required, found {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_node_version() -> None:
    """Check if Node.js version is 18+."""
    import subprocess  # nosec B404 - needed for Node.js version check

    try:
        result = subprocess.run(  # nosec: B603, B607
            ["node", "--version"], capture_output=True, text=True, check=True
        )
        version = result.stdout.strip()
        major_version = int(version.lstrip("v").split(".")[0])

        if major_version < 18:
            print(f"❌ Node.js 18+ required, found {version}")
            sys.exit(1)

        print(f"✅ Node.js {version} detected")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found. Please install Node.js 18+")
        sys.exit(1)


def create_directories() -> None:
    """Create necessary directories."""
    dirs = [
        "db/data",
        "db/migrations",
        "out/coverage",
        "out/reports",
        "out/debug",
        "out/logs/backend",
        "out/logs/frontend",
        ".cache",
        ".auditor/venv",
        ".auditor/reports",
    ]

    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)

    print(f"✅ Created {len(dirs)} directories")


def main() -> None:
    """Run environment setup."""
    print("🚀 Setting up Deep Agent AGI environment...\n")

    check_python_version()
    check_node_version()
    create_directories()
    create_env_file()

    print("\n✅ Environment setup complete!")
    print("\nNext steps:")
    print("  1. Edit .env file with your API keys")
    print("  2. Run: ./scripts/dev.sh")
    print("  3. Start development!")


if __name__ == "__main__":
    main()
