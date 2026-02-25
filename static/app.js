/**
 * Multilingual Video Text Pipeline — Frontend Logic
 * Handles file upload, API interaction, and result rendering.
 */

(function () {
    'use strict';

    // --- DOM Elements ---
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const btnClear = document.getElementById('btn-clear');
    const btnProcess = document.getElementById('btn-process');
    const targetLang = document.getElementById('target-lang');
    const maxFrames = document.getElementById('max-frames');

    const statusSection = document.getElementById('status-section');
    const statusTitle = document.getElementById('status-title');
    const statusDetail = document.getElementById('status-detail');
    const progressFill = document.getElementById('progress-fill');

    const resultsSection = document.getElementById('results-section');
    const statFrames = document.getElementById('stat-frames');
    const statRegions = document.getElementById('stat-regions');
    const statLanguages = document.getElementById('stat-languages');
    const statTarget = document.getElementById('stat-target');
    const frameGallery = document.getElementById('frame-gallery');
    const resultsTbody = document.getElementById('results-tbody');

    const toggleAnnotated = document.getElementById('toggle-annotated');
    const toggleOriginal = document.getElementById('toggle-original');
    const btnDownloadJson = document.getElementById('btn-download-json');
    const btnNew = document.getElementById('btn-new');

    let selectedFile = null;
    let currentResults = null;
    let currentView = 'annotated';

    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

    // --- Language Display Map ---
    const LANG_NAMES = {
        eng: 'English',
        hin: 'Hindi',
        ben: 'Bengali',
        tam: 'Tamil',
        en: 'EN',
        hi: 'HI',
        bn: 'BN',
        ta: 'TA',
    };

    // --- Utility ---
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    // --- File Selection ---
    function handleFileSelect(file) {
        if (!file) return;

        // Client-side file size check
        if (file.size > MAX_FILE_SIZE) {
            alert(`File too large (${formatFileSize(file.size)}). Maximum size is 50 MB.`);
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);

        // Preview
        filePreview.innerHTML = '';
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.onload = () => URL.revokeObjectURL(img.src);
            filePreview.appendChild(img);
        } else if (file.type.startsWith('video/')) {
            const video = document.createElement('video');
            video.src = URL.createObjectURL(file);
            video.muted = true;
            video.autoplay = false;
            video.onloadeddata = () => URL.revokeObjectURL(video.src);
            filePreview.appendChild(video);
        } else {
            filePreview.textContent = '📁';
        }

        fileInfo.style.display = 'flex';
        btnProcess.disabled = false;
    }

    function clearFile() {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        btnProcess.disabled = true;
    }

    // --- Upload Zone Events ---
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    btnClear.addEventListener('click', clearFile);

    // --- Process ---
    btnProcess.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Show status
        statusSection.style.display = 'block';
        resultsSection.style.display = 'none';
        btnProcess.disabled = true;
        progressFill.style.width = '0%';

        const steps = [
            { pct: 10, title: 'Uploading...', detail: 'Sending file to server' },
            { pct: 30, title: 'Extracting Frames...', detail: 'Capturing frames from video' },
            { pct: 60, title: 'Running OCR...', detail: 'Detecting text with Tesseract' },
            { pct: 80, title: 'Translating...', detail: 'Translating detected text' },
            { pct: 90, title: 'Generating Annotations...', detail: 'Drawing bounding boxes and overlays' },
        ];

        // Simulate progress steps
        let stepIdx = 0;
        const progressInterval = setInterval(() => {
            if (stepIdx < steps.length) {
                const s = steps[stepIdx];
                progressFill.style.width = s.pct + '%';
                statusTitle.textContent = s.title;
                statusDetail.textContent = s.detail;
                stepIdx++;
            }
        }, 800);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const lang = targetLang.value;
            const frames = maxFrames.value;

            const response = await fetch(
                `/api/process?target_lang=${lang}&max_frames=${frames}`,
                { method: 'POST', body: formData }
            );

            clearInterval(progressInterval);

            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(err.detail || `Server error ${response.status}`);
            }

            const data = await response.json();
            currentResults = data;

            progressFill.style.width = '100%';
            statusTitle.textContent = 'Complete!';
            statusDetail.textContent = `Processed ${data.frames_processed} frames, found ${data.total_text_regions} text regions`;

            setTimeout(() => {
                statusSection.style.display = 'none';
                renderResults(data);
            }, 800);

        } catch (error) {
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            progressFill.style.background = 'var(--accent-red)';
            statusTitle.textContent = 'Error';
            statusDetail.textContent = error.message;
            btnProcess.disabled = false;

            setTimeout(() => {
                progressFill.style.background = '';
            }, 3000);
        }
    });

    // --- Render Results ---
    function renderResults(data) {
        resultsSection.style.display = 'block';

        // Stats
        statFrames.textContent = data.frames_processed;
        statRegions.textContent = data.total_text_regions;
        statLanguages.textContent = data.languages_detected
            .map((l) => LANG_NAMES[l] || l)
            .join(', ') || '-';
        statTarget.textContent = (LANG_NAMES[data.target_language] || data.target_language).toUpperCase();

        // Frame gallery
        renderFrameGallery(data.frames, currentView);

        // Table
        renderTable(data.frames);

        btnProcess.disabled = false;

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function renderFrameGallery(frames, view) {
        frameGallery.innerHTML = '';
        frames.forEach((frame, idx) => {
            const card = document.createElement('div');
            card.className = 'frame-card';

            const imgSrc =
                view === 'annotated'
                    ? `data:image/jpeg;base64,${frame.annotated_frame}`
                    : `data:image/jpeg;base64,${frame.original_frame}`;

            card.innerHTML = `
                <img src="${imgSrc}" alt="Frame ${frame.frame_number}" loading="lazy">
                <div class="frame-card-footer">
                    <span class="frame-label">Frame #${frame.frame_number}</span>
                    <span class="frame-count">${frame.detections.length} region${frame.detections.length !== 1 ? 's' : ''}</span>
                </div>
            `;
            frameGallery.appendChild(card);
        });
    }

    function renderTable(frames) {
        resultsTbody.innerHTML = '';
        frames.forEach((frame) => {
            frame.detections.forEach((det) => {
                const tr = document.createElement('tr');
                const confClass =
                    det.confidence >= 70 ? 'confidence-high' :
                        det.confidence >= 40 ? 'confidence-mid' : 'confidence-low';

                tr.innerHTML = `
                    <td>#${frame.frame_number}</td>
                    <td>${escapeHtml(det.text)}</td>
                    <td><span class="lang-badge lang-${det.language}">${LANG_NAMES[det.language] || det.language}</span></td>
                    <td>${escapeHtml(det.translated_text || det.text)}</td>
                    <td>
                        <div class="confidence-bar">
                            <div class="confidence-fill">
                                <div class="confidence-fill-inner ${confClass}" style="width:${det.confidence}%"></div>
                            </div>
                            <span style="font-size:0.78rem;color:var(--text-muted)">${det.confidence}%</span>
                        </div>
                    </td>
                `;
                resultsTbody.appendChild(tr);
            });
        });

        if (resultsTbody.children.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td colspan="5" style="text-align:center;color:var(--text-muted);padding:24px;">No text detected in the processed frames</td>';
            resultsTbody.appendChild(tr);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // --- View Toggle ---
    toggleAnnotated.addEventListener('click', () => {
        currentView = 'annotated';
        toggleAnnotated.classList.add('active');
        toggleOriginal.classList.remove('active');
        if (currentResults) renderFrameGallery(currentResults.frames, 'annotated');
    });

    toggleOriginal.addEventListener('click', () => {
        currentView = 'original';
        toggleOriginal.classList.add('active');
        toggleAnnotated.classList.remove('active');
        if (currentResults) renderFrameGallery(currentResults.frames, 'original');
    });

    // --- Download JSON ---
    btnDownloadJson.addEventListener('click', () => {
        if (!currentResults) return;

        // Strip base64 data for cleaner export
        const exportData = {
            ...currentResults,
            frames: currentResults.frames.map((f) => ({
                frame_number: f.frame_number,
                detections: f.detections,
            })),
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pipeline_results_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // --- New Upload ---
    btnNew.addEventListener('click', () => {
        clearFile();
        resultsSection.style.display = 'none';
        statusSection.style.display = 'none';
        currentResults = null;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
