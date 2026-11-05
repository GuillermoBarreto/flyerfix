"use strict";

const file = document.getElementById("flyerFile");
const ratio = document.getElementById("cropRatio");
const horizontal = document.getElementById("cropX");
const vertical = document.getElementById("cropY");
const save = document.getElementById("saveCrop");
const status = document.getElementById("cropStatus");
const canvas = document.getElementById("cropPreview");
const context = canvas.getContext("2d");
let currentImage;
let loadId = 0;

function drawCrop() {
  if (!currentImage) return;
  const { naturalWidth, naturalHeight } = currentImage;
  const aspect = Number(ratio.value);
  const width = Math.max(1, Math.floor(Math.min(naturalWidth, naturalHeight * aspect)));
  const height = Math.max(1, Math.floor(Math.min(naturalHeight, naturalWidth / aspect)));
  const x = Math.round((naturalWidth - width) * Number(horizontal.value) / 100);
  const y = Math.round((naturalHeight - height) * Number(vertical.value) / 100);
  const scale = Math.min(1, 1800 / Math.max(width, height));

  horizontal.disabled = width === naturalWidth;
  vertical.disabled = height === naturalHeight;
  canvas.width = Math.max(1, Math.round(width * scale));
  canvas.height = Math.max(1, Math.round(height * scale));
  context.drawImage(currentImage, x, y, width, height, 0, 0, canvas.width, canvas.height);
  status.textContent = `Download size: ${canvas.width} × ${canvas.height} px.`;
}

async function loadFlyer(url) {
  const requestId = ++loadId;
  const image = new Image();
  save.disabled = true;
  status.textContent = "Loading image…";
  image.src = url;
  try {
    await image.decode();
    if (requestId !== loadId) return;
    currentImage = image;
    horizontal.value = "50";
    vertical.value = "50";
    drawCrop();
  } catch {
    if (requestId === loadId) status.textContent = "Could not open that image. Try a PNG, JPEG, or WebP.";
  } finally {
    if (url.startsWith("blob:")) URL.revokeObjectURL(url);
    if (requestId === loadId) save.disabled = !currentImage;
  }
}

for (const control of [ratio, horizontal, vertical]) {
  control.addEventListener("input", drawCrop);
}

file.addEventListener("change", () => {
  if (file.files[0]) loadFlyer(URL.createObjectURL(file.files[0]));
});

document.getElementById("resetCrop").addEventListener("click", () => {
  file.value = "";
  ratio.value = "1";
  loadFlyer("original.png");
});

save.addEventListener("click", () => {
  canvas.toBlob((blob) => {
    if (!blob) {
      status.textContent = "Could not create the PNG. Try another image.";
      return;
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "flyerfix-crop.png";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, "image/png");
});

loadFlyer("original.png");
