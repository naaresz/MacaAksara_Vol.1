// MacaAksara Frontend Controller

// API Endpoints
const API_URL = (window.location.port === "8000" || (window.location.origin.startsWith("http") && !window.location.port))
    ? window.location.origin 
    : "http://localhost:8000";

// State variables
let activeStream = null;
let currentFile = null;
let isCameraMirroredH = false;
let isCameraMirroredV = false;
let cameraRotation = 0;

// Real-Time scanning variables
let isRealtimeScanning = false;
let realtimeInterval = null;
let isPredicting = false;
let stablePredictionHistory = [];
let stableDebounceCount = 0;

// DOM Elements
const video = document.getElementById("webcam");
const canvas = document.getElementById("capture-canvas");
const captureBtn = document.getElementById("capture-btn");
const tabCamera = document.getElementById("tab-camera");
const tabUpload = document.getElementById("tab-upload");
const cameraContainer = document.getElementById("camera-container");
const uploadContainer = document.getElementById("upload-container");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const previewContainer = document.getElementById("preview-container");
const imagePreview = document.getElementById("image-preview");
const clearImageBtn = document.getElementById("clear-image");

// Output panels
const emptyView = document.getElementById("empty-view");
const loadingView = document.getElementById("loading-view");
const resultsView = document.getElementById("results-view");
const resultSource = document.getElementById("result-source");
const outputLatin = document.getElementById("output-latin");
const outputPronunciation = document.getElementById("output-pronunciation");
const outputTranslation = document.getElementById("output-translation");
const outputExplanation = document.getElementById("output-explanation");
const breakdownContainer = document.getElementById("breakdown-container");
const speakLatinBtn = document.getElementById("speak-latin");

// Modals
const modalCheatsheet = document.getElementById("modal-cheatsheet");
const toggleCheatsheetBtn = document.getElementById("cheatsheet-toggle");
const closeCheatsheetBtn = document.getElementById("close-cheatsheet");

// Toast
const toast = document.getElementById("toast");
const toastMessage = document.getElementById("toast-message");

/* --- Init and Event Listeners --- */
document.addEventListener("DOMContentLoaded", () => {
    // Setup camera stream on start
    startCamera();
    
    // Tab switching
    tabCamera.addEventListener("click", () => switchTab("camera"));
    tabUpload.addEventListener("click", () => switchTab("upload"));
    
    // Real-time scan toggle listener
    const realtimeToggle = document.getElementById("realtime-toggle");
    const scanFrame = document.getElementById("scan-frame");
    if (realtimeToggle) {
        realtimeToggle.addEventListener("change", (e) => {
            isRealtimeScanning = e.target.checked;
            if (isRealtimeScanning) {
                if (scanFrame) scanFrame.classList.add("scanning");
                captureBtn.disabled = true;
                captureBtn.style.opacity = "0.5";
                startRealtimeLoop();
            } else {
                if (scanFrame) scanFrame.classList.remove("scanning");
                captureBtn.disabled = false;
                captureBtn.style.opacity = "1";
                stopRealtimeLoop();
            }
        });
    }
    
    // Camera capture
    captureBtn.addEventListener("click", captureAndPredict);
    
    // Upload dropzone interactions
    dropzone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFileSelect);
    
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });
    
    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });
    
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    clearImageBtn.addEventListener("click", clearImageUpload);
    
    // Camera Transform controls
    const mirrorHBtn = document.getElementById("mirror-h-btn");
    const mirrorVBtn = document.getElementById("mirror-v-btn");
    const rotateBtn = document.getElementById("rotate-btn");
    
    function updateCameraTransform() {
        let transformStr = "";
        if (isCameraMirroredH) transformStr += " scaleX(-1)";
        if (isCameraMirroredV) transformStr += " scaleY(-1)";
        if (cameraRotation !== 0) transformStr += ` rotate(${cameraRotation}deg)`;
        video.style.transform = transformStr;
    }
    
    if (mirrorHBtn) {
        mirrorHBtn.addEventListener("click", () => {
            isCameraMirroredH = !isCameraMirroredH;
            mirrorHBtn.style.backgroundColor = isCameraMirroredH ? "var(--accent)" : "rgba(0, 0, 0, 0.4)";
            updateCameraTransform();
        });
    }
    
    if (mirrorVBtn) {
        mirrorVBtn.addEventListener("click", () => {
            isCameraMirroredV = !isCameraMirroredV;
            mirrorVBtn.style.backgroundColor = isCameraMirroredV ? "var(--accent)" : "rgba(0, 0, 0, 0.4)";
            updateCameraTransform();
        });
    }
    
    if (rotateBtn) {
        rotateBtn.addEventListener("click", () => {
            cameraRotation = (cameraRotation + 90) % 360;
            rotateBtn.style.backgroundColor = cameraRotation !== 0 ? "var(--accent)" : "rgba(0, 0, 0, 0.4)";
            updateCameraTransform();
        });
    }
    
    // Speak pelafalan
    speakLatinBtn.addEventListener("click", speakText);
    
    // Modals
    toggleCheatsheetBtn.addEventListener("click", () => openModal(modalCheatsheet));
    const toggleHeroCheatsheet = document.getElementById("cheatsheet-toggle-hero");
    if (toggleHeroCheatsheet) {
        toggleHeroCheatsheet.addEventListener("click", () => openModal(modalCheatsheet));
    }
    closeCheatsheetBtn.addEventListener("click", () => closeModal(modalCheatsheet));
    
    // Close modal on outside click
    window.addEventListener("click", (e) => {
        if (e.target === modalCheatsheet) closeModal(modalCheatsheet);
    });
});

/* --- Toast Notification Helper --- */
function showToast(message, isError = false) {
    toastMessage.textContent = message;
    const icon = toast.querySelector(".toast-icon");
    if (isError) {
        toast.style.borderColor = "var(--error)";
        icon.className = "fa-solid fa-triangle-exclamation toast-icon";
        icon.style.color = "var(--error)";
    } else {
        toast.style.borderColor = "var(--border)";
        icon.className = "fa-solid fa-circle-check toast-icon";
        icon.style.color = "var(--accent)";
    }
    
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 4000);
}

/* --- Camera Streaming Management --- */
async function startCamera() {
    if (activeStream) {
        stopCamera();
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "environment", // Use back camera on mobile phones
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });
        video.srcObject = stream;
        activeStream = stream;
    } catch (err) {
        console.error("Camera access failed:", err);
        showToast("Gagal mengakses kamera. Silakan periksa izin kamera Anda.", true);
    }
}

function stopCamera() {
    // Turn off real-time scan when stopping camera
    const realtimeToggle = document.getElementById("realtime-toggle");
    if (realtimeToggle && realtimeToggle.checked) {
        realtimeToggle.checked = false;
        isRealtimeScanning = false;
        const scanFrame = document.getElementById("scan-frame");
        if (scanFrame) scanFrame.classList.remove("scanning");
        captureBtn.disabled = false;
        captureBtn.style.opacity = "1";
        stopRealtimeLoop();
    }

    if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        activeStream = null;
    }
}

/* --- Tab Switching --- */
function switchTab(tabType) {
    if (tabType === "camera") {
        tabCamera.classList.add("active");
        tabUpload.classList.remove("active");
        cameraContainer.classList.add("active");
        uploadContainer.classList.remove("active");
        startCamera();
    } else {
        tabCamera.classList.remove("active");
        tabUpload.classList.add("active");
        cameraContainer.classList.remove("active");
        uploadContainer.classList.add("active");
        
        // Turn off real-time scan when switching tab
        const realtimeToggle = document.getElementById("realtime-toggle");
        if (realtimeToggle && realtimeToggle.checked) {
            realtimeToggle.checked = false;
            isRealtimeScanning = false;
            const scanFrame = document.getElementById("scan-frame");
            if (scanFrame) scanFrame.classList.remove("scanning");
            captureBtn.disabled = false;
            captureBtn.style.opacity = "1";
            stopRealtimeLoop();
        }
        
        stopCamera();
    }
}

/* --- Upload Handling --- */
function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    if (!file.type.match("image.*")) {
        showToast("Format berkas harus berupa gambar!", true);
        return;
    }
    
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        dropzone.style.display = "none";
        previewContainer.style.display = "flex";
        
        // Trigger prediction directly on upload
        predictImage(file, false);
    };
    reader.readAsDataURL(file);
}

function clearImageUpload() {
    currentFile = null;
    imagePreview.src = "";
    previewContainer.style.display = "none";
    dropzone.style.display = "flex";
    fileInput.value = "";
    
    // Reset output views
    resultsView.style.display = "none";
    loadingView.style.display = "none";
    emptyView.style.display = "flex";
}

/* --- Capture Frame from Video --- */
function captureAndPredict() {
    if (!activeStream) {
        showToast("Kamera tidak aktif!", true);
        return;
    }
    
    // Draw current frame to canvas (ROI only: center 80% width, 60% height)
    const ctx = canvas.getContext("2d");
    const videoW = video.videoWidth;
    const videoH = video.videoHeight;
    
    const roiW = videoW * 0.8;
    const roiH = videoH * 0.6;
    
    // Swap canvas dimensions if rotated 90 or 270 degrees
    if (cameraRotation === 90 || cameraRotation === 270) {
        canvas.width = roiH;
        canvas.height = roiW;
    } else {
        canvas.width = roiW;
        canvas.height = roiH;
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    
    // Move coordinate origin to the center of the canvas
    ctx.translate(canvas.width / 2, canvas.height / 2);
    
    // Rotate canvas context
    if (cameraRotation !== 0) {
        ctx.rotate((cameraRotation * Math.PI) / 180);
    }
    
    // Apply horizontal & vertical scaling reflection
    const scaleX = isCameraMirroredH ? -1 : 1;
    const scaleY = isCameraMirroredV ? -1 : 1;
    ctx.scale(scaleX, scaleY);
    
    // Draw the source frame centered (outer margins are automatically clipped)
    ctx.drawImage(video, -videoW / 2, -videoH / 2, videoW, videoH);
    
    ctx.restore();
    
    // Convert to Blob and Predict
    canvas.toBlob((blob) => {
        const file = new File([blob], "capture.png", { type: "image/png" });
        predictImage(file, true);
    }, "image/png");
    
    // Visual flash animation
    cameraContainer.style.animation = "none";
    setTimeout(() => {
        cameraContainer.style.animation = "flashPulse 0.5s ease-out";
    }, 10);
}

/* --- Real-Time Camera Scan Loop & Stabilization --- */
function startRealtimeLoop() {
    stopRealtimeLoop();
    stablePredictionHistory = [];
    stableDebounceCount = 0;
    
    // Scan immediately on toggle
    captureRealtimeFrame();
    
    // Setup interval to scan every 800ms
    realtimeInterval = setInterval(() => {
        if (!isPredicting) {
            captureRealtimeFrame();
        }
    }, 800);
}

function stopRealtimeLoop() {
    if (realtimeInterval) {
        clearInterval(realtimeInterval);
        realtimeInterval = null;
    }
}

function captureRealtimeFrame() {
    if (!activeStream || !isRealtimeScanning) return;
    
    const ctx = canvas.getContext("2d");
    const videoW = video.videoWidth;
    const videoH = video.videoHeight;
    if (!videoW || !videoH) return;
    
    const roiW = videoW * 0.8;
    const roiH = videoH * 0.6;
    
    if (cameraRotation === 90 || cameraRotation === 270) {
        canvas.width = roiH;
        canvas.height = roiW;
    } else {
        canvas.width = roiW;
        canvas.height = roiH;
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    if (cameraRotation !== 0) {
        ctx.rotate((cameraRotation * Math.PI) / 180);
    }
    const scaleX = isCameraMirroredH ? -1 : 1;
    const scaleY = isCameraMirroredV ? -1 : 1;
    ctx.scale(scaleX, scaleY);
    ctx.drawImage(video, -videoW / 2, -videoH / 2, videoW, videoH);
    ctx.restore();
    
    isPredicting = true;
    canvas.toBlob((blob) => {
        if (blob && isRealtimeScanning) {
            const file = new File([blob], "capture.png", { type: "image/png" });
            predictImageRealtime(file);
        } else {
            isPredicting = false;
        }
    }, "image/png");
}

async function predictImageRealtime(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", "sentence");
    formData.append("is_webcam", "true");
    
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            throw new Error("Prediction error");
        }
        
        const data = await response.json();
        
        // Stabilize prediction output
        const cleanNew = (data.transliteration || "").trim();
        
        if (!cleanNew || cleanNew === "-") {
            stableDebounceCount++;
            // Ignore temporary empty misses for up to 3 cycles (2.4 seconds)
            if (stableDebounceCount <= 3 && stablePredictionHistory.length > 0) {
                isPredicting = false;
                return;
            }
        } else {
            stableDebounceCount = 0;
        }
        
        // Push to history
        stablePredictionHistory.push(cleanNew);
        if (stablePredictionHistory.length > 5) {
            stablePredictionHistory.shift();
        }
        
        // Update display view
        if (emptyView.style.display !== "none") emptyView.style.display = "none";
        if (loadingView.style.display !== "none") loadingView.style.display = "none";
        if (resultsView.style.display !== "flex") resultsView.style.display = "flex";
        
        renderResults(data);
        
    } catch (err) {
        console.error("Realtime translation request failed:", err);
    } finally {
        isPredicting = false;
    }
}

/* --- API Prediction Request --- */
async function predictImage(file, isWebcam = false) {
    // Show loading state
    emptyView.style.display = "none";
    resultsView.style.display = "none";
    loadingView.style.display = "flex";
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", "sentence");
    formData.append("is_webcam", isWebcam);
    
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Gagal menerjemahkan gambar.");
        }
        
        const data = await response.json();
        renderResults(data);
        
    } catch (err) {
        console.error("Prediction error:", err);
        showToast(err.message, true);
        
        loadingView.style.display = "none";
        resultsView.style.display = "none";
        emptyView.style.display = "flex";
    }
}

/* --- Render API Results to UI --- */
function renderResults(data) {
    loadingView.style.display = "none";
    resultsView.style.display = "flex";
    
    // Set Badge Source
    if (resultSource) {
        if (data.source === "gemini") {
            resultSource.textContent = "MESIN AWAN (GEMINI)";
            resultSource.className = "source-badge badge-gemini";
        } else {
            resultSource.textContent = "MESIN LOKAL";
            resultSource.className = "source-badge badge-local";
        }
    }
    
    // Set text contents
    outputLatin.textContent = data.transliteration || "-";
    outputPronunciation.textContent = `Pengucapan Jawa: ${data.pronunciation || "-"}`;
    outputTranslation.textContent = data.translation || "-";
    if (outputExplanation) {
        outputExplanation.textContent = data.explanation || "";
    }
    
    // Clear & Populate Breakdown cards
    breakdownContainer.innerHTML = "";
    
    if (data.breakdown && data.breakdown.length > 0) {
        data.breakdown.forEach(item => {
            const card = document.createElement("div");
            card.className = "breakdown-card";
            
            // Format sandhangan indicator
            let sandText = "None";
            if (item.sandhangan) {
                sandText = `<strong>${item.sandhangan}</strong>`;
            }
            
            card.innerHTML = `
                <div class="breakdown-syl">${item.syllable}</div>
                <div class="breakdown-parts">
                    Base: <strong>${item.base}</strong>
                    <em>Sandhangan: ${sandText}</em>
                </div>
            `;
            
            // Add mouse hover description using tooltip/title attribute
            card.title = `${item.base_desc}\n${item.sandhangan_desc}`;
            
            breakdownContainer.appendChild(card);
        });
    } else {
        // No breakdown (e.g. Gemini mode has no breakdown items)
        const emptyBreakdown = document.createElement("p");
        emptyBreakdown.className = "small-text";
        emptyBreakdown.style.gridColumn = "1 / -1";
        emptyBreakdown.style.textAlign = "center";
        emptyBreakdown.textContent = "Detail breakdown per suku kata tidak tersedia untuk mode Gemini.";
        breakdownContainer.appendChild(emptyBreakdown);
    }
}

/* --- TTS Javanese Pronunciation --- */
function speakText() {
    const text = outputPronunciation.textContent.replace("Pengucapan Jawa: ", "").trim();
    if (!text || text === "-") return;
    
    if ("speechSynthesis" in window) {
        // Stop any playing sound
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "id-ID"; // Indonesian voices pronounces Javanese vowels /o/ and consonants perfectly
        utterance.pitch = 1.0;
        utterance.rate = 0.85; // Slow down slightly for clarity
        
        // Add active glowing class to btn
        speakLatinBtn.style.color = "var(--accent)";
        utterance.onend = () => {
            speakLatinBtn.style.color = "var(--text-secondary)";
        };
        utterance.onerror = () => {
            speakLatinBtn.style.color = "var(--text-secondary)";
        };
        
        window.speechSynthesis.speak(utterance);
    } else {
        showToast("Pelafalan suara tidak didukung di peramban ini.", true);
    }
}

/* --- Modals Helper --- */
function openModal(modalEl) {
    modalEl.style.display = "flex";
    setTimeout(() => {
        modalEl.classList.add("active");
    }, 10);
}

function closeModal(modalEl) {
    modalEl.classList.remove("active");
    setTimeout(() => {
        modalEl.style.display = "none";
    }, 300);
}

/* --- Model Latihan (Dihapus) --- */
