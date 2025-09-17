#!/usr/bin/env python3
"""
Setup script for ROKO Token Data Extractor
"""

import os
import sys
import shutil
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from env.example")
            print("📝 Please edit .env file and add your API keys")
        else:
            print("❌ env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def create_directories():
    """Create necessary directories."""
    directories = [
        'data',
        'data/exports',
        'data/historical',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_gitkeep_files():
    """Create .gitkeep files for empty directories."""
    gitkeep_dirs = [
        'data/exports',
        'data/historical',
        'logs'
    ]
    
    for directory in gitkeep_dirs:
        gitkeep_file = Path(directory) / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.touch()
            print(f"✅ Created .gitkeep in {directory}")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import web3
        import requests
        import yaml
        import pandas
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please run: pip install -r requirements.txt")
        return False

def display_setup_instructions():
    """Display setup instructions."""
    print("\n" + "="*80)
    print("🚀 ROKO TOKEN DATA EXTRACTOR - SETUP COMPLETE")
    print("="*80)
    print("\n📋 NEXT STEPS:")
    print("\n1. Configure API Keys:")
    print("   • Edit .env file and add your API keys")
    print("   • At minimum, add ALCHEMY_API_KEY or INFURA_API_KEY")
    print("   • Get free API keys from:")
    print("     - Alchemy: https://www.alchemy.com/")
    print("     - Infura: https://infura.io/")
    
    print("\n2. Test the Setup:")
    print("   • python test_connection.py")
    print("   • python test_load_balancer.py")
    print("   • python run.py --help")
    
    print("\n3. Run the Extractor:")
    print("   • python run.py --export json")
    print("   • python run.py --analytics --export json csv")
    print("   • python run.py --monitor --interval 60")
    
    print("\n4. Get Help:")
    print("   • python run.py --help-detailed")
    print("   • python run.py --help-detailed examples")
    print("   • python run.py --help-detailed configuration")
    
    print("\n📚 DOCUMENTATION:")
    print("   • README.md - Basic usage and setup")
    print("   • DOCUMENTATION.md - Complete documentation")
    print("   • RPC_LOAD_BALANCING_SUMMARY.md - Load balancing details")
    
    print("\n🔧 CONFIGURATION:")
    print("   • config/config.yaml - Main configuration")
    print("   • .env - API keys and environment variables")
    print("   • logs/ - Application logs")
    print("   • data/ - Exported data and historical records")
    
    print("\n" + "="*80)
    print("🎉 Setup complete! Happy token data extracting!")
    print("="*80)

def main():
    """Main setup function."""
    print("🔧 Setting up ROKO Token Data Extractor...")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .gitkeep files
    create_gitkeep_files()
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Display instructions
    display_setup_instructions()

if __name__ == "__main__":
    main()