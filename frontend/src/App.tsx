import React, { useState } from 'react';
import { Header } from './layouts/Header';
import { Footer } from './layouts/Footer';
import { Hero } from './components/Hero';
import { Beranda } from './page/Beranda';
import { Workspace } from './page/Workspace';
import { PedomanModal } from './components/PedomanModal';

function App() {
  const [activeTab, setActiveTab] = useState<string>('beranda');
  const [isPedomanOpen, setIsPedomanOpen] = useState<boolean>(false);

  const handleStartTranslate = (e: React.MouseEvent) => {
    e.preventDefault();
    setActiveTab('workspace');
    setTimeout(() => {
      const el = document.getElementById('workspace-section');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <div className="react-app-root">
      {/* Watermarks */}
      <div className="watermark watermark-left">
        <svg viewBox="0 0 100 150" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M50,10 C20,70 10,110 10,130 C10,140 25,145 50,145 C75,145 90,140 90,130 C90,110 80,70 50,10 Z" stroke="var(--border)" strokeWidth="0.8"/>
          <path d="M50,145 L50,60 M50,120 C40,115 35,110 35,100 M50,105 C60,100 65,95 65,85" stroke="var(--border)" strokeWidth="1.2"/>
          <path d="M30,135 C15,120 20,90 40,95 M70,135 C85,120 80,90 60,95" stroke="var(--border)" strokeWidth="0.6"/>
          <rect x="44" y="130" width="12" height="15" rx="1.5" stroke="var(--border)" strokeWidth="0.8"/>
        </svg>
      </div>
      <div className="watermark watermark-right">
        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M50,10 C25,10 20,40 20,60 C20,80 35,95 50,95 C65,95 80,80 80,60 C80,40 75,10 50,10 Z" stroke="var(--border)" strokeWidth="0.8"/>
          <path d="M22,25 C30,12 40,5 50,5 C60,5 70,12 78,25" stroke="var(--border)" strokeWidth="0.6"/>
          <path d="M32,48 C35,42 43,42 46,48 M68,48 C65,42 57,42 54,48" stroke="var(--border)" strokeWidth="1.2"/>
          <path d="M50,40 L50,65 L46,65 L50,70 L54,65 Z" stroke="var(--border)" strokeWidth="1.2"/>
          <path d="M38,78 C42,85 58,85 62,78 Z" stroke="var(--border)" strokeWidth="0.8"/>
        </svg>
      </div>

      {/* Hero Section */}
      <Hero 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onStartTranslate={handleStartTranslate}
        onOpenPedoman={() => setIsPedomanOpen(true)}
      />

      {/* App Body Container */}
      <div className="app-container">
        <Beranda />
        <Workspace />
      </div>

      {/* Footer */}
      <Footer />

      {/* Cheatsheet Modal */}
      <PedomanModal 
        isOpen={isPedomanOpen} 
        onClose={() => setIsPedomanOpen(false)} 
      />
    </div>
  );
}

export default App;
