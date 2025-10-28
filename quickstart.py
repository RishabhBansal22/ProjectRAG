#!/usr/bin/env python3
"""Quick start script for RAG project."""
import sys
import os
import subprocess
from pathlib import Path


def check_env_file():
    """Check if .env file exists."""
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("📝 Please create a .env file from .env.example:")
        print("   cp .env.example .env")
        print("   Then edit .env and add your API keys")
        return False
    print("✅ .env file found")
    return True


def check_env_variables():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["GOOGLE_API_KEY", "QDRANT_API_KEY", "QDRANT_URL"]
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("📝 Please set them in your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True


def main():
    """Main function."""
    print("� RAG Project Quick Start")
    print("=" * 50)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    if not check_env_variables():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("� Starting RAG Agent")
    print("=" * 50)
    print("\nYou will be prompted to provide a URL.")
    print("The system will automatically index it if needed.")
    print("\n" + "=" * 50)
    
    # Get URL from user
    url = input("\n🔗 Enter the URL to chat about: ").strip()
    
    if not url:
        print("❌ No URL provided")
        sys.exit(1)
    
    # Run the agent with the URL
    try:
        subprocess.run(
            [sys.executable, "agent/main.py", url],
            cwd=Path(__file__).parent
        )
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
