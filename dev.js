const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const isWindows = process.platform === 'win32';
const venvDir = path.join(__dirname, '.venv');
const venvPython = isWindows 
  ? path.join(venvDir, 'Scripts', 'python.exe')
  : path.join(venvDir, 'bin', 'python');

const pipPath = isWindows 
  ? path.join(venvDir, 'Scripts', 'pip.exe')
  : path.join(venvDir, 'bin', 'pip');

// 1. Check Python installation on system
try {
  execSync('python --version', { stdio: 'ignore' });
} catch (err) {
  console.error('[ERROR] Python is not installed or not in system PATH.');
  console.error('Please install Python 3.10+ and make sure it is added to your environment variables.');
  process.exit(1);
}

// 2. Create virtual environment if it does not exist
if (!fs.existsSync(venvDir)) {
  console.log('[INFO] Creating Python virtual environment (.venv)...');
  try {
    execSync('python -m venv .venv', { stdio: 'inherit' });
    console.log('[INFO] Virtual environment created successfully.');
  } catch (err) {
    console.error('[ERROR] Failed to create virtual environment.');
    process.exit(1);
  }
}

// 3. Install requirements
const requirementsFile = path.join(__dirname, 'requirements.txt');
if (fs.existsSync(requirementsFile)) {
  console.log('[INFO] Verifying and installing dependencies from requirements.txt...');
  try {
    execSync(`"${pipPath}" install -r requirements.txt`, { stdio: 'inherit' });
    console.log('[INFO] Dependencies are up to date.');
  } catch (err) {
    console.error('[ERROR] Dependency installation failed.');
    process.exit(1);
  }
}

// 4. Check for model weights
const modelWeights = path.join(__dirname, 'backend', 'app', 'models', 'best_model.pth');
if (!fs.existsSync(modelWeights)) {
  console.log('\n===================================================');
  console.log('[WARNING] Model weights file (backend/app/models/best_model.pth) is missing.');
  console.log('You must train the model for Local OCR mode to function.');
  console.log('You can do this by running the training process automatically');
  console.log('via the web dashboard AI section.');
  console.log('===================================================\n');
}

// 5. Start FastAPI Backend & Vite Frontend Concurrently
console.log('[INFO] Starting FastAPI server on http://localhost:8000 ...');
console.log('[INFO] Starting Vite React dev server on http://localhost:5173 ...');
console.log('[INFO] Press Ctrl+C to stop both servers.');
console.log('');

const uvicornPath = path.join(__dirname, '.venv', 'Scripts', 'uvicorn.exe');
const backend = spawn(uvicornPath, ['backend.app.main:app', '--host', '0.0.0.0', '--port', '8000'], { stdio: 'inherit', shell: isWindows });

const npmCmd = isWindows ? 'npm.cmd' : 'npm';
const frontend = spawn(npmCmd, ['run', 'dev'], { 
  cwd: path.join(__dirname, 'frontend'), 
  stdio: 'inherit',
  shell: isWindows
});

// Close helper
function cleanup() {
  try { backend.kill(); } catch(e){}
  try { frontend.kill(); } catch(e){}
}

process.on('SIGINT', () => {
  cleanup();
  process.exit(0);
});

process.on('exit', () => {
  cleanup();
});

backend.on('close', (code) => {
  cleanup();
  process.exit(code);
});

frontend.on('close', (code) => {
  cleanup();
  process.exit(code);
});
