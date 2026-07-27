import React, { useRef, useState } from 'react';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  onClear: () => void;
  selectedImage: string | null;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onFileSelect, onClear, selectedImage }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("image/")) {
        onFileSelect(file);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div id="upload-container" className="media-container active" style={{ backgroundColor: 'transparent', border: 'none' }}>
      {!selectedImage ? (
        <div 
          id="dropzone" 
          className={`dropzone ${isDragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={onButtonClick}
        >
          <i className="fa-solid fa-cloud-arrow-up drop-icon"></i>
          <h3>Drag & Drop Gambar Aksara Jawa</h3>
          <p>atau klik untuk menelusuri berkas</p>
          <span className="file-limits">Mendukung PNG, JPG, JPEG</span>
          <input 
            type="file" 
            ref={fileInputRef}
            id="file-input" 
            accept="image/*" 
            style={{ display: 'none' }} 
            onChange={handleChange}
          />
        </div>
      ) : (
        <div id="preview-container" className="preview-container">
          <img id="image-preview" src={selectedImage} alt="Preview gambar" />
          <button id="clear-image" className="btn-clear" title="Hapus Gambar" onClick={onClear}>
            <i className="fa-solid fa-xmark"></i>
          </button>
        </div>
      )}
    </div>
  );
};
