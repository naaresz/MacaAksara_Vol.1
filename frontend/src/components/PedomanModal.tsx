import React from 'react';

interface PedomanModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PedomanModal: React.FC<PedomanModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div id="modal-cheatsheet" className="modal active" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><i className="fa-solid fa-book-open"></i> Pedoman Aksara Jawa</h2>
          <button className="modal-close" id="close-cheatsheet" onClick={onClose}>
            <i className="fa-solid fa-xmark"></i>
          </button>
        </div>
        <div className="modal-body">
          <h3>Aksara Carakan (20 Aksara Dasar)</h3>
          <div className="aksara-grid">
            <div className="aksara-card"><span>ꦲ</span><strong>ha</strong></div>
            <div className="aksara-card"><span>ꦤ</span><strong>na</strong></div>
            <div className="aksara-card"><span>ꦕ</span><strong>ca</strong></div>
            <div className="aksara-card"><span>ꦫ</span><strong>ra</strong></div>
            <div className="aksara-card"><span>ꦏ</span><strong>ka</strong></div>
            <div className="aksara-card"><span>ꦢ</span><strong>da</strong></div>
            <div className="aksara-card"><span>ꦠ</span><strong>ta</strong></div>
            <div className="aksara-card"><span>ꦱ</span><strong>sa</strong></div>
            <div className="aksara-card"><span>ꦮ</span><strong>wa</strong></div>
            <div className="aksara-card"><span>ꦭ</span><strong>la</strong></div>
            <div className="aksara-card"><span>ꦥ</span><strong>pa</strong></div>
            <div className="aksara-card"><span>ꦝ</span><strong>dha</strong></div>
            <div className="aksara-card"><span>ꦗ</span><strong>ja</strong></div>
            <div className="aksara-card"><span>ꦪ</span><strong>ya</strong></div>
            <div className="aksara-card"><span>ꦚ</span><strong>nya</strong></div>
            <div className="aksara-card"><span>ꦩ</span><strong>ma</strong></div>
            <div className="aksara-card"><span>ꦒ</span><strong>ga</strong></div>
            <div className="aksara-card"><span>ꦧ</span><strong>ba</strong></div>
            <div className="aksara-card"><span>ꦛ</span><strong>tha</strong></div>
            <div className="aksara-card"><span>ꦔ</span><strong>nga</strong></div>
          </div>
          
          <h3>Sandhangan Swara (Vokal)</h3>
          <div className="sandhangan-list">
            <div className="sandhangan-row">
              <div className="sand-icon">ꦶ</div>
              <div className="sand-desc"><strong>Wulu (i)</strong>: Menambahkan vokal /i/ di atas aksara. Contoh: ꦧꦶ (bi).</div>
            </div>
            <div className="sandhangan-row">
              <div className="sand-icon">ꦸ</div>
              <div className="sand-desc"><strong>Suku (u)</strong>: Menambahkan vokal /u/ di bawah aksara. Contoh: ꦧꦸ (bu).</div>
            </div>
            <div className="sandhangan-row">
              <div className="sand-icon">ꦺ</div>
              <div className="sand-desc"><strong>Taling (è)</strong>: Mengubah vokal menjadi /è/ di depan aksara. Contoh: ꦺꦧ (bè).</div>
            </div>
            <div className="sandhangan-row">
              <div className="sand-icon">ꦺꦴ</div>
              <div className="sand-desc"><strong>Taling Tarung (o)</strong>: Mengapit aksara untuk mengubah vokal menjadi /o/. Contoh: ꦺꦧꦴ (bo).</div>
            </div>
            <div className="sandhangan-row">
              <div className="sand-icon">ꦼ</div>
              <div className="sand-desc"><strong>Pepet (e)</strong>: Mengubah vokal menjadi /e/ pepet (seperti pada kata 'segar') di atas aksara. Contoh: ꦧꦼ (be).</div>
            </div>
          </div>

          <h3>Sandhangan Panyigeg Sigeg (Akhiran Konsonan)</h3>
          <div className="sandhangan-list">
            <div className="sandhangan-row">
              <div className="sand-icon">ꦃ</div>
              <div className="sand-desc"><strong>Wignyan (h)</strong>: Menambahkan konsonan akhir /h/. Contoh: ꦧꦃ (bah).</div>
            </div>
            <div className="sandhangan-row">
              <div className="sand-icon">ꦁ</div>
              <div className="sand-desc"><strong>Cecak (ng)</strong>: Menambahkan konsonan akhir /ng/. Contoh: ꦧꦁ (bang).</div>
            </div>
            <div className="sandhangan-row">
              <div className="sand-icon">ꦂ</div>
              <div className="sand-desc"><strong>Layar (r)</strong>: Menambahkan konsonan akhir /r/. Contoh: ꦧꦂ (bar).</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
