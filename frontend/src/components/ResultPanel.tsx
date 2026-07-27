import React, { useState } from 'react';
import type { PredictionResult } from '../lib/api';
import { speakJavanese } from '../lib/speech';

interface ResultPanelProps {
  result: PredictionResult | null;
  loading: boolean;
  error: string | null;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({ result, loading, error }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [activeTab, setActiveTab] = useState<'translation' | 'transliteration' | 'breakdown'>('transliteration');

  const handleSpeak = () => {
    if (!result || !result.pronunciation) return;
    speakJavanese(
      result.pronunciation,
      () => setIsSpeaking(true),
      () => setIsSpeaking(false)
    );
  };

  if (loading) {
    return (
      <div id="results-panel" className="result-panel panel active dark-theme-panel">
        <div id="loading-spinner" className="loading-spinner active">
          <div className="spinner"></div>
          <p style={{ color: '#ffffff', marginTop: '12px' }}>Menganalisis aksara dengan AI...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id="results-panel" className="result-panel panel active dark-theme-panel">
        <div className="error-message" style={{ textAlign: 'center', padding: '40px 20px', color: '#ffb3b3' }}>
          <i className="fa-solid fa-circle-exclamation error-icon" style={{ fontSize: '3rem', marginBottom: '15px' }}></i>
          <p style={{ fontSize: '1.1rem', fontWeight: 500 }}>{error}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div id="results-panel" className="result-panel panel active dark-theme-panel">
        <div id="empty-state" className="empty-state active" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '300px', color: '#ebdcc5', textAlign: 'center', padding: '24px' }}>
          <i className="fa-solid fa-wand-magic-sparkles magic-icon" style={{ fontSize: '3.5rem', color: '#d4af37', marginBottom: '16px' }}></i>
          <h3 style={{ fontFamily: 'Lora, serif', fontSize: '1.5rem', color: '#ffffff', marginBottom: '8px' }}>Menunggu Masukan Gambar</h3>
          <p style={{ fontSize: '0.95rem', maxWidth: '340px', lineHeight: '1.5', color: '#ebdcc5' }}>Unggah berkas foto aksara Jawa atau gunakan kamera laptop Anda untuk memulai deteksi sarta penerjemahan otomatis secara real-time.</p>
        </div>
      </div>
    );
  }

  return (
    <div id="results-panel" className="result-panel panel active dark-theme-panel">
      {/* Navbar Tabs inside Results Panel */}
      <div className="result-navbar">
        <button 
          className={`result-nav-btn ${activeTab === 'transliteration' ? 'active' : ''}`}
          onClick={() => setActiveTab('transliteration')}
        >
          <i className="fa-solid fa-font"></i> Transliterasi Latin
        </button>
        <button 
          className={`result-nav-btn ${activeTab === 'translation' ? 'active' : ''}`}
          onClick={() => setActiveTab('translation')}
        >
          <i className="fa-solid fa-language"></i> Terjemahan Indo
        </button>
        <button 
          className={`result-nav-btn ${activeTab === 'breakdown' ? 'active' : ''}`}
          onClick={() => setActiveTab('breakdown')}
        >
          <i className="fa-solid fa-circle-info"></i> Rincian Aksara
        </button>
      </div>

      <div className="result-content-area">
        {activeTab === 'translation' && (
          <div className="translation-tab-content">
            <div className="translation-card-premium">
              <div className="card-top-header">
                <span className="card-label-tag">Terjemahan Indonesia</span>
              </div>
              <div className="translation-output-text">
                {result.translation || "Gagal mendapatkan terjemahan."}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'transliteration' && (
          <div className="translation-tab-content">
            <div className="translation-card-premium">
              <div className="card-top-header">
                <span className="card-label-tag">Transliterasi Latin</span>
                {result.pronunciation && result.pronunciation !== "-" && (
                  <button 
                    id="speak-latin" 
                    className={`speak-icon-btn ${isSpeaking ? 'speaking' : ''}`} 
                    title="Dengarkan Pelafalan" 
                    onClick={handleSpeak}
                  >
                    <i className="fa-solid fa-volume-high"></i>
                  </button>
                )}
              </div>
              <div className="translation-output-text">
                {result.transliteration || "-"}
              </div>
            </div>
            
            {result.pronunciation && result.pronunciation !== "-" && (
              <div className="pronunciation-meta-info">
                <span>Pelafalan: <em>{result.pronunciation}</em></span>
              </div>
            )}
          </div>
        )}

        {activeTab === 'breakdown' && (
          <div className="breakdown-tab-content">
            {result.breakdown && result.breakdown.length > 0 ? (
              <div className="breakdown-grid-premium">
                {result.breakdown.map((item: any, index) => (
                  <div key={index} className="breakdown-card-premium" title={`${item.base_desc || ''}\n${item.sandhangan_desc || ''}`}>
                    <div className="breakdown-javanese-char">{item.javanese_script || item.syllable}</div>
                    <div className="breakdown-latin-label">Base: {item.base || "-"}</div>
                    {item.sandhangan && item.sandhangan !== "" && (
                      <div className="breakdown-badge-wrapper">
                        <span className="diacritic-badge-premium">{item.sandhangan}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#ebdcc5', textAlign: 'center', padding: '20px' }}>Tidak ada rincian suku kata yang tersedia.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
