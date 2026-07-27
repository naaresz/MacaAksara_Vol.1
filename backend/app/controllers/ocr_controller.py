import os
import json
import torch
import cv2
import numpy as np
import torchvision.transforms as transforms
from PIL import Image

from backend.app.models.classifier import JavaneseCNN
from backend.app.controllers.segmentation import segment_javanese_script
from backend.app.controllers.dict_controller import (
    clean_and_format_transliteration,
    translate_javanese_to_indonesian,
    get_character_breakdown,
    try_fuzzy_phrase_matching
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global variables for model state
model = None
classes = []
bases = []
vowels = []
finals = []

# Image transforms (Grayscale, resize, normalize)
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

def load_classifier():
    global model, classes, bases, vowels, finals
    
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_path = os.path.join(models_dir, "best_model.pth")
    classes_path = os.path.join(models_dir, "classes.json")
    
    if os.path.exists(model_path) and os.path.exists(classes_path):
        try:
            with open(classes_path, "r") as f:
                class_data = json.load(f)
                
            classes = class_data["classes"]
            bases = class_data["bases"]
            vowels = class_data["vowels"]
            finals = class_data["finals"]
            
            # Reconstruct the dynamic CNN architecture with actual parameter sizes
            model = JavaneseCNN(num_bases=len(bases), num_vowels=len(vowels), num_finals=len(finals))
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.to(device)
            model.eval()
            print(f"[INFO] Classifier loaded successfully on {device} (bases: {len(bases)}, vowels: {len(vowels)}, finals: {len(finals)}).")
        except Exception as e:
            print(f"[ERROR] Failed to load model weights: {e}")
    else:
        print("[WARNING] Model weights or configuration files are missing in backend/app/models/.")

# Load immediately on import
load_classifier()

def combine_components(base, vowel, final):
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
    sub_contours, _ = cv2.findContours(crop_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    sorted_sub = sorted(sub_contours, key=cv2.contourArea, reverse=True)
    
    geom_vowel = None
    if len(sorted_sub) > 1:
        largest_area = cv2.contourArea(sorted_sub[0])
        for sub_cnt in sorted_sub[1:]:
            sub_area = cv2.contourArea(sub_cnt)
            if sub_area > 8 and largest_area * 0.01 < sub_area < largest_area * 0.4:
                c_x, c_y, c_w, c_h = cv2.boundingRect(sub_cnt)
                if c_y < bh * 0.5:
                    perimeter = cv2.arcLength(sub_cnt, True)
                    circularity = 4 * np.pi * sub_area / (perimeter ** 2) if perimeter > 0 else 0
                    if circularity > 0.4:
                        geom_vowel = "i"
                        break
    return geom_vowel, None

def perform_ocr_inference(image_bytes: bytes, is_webcam: bool = False):
    global model, bases, vowels, finals
    
    if model is None:
        return {
            "error": "Model classifier belum dimuat. Jalankan generate_dataset.py sarta train.py untuk membuat model."
        }
        
    try:
        # Segment the script into cropped letters
        crops, boxes = segment_javanese_script(image_bytes, is_bytes=True, is_webcam=is_webcam)
        
        if not crops:
            return {
                "source": "local",
                "transliteration": "",
                "pronunciation": "",
                "translation": "",
                "explanation": "Tidak ada aksara Jawa yang terdeteksi pada gambar.",
                "breakdown": []
            }
            
        n_crops = len(crops)
        
        # Binarize original full image for secondary geometric check
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.medianBlur(img_gray, 3)
        thresh_cv = cv2.adaptiveThreshold(
            img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 55, 9
        )
        
        raw_syllables = []
        for idx in range(n_crops):
            crop = crops[idx]
            bx, by, bw, bh = boxes[idx]
            
            # Run CNN inference first (to detect "pangkon" directly from visual class)
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
                
                # Direct CNN classification of pangkon
                is_pangkon = (base_str == "pangkon")
                
                if not is_pangkon:
                    # Fallback geometric check for very small standalone pangkon
                    if bw < 35.0 and bh < 35.0 and idx == n_crops - 1:
                        is_pangkon = True
                    elif idx > 0:
                        bx_prev, by_prev, bw_prev, bh_prev = boxes[idx-1]
                        overlap_prev = min(bx+bw, bx_prev+bw_prev) - max(bx, bx_prev)
                        if overlap_prev > 20.0 and bx > bx_prev and bw < 60.0 and bh < 60.0:
                            is_pangkon = True
                            
            if is_pangkon:
                predicted_class = "pangkon"
            else:
                if geom_vowel:
                    vowel_str = geom_vowel
                if geom_final:
                    final_str = geom_final
                predicted_class = combine_components(base_str, vowel_str, final_str)
            raw_syllables.append(predicted_class)
            
        # Post-process for pasangan muting, pangkon muting, and spacing
        all_h = [b[3] for b in boxes]
        ref_h = np.median(all_h) if all_h else 30.0
        min_char_h = max(18.0, ref_h * 0.45)
        
        predicted_syllables = []
        breakdown = []
        
        i = 0
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
                breakdown.append(get_character_breakdown("pangkon"))
                
                # Check for spatial gap space insertion or newline insertion
                if i + 2 < n_crops:
                    bx_B, by_B, bw_B, bh_B = boxes[i+2]
                    bx_P, by_P, bw_P, bh_P = boxes[i+1]
                    same_line = abs(by_P - by_B) < max(bh_P, bh_B) * 1.5
                    if same_line:
                        if bx_B > bx_P + bw_P:
                            gap = bx_B - (bx_P + bw_P)
                            avg_w = (bw_P + bw_B) / 2
                            if gap > avg_w * 0.85:
                                predicted_syllables.append(" ")
                    else:
                        if by_B > by_P + bh_P * 0.7:
                            predicted_syllables.append("\n")
                            
                i += 2
                continue
                
            # Check if next box is a pasangan (either written below or to the side/right)
            is_pasangan = False
            if i + 1 < n_crops:
                bx_B, by_B, bw_B, bh_B = boxes[i+1]
                
                # Check 1: Vertical overlap (written below)
                overlap_x = max(bx_A, bx_B) < min(bx_A + bw_A, bx_B + bw_B)
                if overlap_x:
                    overlap_w = min(bx_A + bw_A, bx_B + bw_B) - max(bx_A, bx_B)
                    overlap_ratio = overlap_w / min(bw_A, bw_B)
                    if overlap_ratio > 0.4:
                        if by_B > by_A + bh_A * 0.4:
                            if bh_A >= min_char_h and bh_B >= min_char_h:
                                is_pasangan = True
                                
                # Check 2: Horizontal alignment (side pasangan, e.g. sa, pa, ha)
                if not is_pasangan:
                    same_line = abs(by_A - by_B) < max(bh_A, bh_B) * 1.5
                    if same_line and bx_B > bx_A + bw_A * 0.3:
                        gap = bx_B - (bx_A + bw_A)
                        avg_w = (bw_A + bw_B) / 2
                        if gap < avg_w * 0.85 and by_B > by_A + bh_A * 0.22:
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
            
            # Check for spatial gap space insertion or newline insertion
            if not is_pasangan and i + 1 < n_crops:
                bx_B, by_B, bw_B, bh_B = boxes[i+1]
                same_line = abs(by_A - by_B) < max(bh_A, bh_B) * 1.5
                if same_line:
                    if bx_B > bx_A + bw_A:
                        gap = bx_B - (bx_A + bw_A)
                        avg_w = (bw_A + bw_B) / 2
                        if gap > avg_w * 0.85:
                            predicted_syllables.append(" ")
                else:
                    # New line detected (going downwards)
                    if by_B > by_A + bh_A * 0.7:
                        predicted_syllables.append("\n")
                        
            i += 1
            
        # Format the result using dictionary helper
        latin, pronunciation = clean_and_format_transliteration(predicted_syllables)
        
        explanation = "Diterjemahkan secara mandiri suku kata demi suku kata oleh mesin lokal."
        
        # Check for fuzzy phrase overrides (e.g. ngiris sawo)
        fuzzy_match = try_fuzzy_phrase_matching(latin)
        if fuzzy_match:
            return {
                "source": "local",
                "transliteration": fuzzy_match["transliteration"],
                "pronunciation": fuzzy_match["pronunciation"],
                "translation": fuzzy_match["translation"],
                "explanation": fuzzy_match.get("explanation", explanation),
                "breakdown": breakdown
            }
            
        translation = translate_javanese_to_indonesian(latin)
            
        return {
            "source": "local",
            "transliteration": latin,
            "pronunciation": pronunciation,
            "translation": translation,
            "explanation": explanation,
            "breakdown": breakdown
        }
    except Exception as e:
        return {"error": f"Inference error: {str(e)}"}
