/* ======================================================
   AI CONSTRUCTION PPE DETECTION SYSTEM - FRONTEND JAVASCRIPT
   ====================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initNavigationTabs();
    setupFormHandlers();
    setupDragAndDrop();
});

// Smooth Scroll to Active Inspection Tab Upload/Controls Section
function scrollToActiveInspection() {
    const activeTab = document.querySelector('.content-tab.active');
    if (!activeTab) return;

    let target = null;
    const tabId = activeTab.getAttribute('id');

    if (tabId === 'tab-image') {
        target = document.getElementById('form-upload-image') || document.getElementById('image-dropzone');
    } else if (tabId === 'tab-video') {
        target = document.getElementById('form-upload-video') || document.getElementById('video-dropzone');
    } else if (tabId === 'tab-webcam') {
        target = activeTab.querySelector('.premium-card') || document.getElementById('webcam-index');
    } else if (tabId === 'tab-rtsp') {
        target = activeTab.querySelector('.premium-card') || document.getElementById('rtsp-url-input');
    }

    if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Sidebar Navigation Tab Switcher
function initNavigationTabs() {
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link[data-tab]');
    const tabs = document.querySelectorAll('.content-tab');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTabId = link.getAttribute('data-tab');

            navLinks.forEach(l => l.classList.remove('active'));
            tabs.forEach(t => t.classList.remove('active'));

            link.classList.add('active');
            const targetTab = document.getElementById(targetTabId);
            if (targetTab) {
                targetTab.classList.add('active');
            }
        });
    });
}

// Drag & Drop visual feedback handlers
function setupDragAndDrop() {
    const dropzones = [
        { zone: document.getElementById('image-dropzone'), input: document.getElementById('image-file-input'), handler: handleImageFileSelected },
        { zone: document.getElementById('video-dropzone'), input: document.getElementById('video-file-input'), handler: handleVideoFileSelected }
    ];

    dropzones.forEach(({ zone, input, handler }) => {
        if (!zone || !input) return;

        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('dragover');
            }, false);
        });

        zone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                input.files = files;
                if (typeof handler === 'function') handler(input);
            }
        }, false);
    });
}

// File Selection Handlers
function handleImageFileSelected(input) {
    const nameBadge = document.getElementById('image-file-name');
    if (input.files && input.files[0]) {
        nameBadge.textContent = 'Selected: ' + input.files[0].name;
        nameBadge.classList.remove('d-none');
    }
}

function handleVideoFileSelected(input) {
    const nameBadge = document.getElementById('video-file-name');
    if (input.files && input.files[0]) {
        nameBadge.textContent = 'Selected: ' + input.files[0].name;
        nameBadge.classList.remove('d-none');
    }
}

// Form Handlers
function setupFormHandlers() {
    // Image Upload Form
    const imgForm = document.getElementById('form-upload-image');
    if (imgForm) {
        imgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('image-file-input');
            if (!fileInput.files || !fileInput.files[0]) {
                alert('Please select an image file first.');
                return;
            }

            const formData = new FormData();
            formData.append('image', fileInput.files[0]);
            await runImageInspection(formData);
        });
    }

    // Video Upload Form
    const vidForm = document.getElementById('form-upload-video');
    if (vidForm) {
        vidForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('video-file-input');
            if (!fileInput.files || !fileInput.files[0]) {
                alert('Please select a video file first.');
                return;
            }

            const formData = new FormData();
            formData.append('video', fileInput.files[0]);
            await runVideoProcessing(formData);
        });
    }

    // PDF Report Form (Dashboard Page)
    const pdfForm = document.getElementById('form-generate-pdf');
    if (pdfForm) {
        pdfForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const titleInput = document.getElementById('pdf-report-title').value;

            try {
                const response = await fetch('/api/generate-pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: titleInput })
                });

                if (!response.ok) throw new Error('PDF generation failed');

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = 'Construction_PPE_Safety_Report.pdf';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (err) {
                alert('Failed to generate PDF report: ' + err.message);
            }
        });
    }
}

// Run Image Inspection Request
async function runImageInspection(formData) {
    const resultsContainer = document.getElementById('image-results-container');
    try {
        const response = await fetch('/api/inspect-image', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        // Render Images
        document.getElementById('img-original').src = data.original_url;
        document.getElementById('img-annotated').src = data.annotated_url;

        // Set Action Download Links
        document.getElementById('btn-download-image-asset').href = data.download_annotated_url;
        document.getElementById('btn-download-image-pdf').href = data.download_pdf_url;

        // Render KPI Cards
        renderKpiCards('image-kpi-grid', data.compliance);

        // Render Alerts
        renderAlertsFeed('image-alerts-container', data.alerts);

        // Render Worker Matrix Summary
        renderWorkerChecklist('image-workers-container', data.compliance.workers);

        resultsContainer.classList.remove('d-none');
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        alert('Inspection request failed: ' + err.message);
    }
}

// Run Video Processing Request
async function runVideoProcessing(formData) {
    const spinner = document.getElementById('video-processing-spinner');
    const resultsContainer = document.getElementById('video-results-container');

    spinner.classList.remove('d-none');
    resultsContainer.classList.add('d-none');

    try {
        const response = await fetch('/api/process-video', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        spinner.classList.add('d-none');

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        // Load Original & Annotated Playable Video Player Sources
        const playerOrig = document.getElementById('video-player-original');
        const playerAnn = document.getElementById('video-player-annotated');

        if (playerOrig) playerOrig.src = data.original_video_url;
        if (playerAnn) playerAnn.src = data.annotated_video_url;

        // Set Download Action Links
        document.getElementById('btn-download-video-asset').href = data.download_video_url;
        document.getElementById('btn-download-video-pdf').href = data.download_pdf_url;

        // Render KPI Cards & Alerts
        renderKpiCards('video-kpi-grid', data.stats);
        renderAlertsFeed('video-alerts-container', data.alerts);

        resultsContainer.classList.remove('d-none');
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        spinner.classList.add('d-none');
        alert('Video processing request failed: ' + err.message);
    }
}

// Stream Handlers
function startWebcamStream() {
    const indexInput = document.getElementById('webcam-index');
    const index = indexInput ? indexInput.value : '0';
    const img = document.getElementById('webcam-stream-img');
    const placeholder = document.getElementById('webcam-placeholder');

    console.log(`[WEBCAM FRONTEND LOG] Requesting camera stream for device index: ${index}`);
    img.src = `/api/video-feed?source=${encodeURIComponent(index)}&t=${Date.now()}`;
    img.classList.remove('d-none');
    placeholder.classList.add('d-none');
}

function stopWebcamStream() {
    const img = document.getElementById('webcam-stream-img');
    const placeholder = document.getElementById('webcam-placeholder');

    img.src = '';
    img.classList.add('d-none');
    placeholder.classList.remove('d-none');
}

function startRtspStream() {
    const url = document.getElementById('rtsp-url-input').value;
    if (!url) {
        alert('Please enter a valid RTSP stream URL.');
        return;
    }
    const img = document.getElementById('rtsp-stream-img');
    const placeholder = document.getElementById('rtsp-placeholder');

    img.src = `/api/video-feed?source=${encodeURIComponent(url)}`;
    img.classList.remove('d-none');
    placeholder.classList.add('d-none');
}

function stopRtspStream() {
    const img = document.getElementById('rtsp-stream-img');
    const placeholder = document.getElementById('rtsp-placeholder');

    img.src = '';
    img.classList.add('d-none');
    placeholder.classList.remove('d-none');
}

// Capture Current Stream Frame & Generate PDF Report
async function captureStreamFrame(streamType) {
    const containerId = streamType === 'Webcam' ? 'webcam-capture-container' : 'rtsp-capture-container';
    const imgId = streamType === 'Webcam' ? 'webcam-captured-img' : 'rtsp-captured-img';
    const detailsId = streamType === 'Webcam' ? 'webcam-captured-details' : 'rtsp-captured-details';
    const btnImgId = streamType === 'Webcam' ? 'btn-download-webcam-image' : 'btn-download-rtsp-image';
    const btnPdfId = streamType === 'Webcam' ? 'btn-download-webcam-pdf' : 'btn-download-rtsp-pdf';

    try {
        const response = await fetch('/api/capture-frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stream_type: streamType })
        });
        const data = await response.json();

        if (data.error) {
            alert('Capture Error: ' + data.error);
            return;
        }

        // Set Images & Links
        document.getElementById(imgId).src = data.captured_image_url;
        document.getElementById(btnImgId).href = data.download_image_url;
        document.getElementById(btnPdfId).href = data.download_pdf_url;

        // Render Details Scorecard
        const comp = data.compliance;
        document.getElementById(detailsId).innerHTML = `
            <div class="p-3 bg-light border rounded-3 shadow-sm">
                <h6 class="text-navy fw-bold mb-2"><i class="fa-solid fa-camera-retro text-warning me-2"></i> Snapshot Captured (${streamType})</h6>
                <div class="row g-2 mb-2">
                    <div class="col-6"><span class="text-muted small d-block">Active Workers</span><strong class="fs-6 text-dark">${comp.total_workers}</strong></div>
                    <div class="col-6"><span class="text-muted small d-block">Safety Score</span><strong class="fs-6 text-success">${(comp.overall_safety_score ?? 0).toFixed(1)}%</strong></div>
                    <div class="col-6"><span class="text-muted small d-block">Helmet Rate</span><strong class="text-dark">${(comp.helmet_compliance_pct ?? 0).toFixed(1)}%</strong></div>
                    <div class="col-6"><span class="text-muted small d-block">Vest Rate</span><strong class="text-dark">${(comp.vest_compliance_pct ?? 0).toFixed(1)}%</strong></div>
                    <div class="col-6"><span class="text-muted small d-block">Gloves Rate</span><strong class="text-dark">${(comp.glove_compliance_pct ?? 0).toFixed(1)}%</strong></div>
                    <div class="col-6"><span class="text-muted small d-block">Boots Rate</span><strong class="text-dark">${(comp.boot_compliance_pct ?? 0).toFixed(1)}%</strong></div>
                </div>
                <div class="alert alert-success border-0 py-1 px-2 small fw-bold mb-0"><i class="fa-solid fa-circle-check me-1"></i> Snapshot PDF Audit Report Compiled & Ready!</div>
            </div>
        `;

        document.getElementById(containerId).classList.remove('d-none');
        document.getElementById(containerId).scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        alert('Frame capture failed: ' + err.message);
    }
}

// Load Dashboard Data (Analytics View)
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();

        // Render KPI Cards
        renderKpiCards('dashboard-kpi-cards', data.compliance);

        // Render Plotly Charts
        if (data.bar_chart) {
            const barObj = JSON.parse(data.bar_chart);
            if (barObj.layout) {
                barObj.layout.paper_bgcolor = 'rgba(0,0,0,0)';
                barObj.layout.plot_bgcolor = 'rgba(0,0,0,0)';
                barObj.layout.font = { family: 'Inter, sans-serif', color: '#0F172A' };
            }
            Plotly.newPlot('chart-bar', barObj.data, barObj.layout, { responsive: true, displayModeBar: false });
        }
        if (data.pie_chart) {
            const pieObj = JSON.parse(data.pie_chart);
            if (pieObj.layout) {
                pieObj.layout.paper_bgcolor = 'rgba(0,0,0,0)';
                pieObj.layout.plot_bgcolor = 'rgba(0,0,0,0)';
                pieObj.layout.font = { family: 'Inter, sans-serif', color: '#0F172A' };
            }
            Plotly.newPlot('chart-pie', pieObj.data, pieObj.layout, { responsive: true, displayModeBar: false });
        }

        // Render Worker Matrix Table
        renderWorkerMatrixTable('worker-matrix-tbody', data.compliance.workers);
    } catch (err) {
        console.error('Failed to load dashboard analytics:', err);
    }
}

// UI Render Helpers
function renderKpiCards(containerId, comp) {
    const container = document.getElementById(containerId);
    if (!container || !comp) return;

    function getTag(pct) {
        if (pct >= 85) return { bg: '#DCFCE7', col: '#16A34A', label: 'Optimal' };
        if (pct >= 60) return { bg: '#FEF3C7', col: '#D97706', label: 'Warning' };
        return { bg: '#FEE2E2', col: '#DC2626', label: 'Critical' };
    }

    const tH = getTag(comp.helmet_compliance_pct ?? 0);
    const tV = getTag(comp.vest_compliance_pct ?? 0);
    const tG = getTag(comp.glove_compliance_pct ?? 0);
    const tB = getTag(comp.boot_compliance_pct ?? 0);
    const tS = getTag(comp.overall_safety_score ?? 0);

    container.innerHTML = `
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon-wrapper" style="background:#DBEAFE; color:#1E3A8A;"><i class="fa-solid fa-users"></i></div>
                <span class="kpi-pill" style="background:#DBEAFE; color:#1E3A8A;">Live</span>
            </div>
            <div class="kpi-title">Workers</div>
            <div class="kpi-value">${comp.total_workers ?? 0}</div>
            <div class="kpi-subtext">Personnel On-Site</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon-wrapper" style="background:#FEF3C7; color:#D97706;"><i class="fa-solid fa-helmet-safety"></i></div>
                <span class="kpi-pill" style="background:${tH.bg}; color:${tH.col};">${tH.label}</span>
            </div>
            <div class="kpi-title">Helmet %</div>
            <div class="kpi-value" style="color:${tH.col};">${(comp.helmet_compliance_pct ?? 0).toFixed(1)}%</div>
            <div class="kpi-subtext">Head Protection</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon-wrapper" style="background:#DCFCE7; color:#16A34A;"><i class="fa-solid fa-vest"></i></div>
                <span class="kpi-pill" style="background:${tV.bg}; color:${tV.col};">${tV.label}</span>
            </div>
            <div class="kpi-title">Vest %</div>
            <div class="kpi-value" style="color:${tV.col};">${(comp.vest_compliance_pct ?? 0).toFixed(1)}%</div>
            <div class="kpi-subtext">High-Vis Vest</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon-wrapper" style="background:#E0F2FE; color:#0284C7;"><i class="fa-solid fa-mitten"></i></div>
                <span class="kpi-pill" style="background:${tG.bg}; color:${tG.col};">${tG.label}</span>
            </div>
            <div class="kpi-title">Gloves %</div>
            <div class="kpi-value" style="color:${tG.col};">${(comp.glove_compliance_pct ?? 0).toFixed(1)}%</div>
            <div class="kpi-subtext">Hand Protection</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon-wrapper" style="background:#F1F5F9; color:#475569;"><i class="fa-solid fa-shoe-prints"></i></div>
                <span class="kpi-pill" style="background:${tB.bg}; color:${tB.col};">${tB.label}</span>
            </div>
            <div class="kpi-title">Boots %</div>
            <div class="kpi-value" style="color:${tB.col};">${(comp.boot_compliance_pct ?? 0).toFixed(1)}%</div>
            <div class="kpi-subtext">Steel-Toe Boots</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon-wrapper" style="background:#DCFCE7; color:#16A34A;"><i class="fa-solid fa-shield-check"></i></div>
                <span class="kpi-pill" style="background:${tS.bg}; color:${tS.col};">${tS.label}</span>
            </div>
            <div class="kpi-title">Safety Score</div>
            <div class="kpi-value" style="color:${tS.col};">${(comp.overall_safety_score ?? 0).toFixed(1)}%</div>
            <div class="kpi-subtext">Overall Compliance Index</div>
        </div>
    `;
}

function renderAlertsFeed(containerId, alerts) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div class="alert alert-success border-0 rounded-3 mb-0"><i class="fa-solid fa-circle-check me-2"></i> All detected workers are fully compliant with mandatory safety equipment!</div>';
        return;
    }

    const nonCompliant = alerts.filter(a => a.severity !== 'SUCCESS');
    if (nonCompliant.length === 0) {
        container.innerHTML = '<div class="alert alert-success border-0 rounded-3 mb-0"><i class="fa-solid fa-circle-check me-2"></i> All detected workers are fully compliant with mandatory safety equipment!</div>';
        return;
    }

    let html = '';
    nonCompliant.forEach(alt => {
        const isCrit = alt.severity === 'CRITICAL';
        const cardClass = isCrit ? 'alert-card-critical' : 'alert-card-warning';
        const icon = isCrit ? '<i class="fa-solid fa-triangle-exclamation text-danger me-2"></i>' : '<i class="fa-solid fa-circle-exclamation text-warning me-2"></i>';
        const label = isCrit ? 'CRITICAL VIOLATION' : 'WARNING';
        const badgeBg = isCrit ? '#FEE2E2' : '#FEF3C7';
        const badgeCol = isCrit ? '#DC2626' : '#D97706';

        html += `
            <div class="alert-card ${cardClass}">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="fw-bold text-dark">${icon}${alt.title}</div>
                    <div>
                        <span class="badge" style="background:${badgeBg}; color:${badgeCol}; font-weight:700;">${label}</span>
                        <span class="text-muted small ms-2">${alt.timestamp}</span>
                    </div>
                </div>
                <div class="small text-secondary ms-4">${alt.message}</div>
            </div>
        `;
    });
    container.innerHTML = html;
}

function renderWorkerChecklist(containerId, workers) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!workers || workers.length === 0) {
        container.innerHTML = '<div class="text-muted p-3">No worker personnel detected in image input.</div>';
        return;
    }

    let html = '';
    workers.forEach(w => {
        const isComp = w.is_fully_compliant;
        const color = isComp ? '#16A34A' : '#DC2626';
        const statusText = isComp ? '🟢 COMPLIANT' : `🔴 NON-COMPLIANT (${w.missing_items.length} missing)`;
        const badgeBg = isComp ? '#DCFCE7' : '#FEE2E2';

        html += `
            <div class="worker-card">
                <div>
                    <span class="fw-bold text-dark d-block">Worker #${w.worker_id}</span>
                    <span class="small fw-bold" style="color:${color};">${statusText}</span>
                </div>
                <div>
                    <span class="badge" style="background:${badgeBg}; color:${color}; font-size:0.82rem; font-weight:700;">Score: ${w.score}%</span>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

function renderWorkerMatrixTable(tbodyId, workers) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;

    if (!workers || workers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No active worker inspection records loaded.</td></tr>';
        return;
    }

    let html = '';
    workers.forEach(w => {
        const isComp = w.is_fully_compliant;
        const statusBadge = isComp
            ? '<span class="badge" style="background:#DCFCE7; color:#16A34A; font-weight:700;">🟢 COMPLIANT</span>'
            : `<span class="badge" style="background:#FEE2E2; color:#DC2626; font-weight:700;">🔴 NON-COMPLIANT (${w.missing_items.length} missing)</span>`;

        html += `
            <tr>
                <td class="fw-bold text-navy">Worker #${w.worker_id}</td>
                <td>${w.detected_items.helmet ? '<span class="text-success fw-bold">✅ Worn</span>' : '<span class="text-danger fw-bold">❌ Missing</span>'}</td>
                <td>${w.detected_items.vest ? '<span class="text-success fw-bold">✅ Worn</span>' : '<span class="text-danger fw-bold">❌ Missing</span>'}</td>
                <td>${w.detected_items.glove ? '<span class="text-success fw-bold">✅ Worn</span>' : '<span class="text-danger fw-bold">❌ Missing</span>'}</td>
                <td>${w.detected_items.boots ? '<span class="text-success fw-bold">✅ Worn</span>' : '<span class="text-danger fw-bold">❌ Missing</span>'}</td>
                <td>${statusBadge}</td>
                <td class="fw-bold fs-6">${w.score}%</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}
