import os
import sys
import urllib.request
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# Add project root directory to sys.path to resolve backend imports
backend_dir = os.path.dirname(__file__)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

# Create dataset directory
dataset_dir = os.path.join(backend_dir, "dataset")
os.makedirs(dataset_dir, exist_ok=True)

# Database Setup
db_connected = False
try:
    from sqlmodel import Session, select, text
    from backend.app.models.database import engine, DatasetCatalog
    with Session(engine) as session:
        # Clear previous dataset catalogs in bulk to prevent timeout
        session.execute(text("DELETE FROM datasetcatalog"))
        session.commit()
        print("[INFO] Cleared previous database dataset catalog in bulk.")
    db_connected = False
except Exception as e:
    print(f"[WARNING] Database connection failed for dataset cataloging: {e}")
    db_connected = False

# 1. Download Font if not present
font_path = os.path.join(backend_dir, "NotoSansJavanese-Regular.ttf")
if not os.path.exists(font_path):
    print("[INFO] Downloading Javanese Unicode font...")
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansJavanese/NotoSansJavanese-Regular.ttf"
    try:
        urllib.request.urlretrieve(font_url, font_path)
        print("[INFO] Font downloaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to download font: {e}")
        os._exit(1)

# 2. Define Character Mappings
bases_mapping = {
    # Standard bases (20)
    "ha": "ꦲ", "na": "ꦤ", "ca": "ꦕ", "ra": "ꦫ", "ka": "ꦏ",
    "da": "ꦢ", "ta": "ꦠ", "sa": "ꦱ", "wa": "ꦮ", "la": "ꦭ",
    "pa": "ꦥ", "dha": "ꦝ", "ja": "ꦗ", "ya": "ꦪ", "nya": "ꦚ",
    "ma": "ꦩ", "ga": "ꦒ", "ba": "ꦧ", "tha": "ꦛ", "nga": "ꦔ",
    "pangkon": "\uA9C0",
}

bases_list = list(bases_mapping.keys())
vowels_list = ["a", "e", "i", "o", "u", "è"]
finals_list = ["none", "h", "ng", "r"]

def generate_char_image(text, font_path, size=64, font_size=38, rotate=0, blur=0.0, shift=(0, 0)):
    # Render text to image
    img = Image.new("L", (size * 2, size * 2), 255) # Larger canvas to avoid cropping during rotation
    draw = ImageDraw.Draw(img)
    
    font = ImageFont.truetype(font_path, font_size)
    
    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    # Draw centered with slight shift
    x = (size * 2 - w) // 2 - bbox[0] + shift[0]
    y = (size * 2 - h) // 2 - bbox[1] + shift[1]
    draw.text((x, y), text, fill=0, font=font)
    
    # Apply rotation
    if rotate != 0:
        img = img.rotate(rotate, fillcolor=255)
        
    # Crop back to size
    crop_x = (size * 2 - size) // 2
    crop_y = (size * 2 - size) // 2
    img = img.crop((crop_x, crop_y, crop_x + size, crop_y + size))
    
    # Apply blur
    if blur > 0.0:
        img = img.filter(ImageFilter.GaussianBlur(blur))
        
    return img

print("[INFO] Generating synthetic augmented Javanese script dataset...")

db_entries = []
count = 0
# Generate combinations
# To keep training fast, we generate 3 variations for each possible combination of standard/rekan/murda bases + diacritics
# And we also generate pasangans mapped to the standard base folders!
for base_name, unicode_char in bases_mapping.items():
    # Detect if Swara, Number, or Pangkon (doesn't take vowels/finals)
    is_standalone = base_name in ["A", "I", "U", "E", "O", "pangkon"] or base_name.isdigit()
    
    if is_standalone:
        # Just generate standalone variations
        var_limit = 500 if base_name == "pangkon" else 25
        for var in range(var_limit): # More variations for standalone symbols to balance the dataset
            rotate = random.uniform(-10, 10)
            font_size = random.randint(34, 42)
            shift = (random.randint(-4, 4), random.randint(-4, 4))
            blur = random.uniform(0, 0.6)
            
            img = generate_char_image(unicode_char, font_path, font_size=font_size, rotate=rotate, blur=blur, shift=shift)
            
            filename = f"{base_name}_a_none_{count}.png"
            img.save(os.path.join(dataset_dir, filename))
            
            if db_connected:
                db_entries.append(DatasetCatalog(
                    filename=filename,
                    base_label=base_name,
                    vowel_label="a",
                    final_label="none",
                    origin="standalone"
                ))
            count += 1
    else:
        # Generate vowel & final combinations
        for vowel in vowels_list:
            for final in finals_list:
                # Build Unicode String
                char_str = unicode_char
                
                # Apply Vowel
                if vowel == "i":
                    char_str += "\uA9B6" # wulu
                elif vowel == "u":
                    char_str += "\uA9B8" # suku
                elif vowel == "e":
                    char_str += "\uA9BC" # pepet
                elif vowel == "o":
                    char_str = "\uA9BA" + char_str + "\uA9B4" # taling-tarung
                elif vowel == "è":
                    char_str = "\uA9BA" + char_str # taling
                    
                # Apply Final
                if final == "h":
                    char_str += "\uA9C3" # wignyan
                elif final == "ng":
                    char_str += "\uA9C1" # cecak
                elif final == "r":
                    char_str += "\uA9C2" # layar
                    
                # Generate standard base character variations
                for var in range(25):
                    rotate = random.uniform(-8, 8)
                    font_size = random.randint(35, 41)
                    shift = (random.randint(-3, 3), random.randint(-3, 3))
                    blur = random.uniform(0, 0.5)
                    
                    img = generate_char_image(char_str, font_path, font_size=font_size, rotate=rotate, blur=blur, shift=shift)
                    
                    filename = f"{base_name}_{vowel}_{final}_std_{count}.png"
                    img.save(os.path.join(dataset_dir, filename))
                    
                    if db_connected:
                        db_entries.append(DatasetCatalog(
                            filename=filename,
                            base_label=base_name,
                            vowel_label=vowel,
                            final_label=final,
                            origin="standard"
                        ))
                    count += 1
                
                # If it's a standard base, also generate its pasangan shape mapped to the same base class
                is_standard_base = base_name in ["ha", "na", "ca", "ra", "ka", "da", "ta", "sa", "wa", "la", "pa", "dha", "ja", "ya", "nya", "ma", "ga", "ba", "tha", "nga"]
                if is_standard_base:
                    # Prepend pangkon \uA9C0 to construct pasangan ligature layout
                    pasangan_str = "\uA9C0" + unicode_char
                    
                    # Apply Vowel
                    if vowel == "i":
                        pasangan_str += "\uA9B6"
                    elif vowel == "u":
                        pasangan_str += "\uA9B8"
                    elif vowel == "e":
                        pasangan_str += "\uA9BC"
                    elif vowel == "o":
                        pasangan_str = "\uA9BA" + pasangan_str + "\uA9B4"
                    elif vowel == "è":
                        pasangan_str = "\uA9BA" + pasangan_str
                        
                    # Apply Final
                    if final == "h":
                        pasangan_str += "\uA9C3"
                    elif final == "ng":
                        pasangan_str += "\uA9C1"
                    elif final == "r":
                        pasangan_str += "\uA9C2"
                        
                    # Generate pasangan shape variations
                    for var in range(25):
                        rotate = random.uniform(-8, 8)
                        font_size = random.randint(35, 41)
                        shift = (random.randint(-3, 3), random.randint(-3, 3))
                        blur = random.uniform(0, 0.5)
                        
                        img = generate_char_image(pasangan_str, font_path, font_size=font_size, rotate=rotate, blur=blur, shift=shift)
                        
                        filename = f"{base_name}_{vowel}_{final}_pas_{count}.png"
                        img.save(os.path.join(dataset_dir, filename))
                        
                        if db_connected:
                            db_entries.append(DatasetCatalog(
                                filename=filename,
                                base_label=base_name,
                                vowel_label=vowel,
                                final_label=final,
                                origin="pasangan"
                            ))
                        count += 1

print(f"[SUCCESS] Dataset generated with {count} images in '{dataset_dir}'.")

if db_connected and db_entries:
    print("[INFO] Writing dataset metadata catalog to Supabase...")
    try:
        with Session(engine) as session:
            session.add_all(db_entries)
            session.commit()
        print(f"[SUCCESS] Wrote {len(db_entries)} records to Supabase 'datasetcatalog' table.")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata to Supabase: {e}")
