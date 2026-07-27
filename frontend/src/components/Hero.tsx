import React from 'react';
import { Header } from '../layouts/Header';

interface HeroProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onStartTranslate: (e: React.MouseEvent) => void;
  onOpenPedoman: () => void;
}

export const Hero: React.FC<HeroProps> = ({ 
  activeTab, 
  setActiveTab, 
  onStartTranslate, 
  onOpenPedoman 
}) => {
  return (
    <section className="theater-hero-container">
      <div className="theater-overlay"></div>
      
      {/* Integrated Navigation Bar inside theatrical stage */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onOpenPedoman={onOpenPedoman} 
      />

      {/* Hero stage content */}
      <div className="hero-stage-content">
        <h1 className="hero-title-main">ꦩꦕꦲꦏ꧀ꦱꦫ</h1>
        <h2 className="hero-title-sub">MacaAksara</h2>
        <p className="hero-description">
          Terjemahkan, baca, dan pahami Aksara Jawa dalam hitungan detik dengan teknologi OCR berbasis AI. Cepat, akurat, dan langsung dari browser.
        </p>
        
        <div className="hero-stage-ctas">
          <a href="#workspace-section" className="btn btn-accent btn-lg" onClick={onStartTranslate}>
            <i className="fa-solid fa-camera"></i> Mulai Terjemahkan
          </a>
          <button className="btn btn-secondary btn-lg" onClick={onOpenPedoman}>
            <i className="fa-solid fa-book-open"></i> Pedoman Aksara
          </button>
        </div>
      </div>
      

    </section>
  );
};
