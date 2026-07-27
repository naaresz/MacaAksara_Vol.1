import React from 'react';

export const Beranda: React.FC = () => {
  return (
    <section className="tutorial-section" id="tutorial-section">
      <div className="section-title">
        <h2>Tata Cara Kerja</h2>
        <p>Tutorial 3 langkah mudah penggunaan aplikasi MacaAksara</p>
      </div>
      
      <div className="tutorial-grid">
        {/* Card 1 */}
        <div className="tutorial-card">
          <div className="step-num">01</div>
          <div className="card-visual visual-upload">
            <div className="mock-dropzone">
              <i className="fa-solid fa-cloud-arrow-up"></i>
              <div className="mock-lines">
                <div className="mock-line-s"></div>
                <div className="mock-line-xs"></div>
              </div>
            </div>
          </div>
          <h3>1. Unggah Gambar Aksara</h3>
          <p>Siapkan foto aksara Jawa (tulis tangan atau cetak), lalu ambil gambar menggunakan kamera atau unggah berkas gambar.</p>
        </div>
        
        {/* Card 2 */}
        <div className="tutorial-card">
          <div className="step-num">02</div>
          <div className="card-visual visual-processing">
            <div className="mock-box">ꦩꦕ</div>
            <div className="mock-arrow"><i className="fa-solid fa-arrows-spin"></i></div>
            <div className="mock-split">
              <span>ma</span>
              <span>ca</span>
            </div>
          </div>
          <h3>2. Klasifikasi Aksara</h3>
          <p>Sistem akan mengenali karakter, memisahkan sandhangan, serta membaca pasangan secara otomatis.</p>
        </div>
        
        {/* Card 3 */}
        <div className="tutorial-card">
          <div className="step-num">03</div>
          <div className="card-visual visual-output">
            <div className="mock-word-group">
              <div className="mock-word-tag">maca</div>
              <div className="mock-word-arrow"><i className="fa-solid fa-arrow-right"></i></div>
              <div className="mock-word-result">membaca</div>
            </div>
          </div>
          <h3>3. Hasil Transliterasi & Spasi</h3>
          <p>Dapatkan hasil pembacaan latin per kata dengan spasi yang tepat, cara pelafalan Jawa, serta terjemahan bahasa Indonesia.</p>
        </div>
      </div>
    </section>
  );
};
