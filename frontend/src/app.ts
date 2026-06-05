import axios from 'axios';

const API = axios.create({ baseURL: 'https://emeritus-21-scanleni-pro.hf.space/api/v1' });
let lastScanContext = '';
let videoStream: MediaStream | null = null;
let isCameraActive = false;
let lastBoxes: any[] = [];
let currentImage: HTMLImageElement | null = null;
let frameWidth = 0;
let frameHeight = 0;

export function initApp() {
  const fileInput = document.getElementById('fileInput') as HTMLInputElement;
  const scanBtn = document.getElementById('scanBtn') as HTMLButtonElement;
  const chatInput = document.getElementById('chatInput') as HTMLInputElement;
  const chatSend = document.getElementById('chatSend') as HTMLButtonElement;
  const chatHistory = document.getElementById('chatHistory') as HTMLDivElement;
  const resultBox = document.getElementById('scanResult') as HTMLDivElement;
  const canvas = document.getElementById('arOverlay') as HTMLCanvasElement;
  const ctx = canvas.getContext('2d')!;
  const video = document.getElementById('cameraFeed') as HTMLVideoElement;
  const camToggle = document.getElementById('camToggle') as HTMLButtonElement;
  const uploadToggle = document.getElementById('uploadToggle') as HTMLButtonElement;
  const camStatus = document.getElementById('camStatus') as HTMLDivElement;

  camToggle.addEventListener('click', () => startCamera(video, canvas, ctx, camStatus, camToggle, uploadToggle));
  uploadToggle.addEventListener('click', () => stopCamera(video, canvas, ctx, camStatus, camToggle, uploadToggle));

  fileInput.addEventListener('change', (e) => {
    if (isCameraActive) stopCamera(video, canvas, ctx, camStatus, camToggle, uploadToggle);
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      currentImage = new Image();
      currentImage.onload = () => drawBaseImage(canvas, ctx, currentImage!);
      currentImage.src = evt.target?.result as string;
    };
    reader.readAsDataURL(file);
  });

  scanBtn.addEventListener('click', async () => {
    if (isCameraActive) {
      await captureAndScan(canvas, ctx, video, scanBtn, resultBox);
    } else if (fileInput.files?.length) {
      await scanUploadedFile(fileInput.files[0], canvas, ctx, scanBtn, resultBox);
    } else {
      alert('Select an image or enable Live Cam first.');
    }
  });

  chatSend.addEventListener('click', async () => {
    const msg = chatInput.value.trim();
    if (!msg) return;
    appendChat('user', msg);
    chatInput.value = '';
    try {
      const payload: any = { message: msg };
      if (lastScanContext) payload.context_product = `Scanned ingredients: ${lastScanContext}`;
      const { data } = await API.post('/chat/', payload);
      appendChat('ai', data.reply);
    } catch { appendChat('ai', 'AI service unavailable. Check API key.'); }
  });
}

async function startCamera(video: HTMLVideoElement, canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, status: HTMLDivElement, camBtn: HTMLButtonElement, uploadBtn: HTMLButtonElement) {
  try {
    videoStream = await navigator.mediaDevices.getUserMedia({ 
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } 
    });
    video.srcObject = videoStream;
    video.classList.remove('d-none');
    isCameraActive = true;
    status.textContent = 'Camera On • Hold Steady';
    status.className = 'position-absolute top-0 start-0 m-2 badge bg-success';
    camBtn.classList.add('active');
    uploadBtn.classList.remove('active');
    document.getElementById('fileInput')!.classList.add('d-none');
    lastBoxes = [];

    video.onloadedmetadata = () => {
      frameWidth = video.videoWidth;
      frameHeight = video.videoHeight;
      requestAnimationFrame(() => drawCameraLoop(video, canvas, ctx));
    };
  } catch (err) {
    alert('Camera access denied. Allow permissions or use Upload mode.');
  }
}

function stopCamera(video: HTMLVideoElement, canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, status: HTMLDivElement, camBtn: HTMLButtonElement, uploadBtn: HTMLButtonElement) {
  if (videoStream) {
    videoStream.getTracks().forEach(t => t.stop());
    videoStream = null;
  }
  video.srcObject = null;
  video.classList.add('d-none');
  isCameraActive = false;
  status.textContent = 'Camera Off';
  status.className = 'position-absolute top-0 start-0 m-2 badge bg-dark opacity-75';
  camBtn.classList.remove('active');
  uploadBtn.classList.add('active');
  document.getElementById('fileInput')!.classList.remove('d-none');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (currentImage) drawBaseImage(canvas, ctx, currentImage);
}

function drawCameraLoop(video: HTMLVideoElement, canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) {
  if (!isCameraActive) return;
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  const scale = Math.min(canvas.width / frameWidth, canvas.height / frameHeight);
  const x = (canvas.width - frameWidth * scale) / 2;
  const y = (canvas.height - frameHeight * scale) / 2;
  ctx.drawImage(video, x, y, frameWidth * scale, frameHeight * scale);
  
  lastBoxes.forEach(b => drawBox(ctx, b, scale, x, y));
  requestAnimationFrame(() => drawCameraLoop(video, canvas, ctx));
}

function drawBox(ctx: CanvasRenderingContext2D, b: any, scale: number, offsetX: number, offsetY: number) {
  const pts = b.bbox.points;
  if (!pts || pts.length < 4) return;
  ctx.beginPath();
  ctx.moveTo(pts[0][0] * scale + offsetX, pts[0][1] * scale + offsetY);
  for (let i = 1; i < pts.length; i++) {
    ctx.lineTo(pts[i][0] * scale + offsetX, pts[i][1] * scale + offsetY);
  }
  ctx.closePath();
  ctx.strokeStyle = b.is_harmful ? '#ff4444' : '#00e599';
  ctx.lineWidth = 2.5;
  ctx.stroke();
  
  ctx.fillStyle = b.is_harmful ? 'rgba(255,68,68,0.8)' : 'rgba(0,229,153,0.8)';
  ctx.font = '12px system-ui';
  ctx.fillRect(pts[0][0] * scale + offsetX, pts[0][1] * scale + offsetY - 18, 60, 16);
  ctx.fillStyle = '#fff';
  ctx.fillText(`${(b.confidence * 100).toFixed(0)}%`, pts[0][0] * scale + offsetX + 4, pts[0][1] * scale + offsetY - 5);
}

function drawBaseImage(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, img: HTMLImageElement) {
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const scale = Math.min(canvas.width / img.naturalWidth, canvas.height / img.naturalHeight);
  const x = (canvas.width - img.naturalWidth * scale) / 2;
  const y = (canvas.height - img.naturalHeight * scale) / 2;
  ctx.drawImage(img, x, y, img.naturalWidth * scale, img.naturalHeight * scale);
  lastBoxes.forEach(b => drawBox(ctx, b, scale, x, y));
}

async function captureAndScan(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, video: HTMLVideoElement, btn: HTMLButtonElement, resultBox: HTMLDivElement) {
  if (frameWidth === 0) return alert('Camera still initializing. Wait 1 second.');
  btn.disabled = true;
  btn.textContent = 'Scanning...';
  
  const frameCanvas = document.createElement('canvas');
  frameCanvas.width = frameWidth;
  frameCanvas.height = frameHeight;
  const fCtx = frameCanvas.getContext('2d')!;
  fCtx.drawImage(video, 0, 0, frameWidth, frameHeight);
  
  frameCanvas.toBlob(async (blob) => {
    if (!blob) return;
    const file = new File([blob], 'cam_frame.jpg', { type: 'image/jpeg' });
    await runScan(file, canvas, ctx, btn, resultBox, true);
  }, 'image/jpeg', 0.85);
}

async function scanUploadedFile(file: File, canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, btn: HTMLButtonElement, resultBox: HTMLDivElement) {
  btn.disabled = true;
  btn.textContent = 'Analyzing...';
  await runScan(file, canvas, ctx, btn, resultBox, false);
}

async function runScan(file: File, canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, btn: HTMLButtonElement, resultBox: HTMLDivElement, isCam: boolean) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const { data } = await API.post('/scan/', formData);
    lastScanContext = data.ocr_data.map((b: any) => b.text).join(', ');
    lastBoxes = data.ocr_data;
    
    // 🔑 NEW: Display Product Identification
    const identityBox = document.getElementById('productIdentity') as HTMLDivElement;
    if (data.product_name) {
      document.getElementById('detectedProductName')!.textContent = data.product_name;
      document.getElementById('detectedProductBrand')!.textContent = data.brand || 'Unknown Brand';
      document.getElementById('detectedProductCategory')!.textContent = data.category || 'Uncategorized';
      identityBox.classList.remove('d-none');
    } else {
      identityBox.classList.add('d-none');
    }
    
    if (!isCam && currentImage) drawBaseImage(canvas, ctx, currentImage);
    
    const ingredientsHtml = data.ocr_data.length > 0 
      ? data.ocr_data.map((b: any) => 
          `<div class="d-flex justify-content-between align-items-center p-2 mb-2 rounded ${b.is_harmful ? 'bg-danger-subtle text-danger' : 'bg-success-subtle text-success'}">
             <span>${b.text}</span>
             <span class="badge ${b.is_harmful ? 'bg-danger' : 'bg-success'}">${(b.confidence * 100).toFixed(0)}%</span>
           </div>`
        ).join('')
      : '<div class="text-muted small">No text/ingredients detected.</div>';

    resultBox.innerHTML = `
      <div class="fw-bold mb-2 ${data.risk_analysis.risk_level === 'SAFE' ? 'text-success' : 'text-warning'}">
        ${data.ai_summary}
      </div>
      <div class="small mb-3">Risk: ${data.risk_analysis.risk_level} | Score: ${data.risk_analysis.health_score}/100</div>
      <h6 class="mt-3 mb-2 border-bottom pb-2">Extracted Ingredients / Text</h6>
      <div class="ingredients-list" style="max-height: 260px; overflow-y: auto;">
        ${ingredientsHtml}
      </div>
    `;
    resultBox.classList.remove('d-none');
    updateDashboard(data);
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Scan failed');
  } finally {
    btn.disabled = false;
    btn.textContent = isCam ? 'Scan Frame' : 'Analyze';
  }
}

function appendChat(role: string, text: string) {
  const box = document.getElementById('chatHistory')!;
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function updateDashboard(data: any) {
  const score = data.risk_analysis.health_score;
  document.getElementById('healthScore')!.textContent = `${score}/100`;
  document.getElementById('healthBar')!.style.width = `${score}%`;
  const badges = document.getElementById('badgesContainer')!;
  badges.innerHTML = '';
  data.gamification.badges.forEach((b: string) => {
    const span = document.createElement('span');
    span.className = 'badge-pill';
    span.textContent = b;
    badges.appendChild(span);
  });
}