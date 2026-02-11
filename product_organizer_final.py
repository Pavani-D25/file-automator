#!/usr/bin/env python3
"""
Product Asset Organizer - Production Version
Organizes product files and uploads to S3

Structure for each product (e.g., OBC-005):
  OBC-005/
    ├── OBC-005.zip (contains: .gltf, .bin, 3x texture PNGs)
    ├── OBC-005.glb
    ├── OBC-005_thumbnail.png
    └── OBC-005_metadata.json
"""

import os
import json
import zipfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_organizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductOrganizer:
    """Organizes product assets and uploads to S3"""
    
    def __init__(self, source_dir: str, output_dir: str, 
                 s3_bucket: Optional[str] = None, s3_prefix: str = "products"):
        """
        Initialize organizer
        
        Args:
            source_dir: Directory containing raw product files
            output_dir: Directory for organized product folders
            s3_bucket: S3 bucket name (optional)
            s3_prefix: S3 path prefix (default: "products")
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        
        # Initialize S3 client
        self.s3_client = None
        if s3_bucket:
            try:
                self.s3_client = boto3.client('s3')
                logger.info(f"✓ S3 client initialized for bucket: {s3_bucket}")
            except NoCredentialsError:
                logger.error("AWS credentials not found! Please configure AWS credentials.")
                logger.info("Run: aws configure")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'uploaded': 0
        }
    
    def extract_product_id(self, filename: str) -> str:
        """
        Extract product ID from filename
        
        Examples:
            OBC-005_model.gltf -> OBC-005
            PROD_123_texture.png -> PROD_123
        """
        # Split by underscore and take first part
        parts = filename.split('_')
        if parts:
            return parts[0]
        return filename
    
    def scan_products(self) -> Dict[str, Dict[str, List[Path]]]:
        """
        Scan source directory for product folders and group files by product ID
        
        Returns:
            Dict mapping product_id to categorized files
        """
        if not self.source_dir.exists():
            logger.error(f"Source directory not found: {self.source_dir}")
            return {}
        
        products = {}
        logger.info(f"Scanning directory: {self.source_dir}")
        
        # Scan for product folders (first level subdirectories)
        for product_folder in self.source_dir.iterdir():
            if not product_folder.is_dir():
                continue
            
            # Use folder name as product ID
            product_id = product_folder.name
            
            # Initialize product entry
            products[product_id] = {
                'gltf': [],
                'bin': [],
                'textures': [],
                'glb': [],
                'thumbnail': [],
                'json': []
            }
            
            # Scan files within product folder
            for file_path in product_folder.iterdir():
                if not file_path.is_file():
                    continue
                
                # Categorize file
                ext = file_path.suffix.lower()
                name_lower = file_path.stem.lower()
                
                if ext == '.gltf':
                    products[product_id]['gltf'].append(file_path)
                elif ext == '.bin':
                    products[product_id]['bin'].append(file_path)
                elif ext == '.glb':
                    products[product_id]['glb'].append(file_path)
                elif ext == '.json':
                    products[product_id]['json'].append(file_path)
                elif ext == '.png' or ext == '.jpg':
                    # Check if it's a texture or thumbnail
                    texture_keywords = ['basecolor', 'normal', 'occlusion', 'roughness', 
                                      'metallic', 'orm', 'material']
                    is_texture = any(kw in name_lower for kw in texture_keywords)
                    
                    if 'thumbnail' in name_lower or 'thumb' in name_lower:
                        products[product_id]['thumbnail'].append(file_path)
                    elif is_texture:
                        products[product_id]['textures'].append(file_path)
                    else:
                        # If no clear indication, check if we already have a thumbnail
                        if not products[product_id]['thumbnail']:
                            products[product_id]['thumbnail'].append(file_path)
                        else:
                            products[product_id]['textures'].append(file_path)
        
        self.stats['total'] = len(products)
        logger.info(f"Found {len(products)} product(s)")
        
        return products
    
    def validate_product(self, product_id: str, files: Dict[str, List[Path]]) -> tuple:
        """
        Validate product has required files
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required files for ZIP
        if not files['gltf']:
            issues.append("Missing .gltf file")
        if not files['bin']:
            issues.append("Missing .bin file")
        if len(files['textures']) < 3:
            issues.append(f"Only {len(files['textures'])} texture(s) found (need 3)")
        
        # Check required standalone files
        if not files['glb']:
            issues.append("Missing .glb file")
        # Thumbnail is optional (can use product .jpg instead)
        
        return (len(issues) == 0, issues)
    
    def create_zip(self, product_folder: Path, product_id: str, files: Dict) -> bool:
        """
        Create ZIP file containing .gltf, .bin, and 3 texture PNGs
        
        Returns:
            True if successful
        """
        try:
            zip_path = product_folder / f"{product_id}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add .gltf file
                if files['gltf']:
                    gltf_file = files['gltf'][0]
                    zipf.write(gltf_file, gltf_file.name)
                    logger.info(f"    Added to ZIP: {gltf_file.name}")
                
                # Add .bin file
                if files['bin']:
                    bin_file = files['bin'][0]
                    zipf.write(bin_file, bin_file.name)
                    logger.info(f"    Added to ZIP: {bin_file.name}")
                
                # Add 3 texture files
                for i, texture in enumerate(files['textures'][:3], 1):
                    zipf.write(texture, texture.name)
                    logger.info(f"    Added to ZIP: {texture.name}")
            
            logger.info(f"  ✓ Created: {zip_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Failed to create ZIP: {e}")
            return False
    
    def create_metadata(self, product_folder: Path, product_id: str, files: Dict):
        """Create metadata JSON file"""
        metadata = {
            "product_id": product_id,
            "created_at": datetime.now().isoformat(),
            "files": {
                "zip": f"{product_id}.zip",
                "glb": f"{product_id}.glb",
                "thumbnail": f"{product_id}_thumbnail.png"
            },
            "zip_contents": {
                "gltf": files['gltf'][0].name if files['gltf'] else None,
                "bin": files['bin'][0].name if files['bin'] else None,
                "textures": [t.name for t in files['textures'][:3]]
            },
            "status": "processed"
        }
        
        # If original metadata exists, merge it
        if files['json']:
            try:
                with open(files['json'][0], 'r') as f:
                    original_metadata = json.load(f)
                    metadata.update(original_metadata)
            except Exception as e:
                logger.warning(f"  ⚠ Could not read original metadata: {e}")
        
        # Save metadata
        metadata_path = product_folder / f"{product_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"  ✓ Created: {metadata_path.name}")
    
    def process_product(self, product_id: str, files: Dict) -> Optional[Path]:
        """
        Process a single product: create folder structure
        
        Returns:
            Path to product folder if successful
        """
        logger.info(f"\n📦 Processing: {product_id}")
        
        # Validate files
        is_valid, issues = self.validate_product(product_id, files)
        
        if not is_valid:
            logger.warning(f"  ⚠ Validation issues:")
            for issue in issues:
                logger.warning(f"    - {issue}")
            
            # Only skip if critical files are missing
            if not files['gltf'] or not files['bin'] or not files['glb']:
                logger.error(f"  ✗ Skipping: Missing critical files")
                return None
        
        # Create product folder
        product_folder = self.output_dir / product_id
        product_folder.mkdir(exist_ok=True)
        logger.info(f"  Created folder: {product_folder.name}/")
        
        # Create ZIP file
        if not self.create_zip(product_folder, product_id, files):
            return None
        
        # Copy .glb file
        if files['glb']:
            glb_src = files['glb'][0]
            glb_dest = product_folder / f"{product_id}.glb"
            shutil.copy2(glb_src, glb_dest)
            logger.info(f"  ✓ Copied: {glb_dest.name}")
        
        # Copy thumbnail (use .png if available, otherwise .jpg)
        thumbnail_file = None
        if files['thumbnail']:
            thumbnail_file = files['thumbnail'][0]
        else:
            # Look for .jpg file as fallback
            for file_path in (self.source_dir / product_id).iterdir():
                if file_path.suffix.lower() == '.jpg':
                    thumbnail_file = file_path
                    break
        
        if thumbnail_file:
            thumb_dest = product_folder / f"{product_id}_thumbnail.png"
            shutil.copy2(thumbnail_file, thumb_dest)
            logger.info(f"  ✓ Copied: {thumb_dest.name}")
        
        # Create metadata
        self.create_metadata(product_folder, product_id, files)
        
        logger.info(f"✅ Completed: {product_id}")
        return product_folder
    
    def upload_to_s3(self, product_folder: Path, product_id: str) -> bool:
        """
        Upload product folder to S3
        
        Uploads to: s3://bucket/products/PRODUCT_ID/
        """
        if not self.s3_client or not self.s3_bucket:
            return False
        
        try:
            uploaded_count = 0
            
            for file_path in product_folder.iterdir():
                if file_path.is_file():
                    # Construct S3 key
                    s3_key = f"{self.s3_prefix}/{product_id}/{file_path.name}"
                    
                    # Upload file
                    self.s3_client.upload_file(
                        str(file_path),
                        self.s3_bucket,
                        s3_key
                    )
                    uploaded_count += 1
                    logger.info(f"  ☁ Uploaded: s3://{self.s3_bucket}/{s3_key}")
            
            logger.info(f"  ✓ Uploaded {uploaded_count} file(s) to S3")
            return True
            
        except ClientError as e:
            logger.error(f"  ✗ S3 upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"  ✗ Unexpected error during upload: {e}")
            return False
    
    def process_all(self, upload_s3: bool = True):
        """
        Main processing function
        
        Args:
            upload_s3: Whether to upload to S3 after organizing
        """
        logger.info("=" * 70)
        logger.info("PRODUCT ASSET ORGANIZER")
        logger.info("=" * 70)
        
        # Scan products
        products = self.scan_products()
        
        if not products:
            logger.warning("No products found!")
            return
        
        # Process each product
        for product_id, files in products.items():
            product_folder = self.process_product(product_id, files)
            
            if product_folder:
                self.stats['success'] += 1
                
                # Upload to S3 if enabled
                if upload_s3 and self.s3_client:
                    if self.upload_to_s3(product_folder, product_id):
                        self.stats['uploaded'] += 1
            else:
                self.stats['failed'] += 1
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total products:        {self.stats['total']}")
        logger.info(f"Successfully processed: {self.stats['success']}")
        logger.info(f"Failed:                {self.stats['failed']}")
        
        if self.s3_client:
            logger.info(f"Uploaded to S3:        {self.stats['uploaded']}")
            logger.info(f"\nS3 Location: s3://{self.s3_bucket}/{self.s3_prefix}/")
        
        logger.info(f"\nLocal Output: {self.output_dir.absolute()}")
        logger.info("=" * 70)


def main():
    """Main execution"""
    
    # ============================================
    # CONFIGURATION - EDIT THESE VALUES
    # ============================================
    
    SOURCE_DIR = "./raw_assets"              # Your source folder with all product files
    OUTPUT_DIR = "./organized_products"       # Where to create organized folders
    
    # S3 Configuration (optional)
    S3_BUCKET = None                          # Set to your bucket name, e.g., "my-products-bucket"
    S3_PREFIX = "products"                    # S3 folder prefix
    
    # ============================================
    
    # Create organizer
    organizer = ProductOrganizer(
        source_dir=SOURCE_DIR,
        output_dir=OUTPUT_DIR,
        s3_bucket=S3_BUCKET,
        s3_prefix=S3_PREFIX
    )
    
    # Process all products
    upload_to_s3 = (S3_BUCKET is not None)
    organizer.process_all(upload_s3=upload_to_s3)


if __name__ == "__main__":
    main()
