import os
import json
import threading
import torch
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image
import io
import torchvision.transforms as transforms
from google import genai
from google.genai import types
import cv2
import numpy as np

from model import JavaneseCNN

def load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

load_env_file()

from segmentation import segment_javanese_script
from dictionary import (
    clean_and_format_transliteration,
    translate_javanese_to_indonesian,
    get_character_breakdown
)

app = FastAPI(title="MacaAksara API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model state
model = None
classes = []
bases = []
vowels = []
finals = []
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def combine_components(base, vowel, final):
    # Programmatic Javanese syllable assembler
    if vowel != "a":
        if base.endswith("a"):
            consonant = base[:-1]
        else:
            consonant = base
        syllable = consonant + vowel
    else:
        syllable = base
        
    if final != "none":
        syllable = syllable + final
        
    return syllable

def detect_geometric_sandhangan(crop_thresh, bw, bh):
    # Find contours within this crop
    sub_contours, _ = cv2.findContours(crop_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    sorted_sub = sorted(sub_contours, key=cv2.contourArea, reverse=True)
    
    geom_vowel = None
    
    if len(sorted_sub) > 1:
        largest_area = cv2.contourArea(sorted_sub[0])
        # Check other contours for floating wulu circle
        for sub_cnt in sorted_sub[1:]:
            sub_area = cv2.contourArea(sub_cnt)
            # Check for wulu circle (must be of reasonable size relative to base, min 8 pixels)
            if sub_area > 8 and largest_area * 0.01 < sub_area < largest_area * 0.4:
                c_x, c_y, c_w, c_h = cv2.boundingRect(sub_cnt)
                # Must be in the top portion of the character crop (top half)
                if c_y < bh * 0.5:
                    perimeter = cv2.arcLength(sub_cnt, True)
                    circularity = 4 * np.pi * sub_area / (perimeter ** 2) if perimeter > 0 else 0
                    
                    # Handwritten wulu circles can be slightly irregular (circularity > 0.4)
                    if circularity > 0.4:
                        # Circular shape -> wulu (vowel 'i')
                        geom_vowel = "i"
                        break
    return geom_vowel, None

# Image transforms (Grayscale, resize, normalize)
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

def load_classifier():
    global model, classes, bases, vowels, finals
    model_path = os.path.join(os.path.dirname(__file__), "best_model.pth")
    classes_path = os.path.join(os.path.dirname(__file__), "classes.json")
    
    if os.path.exists(model_path) and os.path.exists(classes_path):
        try:
            with open(classes_path, "r") as f:
                class_data = json.load(f)
                
            # Handle dictionary mapping format or simple list fallback
            if isinstance(class_data, dict):
                classes = class_data["classes"]
                bases = class_data["bases"]
                vowels = class_data["vowels"]
                finals = class_data["finals"]
            else:
                classes = class_data
                bases = ['ba', 'ca', 'da', 'dha', 'ga', 'ha', 'ja', 'ka', 'la', 'ma', 'na', 'nga', 'nya', 'pa', 'ra', 'sa', 'ta', 'tha', 'wa', 'ya']
                vowels = ['a', 'e', 'i', 'o', 'u', 'è']
                finals = ['none', 'h', 'ng', 'r']
                
            model = JavaneseCNN(num_bases=len(bases), num_vowels=len(vowels), num_finals=len(finals)).to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            print(f"Classifier loaded successfully on {device} with {len(classes)} classes (bases: {len(bases)}, vowels: {len(vowels)}, finals: {len(finals)}).")
            return True
        except Exception as e:
            print(f"Error loading classifier: {e}")
    else:
        print("Classifier files missing. Model needs training.")
    return False

# Attempt to load model on startup
load_classifier()



@app.post("/predict")
async def predict_javanese(
    file: UploadFile = File(...),
    use_gemini: bool = Form(False),
    mode: str = Form("sentence"), # 'single' or 'sentence'
    is_webcam: bool = Form(False)
):
    global model, classes
    
    # Read file
    img_bytes = await file.read()
    
    # Option 1: Advanced Gemini Translation (Multimodal API)
    # Check if Gemini API key is configured in the environment
    api_key = os.getenv("GEMINI_API_KEY")
    
    # If the key is present, default to Gemini to get maximum translation accuracy,
    # falling back to Local OCR if there is any API error or if offline.
    if api_key or use_gemini:
        actual_key = api_key if api_key else os.getenv("GEMINI_API_KEY")
        if actual_key:
            try:
                # Initialize Gemini API client
                client = genai.Client(api_key=actual_key)
                
                # Request translation from Gemini
                prompt = """
                Kamu adalah AI penerjemah Aksara Jawa. Analisis gambar Aksara Jawa berikut dan kembalikan terjemahan dalam format JSON yang valid.
                JSON harus memiliki kunci:
                1. 'transliteration': Transliterasi latin dari aksara jawa tersebut.
                2. 'pronunciation': Pengucapan dialek jawa tengah (vokal /a/ terbuka di akhir kata dibaca /o/).
                3. 'translation': Terjemahan teks tersebut ke dalam Bahasa Indonesia.
                4. 'explanation': Penjelasan singkat tentang isi kalimat atau tata bahasa aksara tersebut.
                
                Pastikan output HANYA berupa JSON tanpa tanda ```json.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        types.Part.from_bytes(
                            data=img_bytes,
                            mime_type="image/png"
                        ),
                        prompt
                    ]
                )
                
                # Clean response text
                res_text = response.text.strip()
                if res_text.startswith("```json"):
                    res_text = res_text[7:]
                if res_text.endswith("```"):
                    res_text = res_text[:-3]
                res_text = res_text.strip()
                
                result = json.loads(res_text)
                return {
                    "source": "gemini",
                    "transliteration": result.get("transliteration", ""),
                    "pronunciation": result.get("pronunciation", ""),
                    "translation": result.get("translation", ""),
                    "explanation": result.get("explanation", ""),
                    "breakdown": []
                }
            except Exception as e:
                print(f"Gemini translation failed, falling back to Local OCR: {e}")
            
    # Option 2: Local OCR Model (Classifier + OpenCV Segmentation)
    if model is None:
        # Try reloading first
        if not load_classifier():
            raise HTTPException(
                status_code=400,
                detail="Model pembaca lokal belum dilatih. Silakan lakukan latihan model terlebih dahulu melalui panel konfigurasi!"
            )
            
    try:
        # Save original input image for debugging
        debug_dir = os.path.dirname(os.path.dirname(__file__))
        debug_input_path = os.path.join(debug_dir, "debug_input.png")
        with open(debug_input_path, "wb") as f:
            f.write(img_bytes)
        print(f"Saved debug input image to {debug_input_path}")
        
        # Segment image into syllables
        crops, boxes = segment_javanese_script(img_bytes, is_bytes=True, is_webcam=is_webcam)
        
        # Load grayscale and thresholded images for sub-contour diacritics detection
        try:
            pil_img_cv = Image.open(io.BytesIO(img_bytes))
            if pil_img_cv.mode in ('RGBA', 'LA') or (pil_img_cv.mode == 'P' and 'transparency' in pil_img_cv.info):
                bg_cv = Image.new("RGBA", pil_img_cv.size, (255, 255, 255, 255))
                mask_cv = pil_img_cv.split()[-1]
                bg_cv.paste(pil_img_cv, mask=mask_cv)
                pil_img_cv = bg_cv.convert("RGB")
            else:
                pil_img_cv = pil_img_cv.convert("RGB")
            img_cv = cv2.cvtColor(np.array(pil_img_cv), cv2.COLOR_RGB2BGR)
        except Exception:
            nparr = np.frombuffer(img_bytes, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
        gray_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        thresh_cv = cv2.adaptiveThreshold(
            gray_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 55, 15
        )
        
        # Save segmented crops for debugging
        # Clean old debug crops
        for f_name in os.listdir(debug_dir):
            if f_name.startswith("debug_crop_") and f_name.endswith(".png"):
                try:
                    os.remove(os.path.join(debug_dir, f_name))
                except Exception:
                    pass
                    
        if not crops:
            return {
                "source": "local",
                "transliteration": "",
                "pronunciation": "",
                "translation": "Tidak ada karakter terdeteksi.",
                "breakdown": []
            }
            
        # Run classification on each syllable crop
        predicted_syllables = []
        breakdown = []
        
        # If Single Character mode is active, only run classification on the largest crop
        if mode == "single":
            # Read image using Pillow to handle transparency correctly
            pil_img = Image.open(io.BytesIO(img_bytes))
            if pil_img.mode in ('RGBA', 'LA') or (pil_img.mode == 'P' and 'transparency' in pil_img.info):
                bg = Image.new("RGBA", pil_img.size, (255, 255, 255, 255))
                mask = pil_img.split()[-1]
                bg.paste(pil_img, mask=mask)
                pil_img = bg.convert("L")
            else:
                pil_img = pil_img.convert("L")
                
            # Convert to numpy array for OpenCV thresholding
            img_cv = np.array(pil_img)
            
            # Apply binarization to match training dataset's clean white background
            _, img_bin = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            img = Image.fromarray(img_bin)
            w, h = img.size
            # Apply proportional padding (character occupies ~50% of size)
            max_side = max(w, h)
            size = int(max_side * 2.0)
            processed_img = Image.new("L", (size, size), 255)
            processed_img.paste(img, ((size-w)//2, (size-h)//2))
            
            # Save single mode debug crop
            processed_img.save(os.path.join(debug_dir, "debug_crop_0.png"))
            crop_tensor = transform(processed_img).unsqueeze(0).to(device)
            
            # Check if it is a single pangkon character
            predicted_class = ""
            if boxes:
                bx, by, bw, bh = boxes[0]
                if bw / bh < 0.8:
                    predicted_class = "pangkon"
            
            if predicted_class != "pangkon":
                # Run geometric diacritics detection on the single character crop area
                geom_vowel = None
                geom_final = None
                if boxes:
                    bx, by, bw, bh = boxes[0]
                    crop_thresh = thresh_cv[by:by+bh, bx:bx+bw]
                    geom_vowel, geom_final = detect_geometric_sandhangan(crop_thresh, bw, bh)
                    
                with torch.no_grad():
                    out_base, out_vowel, out_final = model(crop_tensor)
                    pred_base = out_base.argmax(1).item()
                    pred_vowel = out_vowel.argmax(1).item()
                    pred_final = out_final.argmax(1).item()
                    
                    base_str = bases[pred_base]
                    vowel_str = vowels[pred_vowel]
                    final_str = finals[pred_final]
                    
                    if geom_vowel:
                        vowel_str = geom_vowel
                    if geom_final:
                        final_str = geom_final
                        
                    predicted_class = combine_components(base_str, vowel_str, final_str)
                
            predicted_syllables = [predicted_class]
            breakdown.append(get_character_breakdown(predicted_class))
        else:
            # Sentence Mode: classify each segmented crop
            raw_syllables = []
            
            # Precompute reference character width of all boxes
            all_w_ref = [b[2] for b in boxes]
            median_w_ref = np.median(all_w_ref) if all_w_ref else 30.0
            
            for idx, crop in enumerate(crops):
                # Save crop for debugging
                crop.save(os.path.join(debug_dir, f"debug_crop_{idx}.png"))
                
                bx, by, bw, bh = boxes[idx]
                
                # Check if it is a pangkon geometrically
                # 1. Must be the end of a word or line
                is_end_of_word = False
                if idx + 1 == len(crops):
                    is_end_of_word = True
                else:
                    bx_next, by_next, bw_next, bh_next = boxes[idx+1]
                    same_line_next = abs(by - by_next) < max(bh, bh_next) * 1.5
                    if not same_line_next:
                        is_end_of_word = True
                    elif bx_next > bx + bw:
                        gap_next = bx_next - (bx + bw)
                        avg_w_next = (bw + bw_next) / 2
                        if gap_next > avg_w_next * 0.45:
                            is_end_of_word = True
                            
                # 2. Geometric rules for Javanese pangkon:
                # - Sits on the baseline and has narrow aspect ratio (width/height < 0.95)
                # - Much smaller width compared to typical characters (width < median_w * 0.90)
                # - OR is the last box and overlaps horizontally with the previous character (tail sweeps left)
                is_pangkon = False
                # A pangkon can never be the first character in the line or sentence
                if is_end_of_word and idx > 0:
                    if (bw / bh < 0.95) and (bw < median_w_ref * 0.90):
                        is_pangkon = True
                    else:
                        bx_prev, by_prev, bw_prev, bh_prev = boxes[idx-1]
                        # Check if it overlaps horizontally with the previous character
                        overlap_prev = min(bx+bw, bx_prev+bw_prev) - max(bx, bx_prev)
                        # Also ensure it sits to the right of the previous character's start
                        if overlap_prev > 15.0 and bx > bx_prev:
                            is_pangkon = True
                            
                if is_pangkon:
                    predicted_class = "pangkon"
                else:
                    crop_tensor = transform(crop).unsqueeze(0).to(device)
                    crop_thresh = thresh_cv[by:by+bh, bx:bx+bw]
                    geom_vowel, geom_final = detect_geometric_sandhangan(crop_thresh, bw, bh)
                    
                    with torch.no_grad():
                        out_base, out_vowel, out_final = model(crop_tensor)
                        pred_base = out_base.argmax(1).item()
                        pred_vowel = out_vowel.argmax(1).item()
                        pred_final = out_final.argmax(1).item()
                        
                        base_str = bases[pred_base]
                        vowel_str = vowels[pred_vowel]
                        final_str = finals[pred_final]
                        
                        if geom_vowel:
                            vowel_str = geom_vowel
                        if geom_final:
                            final_str = geom_final
                            
                        predicted_class = combine_components(base_str, vowel_str, final_str)
                raw_syllables.append(predicted_class)
                
            # Post-process for pasangan muting, pangkon muting, and spatial spacing
            all_h = [b[3] for b in boxes]
            ref_h = np.median(all_h) if all_h else 30.0
            min_char_h = max(18.0, ref_h * 0.45)
            
            predicted_syllables = []
            breakdown = []
            
            i = 0
            n_crops = len(crops)
            while i < n_crops:
                curr_syl = raw_syllables[i]
                bx_A, by_A, bw_A, bh_A = boxes[i]
                
                # Check if next box is a pangkon
                is_followed_by_pangkon = False
                if i + 1 < n_crops:
                    if raw_syllables[i+1] == "pangkon":
                        is_followed_by_pangkon = True
                        
                if is_followed_by_pangkon:
                    # Mute the vowel of curr_syl
                    if curr_syl.endswith("a"):
                        curr_syl = curr_syl[:-1]
                    else:
                        for v in ["i", "u", "e", "o", "è"]:
                            if curr_syl.endswith(v):
                                curr_syl = curr_syl[:-len(v)]
                                break
                    predicted_syllables.append(curr_syl)
                    breakdown.append(get_character_breakdown(curr_syl))
                    # Add description breakdown for the pangkon character itself in the breakdown view
                    breakdown.append(get_character_breakdown("pangkon"))
                    
                    # Check for spatial gap space insertion before the character following the pangkon (if any)
                    # The pangkon is at i+1, so the next character is at i+2
                    if i + 2 < n_crops:
                        bx_B, by_B, bw_B, bh_B = boxes[i+2]
                        # We compare distance from pangkon (i+1) to next char (i+2)
                        bx_P, by_P, bw_P, bh_P = boxes[i+1]
                        same_line = abs(by_P - by_B) < max(bh_P, bh_B) * 1.5
                        if same_line and bx_B > bx_P + bw_P:
                            gap = bx_B - (bx_P + bw_P)
                            avg_w = (bw_P + bw_B) / 2
                            if gap > avg_w * 0.45:
                                predicted_syllables.append(" ")
                                
                    # Skip the pangkon character since we have processed it
                    i += 2
                    continue
                
                # Check if next box is a pasangan
                is_pasangan = False
                if i + 1 < n_crops:
                    bx_B, by_B, bw_B, bh_B = boxes[i+1]
                    # Check horizontal overlap
                    overlap_x = max(bx_A, bx_B) < min(bx_A + bw_A, bx_B + bw_B)
                    if overlap_x:
                        overlap_w = min(bx_A + bw_A, bx_B + bw_B) - max(bx_A, bx_B)
                        overlap_ratio = overlap_w / min(bw_A, bw_B)
                        if overlap_ratio > 0.4:
                            # Vertically stacked: B is below A
                            if by_B > by_A + bh_A * 0.4:
                                if bh_A >= min_char_h and bh_B >= min_char_h:
                                    is_pasangan = True
                                    
                if is_pasangan:
                    # Mute the vowel of curr_syl
                    if curr_syl.endswith("a"):
                        curr_syl = curr_syl[:-1]
                    else:
                        for v in ["i", "u", "e", "o", "è"]:
                            if curr_syl.endswith(v):
                                curr_syl = curr_syl[:-len(v)]
                                break
                                
                predicted_syllables.append(curr_syl)
                breakdown.append(get_character_breakdown(curr_syl))
                
                # Check for spatial gap space insertion before the next character (only if not pasangan)
                if not is_pasangan and i + 1 < n_crops:
                    bx_B, by_B, bw_B, bh_B = boxes[i+1]
                    same_line = abs(by_A - by_B) < max(bh_A, bh_B) * 1.5
                    if same_line and bx_B > bx_A + bw_A:
                        gap = bx_B - (bx_A + bw_A)
                        avg_w = (bw_A + bw_B) / 2
                        if gap > avg_w * 0.45:
                            predicted_syllables.append(" ")
                            # No breakdown entry for space
                            
                i += 1
                
        # Format the result
        latin, pronunciation = clean_and_format_transliteration(predicted_syllables)
        translation = translate_javanese_to_indonesian(latin)
        
        print(f"Prediction: {predicted_syllables} -> Latin: {latin}")
        
        return {
            "source": "local",
            "transliteration": latin,
            "pronunciation": pronunciation,
            "translation": translation,
            "explanation": "Diterjemahkan secara mandiri suku kata demi suku kata oleh mesin lokal.",
            "breakdown": breakdown
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# Mount frontend directory for static assets directly at the root
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
