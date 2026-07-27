import os
import zipfile
import io
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import unicodedata
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.models.classifier import JavaneseCNN

# Global Component Lists
BASES = ['ba', 'ca', 'da', 'dha', 'ga', 'ha', 'ja', 'ka', 'la', 'ma', 'na', 'nga', 'nya', 'pa', 'ra', 'sa', 'ta', 'tha', 'wa', 'ya', 'pangkon']
VOWELS = ['a', 'e', 'i', 'o', 'u', 'è']
FINALS = ['none', 'h', 'ng', 'r']

# Syllable parser to target components
def parse_syllable(syl):
    prefixes = [
        ("dh", "dha"), ("th", "tha"), ("ng", "nga"), ("ny", "nya"),
        ("h", "ha"),   ("n", "na"),   ("c", "ca"),   ("r", "ra"),
        ("k", "ka"),   ("d", "da"),   ("t", "ta"),   ("s", "sa"),
        ("w", "wa"),   ("l", "la"),   ("p", "pa"),   ("j", "ja"),
        ("y", "ya"),   ("m", "ma"),   ("g", "ga"),   ("b", "ba")
    ]
    
    base = None
    prefix_matched = ""
    for pref, base_name in prefixes:
        if syl.startswith(pref):
            base = base_name
            prefix_matched = pref
            break
            
    if base is None:
        return "ha", "a", "none"
        
    remainder = syl[len(prefix_matched):]
    
    vowel = "a"
    final = "none"
    
    # Parse remainder
    if remainder.startswith("i"):
        vowel = "i"
        remainder = remainder[1:]
    elif remainder.startswith("u"):
        vowel = "u"
        remainder = remainder[1:]
    elif remainder.startswith("e"):
        vowel = "e"
        remainder = remainder[1:]
    elif remainder.startswith("o"):
        vowel = "o"
        remainder = remainder[1:]
    elif remainder.startswith("è") or remainder.startswith("\u00e8"):
        vowel = "è"
        remainder = remainder[1:]
    elif remainder.startswith("a"):
        vowel = "a"
        remainder = remainder[1:]
        
    # Final consonant is whatever is left in remainder
    if remainder in ["h", "ng", "r"]:
        final = remainder
        
    return base, vowel, final

# Find the dataset zip file in Downloads
def find_dataset_zip():
    possible_paths = [
        "C:/Users/LenovoIdeapad/Downloads/archive (4).zip",
        "C:/Users/LenovoIdeapad/Downloads/archive (6).zip",
        "C:/Users/LenovoIdeapad/Downloads/aksara-jawa-kombinasi-sandhangan-dataset.zip"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    downloads_dir = "C:/Users/LenovoIdeapad/Downloads"
    if os.path.exists(downloads_dir):
        for f in os.listdir(downloads_dir):
            if f.endswith(".zip"):
                path = os.path.join(downloads_dir, f)
                try:
                    with zipfile.ZipFile(path, 'r') as z:
                        first_few = z.namelist()[:10]
                        if any("aksara_jawa_kombinasi" in x for x in first_few):
                            return path
                except Exception:
                    pass
    return None

class JavaneseFolderDataset(Dataset):
    def __init__(self, dataset_dir, is_train=True, transform=None):
        self.transform = transform
        self.is_train = is_train
        self.samples = []
        self.cache = {}
        
        split_folder = "train" if is_train else "val"
        split_dir = os.path.join(dataset_dir, split_folder)
        
        print(f"Initializing dataset paths from folder: {split_dir}")
        
        # Get list of classes
        self.classes = sorted([d for d in os.listdir(split_dir) if os.path.isdir(os.path.join(split_dir, d))])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        
        for cls_name in self.classes:
            cls_dir = os.path.join(split_dir, cls_name)
            
            # Parse Javanese syllable into base, vowel, final components
            base, vowel, final = parse_syllable(cls_name)
            try:
                base_idx = BASES.index(base)
                vowel_idx = VOWELS.index(vowel)
                final_idx = FINALS.index(final)
            except ValueError:
                continue
                
            for filename in os.listdir(cls_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(cls_dir, filename)
                    self.samples.append((img_path, base_idx, vowel_idx, final_idx))
                        
        print(f"Registered {len(self.samples)} image samples.")
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        img_path, base_idx, vowel_idx, final_idx = self.samples[idx]
        if idx in self.cache:
            img = self.cache[idx]
        else:
            try:
                img = Image.open(img_path).convert("L")
                img = img.resize((64, 64), Image.Resampling.BILINEAR)
                self.cache[idx] = img
            except Exception:
                img = Image.new("L", (64, 64), 255)
            
        if self.transform:
            img = self.transform(img)
            
        return img, base_idx, vowel_idx, final_idx

class JavaneseSyntheticDataset(Dataset):
    def __init__(self, dataset_dir, transform=None):
        self.transform = transform
        self.samples = []
        self.cache = {}
        
        if not os.path.exists(dataset_dir):
            print(f"[WARNING] Synthetic dataset directory does not exist: {dataset_dir}")
            return
            
        print(f"Loading synthetic dataset path list from: {dataset_dir}")
        for filename in os.listdir(dataset_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                parts = filename.split("_")
                if len(parts) >= 3:
                    base = parts[0]
                    vowel = parts[1]
                    final = parts[2]
                    
                    if base in BASES and vowel in VOWELS and final in FINALS:
                        base_idx = BASES.index(base)
                        vowel_idx = VOWELS.index(vowel)
                        final_idx = FINALS.index(final)
                        img_path = os.path.join(dataset_dir, filename)
                        self.samples.append((img_path, base_idx, vowel_idx, final_idx))
                            
        print(f"Registered {len(self.samples)} synthetic image samples on-the-fly.")
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        img_path, base_idx, vowel_idx, final_idx = self.samples[idx]
        if idx in self.cache:
            img = self.cache[idx]
        else:
            try:
                img = Image.open(img_path).convert("L")
                img = img.resize((64, 64), Image.Resampling.BILINEAR)
                self.cache[idx] = img
            except Exception:
                img = Image.new("L", (64, 64), 255)
            
        if self.transform:
            img = self.transform(img)
            
        return img, base_idx, vowel_idx, final_idx

class JavaneseZipDataset(Dataset):
    def __init__(self, zip_path, is_train=True, transform=None):
        self.transform = transform
        self.is_train = is_train
        
        self.images = []
        self.samples = []
        self.classes = []
        
        print(f"Loading dataset in memory from zip: {zip_path}")
        split_folder = "train" if is_train else "test"
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            namelist = z.namelist()
            
            # First filter list of entries
            valid_entries = []
            for name in namelist:
                if name.endswith(".png") and not name.startswith("__MACOSX"):
                    parts = name.split("/")
                    if len(parts) >= 4 and parts[-3] == split_folder:
                        class_name = unicodedata.normalize('NFC', parts[-2])
                        valid_entries.append((name, class_name))
            
            # Get all classes for consistent mapping
            all_classes = set()
            for name in namelist:
                if name.endswith(".png") and not name.startswith("__MACOSX"):
                    parts = name.split("/")
                    if len(parts) >= 4 and parts[-3] == "train":
                        all_classes.add(unicodedata.normalize('NFC', parts[-2]))
            
            self.classes = sorted(list(all_classes))
            self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
            
            # Load images directly to memory (RAM) and squarify them immediately
            count = 0
            for path, cls_name in valid_entries:
                if cls_name not in self.class_to_idx:
                    continue
                    
                # Parse to component indices
                base, vowel, final = parse_syllable(cls_name)
                base_idx = BASES.index(base)
                vowel_idx = VOWELS.index(vowel)
                final_idx = FINALS.index(final)
                
                # Read bytes and load PIL image
                data = z.read(path)
                img = Image.open(io.BytesIO(data)).convert("L")
                
                # Resize immediately to 64x64 to save RAM and speed up DataLoader
                img_resized = img.resize((64, 64), Image.Resampling.BILINEAR)
                
                self.images.append(img_resized)
                self.samples.append((base_idx, vowel_idx, final_idx))
                
                count += 1
                if count % 10000 == 0:
                    print(f"Loaded {count} images into memory...")
                    
        print(f"Loaded {len(self.images)} images in memory.")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx]
        base_idx, vowel_idx, final_idx = self.samples[idx]
        
        if self.transform:
            img = self.transform(img)
            
        return img, base_idx, vowel_idx, final_idx

def save_progress(status, epoch=0, total_epochs=0, batch=0, total_batches=0, loss=0.0, train_acc=0.0, val_acc=0.0, best_acc=0.0, error=None):
    progress_file = "D:/MacaAksara/backend/training_progress.json"
    data = {
        "status": status,
        "epoch": epoch,
        "total_epochs": total_epochs,
        "batch": batch,
        "total_batches": total_batches,
        "loss": round(loss, 4),
        "train_acc": round(train_acc, 2),
        "val_acc": round(val_acc, 2),
        "best_acc": round(best_acc, 2),
        "error": error
    }
    with open(progress_file, "w") as f:
        json.dump(data, f)

def train_model(epochs=8, batch_size=64, learning_rate=0.001):
    try:
        save_progress("initializing", total_epochs=epochs)
        
        # Setup transformation pipelines
        train_transform = transforms.Compose([
            transforms.RandomRotation(10),
            transforms.RandomAffine(degrees=8, translate=(0.06, 0.06), scale=(0.94, 1.06)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])
        
        test_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])
        
        # Check if extracted dataset directory exists
        backend_dir = os.path.dirname(__file__)
        extracted_dir = os.path.join(os.path.dirname(backend_dir), "dataset", "aksara_jawa_kombinasi_sandangan", "aksara_jawa_kombinasi_sandangan")
        if not os.path.exists(extracted_dir):
            extracted_dir = "dataset/aksara_jawa_kombinasi_sandangan/aksara_jawa_kombinasi_sandangan"
            
        # Load synthetic dataset too
        synthetic_dir = os.path.join(backend_dir, "dataset")
        train_synthetic = JavaneseSyntheticDataset(synthetic_dir, transform=train_transform)
        
        if os.path.exists(extracted_dir):
            print(f"Using extracted dataset folder: {extracted_dir}")
            train_handwritten = JavaneseFolderDataset(extracted_dir, is_train=True, transform=train_transform)
            test_dataset = JavaneseFolderDataset(extracted_dir, is_train=False, transform=test_transform)
        else:
            zip_path = find_dataset_zip()
            if not zip_path:
                raise FileNotFoundError("Could not find Javanese script dataset zip or extracted folder.")
            print(f"Using dataset zip: {zip_path}")
            train_handwritten = JavaneseZipDataset(zip_path, is_train=True, transform=train_transform)
            test_dataset = JavaneseZipDataset(zip_path, is_train=False, transform=test_transform)
            
        # Combine them using ConcatDataset
        from torch.utils.data import ConcatDataset
        train_dataset = ConcatDataset([train_handwritten, train_synthetic])
        print(f"Combined Training Dataset has {len(train_dataset)} samples.")
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        
        # Determine model save path folder
        models_dir = "D:/MacaAksara/backend/app/models"
            
        # Save classes and components mapping to classes.json
        classes_file = os.path.join(models_dir, "classes.json")
        with open(classes_file, "w") as f:
            json.dump({
                "classes": train_handwritten.classes if hasattr(train_handwritten, "classes") else [],
                "bases": BASES,
                "vowels": VOWELS,
                "finals": FINALS
            }, f)
        print(f"Saved class mappings to {classes_file}")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Training on device: {device}")
        
        # Instantiate model with component sizes
        model = JavaneseCNN(num_bases=len(BASES), num_vowels=len(VOWELS), num_finals=len(FINALS)).to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        best_acc = 0.0
        model_save_path = os.path.join(models_dir, "best_model.pth")
        
        save_progress("training", epoch=0, total_epochs=epochs, total_batches=len(train_loader))
        import time
        
        for epoch in range(epochs):
            model.train()
            running_loss = 0.0
            correct_train = 0
            total_train = 0
            epoch_start = time.time()
            
            print(f"\n--- Epoch {epoch+1}/{epochs} ---")
            
            for batch_idx, (inputs, targets_base, targets_vowel, targets_final) in enumerate(train_loader):
                inputs = inputs.to(device)
                targets_base = targets_base.to(device)
                targets_vowel = targets_vowel.to(device)
                targets_final = targets_final.to(device)
                
                optimizer.zero_grad()
                outputs_base, outputs_vowel, outputs_final = model(inputs)
                
                loss_base = criterion(outputs_base, targets_base)
                loss_vowel = criterion(outputs_vowel, targets_vowel)
                loss_final = criterion(outputs_final, targets_final)
                
                loss = loss_base + loss_vowel + loss_final
                loss.backward()
                optimizer.step()
                
                running_loss += loss.item()
                
                # Accuracies (Strict Joint Accuracy)
                _, pred_base = outputs_base.max(1)
                _, pred_vowel = outputs_vowel.max(1)
                _, pred_final = outputs_final.max(1)
                
                total_train += inputs.size(0)
                correct_joint = ((pred_base == targets_base) & (pred_vowel == targets_vowel) & (pred_final == targets_final)).sum().item()
                correct_train += correct_joint
                
                acc = 100.0 * correct_train / total_train
                
                if (batch_idx + 1) % 50 == 0 or (batch_idx + 1) == len(train_loader):
                    print(f"Batch {batch_idx+1}/{len(train_loader)} | Loss: {running_loss/(batch_idx+1):.4f} | Train Acc (Joint): {acc:.2f}%")
                    save_progress(
                        "training", 
                        epoch=epoch+1, 
                        total_epochs=epochs, 
                        batch=batch_idx+1, 
                        total_batches=len(train_loader), 
                        loss=running_loss/(batch_idx+1), 
                        train_acc=acc, 
                        best_acc=best_acc
                    )
                    
            # Evaluate
            model.eval()
            correct_test = 0
            total_test = 0
            val_loss = 0.0
            
            with torch.no_grad():
                for inputs, targets_base, targets_vowel, targets_final in test_loader:
                    inputs = inputs.to(device)
                    targets_base = targets_base.to(device)
                    targets_vowel = targets_vowel.to(device)
                    targets_final = targets_final.to(device)
                    
                    outputs_base, outputs_vowel, outputs_final = model(inputs)
                    loss_base = criterion(outputs_base, targets_base)
                    loss_vowel = criterion(outputs_vowel, targets_vowel)
                    loss_final = criterion(outputs_final, targets_final)
                    loss = loss_base + loss_vowel + loss_final
                    val_loss += loss.item()
                    
                    _, pred_base = outputs_base.max(1)
                    _, pred_vowel = outputs_vowel.max(1)
                    _, pred_final = outputs_final.max(1)
                    
                    total_test += inputs.size(0)
                    correct_joint = ((pred_base == targets_base) & (pred_vowel == targets_vowel) & (pred_final == targets_final)).sum().item()
                    correct_test += correct_joint
                    
            val_acc = 100.0 * correct_test / total_test
            avg_val_loss = val_loss / len(test_loader)
            print(f"Validation Loss: {avg_val_loss:.4f} | Validation Acc (Joint): {val_acc:.2f}% | Time: {time.time() - epoch_start:.2f}s")
            
            if val_acc > best_acc:
                best_acc = val_acc
                print(f"New best validation accuracy: {best_acc:.2f}%. Saving model weight to {model_save_path}")
                torch.save(model.state_dict(), model_save_path)
            
            save_progress(
                "training", 
                epoch=epoch+1, 
                total_epochs=epochs, 
                batch=len(train_loader), 
                total_batches=len(train_loader), 
                loss=running_loss/len(train_loader), 
                train_acc=acc, 
                val_acc=val_acc, 
                best_acc=best_acc
            )
                
        print("\nTraining completed!")
        print(f"Best Validation Joint Accuracy: {best_acc:.2f}%")
        save_progress("completed", epoch=epochs, total_epochs=epochs, best_acc=best_acc)
        
    except Exception as e:
        print(f"Training failed: {e}")
        save_progress("failed", error=str(e))
        raise e

if __name__ == "__main__":
    train_model(epochs=3, batch_size=256)
