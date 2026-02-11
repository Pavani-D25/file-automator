# Product Asset Organizer for S3

Automatically organize 3D product assets (glTF, GLB, textures) into structured folders and upload to AWS S3.

## 📁 Output Structure

For each product (e.g., `XOBC_005`), creates:

```
organized_products/
└── XOBC_005/
    ├── XOBC_005.zip                    # Contains: .gltf, .bin, 3 texture PNGs
    ├── XOBC_005.glb                    # Binary glTF file
    ├── XOBC_005_thumbnail.png          # Product thumbnail
    └── XOBC_005_metadata.json          # Product metadata
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip3 install boto3

# Or using the requirements file
pip3 install -r requirements.txt
```

### 2. Setup (Optional automated setup)

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Organize Your Files

Put all your product files in the `raw_assets/` folder:

```
raw_assets/
├── XOBC_005_model.gltf
├── XOBC_005_model.bin
├── XOBC_005_DefaultMaterial_baseColor_1001.png
├── XOBC_005_DefaultMaterial_normal_1001.png
├── XOBC_005_DefaultMaterial_occlusionRoughnessMetallic_1001.png
├── XOBC_005_model.glb
├── XOBC_005_thumbnail.png
├── XOBC_010_model.gltf
├── XOBC_010_model.bin
└── ... (more files)
```

**Important:** Files should start with the same Product ID. The script recognizes:
- `XOBC_005_*` → Product ID: `XOBC_005`
- `XOBC_010_*` → Product ID: `XOBC_010`
- `PROD123_*` → Product ID: `PROD123`

### 4. Configure S3 (Optional)

Edit `product_organizer_final.py` and set your S3 bucket:

```python
S3_BUCKET = "your-bucket-name"  # Change from None to your bucket
S3_PREFIX = "products"           # Optional: change the S3 folder
```

### 5. Run the Organizer

```bash
python3 product_organizer_final.py
```

## 📋 File Requirements

Each product needs:

| File Type | Quantity | Purpose | Example Name |
|-----------|----------|---------|--------------|
| `.gltf` | 1 | 3D model | `XOBC_005_model.gltf` |
| `.bin` | 1 | Binary data | `XOBC_005_model.bin` |
| `.png` (textures) | 3 | Material textures | `XOBC_005_DefaultMaterial_baseColor_1001.png` |
| `.glb` | 1 | Binary glTF | `XOBC_005_model.glb` |
| `.png` (thumbnail) | 1 | Preview image | `XOBC_005_thumbnail.png` |
| `.json` | 0-1 | Metadata (optional) | `XOBC_005_metadata.json` |

### Texture File Naming

The script looks for these keywords in texture filenames:
- `baseColor` or `basecolor`
- `normal`
- `occlusion`, `roughness`, `metallic`, or `ORM`

Example valid names:
- `DefaultMaterial_baseColor_1001.png`
- `OBC-005_normal_map.png`
- `Material_occlusionRoughnessMetallic.png`

## ⚙️ Configuration

### Basic Configuration

Edit these variables in `product_organizer_final.py`:

```python
SOURCE_DIR = "./raw_assets"              # Your input folder
OUTPUT_DIR = "./organized_products"       # Output folder
S3_BUCKET = None                          # S3 bucket name (or None)
S3_PREFIX = "products"                    # S3 path prefix
```

### AWS S3 Setup

**Option 1: AWS CLI (Recommended)**
```bash
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
```

**Option 2: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option 3: IAM Role** (if running on EC2)
- No configuration needed, will use instance role

### S3 Bucket Permissions

Your AWS user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

## 🧪 Testing

Test with sample data before using real files:

```bash
# Generate test files
python3 create_test_data.py

# Run organizer
python3 product_organizer_final.py

# Check output
ls -la organized_products/PROD001/
```

## 📊 S3 Upload Structure

Files are uploaded to:

```
s3://your-bucket-name/
└── products/
    ├── OBC-005/
    │   ├── OBC-005.zip
    │   ├── OBC-005.glb
    │   ├── OBC-005_thumbnail.png
    │   └── OBC-005_metadata.json
    ├── PROD-123/
    │   └── ...
```

You can change `products/` by editing the `S3_PREFIX` variable.

## 🔧 Customization

### Different Product ID Format

If your files use a different naming pattern, edit the `extract_product_id` method:

**Example 1:** Files like `Product_ABC_123_model.gltf` (want `Product_ABC_123`)

```python
def extract_product_id(self, filename: str) -> str:
    # Take first 3 parts
    parts = filename.split('_')
    if len(parts) >= 3:
        return '_'.join(parts[:3])
    return filename
```

**Example 2:** Files like `SKU-12345-v2.gltf` (want `SKU-12345`)

```python
def extract_product_id(self, filename: str) -> str:
    import re
    match = re.search(r'(SKU-\d+)', filename)
    if match:
        return match.group(1)
    return filename.split('_')[0]
```

### Custom Metadata Fields

Add custom fields to metadata by editing `create_metadata`:

```python
metadata = {
    "product_id": product_id,
    "created_at": datetime.now().isoformat(),
    "version": "1.0",
    "category": "furniture",  # Add your fields
    "price": 99.99,
    # ... existing fields
}
```

## 📝 Logs

The script creates a log file: `product_organizer.log`

```bash
# View logs
tail -f product_organizer.log

# View errors only
grep ERROR product_organizer.log
```

## 🐛 Troubleshooting

### "No products found"

**Cause:** Files don't match expected naming pattern

**Solution:**
1. Check files are in `raw_assets/` folder
2. Verify file naming starts with Product ID
3. Run test data generator to verify script works:
   ```bash
   python3 create_test_data.py
   python3 product_organizer_final.py
   ```

### "Missing critical files"

**Cause:** Product missing required .gltf, .bin, or .glb files

**Solution:**
1. Check all required files are present
2. Verify files share the same Product ID prefix
3. Check file extensions are lowercase (.gltf not .GLTF)

### "Only X texture(s) found (need 3)"

**Cause:** Less than 3 texture files found

**Solution:**
1. Check texture files contain required keywords (baseColor, normal, occlusion/roughness/metallic)
2. Verify texture file names
3. Script will still process if other files are present

### S3 Upload Fails

**Problem:** "NoCredentialsError"

**Solution:**
```bash
aws configure
# Or check: aws sts get-caller-identity
```

**Problem:** "Access Denied"

**Solution:** 
- Check bucket exists: `aws s3 ls s3://your-bucket-name/`
- Verify IAM permissions include `s3:PutObject`

**Problem:** "Bucket not found"

**Solution:**
- Create bucket: `aws s3 mb s3://your-bucket-name`
- Or fix bucket name in script

### Permission Errors

```bash
chmod +x product_organizer_final.py
chmod +x setup.sh
```

## 💡 Tips

1. **Test First:** Always run with test data before processing real products
2. **Backup:** Keep original files safe before running
3. **Check Logs:** Review `product_organizer.log` for details
4. **Batch Processing:** Script handles all products in one run
5. **Validation:** Script validates files before processing

## 📚 Examples

### Example 1: Local Organization Only

```python
# product_organizer_final.py
SOURCE_DIR = "./my_products"
OUTPUT_DIR = "./organized"
S3_BUCKET = None  # No S3 upload
```

```bash
python3 product_organizer_final.py
```

### Example 2: With S3 Upload

```python
# product_organizer_final.py
SOURCE_DIR = "./my_products"
OUTPUT_DIR = "./organized"
S3_BUCKET = "my-company-products"
S3_PREFIX = "3d-models"
```

```bash
python3 product_organizer_final.py
```

Files uploaded to: `s3://my-company-products/3d-models/PRODUCT_ID/`

### Example 3: Different Source Location

```python
SOURCE_DIR = "/path/to/dropbox/products"
OUTPUT_DIR = "./processed"
S3_BUCKET = "product-assets-bucket"
```

## 🔐 Security Best Practices

1. **Don't hardcode credentials** in the script
2. **Use IAM roles** when running on AWS
3. **Set bucket policies** to restrict access
4. **Enable S3 versioning** for backup
5. **Use environment variables** for sensitive data

## 📞 Support

Check the log file for detailed error messages:
```bash
cat product_organizer.log
```

## 📄 License

MIT License - Feel free to modify for your needs.

---

**Made with ❤️ for efficient 3D asset management**#   f i l e - a u t o m a t o r  
 