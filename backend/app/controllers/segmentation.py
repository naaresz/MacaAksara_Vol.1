import cv2
import numpy as np
from PIL import Image
import io

def segment_javanese_script(image_path_or_bytes, is_bytes=False, is_webcam=False):
    # Load image using Pillow to handle transparency (alpha channel) correctly
    try:
        if is_bytes:
            pil_img = Image.open(io.BytesIO(image_path_or_bytes))
        else:
            pil_img = Image.open(image_path_or_bytes)
            
        if pil_img.mode in ('RGBA', 'LA') or (pil_img.mode == 'P' and 'transparency' in pil_img.info):
            bg = Image.new("RGBA", pil_img.size, (255, 255, 255, 255))
            mask = pil_img.split()[-1]
            bg.paste(pil_img, mask=mask)
            pil_img = bg.convert("RGB")
        else:
            pil_img = pil_img.convert("RGB")
            
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error loading image in segmentation, falling back: {e}")
        if is_bytes:
            nparr = np.frombuffer(image_path_or_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            img = cv2.imread(image_path_or_bytes)
        
    if img is None:
        raise ValueError("Could not read image for segmentation.")
        
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_h, img_w = gray.shape[:2]
    
    # Apply median blur to reduce high frequency sensor noise
    gray_blur = cv2.medianBlur(gray, 3)
    
    # Apply adaptive Gaussian thresholding
    thresh = cv2.adaptiveThreshold(
        gray_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 55, 9
    )
    
    # 2. Selective Line Erasure (Notebook lines removal)
    row_sums = np.sum(thresh == 255, axis=1)
    threshold_val = img_w * 0.35
    line_y_indices = np.where(row_sums >= threshold_val)[0]
    
    cleaned = thresh.copy()
    if len(line_y_indices) > 0:
        lines_y = []
        current_line = [line_y_indices[0]]
        for y in line_y_indices[1:]:
            if y == current_line[-1] + 1:
                current_line.append(y)
            else:
                lines_y.append(current_line)
                current_line = [y]
        lines_y.append(current_line)
        
        for line_group in lines_y:
            y_min = max(0, line_group[0] - 1)
            y_max = min(img_h - 1, line_group[-1] + 1)
            
            for x in range(img_w):
                window_top = max(0, y_min - 15)
                window_bottom = min(img_h - 1, y_max + 15)
                
                pixels_above = np.sum(thresh[window_top:y_min, x] == 255)
                pixels_below = np.sum(thresh[y_max+1:window_bottom, x] == 255)
                
                if pixels_above < 2 or pixels_below < 2:
                    cleaned[y_min:y_max+1, x] = 0
    thresh = cleaned
    
    # Apply morphological opening to eliminate small speckle noise
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open)
    
    # Dilate slightly to connect close character parts if necessary
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter noise contours and get bounding boxes
    boxes = []
    min_w, min_h = 10, 10  # Filter out small noise
    max_w, max_h = 600, 600  # Filter out huge borders/backgrounds
    
    # Calculate margins to exclude outer borders/background early
    margin_l = int(img_w * 0.14) if is_webcam else 5
    margin_r = int(img_w * 0.06) if is_webcam else 5
    margin_t = int(img_h * 0.08) if is_webcam else 5
    margin_b = int(img_h * 0.08) if is_webcam else 5
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if min_w <= w <= max_w and min_h <= h <= max_h:
            # Exclude skinny lines (border lines/notebook margins)
            aspect_ratio = h / w if w > 0 else 0
            if aspect_ratio > 4.0 or aspect_ratio < 0.25:
                continue
            # Exclude borders touching the edge of the canvas/scanning frame early
            if x <= margin_l or y <= margin_t or x + w >= img_w - margin_r or y + h >= img_h - margin_b:
                continue
            boxes.append([x, y, w, h])
            
    if not boxes:
        return [], []
        
    # Filter out tiny noise when calculating reference metrics
    all_raw_heights = [b[3] for b in boxes]
    valid_heights = [h for h in all_raw_heights if h > 30.0]
    if not valid_heights:
        valid_heights = all_raw_heights
        
    ref_h = np.percentile(valid_heights, 80) if valid_heights else 30.0
    ref_h_median = np.median(valid_heights) if valid_heights else 30.0
    min_char_h = max(18.0, ref_h_median * 0.45)
    
    # Transitive Merge helper functions
    def should_merge_boxes(box1, box2):
        x1, y1, w1, h1 = box1
        mx, my, mw, mh = box2
        
        v_gap = 0
        if y1 + h1 <= my:
            v_gap = my - (y1 + h1)
        elif my + mh <= y1:
            v_gap = y1 - (my + mh)
            
        if v_gap > max(60.0, ref_h * 0.40):
            return False
            
        v_overlap = min(y1+h1, my+mh) - max(y1, my)
        min_char_w = max(18.0, ref_h_median * 0.50)
        if h1 >= min_char_h and mh >= min_char_h and w1 >= min_char_w and mw >= min_char_w:
            if v_overlap <= 0:
                v_gap_val = -v_overlap
                if v_gap_val > ref_h_median * 0.55:
                    return False
            else:
                if v_overlap < min(h1, mh) * 0.45:
                    return False
                
        is_side_by_side = v_overlap > min(h1, mh) * 0.50
        overlap_w = min(x1+w1, mx+mw) - max(x1, mx)
        
        if is_side_by_side and overlap_w <= 0:
            gap = mx - (x1 + w1) if x1 < mx else x1 - (mx + mw)
            if gap > 4.0:
                left_box = box1 if x1 < mx else box2
                right_box = box2 if x1 < mx else box1
                min_char_w = max(18.0, ref_h_median * 0.50)
                if left_box[2] >= min_char_w and right_box[2] >= min_char_w:
                    return False
                    
        overlap_x = overlap_w > 0
        close_x = False
        if not overlap_x:
            dist1 = x1 - (mx + mw)
            dist2 = mx - (x1 + w1)
            merge_dist = 20
            if (dist1 > 0 and dist1 < merge_dist) or (dist2 > 0 and dist2 < merge_dist):
                close_x = True
                
        is_pasangan_pair = False
        if overlap_x:
            if overlap_w > min(w1, mw) * 0.4:
                if 0 < v_overlap < min(h1, mh) * 0.25:
                    if h1 >= min_char_h and mh >= min_char_h:
                        is_pasangan_pair = True
                        
        if (overlap_x or close_x) and not is_pasangan_pair:
            if close_x and not overlap_x:
                left_box = box1 if x1 < mx else box2
                right_box = box2 if x1 < mx else box1
                min_char_w = max(15.0, ref_h_median * 0.50)
                # If both left and right boxes are full-size characters, do not merge
                if left_box[2] >= min_char_w and right_box[2] >= min_char_w:
                    return False
            return True
            
        return False

    def merge_boxes_transitive(raw_boxes):
        changed = True
        curr_boxes = raw_boxes.copy()
        while changed:
            changed = False
            n = len(curr_boxes)
            merged_list = []
            used = set()
            
            for i in range(n):
                if i in used:
                    continue
                curr = curr_boxes[i]
                for j in range(i + 1, n):
                    if j in used:
                        continue
                    if should_merge_boxes(curr, curr_boxes[j]):
                        x1, y1, w1, h1 = curr
                        x2, y2, w2, h2 = curr_boxes[j]
                        new_x = min(x1, x2)
                        new_y = min(y1, y2)
                        new_w = max(x1+w1, x2+w2) - new_x
                        new_h = max(y1+h1, y2+h2) - new_y
                        curr = [new_x, new_y, new_w, new_h]
                        used.add(j)
                        changed = True
                merged_list.append(curr)
                used.add(i)
            curr_boxes = merged_list
        return curr_boxes

    # Transitive Merge
    merged_boxes = merge_boxes_transitive(boxes)
            
    # Group merged boxes into lines (rows) based on vertical overlap
    lines = []
    # Sort by Y-coordinate first to group lines
    merged_boxes.sort(key=lambda b: b[1])
    
    for box in merged_boxes:
        x, y, w, h = box
        added_to_line = False
        
        for line in lines:
            line_ys = [b[1] for b in line]
            line_hs = [b[3] for b in line]
            avg_y = sum(line_ys) / len(line_ys)
            avg_h = sum(line_hs) / len(line_hs)
            
            vertical_overlap = max(y, avg_y) < min(y+h, avg_y+avg_h)
            close_vertical = abs(y - avg_y) < avg_h * 0.8
            
            has_pasangan_relation = False
            for other_box in line:
                ox, oy, ow, oh = other_box
                overlap_x = max(x, ox) < min(x+w, ox+ow)
                if overlap_x:
                    overlap_w = min(x+w, ox+ow) - max(x, ox)
                    if overlap_w > min(w, ow) * 0.4:
                        v_top_dist = abs(y - oy)
                        if v_top_dist < avg_h * 1.1:
                            has_pasangan_relation = True
                            break
                            
            if vertical_overlap or close_vertical or has_pasangan_relation:
                line.append(box)
                added_to_line = True
                break
                
        if not added_to_line:
            lines.append([box])
            
    # Sort lines from top to bottom
    lines.sort(key=lambda line: sum([b[1] for b in line]) / len(line))
    
    # Sort boxes in each line using column-based stack grouping to keep vertically stacked boxes together
    sorted_boxes = []
    for line in lines:
        n = len(line)
        adj = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(i+1, n):
                x1, y1, w1, h1 = line[i]
                x2, y2, w2, h2 = line[j]
                overlap_x = max(x1, x2) < min(x1+w1, x2+w2)
                if overlap_x:
                    overlap_w = min(x1+w1, x2+w2) - max(x1, x2)
                    if overlap_w > min(w1, w2) * 0.4:
                        adj[i].append(j)
                        adj[j].append(i)
                        
        visited = set()
        components = []
        for i in range(n):
            if i not in visited:
                comp = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    comp.append(line[curr])
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)
                
        # Sort components by minimum X-coordinate
        components.sort(key=lambda comp: min(box[0] for box in comp))
        
        # Flatten components while sorting each vertically (top-to-bottom)
        sorted_line_boxes = []
        for comp in components:
            comp.sort(key=lambda box: box[1])
            sorted_line_boxes.extend(comp)
            
        sorted_boxes.extend(sorted_line_boxes)
        
    # Crop and pad characters to create square 64x64 images
    cropped_images = []
    filtered_boxes = []
    
    if sorted_boxes:
        # Calculate reference height based on the 75th percentile of all boxes
        heights = [b[3] for b in sorted_boxes]
        ref_h = np.percentile(heights, 75)
        # Exclude boxes that are extremely short compared to characters (noise/shadow fragments)
        min_h_filter = max(14.0, ref_h * 0.18)
        
        # Determine minimum size thresholds based on image dimensions to filter out camera sensor noise/smudges
        # For a standard 1200px height webcam, character minimum height is 45px, width is 32px
        min_abs_w = max(15, int(img_w * 0.02)) if is_webcam else 15
        min_abs_h = max(20, int(img_h * 0.038)) if is_webcam else 15
        
        for box in sorted_boxes:
            x, y, w, h = box
            
            # 1. Absolute size filter: Javanese script base characters have significant size
            if w < min_abs_w or h < min_abs_h:
                continue
                
            # 2. Height-ratio filter to exclude short speckles/lines
            if h < min_h_filter:
                continue
                
            # 2. Border/Edge-touching filter to exclude room background objects (face, hands, wardrobe)
            if is_webcam:
                # Exclude boxes in the outer margins of the cropped canvas
                # Since the text is centered inside the scanning frame, valid characters
                # are never at the very left (first 14%) or very right (last 6%) edges of the image.
                margin_left = int(img_w * 0.14)
                margin_right = int(img_w * 0.06)
                margin_top = int(img_h * 0.08)
                margin_bottom = int(img_h * 0.08)
                if x < margin_left or x + w > img_w - margin_right or y < margin_top or y + h > img_h - margin_bottom:
                    continue
            else:
                # For uploaded static images, only filter out objects touching the absolute edges (5px margin)
                if x <= 5 or y <= 5 or x + w >= img_w - 5 or y + h >= img_h - 5:
                    continue
                
            filtered_boxes.append(box)
            
            # Crop from grayscale (original contrast)
            crop = gray[y:y+h, x:x+w]
            
            # Binarize crop to clean up background (ensure it's white=255 and text is dark)
            _, crop_bin = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Create a square image with proportional padding (character occupies ~65% of size to match dataset)
            max_side = max(w, h)
            size = int(max_side * 1.54)
            square = np.ones((size, size), dtype=np.uint8) * 255 # White background
            
            # Paste crop in the center
            dx = (size - w) // 2
            dy = (size - h) // 2
            square[dy:dy+h, dx:dx+w] = crop_bin
            
            # Convert to PIL Image and resize to 64x64
            pil_img = Image.fromarray(square).resize((64, 64), Image.Resampling.BICUBIC)
            cropped_images.append(pil_img)
        
    return cropped_images, filtered_boxes

if __name__ == "__main__":
    # Test segmentation on a dummy blank image
    dummy = np.ones((100, 300, 3), dtype=np.uint8) * 255
    # Draw two black squares (characters)
    cv2.rectangle(dummy, (30, 40), (50, 60), (0, 0, 0), -1)
    cv2.rectangle(dummy, (40, 20), (45, 30), (0, 0, 0), -1) # diacritic above character 1
    cv2.rectangle(dummy, (100, 40), (120, 60), (0, 0, 0), -1) # character 2
    
    _, bytes_data = cv2.imencode(".png", dummy)
    crops, boxes = segment_javanese_script(bytes_data.tobytes(), is_bytes=True)
    print("Detected boxes:", boxes) # Should be 2 merged boxes
    print("Number of cropped images:", len(crops))
