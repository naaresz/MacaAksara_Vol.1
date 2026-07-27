import React, { useState, useEffect } from 'react';
import { FileUploader } from '../components/FileUploader';
import { CameraScanner } from '../components/CameraScanner';
import { ResultPanel } from '../components/ResultPanel';
import { predictImage, getTrainingStatus } from '../lib/api';
import type { PredictionResult, TrainingStatus } from '../lib/api';

export const Workspace: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'camera'>('upload');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await getTrainingStatus();
        setTrainingStatus(data);
      } catch (err) {
        console.error("Failed to fetch training status:", err);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleFileSelect = async (file: File) => {
    setSelectedImage(URL.createObjectURL(file));
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const data = await predictImage(file, false);
      setPrediction(data);
    } catch (err: any) {
      console.error("Prediction failed:", err);
      setError(err.message || "Gagal menerjemahkan gambar.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedImage(null);
    setPrediction(null);
    setLoading(false);
    setError(null);
  };

  const handleTabChange = (tab: 'upload' | 'camera') => {
    setActiveTab(tab);
    handleClear();
  };

  return (
    <section className="workspace-section" id="workspace-section">
      <div className="section-title">
        <h2>Workspace Penerjemah</h2>
        <p>Pilih metode input di bawah sarta AI akan membaca Aksara Jawa secara otomatis</p>
      </div>


      <div className="workspace-container main-content">
        {/* Left Input Box */}
        <div className="input-panel panel">
          {/* Tab buttons */}
          <div className="tab-control tabs">
            <button 
              className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => handleTabChange('upload')}
            >
              <i className="fa-solid fa-file-image"></i> Unggah Gambar
            </button>
            <button 
              className={`tab-btn ${activeTab === 'camera' ? 'active' : ''}`}
              onClick={() => handleTabChange('camera')}
            >
              <i className="fa-solid fa-camera"></i> Gunakan Kamera
            </button>
          </div>

          {/* Render Active Input Tab */}
          {activeTab === 'upload' ? (
            <FileUploader 
              selectedImage={selectedImage}
              onFileSelect={handleFileSelect}
              onClear={handleClear}
            />
          ) : (
            <CameraScanner 
              isActive={activeTab === 'camera'}
              onPredictionResult={setPrediction}
              onLoadingChange={setLoading}
              onErrorChange={setError}
            />
          )}
        </div>

        {/* Right Output Box */}
        <ResultPanel 
          result={prediction}
          loading={loading}
          error={error}
        />
      </div>
    </section>
  );
};
