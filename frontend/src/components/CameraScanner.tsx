import React, { useEffect, useRef, useState } from 'react';
import { predictImage } from '../lib/api';
import type { PredictionResult } from '../lib/api';

interface CameraScannerProps {
  onPredictionResult: (result: PredictionResult | null) => void;
  onLoadingChange: (loading: boolean) => void;
  onErrorChange: (error: string | null) => void;
  isActive: boolean;
}

export const CameraScanner: React.FC<CameraScannerProps> = ({
  onPredictionResult,
  onLoadingChange,
  onErrorChange,
  isActive
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  
  // Camera state
  const [rotation, setRotation] = useState<number>(0);
  const [isMirroredH, setIsMirroredH] = useState<boolean>(true);
  const [isMirroredV, setIsMirroredV] = useState<boolean>(false);
  const [isRealtime, setIsRealtime] = useState<boolean>(false);
  
  // Realtime loop state
  const isPredictingRef = useRef(false);
  const realtimeActiveRef = useRef(false);
  const stableHistoryRef = useRef<string[]>([]);
  const stableDebounceRef = useRef<number>(0);

  // Sync state refs to avoid closure stale state in intervals
  const rotationRef = useRef(rotation);
  const mirroredHRef = useRef(isMirroredH);
  const mirroredVRef = useRef(isMirroredV);
  
  useEffect(() => {
    rotationRef.current = rotation;
  }, [rotation]);

  useEffect(() => {
    mirroredHRef.current = isMirroredH;
  }, [isMirroredH]);

  useEffect(() => {
    mirroredVRef.current = isMirroredV;
  }, [isMirroredV]);

  // Start Camera
  const startCamera = async () => {
    try {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
      
      const newStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
      }
      setStream(newStream);
      onErrorChange(null);
    } catch (err) {
      console.error("Camera access error:", err);
      onErrorChange("Gagal mengakses kamera. Silakan periksa izin kamera Anda.");
    }
  };

  // Stop Camera
  const stopCamera = () => {
    setIsRealtime(false);
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setStream(null);
    }
  };

  // Manage camera lifetime based on isActive prop
  useEffect(() => {
    if (isActive) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isActive]);

  // Handle auto-scan loop
  useEffect(() => {
    realtimeActiveRef.current = isRealtime;
    let intervalId: any = null;

    if (isRealtime && stream) {
      stableHistoryRef.current = [];
      stableDebounceRef.current = 0;
      
      // Initial scan
      captureFrame(true);

      intervalId = setInterval(() => {
        if (!isPredictingRef.current && realtimeActiveRef.current) {
          captureFrame(true);
        }
      }, 800);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isRealtime, stream]);

  // Capture current frame from video stream
  const captureFrame = (isRealtimeMode: boolean = false) => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !stream) return;

    const videoW = video.videoWidth;
    const videoH = video.videoHeight;
    if (!videoW || !videoH) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // ROI coordinates (80% width, 60% height)
    const roiW = videoW * 0.8;
    const roiH = videoH * 0.6;

    const currentRotation = rotationRef.current;
    const currentMirroredH = mirroredHRef.current;
    const currentMirroredV = mirroredVRef.current;

    // Set canvas dimensions based on rotation
    if (currentRotation === 90 || currentRotation === 270) {
      canvas.width = roiH;
      canvas.height = roiW;
    } else {
      canvas.width = roiW;
      canvas.height = roiH;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    // Center origin
    ctx.translate(canvas.width / 2, canvas.height / 2);

    // Rotate
    if (currentRotation !== 0) {
      ctx.rotate((currentRotation * Math.PI) / 180);
    }

    // Mirror scale
    const scaleX = currentMirroredH ? -1 : 1;
    const scaleY = currentMirroredV ? -1 : 1;
    ctx.scale(scaleX, scaleY);

    // Draw
    ctx.drawImage(video, -videoW / 2, -videoH / 2, videoW, videoH);
    ctx.restore();

    // Flash animation on manual capture
    if (!isRealtimeMode) {
      const container = document.getElementById('camera-view-container');
      if (container) {
        container.style.animation = "none";
        setTimeout(() => {
          container.style.animation = "flashPulse 0.5s ease-out";
        }, 10);
      }
    }

    // API Prediction
    if (isRealtimeMode) {
      isPredictingRef.current = true;
      canvas.toBlob(async (blob) => {
        if (blob && realtimeActiveRef.current) {
          try {
            const file = new File([blob], "capture.png", { type: "image/png" });
            const data = await predictImage(file, true);
            
            // Stabilization logic
            const cleanNew = (data.transliteration || "").trim();
            if (!cleanNew || cleanNew === "-") {
              stableDebounceRef.current += 1;
              if (stableDebounceRef.current <= 3 && stableHistoryRef.current.length > 0) {
                isPredictingRef.current = false;
                return;
              }
            } else {
              stableDebounceRef.current = 0;
            }

            stableHistoryRef.current.push(cleanNew);
            if (stableHistoryRef.current.length > 5) {
              stableHistoryRef.current.shift();
            }

            onPredictionResult(data);
          } catch (err) {
            console.error("Realtime capture request failed:", err);
          } finally {
            isPredictingRef.current = false;
          }
        } else {
          isPredictingRef.current = false;
        }
      }, "image/png");
    } else {
      onLoadingChange(true);
      onErrorChange(null);
      canvas.toBlob(async (blob) => {
        if (blob) {
          try {
            const file = new File([blob], "capture.png", { type: "image/png" });
            const data = await predictImage(file, true);
            onPredictionResult(data);
          } catch (err: any) {
            console.error("Manual capture prediction failed:", err);
            onErrorChange(err.message || "Gagal menerjemahkan potret kamera.");
          } finally {
            onLoadingChange(false);
          }
        } else {
          onLoadingChange(false);
        }
      }, "image/png");
    }
  };

  const handleRotate = () => {
    setRotation(r => (r + 90) % 360);
  };

  // Transform string for HTML video preview styling
  const getTransformStyle = () => {
    let transformStr = `rotate(${rotation}deg)`;
    if (isMirroredH) transformStr += " scaleX(-1)";
    if (isMirroredV) transformStr += " scaleY(-1)";
    return { transform: transformStr };
  };

  return (
    <div id="camera-container" className="media-container active">
      <div 
        id="camera-view-container" 
        className="camera-view-container"
      >
        <video 
          ref={videoRef}
          id="webcam" 
          autoPlay 
          playsInline 
          style={getTransformStyle()}
        ></video>
        <div id="scan-frame" className={`scan-frame ${isRealtime ? 'scanning' : ''}`}>
          <div className="corner top-left"></div>
          <div className="corner top-right"></div>
          <div className="corner bottom-left"></div>
          <div className="corner bottom-right"></div>
          <div className="scan-line"></div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="camera-controls">
        <button 
          id="mirror-h-btn" 
          className={`control-btn ${isMirroredH ? 'active' : ''}`}
          title="Cermin Horizontal"
          onClick={() => setIsMirroredH(!isMirroredH)}
        >
          <i className="fa-solid fa-arrows-left-right"></i>
        </button>
        <button 
          id="mirror-v-btn" 
          className={`control-btn ${isMirroredV ? 'active' : ''}`}
          title="Cermin Vertical"
          onClick={() => setIsMirroredV(!isMirroredV)}
        >
          <i className="fa-solid fa-arrows-up-down"></i>
        </button>
        <button 
          id="rotate-btn" 
          className="control-btn" 
          title="Putar 90"
          onClick={handleRotate}
        >
          <i className="fa-solid fa-rotate-right"></i>
        </button>
        <div className="toggle-wrapper" title="Terjemahkan otomatis secara langsung saat kamera bergeser">
          <span className="toggle-label">Auto-Scan</span>
          <label className="switch">
            <input 
              type="checkbox" 
              id="realtime-toggle" 
              checked={isRealtime}
              onChange={(e) => setIsRealtime(e.target.checked)}
            />
            <span className="slider round"></span>
          </label>
        </div>
      </div>

      <button 
        id="capture-btn" 
        className="btn-accent capture-trigger-btn"
        disabled={isRealtime}
        style={{ opacity: isRealtime ? 0.5 : 1 }}
        onClick={() => captureFrame(false)}
      >
        <i className="fa-solid fa-camera"></i> Ambil Potret
      </button>

      {/* Hidden canvas for snapshot rendering */}
      <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
    </div>
  );
};
