const jobDescription = document.querySelector("#job-description");
const fileInput = document.querySelector("#resume-files");
const dropzone = document.querySelector("#dropzone");
const fileList = document.querySelector("#file-list");
const analyzeButton = document.querySelector("#analyze-button");
const notice = document.querySelector("#notice");
const resultsSection = document.querySelector("#results");
const resultsBody = document.querySelector("#results-body");
const MAX_FILES = 25;
const MAX_FILE_BYTES = 10 * 1024 * 1024;
let selectedFiles = [];
let currentResults = [];

jobDescription.addEventListener("input", () => {
  document.querySelector("#char-count").textContent =
    `${jobDescription.value.length.toLocaleString()} / 12,000`;
});

function addFiles(files) {
  const next = [...selectedFiles];
  const messages = [];
  for (const file of files) {
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      messages.push(`${file.name}: choose a PDF or DOCX file.`);
    } else if (file.size > MAX_FILE_BYTES) {
      messages.push(`${file.name}: file is larger than 10 MB.`);
    } else if (next.some((existing) => existing.name === file.name && existing.size === file.size)) {
      continue;
    } else if (next.length >= MAX_FILES) {
      messages.push(`Only ${MAX_FILES} resumes can be analyzed at once.`);
      break;
    } else {
      next.push(file);
    }
  }
  selectedFiles = next;
  renderFileList();
  if (messages.length) showNotice(messages.join(" "), "error");
}

function renderFileList() {
  fileList.replaceChildren();
  selectedFiles.forEach((file, index) => {
    const item = document.createElement("li");
    item.className = "file-item";
    const type = document.createElement("span");
    type.className = "file-type";
    type.textContent = file.name.split(".").pop().toUpperCase();
    const name = document.createElement("span");
    name.textContent = file.name;
    const size = document.createElement("span");
    size.className = "file-size";
    size.textContent = `${(file.size / 1024).toFixed(0)} KB`;
    const remove = document.createElement("button");
    remove.className = "remove-file";
    remove.type = "button";
    remove.setAttribute("aria-label", `Remove ${file.name}`);
    remove.textContent = "×";
    remove.addEventListener("click", () => {
      selectedFiles = selectedFiles.filter((_, fileIndex) => fileIndex !== index);
      renderFileList();
    });
    item.append(type, name, size, remove);
    fileList.append(item);
  });
  fileInput.value = "";
}

function showNotice(message, kind) {
  notice.textContent = message;
  notice.className = `notice ${kind}`;
  notice.hidden = false;
}

function renderResults(data) {
  currentResults = data.results;
  const analyzed = currentResults.filter((result) => result.status === "analyzed");
  const top = analyzed[0];
  document.querySelector("#stat-reviewed").textContent = data.summary.analyzed;
  document.querySelector("#stat-average").textContent = `${data.summary.average_score}%`;
  document.querySelector("#stat-top").textContent = top ? `${top.score}%` : "—";
  document.querySelector("#stat-top-name").textContent = top?.filename || "No successful matches";
  document.querySelector("#result-caption").textContent =
    `${data.summary.analyzed} analyzed · ${data.summary.errors} with errors · ranked by relevance`;
  const detected = document.querySelector("#detected-skills");
  detected.replaceChildren();
  if (data.summary.job_skills.length) {
    const label = document.createElement("span");
    label.className = "field-label";
    label.textContent = "Detected role skills";
    detected.append(label);
    data.summary.job_skills.forEach((skill) => {
      const chip = document.createElement("span");
      chip.className = "skill-chip";
      chip.textContent = skill;
      detected.append(chip);
    });
    detected.hidden = false;
  } else {
    detected.hidden = true;
  }

  resultsBody.replaceChildren();
  analyzed.forEach((result, index) => resultsBody.append(createCandidateRow(result, index)));
  currentResults.filter((result) => result.status !== "analyzed")
    .forEach((result) => resultsBody.append(createErrorRow(result)));
  document.querySelector("#empty-results").hidden = analyzed.length > 0;
  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function createCandidateRow(result, index) {
  const row = document.createElement("tr");
  const rank = document.createElement("td");
  rank.className = "rank-cell";
  rank.textContent = `#${index + 1}`;

  const candidate = document.createElement("td");
  const candidateName = document.createElement("div");
  candidateName.className = "candidate-name";
  const icon = document.createElement("span");
  icon.className = "candidate-icon";
  icon.textContent = result.filename.split(".").pop();
  const filename = document.createElement("span");
  filename.textContent = result.filename;
  candidateName.append(icon, filename);
  candidate.append(candidateName);

  const score = document.createElement("td");
  score.className = "score-cell";
  const scoreLabel = document.createElement("div");
  scoreLabel.className = "score-value";
  const percent = document.createElement("span");
  percent.textContent = `${result.score}%`;
  const label = document.createElement("span");
  label.textContent = result.score >= 75 ? "Strong" : result.score >= 45 ? "Good" : "Partial";
  scoreLabel.append(percent, label);
  const track = document.createElement("div");
  track.className = "score-track";
  const fill = document.createElement("div");
  fill.className = `score-fill${result.score >= 75 ? " high" : result.score < 45 ? " low" : ""}`;
  fill.style.width = `${Math.min(100, Math.max(0, result.score))}%`;
  track.append(fill);
  score.append(scoreLabel, track);

  const skillMatch = createMetricCell(result.skill_match);
  const keywordMatch = createMetricCell(result.keyword_match);
  const matched = document.createElement("td");
  const skills = document.createElement("div");
  skills.className = "matched-list";
  const visibleSkills = result.matched_skills.slice(0, 3);
  (visibleSkills.length ? visibleSkills : ["No skill overlap"]).forEach((skill) => {
    const chip = document.createElement("span");
    chip.className = "skill-chip";
    chip.textContent = skill;
    skills.append(chip);
  });
  result.missing_skills.slice(0, 2).forEach((skill) => {
    const chip = document.createElement("span");
    chip.className = "skill-chip missing";
    chip.textContent = `Missing: ${skill}`;
    skills.append(chip);
  });
  if (result.matched_skills.length > 3) {
    const more = document.createElement("span");
    more.className = "metric-pill";
    more.textContent = `+${result.matched_skills.length - 3}`;
    skills.append(more);
  }
  if (result.missing_skills.length > 2) {
    const more = document.createElement("span");
    more.className = "metric-pill";
    more.textContent = `+${result.missing_skills.length - 2} gaps`;
    skills.append(more);
  }
  matched.append(skills);
  row.append(rank, candidate, score, skillMatch, keywordMatch, matched);
  return row;
}

function createMetricCell(value) {
  const cell = document.createElement("td");
  const pill = document.createElement("span");
  pill.className = "metric-pill";
  pill.textContent = `${value}%`;
  cell.append(pill);
  return cell;
}

function createErrorRow(result) {
  const row = document.createElement("tr");
  row.className = "error-row";
  const candidate = document.createElement("td");
  candidate.colSpan = 2;
  candidate.textContent = result.filename;
  const message = document.createElement("td");
  message.colSpan = 4;
  message.textContent = result.error || "Could not analyze this file.";
  row.append(candidate, message);
  return row;
}

fileInput.addEventListener("change", () => addFiles(fileInput.files));
dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragging");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragging");
  addFiles(event.dataTransfer.files);
});

analyzeButton.addEventListener("click", async () => {
  if (!jobDescription.value.trim()) {
    showNotice("Add a job description before analyzing resumes.", "error");
    jobDescription.focus();
    return;
  }
  if (!selectedFiles.length) {
    showNotice("Upload at least one PDF or DOCX resume.", "error");
    return;
  }
  const form = new FormData();
  form.append("job_description", jobDescription.value);
  selectedFiles.forEach((file) => form.append("files", file));
  analyzeButton.disabled = true;
  analyzeButton.innerHTML = '<span class="button-spark">✳</span> Analyzing resumes…';
  notice.hidden = true;
  try {
    const response = await fetch("/api/analyze", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Resume analysis failed.");
    renderResults(data);
    showNotice(`Analysis complete. ${data.summary.analyzed} resume(s) scored.`, "success");
  } catch (error) {
    showNotice(error.message || "Could not connect to the screening service.", "error");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.innerHTML = '<span class="button-spark">✳</span> Analyze resumes <span class="button-arrow">→</span>';
  }
});

document.querySelector("#export-button").addEventListener("click", async () => {
  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ results: currentResults }),
    });
    if (!response.ok) throw new Error("Could not export the results.");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "resume-results.csv";
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    showNotice(error.message || "Could not export the results.", "error");
  }
});
