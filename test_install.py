#!/usr/bin/env python3
"""
Installation Test Script
Run this to verify all dependencies are properly installed.
"""

import sys


def test_imports():
    """Test if all required packages can be imported."""

    print("=" * 60)
    print("Testing Lecture Assistant Agent Dependencies")
    print("=" * 60)

    required_packages = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('websockets', 'WebSocket support'),
        ('pydantic', 'Data validation'),
        ('openai', 'OpenAI API client'),
        ('dotenv', 'Environment variables'),
        ('googleapiclient', 'Google API client'),
        ('aiofiles', 'Async file operations'),
    ]

    optional_packages = [
        ('langgraph', 'LangGraph workflow'),
        ('langchain', 'LangChain framework'),
        ('langchain_openai', 'LangChain OpenAI integration'),
        ('tiktoken', 'Token counting'),
    ]

    failed_required = []
    failed_optional = []

    print("\n📦 Testing Required Packages:")
    print("-" * 60)
    for module, description in required_packages:
        try:
            __import__(module)
            print(f"✓ {module:20} - {description}")
        except ImportError as e:
            print(f"✗ {module:20} - MISSING: {description}")
            failed_required.append((module, str(e)))

    print("\n📦 Testing Optional Packages:")
    print("-" * 60)
    for module, description in optional_packages:
        try:
            __import__(module)
            print(f"✓ {module:20} - {description}")
        except ImportError as e:
            print(f"⚠ {module:20} - WARNING: {description}")
            failed_optional.append((module, str(e)))

    # Test Python version
    print("\n🐍 Python Version:")
    print("-" * 60)
    py_version = sys.version_info
    print(f"Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 9):
        print("⚠ Warning: Python 3.9+ recommended")
    else:
        print("✓ Version OK")

    # Test specific imports
    print("\n🔧 Testing Core Functionality:")
    print("-" * 60)

    try:
        from backend.state import ResearchState
        print("✓ Backend state models")
    except Exception as e:
        print(f"✗ Backend state models: {e}")
        failed_required.append(('backend.state', str(e)))

    try:
        from backend.utils import get_model_settings
        print("✓ Backend utilities")
    except Exception as e:
        print(f"✗ Backend utilities: {e}")
        failed_required.append(('backend.utils', str(e)))

    try:
        from backend.logger import execution_logger
        print("✓ Logging system")
    except Exception as e:
        print(f"✗ Logging system: {e}")
        failed_required.append(('backend.logger', str(e)))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if failed_required:
        print(f"\n❌ {len(failed_required)} REQUIRED packages are missing:")
        for module, error in failed_required:
            print(f"   - {module}")
        print("\n📖 See TROUBLESHOOTING.md for installation help")
        print("\n💡 Quick fixes:")
        print("   1. Try: pip install -r requirements-minimal.txt")
        print("   2. Use conda: conda install -c conda-forge <package>")
        print("   3. Check TROUBLESHOOTING.md for detailed solutions")
        return False
    else:
        print("\n✅ All required packages installed successfully!")

    if failed_optional:
        print(f"\n⚠️  {len(failed_optional)} optional packages missing (non-critical):")
        for module, error in failed_optional:
            print(f"   - {module}")
    else:
        print("✅ All optional packages installed!")

    print("\n🎉 Installation test complete!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env")
    print("2. Add your API keys to .env")
    print("3. Run: uvicorn backend.main:app --reload")
    print("4. In another terminal: cd frontend && npm run dev")

    return True


def test_env_file():
    """Check if .env file exists."""
    import os

    print("\n📝 Testing Environment Configuration:")
    print("-" * 60)

    if os.path.exists('.env'):
        print("✓ .env file found")

        from dotenv import load_dotenv
        load_dotenv()

        keys_to_check = [
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY',
            'GOOGLE_CSE_ID'
        ]

        missing_keys = []
        for key in keys_to_check:
            value = os.getenv(key)
            if value and value != f'your_{key.lower()}_here':
                print(f"✓ {key} configured")
            else:
                print(f"⚠ {key} not configured")
                missing_keys.append(key)

        if missing_keys:
            print(f"\n⚠️  {len(missing_keys)} API keys need configuration")
            print("Edit .env file and add your API keys")
    else:
        print("⚠ .env file not found")
        print("Run: cp .env.example .env")
        print("Then edit .env with your API keys")


if __name__ == "__main__":
    print()
    success = test_imports()
    test_env_file()
    print()

    if not success:
        sys.exit(1)
