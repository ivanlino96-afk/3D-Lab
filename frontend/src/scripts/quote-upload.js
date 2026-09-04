const form = document.querySelector("#quote-form");
const fileInput = document.querySelector("#stl-files");
const buildPlate = document.querySelector("#build-plate");
const uploadList = document.querySelector("#upload-list");
const uploadError = document.querySelector("#upload-error");
const submitButton = document.querySelector("#submit-quote");
const sessionToken = document.querySelector("#submission-token")?.value;
const fileCount = document.querySelector("#file-count");
const totalSize = document.querySelector("#total-size");
const progressBar = document.querySelector("#quote-progress");
const progressLabel = document.querySelector("#quote-progress-label");
const progressValue = document.querySelector("#quote-progress-value");
const reviewContact = document.querySelector("#review-contact");
const reviewFiles = document.querySelector("#review-files");
const reviewContext = document.querySelector("#review-context");
const MAX_FILES = 20;
const MAX_BYTES = 500 * 1024 * 1024;
let submitting = false;

function activeRows() {
  return [...(uploadList?.querySelectorAll("li") ?? [])];
}

function refreshSummary() {
  const rows = activeRows();
  const bytes = rows.reduce((sum, row) => sum + Number(row.dataset.size || 0), 0);
  const valid = rows.filter((row) => row.dataset.status === "valid").length;
  const pending = rows.some((row) => row.dataset.status === "pending");
  if (fileCount) fileCount.textContent = `${rows.length} de ${MAX_FILES} archivos`;
  if (totalSize) totalSize.textContent = `${(bytes / 1024 / 1024).toFixed(1)} MB de 500 MB`;
  if (submitButton) submitButton.disabled = valid === 0 || pending || submitting;
  refreshProgress(valid, bytes);
  return { count: rows.length, bytes };
}

function refreshProgress(validFiles = 0, bytes = 0) {
  if (!form) return;
  const name = form.elements.name?.value.trim() || "";
  const email = form.elements.email?.value.trim() || "";
  const phone = form.elements.phone?.value.trim() || "";
  const comments = form.elements.comments?.value.trim() || "";
  const contactComplete = [form.elements.name, form.elements.email, form.elements.phone]
    .every((field) => field?.value.trim() && field.checkValidity());
  const step = !contactComplete ? 1 : validFiles === 0 ? 2 : 3;
  const labels = ["Datos", "Archivos", "Contexto"];
  document.querySelectorAll(".quote-steps li").forEach((item) => {
    const itemStep = Number(item.dataset.step);
    item.classList.toggle("is-current", itemStep === step);
    item.classList.toggle("is-complete", itemStep < step || (step === 3 && validFiles > 0));
  });
  if (progressBar) progressBar.value = step;
  if (progressLabel) progressLabel.textContent = `Paso ${step} de 3 · ${labels[step - 1]}`;
  if (progressValue) progressValue.textContent = `${Math.round((step / 3) * 100)}%`;
  if (reviewContact) reviewContact.textContent = contactComplete ? `${name} · ${email} · ${phone}` : "Completa tus datos";
  if (reviewFiles) reviewFiles.textContent = validFiles ? `${validFiles} STL válido${validFiles === 1 ? "" : "s"} · ${(bytes / 1024 / 1024).toFixed(1)} MB` : "Ningún STL válido";
  if (reviewContext) reviewContext.textContent = comments ? (comments.length > 90 ? `${comments.slice(0, 90)}…` : comments) : "Sin comentarios adicionales";
}

function showUploadError(message) {
  if (!uploadError) return;
  uploadError.textContent = message;
  uploadError.hidden = !message;
}

function createRow(file) {
  const row = document.createElement("li");
  row.dataset.size = String(file.size);
  row.dataset.status = "pending";
  const information = document.createElement("div");
  const name = document.createElement("strong");
  name.textContent = file.name;
  const status = document.createElement("small");
  status.textContent = "Preparando carga…";
  const progress = document.createElement("span");
  progress.className = "file-progress";
  progress.innerHTML = "<i></i>";
  information.append(name, status, progress);
  const action = document.createElement("button");
  action.type = "button";
  action.className = "remove-file";
  action.textContent = "Retirar";
  action.disabled = true;
  row.append(information, action);
  uploadList?.append(row);
  return { row, status, progress: progress.querySelector("i"), action };
}

function uploadFile(file, existingRow = null) {
  if (!sessionToken) return;
  const parts = existingRow ?? createRow(file);
  parts.row.dataset.status = "pending";
  parts.status.textContent = "Cargando 0 %";
  parts.action.disabled = true;
  refreshSummary();
  const request = new XMLHttpRequest();
  request.open("POST", `/cotizaciones/cargas/${encodeURIComponent(sessionToken)}`);
  request.upload.addEventListener("progress", (event) => {
    if (!event.lengthComputable) return;
    const percentage = Math.round((event.loaded / event.total) * 100);
    parts.status.textContent = `Cargando ${percentage} %`;
    if (parts.progress) parts.progress.style.width = `${percentage}%`;
  });
  request.addEventListener("load", () => {
    const payload = JSON.parse(request.responseText || "{}");
    if (request.status >= 200 && request.status < 300) {
      parts.row.dataset.id = payload.id;
      parts.row.dataset.size = String(payload.size);
      parts.row.dataset.status = payload.status;
      parts.status.textContent = payload.message;
      parts.action.disabled = false;
      parts.action.textContent = "Retirar";
      parts.action.className = "remove-file";
      parts.action.onclick = () => removeFile(parts.row);
      parts.row.querySelector(".remove-interrupted")?.remove();
    } else {
      markInterrupted(parts, file, payload.message || "La carga no pudo completarse.");
    }
    refreshSummary();
  });
  request.addEventListener("error", () => {
    markInterrupted(parts, file, "La conexión se interrumpió. Los demás archivos se conservan.");
    refreshSummary();
  });
  const body = new FormData();
  body.append("file", file);
  request.send(body);
}

function markInterrupted(parts, file, message) {
  parts.row.dataset.status = "error";
  parts.status.textContent = message;
  parts.action.disabled = false;
  parts.action.textContent = "Reintentar";
  parts.action.className = "retry-file";
  parts.action.onclick = () => uploadFile(file, parts);
  if (!parts.row.querySelector(".remove-interrupted")) {
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove-file remove-interrupted";
    remove.textContent = "Retirar";
    remove.addEventListener("click", () => removeFile(parts.row));
    parts.row.append(remove);
  }
}

async function removeFile(row) {
  const id = row.dataset.id;
  if (id) {
    const response = await fetch(`/cotizaciones/cargas/${encodeURIComponent(sessionToken)}/${id}`, { method: "DELETE" });
    if (!response.ok) {
      const payload = await response.json();
      showUploadError(payload.message || "No se pudo retirar el archivo. Intenta de nuevo.");
      return;
    }
  }
  row.remove();
  showUploadError("");
  refreshSummary();
}

function addFiles(files) {
  const summary = refreshSummary();
  let provisionalCount = summary.count;
  let provisionalBytes = summary.bytes;
  for (const file of files) {
    if (!file.name.toLowerCase().endsWith(".stl")) {
      showUploadError(`“${file.name}” no es un archivo STL.`);
      continue;
    }
    if (provisionalCount >= MAX_FILES) {
      showUploadError("Cada solicitud admite como máximo 20 archivos.");
      break;
    }
    if (provisionalBytes + file.size > MAX_BYTES) {
      showUploadError("El tamaño acumulado no puede superar 500 MB.");
      continue;
    }
    uploadFile(file);
    provisionalCount += 1;
    provisionalBytes += file.size;
  }
}

fileInput?.addEventListener("change", () => addFiles([...fileInput.files]));
form?.addEventListener("input", () => refreshSummary());
buildPlate?.addEventListener("dragover", (event) => { event.preventDefault(); buildPlate.classList.add("is-dragging"); });
buildPlate?.addEventListener("dragleave", () => buildPlate.classList.remove("is-dragging"));
buildPlate?.addEventListener("drop", (event) => {
  event.preventDefault();
  buildPlate.classList.remove("is-dragging");
  addFiles([...event.dataTransfer.files]);
});
form?.addEventListener("submit", (event) => {
  if (submitting || submitButton?.disabled) {
    event.preventDefault();
    return;
  }
  submitting = true;
  submitButton.disabled = true;
  submitButton.textContent = "Enviando solicitud…";
});

document.querySelectorAll(".upload-list .remove-file").forEach((button) => {
  button.addEventListener("click", () => removeFile(button.closest("li")));
});
refreshSummary();
