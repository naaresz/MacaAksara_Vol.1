import React from 'react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenPedoman: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, onOpenPedoman }) => {
  const handleNavClick = (tab: string, e: React.MouseEvent) => {
    e.preventDefault();
    setActiveTab(tab);
    if (tab === 'beranda') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (tab === 'workspace') {
      setTimeout(() => {
        const el = document.getElementById('workspace-section');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  const handleTutorialClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setActiveTab('beranda');
    setTimeout(() => {
      const el = document.getElementById('tutorial-section');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <header className="app-header-integrated">
      <div className="header-inner">
        <div className="logo-area-integrated">
          <div className="logo-icon-wrapper-integrated">
            <svg viewBox="0 0 100 150" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M50,10 C20,70 10,110 10,130 C10,140 25,145 50,145 C75,145 90,140 90,130 C90,110 80,70 50,10 Z" fill="var(--accent)" opacity="0.9"/>
              <path d="M50,145 L50,60 M50,120 C40,115 35,110 35,100 M50,105 C60,100 65,95 65,85" stroke="#ffffff" strokeWidth="2"/>
            </svg>
          </div>
          <div className="logo-text-integrated">
            <span className="logo-title">Maca<span>Aksara</span></span>
            <span className="logo-subtitle">Penerjemah Aksara Jawa</span>
          </div>
        </div>
        
        <nav className="nav-menu">
          <a 
            href="#" 
            className={`nav-item ${activeTab === 'beranda' ? 'active' : ''}`}
            onClick={(e) => handleNavClick('beranda', e)}
          >
            Beranda
          </a>
          <a 
            href="#" 
            className="nav-item"
            onClick={handleTutorialClick}
          >
            Tata Cara
          </a>
          <a 
            href="#" 
            className={`nav-item ${activeTab === 'workspace' ? 'active' : ''}`}
            onClick={(e) => handleNavClick('workspace', e)}
          >
            Workspace
          </a>
          <a 
            href="#" 
            className="nav-item"
            onClick={(e) => { e.preventDefault(); onOpenPedoman(); }}
          >
            Buku Pedoman
          </a>
        </nav>
      </div>
    </header>
  );
};
