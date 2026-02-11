#!/usr/bin/env python3
"""
Test data generator - Creates sample product files for testing
"""

import json
from pathlib import Path


def create_test_data():
    """Create sample product files for testing."""
    
    # Create test directory
    test_dir = Path("./raw_assets")
    test_dir.mkdir(exist_ok=True)
    
    # Sample product IDs
    products = ["PROD001", "PROD002", "PROD003"]
    
    for product_id in products:
        # Create dummy GLTF file
        gltf_content = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": [0]}]
        }
        
        gltf_path = test_dir / f"{product_id}_model.gltf"
        with open(gltf_path, 'w') as f:
            json.dump(gltf_content, f, indent=2)
        
        # Create dummy BIN file
        bin_path = test_dir / f"{product_id}_model.bin"
        with open(bin_path, 'wb') as f:
            f.write(b'\x00' * 1024)  # 1KB of zeros
        
        # Create dummy GLB file
        glb_path = test_dir / f"{product_id}_model.glb"
        with open(glb_path, 'wb') as f:
            f.write(b'glTF' + b'\x00' * 1020)  # 1KB GLB file
        
        # Create dummy texture files
        textures = [
            f"{product_id}_DefaultMaterial_baseColor_1001.png",
            f"{product_id}_DefaultMaterial_normal_1001.png",
            f"{product_id}_DefaultMaterial_occlusionRoughnessMetallic_1001.png"
        ]
        
        for texture_name in textures:
            texture_path = test_dir / texture_name
            # Create a minimal PNG (1x1 pixel, black)
            png_data = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixel
                0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
                0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
                0x54, 0x08, 0xD7, 0x63, 0x60, 0x00, 0x00, 0x00,
                0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC, 0x33, 0x00,
                0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
                0x42, 0x60, 0x82
            ])
            with open(texture_path, 'wb') as f:
                f.write(png_data)
        
        # Create dummy thumbnail
        thumbnail_path = test_dir / f"{product_id}_thumbnail.png"
        with open(thumbnail_path, 'wb') as f:
            f.write(png_data)  # Reuse the minimal PNG
        
        # Create dummy metadata (optional)
        metadata = {
            "product_id": product_id,
            "name": f"Test Product {product_id}",
            "description": "Test product for automation script",
            "category": "3D Models"
        }
        metadata_path = test_dir / f"{product_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Created test files for {product_id}")
    
    print(f"\n✅ Test data created in: {test_dir.absolute()}")
    print(f"Total files: {len(list(test_dir.iterdir()))}")
    print("\nYou can now run the organizer script!")


if __name__ == "__main__":
    create_test_data()
