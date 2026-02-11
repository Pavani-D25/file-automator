#!/usr/bin/env python3
"""
Cleanup Script - Remove incorrectly organized product folders
"""

import shutil
from pathlib import Path

def cleanup_organized_products():
    """Remove the organized_products folder to start fresh"""
    
    output_dir = Path("./organized_products")
    
    if output_dir.exists():
        print(f"Removing: {output_dir}")
        shutil.rmtree(output_dir)
        print("✓ Cleaned up organized_products folder")
    else:
        print("✓ No organized_products folder found (already clean)")
    
    print("\nYou can now run the script again:")
    print("  python3 product_organizer_final.py")


if __name__ == "__main__":
    print("=" * 50)
    print("CLEANUP SCRIPT")
    print("=" * 50)
    print("\nThis will delete the organized_products folder")
    print("so you can re-run the organizer with the fixed script.")
    print()
    
    response = input("Continue? (y/n): ")
    
    if response.lower() == 'y':
        cleanup_organized_products()
    else:
        print("Cancelled.")