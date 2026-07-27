export const API_URL = (window.location.port === "8000" || (window.location.origin.startsWith("http") && !window.location.port))
    ? window.location.origin 
    : "http://localhost:8000";

export interface SyllableBreakdown {
  syllable: string;
  transliteration: string;
  meaning: string;
  sandhangan: string[];
}

export interface PredictionResult {
  source: string;
  transliteration: string;
  pronunciation: string;
  translation: string;
  explanation: string;
  breakdown: SyllableBreakdown[];
  error?: string;
}

export async function predictImage(file: File, isWebcam: boolean = false): Promise<PredictionResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("is_webcam", isWebcam ? "true" : "false");

  const response = await fetch(`${API_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Gagal menerjemahkan gambar.");
  }

  return response.json();
}

export interface TrainingStatus {
  status: 'idle' | 'initializing' | 'training' | 'completed' | 'failed' | 'error';
  epoch: number;
  total_epochs: number;
  batch: number;
  total_batches: number;
  loss: number;
  train_acc: number;
  val_acc: number;
  best_acc: number;
  error?: string | null;
}

export async function getTrainingStatus(): Promise<TrainingStatus> {
  const response = await fetch(`${API_URL}/training/status`);
  if (!response.ok) {
    throw new Error("Gagal mengambil status latihan AI.");
  }
  return response.json();
}
