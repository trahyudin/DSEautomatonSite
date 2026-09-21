// AutoPost Matrix - Frontend JavaScript SPA Controller (Phase 2 & Defensiveness)

document.addEventListener('DOMContentLoaded', () => {
    // Global State
    let trackerData = { headers: [], rows: [], campaigns: [], stats: {} };
    let inspectorData = { total_sites: 0, tier_counts: {}, results: [] };
    let selectedFilepath = null;
    let selectedFilename = null;
    let activeJobId = null;
    let jobPollInterval = null;

    let selectedCategoryFilter = "ALL";
    let selectedTierFilter = "ALL";

    // Elements
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const currentTabTitle = document.getElementById('current-tab-title');
    const currentTabDesc = document.getElementById('current-tab-desc');
    const btnReloadExcel = document.getElementById('btn-reload-excel');

    // Tab Titles Mapping
    const tabMeta = {
        'tab-dashboard': { title: 'Dashboard Overview', desc: 'Monitor platform distribution, difficulty tiers, and system health.' },
        'tab-inspector': { title: 'Site Capability & Tier Inspector', desc: 'Audit automation capabilities and difficulty classification across all 227 sites.' },
        'tab-wizard': { title: 'Bulk Upload Wizard', desc: 'Configure content payload and launch multi-platform automated upload jobs.' },
        'tab-tracker': { title: 'Excel Tracker Grid', desc: 'View and manage campaign posting links directly synced with tracker-posting.xlsx.' },
        'tab-verifier': { title: 'Link Health Audit', desc: 'Perform multi-threaded HTTP status verification for posted URLs.' },
        'tab-settings': { title: 'Platform Settings', desc: 'Manage credentials and integration API keys.' }
    };

    // ------------------------------------------------------------------------
    // 1. Navigation & Tab Switching
    // ------------------------------------------------------------------------
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            
            navItems.forEach(n => n.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            const targetPane = document.getElementById(targetTab);
            if (targetPane) targetPane.classList.add('active');

            if (tabMeta[targetTab]) {
                if (currentTabTitle) currentTabTitle.innerText = tabMeta[targetTab].title;
                if (currentTabDesc) currentTabDesc.innerText = tabMeta[targetTab].desc;
            }
        });
    });

    const btnQuickUpload = document.getElementById('btn-quick-upload');
    if (btnQuickUpload) {
        btnQuickUpload.addEventListener('click', () => {
            const wizNav = document.querySelector('[data-tab="tab-wizard"]');
            if (wizNav) wizNav.click();
        });
    }

    // ------------------------------------------------------------------------
    // 2. Fetch & Render Tracker & Inspector Data
    // ------------------------------------------------------------------------
    async function loadTrackerData() {
        try {
            const res = await fetch('/api/tracker');
            const result = await res.json();
            if (result.status === 'success') {
                trackerData = result.data;
                renderDashboard();
                renderWizardSiteChecklist();
                renderWizardCampaignSelect();
                renderExcelTable();
                renderAuditCampaignSelect();
            }
        } catch (err) {
            console.error("Failed to load tracker data:", err);
        }
    }

    async function loadInspectorData() {
        try {
            const res = await fetch('/api/inspector/data');
            const result = await res.json();
            if (result.status === 'success') {
                inspectorData = result.data;
                renderInspectorView();
                renderWizardSiteChecklist();
                renderExcelTable();
            }
        } catch (err) {
            console.error("Failed to load inspector data:", err);
        }
    }

    let knowledgeData = {};
    async function loadKnowledgeData() {
        try {
            const res = await fetch('/api/learn/knowledge');
            knowledgeData = await res.json();
            renderKnowledgeTable();
        } catch (err) {
            console.error("Failed to load knowledge data:", err);
        }
    }

    if (btnReloadExcel) {
        btnReloadExcel.addEventListener('click', () => {
            btnReloadExcel.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Syncing...';
            Promise.all([loadTrackerData(), loadInspectorData(), loadKnowledgeData()]).then(() => {
                setTimeout(() => {
                    btnReloadExcel.innerHTML = '<i class="fa-solid fa-rotate"></i> Sync Excel Data';
                }, 600);
            });
        });
    }

    // ------------------------------------------------------------------------
    // 3. Render Dashboard View
    // ------------------------------------------------------------------------
    function renderDashboard() {
        const stats = trackerData.stats || {};
        const elTotalSites = document.getElementById('stat-total-sites');
        const elTotalCampaigns = document.getElementById('stat-total-campaigns');
        const elTotalPosts = document.getElementById('stat-total-posts');

        if (elTotalSites) elTotalSites.innerText = stats.total_sites || 227;
        if (elTotalCampaigns) elTotalCampaigns.innerText = stats.total_campaigns || 0;

        let totalPosts = 0;
        if (stats.total_posts_per_campaign) {
            totalPosts = Object.values(stats.total_posts_per_campaign).reduce((a, b) => a + b, 0);
        }
        if (elTotalPosts) elTotalPosts.innerText = totalPosts;

        // Categories Breakdown Grid
        const categoriesGrid = document.getElementById('categories-grid');
        if (categoriesGrid) {
            categoriesGrid.innerHTML = '';
            const catCounts = stats.category_counts || {};
            for (const [catName, count] of Object.entries(catCounts)) {
                const box = document.createElement('div');
                box.className = 'category-box';
                box.innerHTML = `
                    <h4>${catName}</h4>
                    <div class="num">${count}</div>
                    <span class="stat-sub text-muted">Platforms available</span>
                `;
                categoriesGrid.appendChild(box);
            }
        }

        // Campaign Progress Grid
        const campaignsGrid = document.getElementById('campaigns-grid');
        if (campaignsGrid) {
            campaignsGrid.innerHTML = '';
            const campaignPosts = stats.total_posts_per_campaign || {};
            for (const [cName, count] of Object.entries(campaignPosts)) {
                const box = document.createElement('div');
                box.className = 'campaign-box';
                box.innerHTML = `
                    <h4>${cName}</h4>
                    <div class="num text-green">${count} / ${stats.total_sites}</div>
                    <span class="stat-sub text-muted">Posted links active</span>
                `;
                campaignsGrid.appendChild(box);
            }
        }
    }

    // ------------------------------------------------------------------------
    // 4. Render Inspector View & Tier Badges
    // ------------------------------------------------------------------------
    function renderInspectorView() {
        const tierCounts = inspectorData.tier_counts || {};
        const easyCount = tierCounts.Mudah || 0;
        const medCount = tierCounts.Sedang || 0;
        const hardCount = tierCounts.Sulit || 0;

        const elEasy = document.getElementById('stat-tier-easy');
        const elMed = document.getElementById('stat-tier-medium');
        const elHard = document.getElementById('stat-tier-hard');

        if (elEasy) elEasy.innerText = easyCount;
        if (elMed) elMed.innerText = medCount;
        if (elHard) elHard.innerText = hardCount;

        const bEasy = document.getElementById('badge-tier-easy');
        const bMed = document.getElementById('badge-tier-medium');
        const bHard = document.getElementById('badge-tier-hard');

        if (bEasy) bEasy.innerText = `🟢 Mudah: ${easyCount}`;
        if (bMed) bMed.innerText = `🟡 Sedang: ${medCount}`;
        if (bHard) bHard.innerText = `🔴 Sulit: ${hardCount}`;

        const tbody = document.getElementById('inspector-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        const results = inspectorData.results || [];
        results.forEach(r => {
            const tr = document.createElement('tr');
            let tierClass = 'badge-mudah';
            let tierDot = '🟢';
            if (r.tier === 'Sedang') { tierClass = 'badge-sedang'; tierDot = '🟡'; }
            if (r.tier === 'Sulit') { tierClass = 'badge-sulit'; tierDot = '🔴'; }

            const httpBadgeClass = r.accessible ? 'badge-success' : 'badge-danger';

            tr.innerHTML = `
                <td><strong>${r.situs}</strong></td>
                <td><span class="btn-chip">${r.category}</span></td>
                <td><span class="badge ${tierClass}">${tierDot} ${r.tier}</span></td>
                <td><code>${r.upload_method}</code></td>
                <td><span class="badge ${httpBadgeClass}">${r.status_code || 'Error'}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderKnowledgeTable() {
        const tbody = document.getElementById('knowledge-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        const sites = Object.keys(knowledgeData);
        if (sites.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No knowledge mapped yet. Run Phase A.</td></tr>';
            return;
        }

        sites.forEach(site => {
            const data = knowledgeData[site];
            const steps = data.steps || [];
            let mappedStepsHtml = '';
            let confidenceHtml = '';
            
            steps.forEach(step => {
                if (step.found) {
                    mappedStepsHtml += `<div><span class="badge badge-success">ID: ${step.target_identifier}</span> (${step.action_type})</div>`;
                    confidenceHtml += `<div>${(step.confidence * 100).toFixed(0)}%</div>`;
                } else {
                    mappedStepsHtml += `<div><span class="badge badge-danger">Not Found</span></div>`;
                    confidenceHtml += `<div>-</div>`;
                }
            });

            if (steps.length === 0) {
                mappedStepsHtml = '<span class="badge badge-danger">No steps</span>';
                confidenceHtml = '-';
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${site}</strong></td>
                <td><code>${data.editor_type || 'Unknown'}</code></td>
                <td>${mappedStepsHtml}</td>
                <td>${confidenceHtml}</td>
                <td><span class="badge badge-success">Mapped</span></td>
            `;
            tbody.appendChild(tr);
        });
        
        // Unhide the container if it's hidden
        const container = document.getElementById('knowledge-container');
        if (container) {
            container.classList.remove('hidden');
        }
    }

    const btnRunInspector = document.getElementById('btn-run-inspector');
    if (btnRunInspector) {
        btnRunInspector.addEventListener('click', async () => {
            btnRunInspector.disabled = true;
            btnRunInspector.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Auditing 227 Sites...';

            try {
                const res = await fetch('/api/inspector/run', { method: 'POST' });
                const result = await res.json();
                if (result.status === 'success') {
                    pollInspectorStatus(result.task_id);
                }
            } catch (err) {
                alert("Inspector audit failed: " + err.message);
                btnRunInspector.disabled = false;
                btnRunInspector.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Run Capability Audit (227 Sites)';
            }
        });
    }

    function pollInspectorStatus(taskId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/inspector/status/${taskId}`);
                const task = await res.json();

                if (task.status === 'COMPLETED') {
                    clearInterval(interval);
                    if (btnRunInspector) {
                        btnRunInspector.disabled = false;
                        btnRunInspector.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Run Capability Audit (227 Sites)';
                    }

                    inspectorData = task.result;
                    renderInspectorView();
                    renderWizardSiteChecklist();
                    renderExcelTable();
                }
            } catch (err) {
                console.error("Inspector poll error:", err);
            }
        }, 2000);
    }

    // ------------------------------------------------------------------------
    // 4b. AI Profiler / Learning Phase Logic (2-Step)
    // ------------------------------------------------------------------------
    let learningPollInterval = null;
    const btnRunHints = document.getElementById('btn-run-hints');
    const btnRunLearning = document.getElementById('btn-run-learning');
    const logsContainer = document.getElementById('learning-logs-container');
    const logsOutput = document.getElementById('learning-logs-output');
    const progressBar = document.getElementById('learning-progress-bar');
    const knowledgeContainer = document.getElementById('knowledge-container');

    if (btnRunHints) {
        btnRunHints.addEventListener('click', async () => {
            if (!confirm("Start Phase A: Generate Hints via Web Search?")) return;
            
            btnRunHints.disabled = true;
            btnRunHints.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
            logsContainer.classList.remove('hidden');
            if (knowledgeContainer) knowledgeContainer.classList.add('hidden');
            logsOutput.innerText = "Initializing Phase A (Web Search)...\n";

            try {
                const allSites = Object.values(trackerData.rows || {}).map(r => r.situs);
                const res = await fetch('/api/learn/hints/start', { 
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ target_sites: allSites })
                });
                const result = await res.json();
                if (result.status === 'success') {
                    pollLearningStatus(result.job_id, 'hints');
                }
            } catch (err) {
                alert("Hint generation failed: " + err.message);
                btnRunHints.disabled = false;
                btnRunHints.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Phase A: Generate Hints';
            }
        });
    }

    if (btnRunLearning) {
        btnRunLearning.addEventListener('click', async () => {
            if (!confirm("Start Phase B: AI UI Profiler? Make sure hints are generated first.")) return;
            
            btnRunLearning.disabled = true;
            btnRunLearning.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Profiling...';
            logsContainer.classList.remove('hidden');
            logsOutput.innerText = "Initializing Phase B (Playwright Traversal)...\n";

            try {
                const allSites = Object.values(trackerData.rows || {}).map(r => r.situs);
                const res = await fetch('/api/learn/execute/start', { 
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ target_sites: allSites })
                });
                const result = await res.json();
                if (result.status === 'success') {
                    pollLearningStatus(result.job_id, 'execute');
                }
            } catch (err) {
                alert("Learning start failed: " + err.message);
                btnRunLearning.disabled = false;
                btnRunLearning.innerHTML = '<i class="fa-solid fa-brain"></i> Phase B: Run AI Profiler';
            }
        });
    }

    function pollLearningStatus(jobId, type) {
        if (learningPollInterval) clearInterval(learningPollInterval);
        
        learningPollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/learn/job/${jobId}`);
                const data = await res.json();

                if (data.status === 'error') {
                    clearInterval(learningPollInterval);
                    return;
                }

                progressBar.style.width = data.percent + '%';
                progressBar.innerText = data.percent + '%';
                
                if (data.logs && data.logs.length > 0) {
                    logsOutput.innerText = data.logs.join("\n");
                    logsOutput.scrollTop = logsOutput.scrollHeight;
                }

                if (data.status === 'COMPLETED') {
                    clearInterval(learningPollInterval);
                    if (type === 'hints') {
                        btnRunHints.disabled = false;
                        btnRunHints.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Phase A: Map Upload Flow';
                        alert("Phase A Completed! You can now review the Site Knowledge Base.");
                        loadKnowledgeData(); // Load into table
                    } else {
                        btnRunLearning.disabled = false;
                        btnRunLearning.innerHTML = '<i class="fa-solid fa-brain"></i> Phase B: Share Link Test (Integrated)';
                        alert("Phase B Completed! AI Profiling finished.");
                    }
                }
            } catch (err) {
                console.error("Learning poll error:", err);
            }
        }, 1500);
    }

    // ------------------------------------------------------------------------
    // 5. Render Wizard Site Checklist & Presets
    // ------------------------------------------------------------------------
    function renderWizardCampaignSelect() {
        const select = document.getElementById('wiz-campaign');
        if (!select) return;
        select.innerHTML = '';
        (trackerData.campaigns || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.innerText = c;
            select.appendChild(opt);
        });
    }

    function renderWizardSiteChecklist() {
        const checklist = document.getElementById('sites-checklist');
        if (!checklist) return;
        checklist.innerHTML = '';

        const rows = trackerData.rows || [];
        const inspectorMap = {};
        (inspectorData.results || []).forEach(r => inspectorMap[r.situs] = r);

        const filteredRows = rows.filter(r => {
            const matchesCat = selectedCategoryFilter === "ALL" || r.category === selectedCategoryFilter;
            const siteInfo = inspectorMap[r.situs] || {};
            const matchesTier = selectedTierFilter === "ALL" || siteInfo.tier === selectedTierFilter;
            return matchesCat && matchesTier;
        });

        const elTotalTarget = document.getElementById('total-target-sites');
        if (elTotalTarget) elTotalTarget.innerText = rows.length;

        filteredRows.forEach((r) => {
            const siteInfo = inspectorMap[r.situs] || {};
            let tierDot = '🟢';
            if (siteInfo.tier === 'Sedang') tierDot = '🟡';
            if (siteInfo.tier === 'Sulit') tierDot = '🔴';

            const label = document.createElement('label');
            label.className = 'site-checkbox-label';
            label.innerHTML = `
                <input type="checkbox" class="site-chk" value="${r.situs}" checked>
                <span>${tierDot} ${r.situs}</span>
            `;
            checklist.appendChild(label);
        });

        updateSelectedSitesCount();
    }

    function updateSelectedSitesCount() {
        const checked = document.querySelectorAll('.site-chk:checked').length;
        const elCount = document.getElementById('selected-sites-count');
        if (elCount) elCount.innerText = checked;
    }

    const elChecklistContainer = document.getElementById('sites-checklist');
    if (elChecklistContainer) {
        elChecklistContainer.addEventListener('change', updateSelectedSitesCount);
    }

    // Filter Chips Events
    document.querySelectorAll('.category-filter-bar .btn-chip[data-cat]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.category-filter-bar .btn-chip[data-cat]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedCategoryFilter = btn.getAttribute('data-cat');
            renderWizardSiteChecklist();
        });
    });

    document.querySelectorAll('.category-filter-bar .btn-chip[data-tier]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.category-filter-bar .btn-chip[data-tier]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTierFilter = btn.getAttribute('data-tier');
            renderWizardSiteChecklist();
        });
    });

    // Preset Dropdown Handler
    const presetDropdown = document.getElementById('wiz-preset-dropdown');
    if (presetDropdown) {
        presetDropdown.addEventListener('change', (e) => {
            const val = e.target.value;
            const inspectorMap = {};
            (inspectorData.results || []).forEach(r => inspectorMap[r.situs] = r);

            if (val === 'ALL') {
                selectedCategoryFilter = "ALL";
                selectedTierFilter = "ALL";
                renderWizardSiteChecklist();
                document.querySelectorAll('.site-chk').forEach(c => c.checked = true);
            } else if (val === 'MUDAH_ONLY') {
                selectedCategoryFilter = "ALL";
                selectedTierFilter = "Mudah";
                renderWizardSiteChecklist();
                document.querySelectorAll('.site-chk').forEach(c => c.checked = true);
            } else if (val === 'SEDANG_ONLY') {
                selectedCategoryFilter = "ALL";
                selectedTierFilter = "Sedang";
                renderWizardSiteChecklist();
                document.querySelectorAll('.site-chk').forEach(c => c.checked = true);
            } else if (val === 'IMAGE_ONLY') {
                selectedCategoryFilter = "Image Host";
                selectedTierFilter = "ALL";
                renderWizardSiteChecklist();
                document.querySelectorAll('.site-chk').forEach(c => c.checked = true);
            } else if (val === 'PASTE_ONLY') {
                selectedCategoryFilter = "Text / Paste Host";
                selectedTierFilter = "ALL";
                renderWizardSiteChecklist();
                document.querySelectorAll('.site-chk').forEach(c => c.checked = true);
            } else if (val === 'DESELECT') {
                document.querySelectorAll('.site-chk').forEach(c => c.checked = false);
            }
            updateSelectedSitesCount();
        });
    }

    const btnSelectAll = document.getElementById('btn-select-all');
    if (btnSelectAll) {
        btnSelectAll.addEventListener('click', () => {
            document.querySelectorAll('.site-chk').forEach(c => c.checked = true);
            updateSelectedSitesCount();
        });
    }

    const btnDeselectAll = document.getElementById('btn-deselect-all');
    if (btnDeselectAll) {
        btnDeselectAll.addEventListener('click', () => {
            document.querySelectorAll('.site-chk').forEach(c => c.checked = false);
            updateSelectedSitesCount();
        });
    }

    // ------------------------------------------------------------------------
    // 6. File Drag & Drop Attachment
    // ------------------------------------------------------------------------
    const dropzone = document.getElementById('file-dropzone');
    const fileInput = document.getElementById('file-input');
    const attachedInfo = document.getElementById('attached-file-info');
    const attachedFileName = document.getElementById('attached-file-name');
    const btnRemoveFile = document.getElementById('btn-remove-file');

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = '#38bdf8';
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.style.borderColor = 'rgba(255, 255, 255, 0.08)';
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = 'rgba(255, 255, 255, 0.08)';
            if (e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });
    }

    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            if (dropzone) dropzone.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><p>Uploading file...</p>';
            const res = await fetch('/api/upload-media', { method: 'POST', body: formData });
            const result = await res.json();
            if (result.status === 'success') {
                selectedFilepath = result.filepath;
                selectedFilename = result.filename;
                if (attachedFileName) attachedFileName.innerText = result.filename;
                if (attachedInfo) attachedInfo.classList.remove('hidden');
                if (dropzone) dropzone.classList.add('hidden');
            }
        } catch (err) {
            alert('File upload failed: ' + err.message);
        } finally {
            if (dropzone) dropzone.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i><p>Drag & drop image/file here or <span>browse</span></p>';
        }
    }

    if (btnRemoveFile) {
        btnRemoveFile.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedFilepath = null;
            selectedFilename = null;
            if (attachedInfo) attachedInfo.classList.add('hidden');
            if (dropzone) dropzone.classList.remove('hidden');
            if (fileInput) fileInput.value = '';
        });
    }

    // ------------------------------------------------------------------------
    // 7. Launch & Track Batch Automation Upload
    // ------------------------------------------------------------------------
    const btnStartBatch = document.getElementById('btn-start-batch');
    const jobStatusBadge = document.getElementById('job-status-badge');
    const jobProgressBar = document.getElementById('job-progress-bar');
    const jobProgressText = document.getElementById('job-progress-text');
    const jobCountsText = document.getElementById('job-counts-text');
    const terminalWindow = document.getElementById('terminal-window');
    const jobResultsSummary = document.getElementById('job-results-summary');
    const resultsTableBody = document.querySelector('#results-table tbody');

    if (btnStartBatch) {
        btnStartBatch.addEventListener('click', async () => {
            const campaignName = document.getElementById('wiz-campaign').value;
            const title = document.getElementById('wiz-title').value || "Auto Post Content";
            const contentText = document.getElementById('wiz-content').value || "";

            const selectedSites = Array.from(document.querySelectorAll('.site-chk:checked')).map(c => c.value);

            if (selectedSites.length === 0) {
                alert("Please select at least one target website!");
                return;
            }

            const visibleBrowser = document.getElementById('wiz-visible-browser') ? document.getElementById('wiz-visible-browser').checked : true;

            btnStartBatch.disabled = true;
            btnStartBatch.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Automation Launching...';

            const modeLabel = visibleBrowser ? "Visible Browser Window" : "Headless Mode";
            if (terminalWindow) terminalWindow.innerHTML = `<p class="sys-msg">[System] Launching batch automation task on ${selectedSites.length} platforms (${modeLabel}). Prioritizing 🟢 Mudah API sites first...</p>`;
            if (jobResultsSummary) jobResultsSummary.classList.add('hidden');
            if (resultsTableBody) resultsTableBody.innerHTML = '';

            try {
                const res = await fetch('/api/upload/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        campaign_name: campaignName,
                        target_sites: selectedSites,
                        title: title,
                        content_text: contentText,
                        file_path: selectedFilepath,
                        visible_browser: visibleBrowser
                    })
                });

                const result = await res.json();
                if (result.status === 'success') {
                    activeJobId = result.job_id;
                    startPollingJobStatus();
                } else {
                    alert("Launch error: " + result.message);
                    btnStartBatch.disabled = false;
                    btnStartBatch.innerHTML = '<i class="fa-solid fa-rocket"></i> Launch Bulk Automation Task';
                }
            } catch (err) {
                alert("Error connecting to server: " + err.message);
                btnStartBatch.disabled = false;
                btnStartBatch.innerHTML = '<i class="fa-solid fa-rocket"></i> Launch Bulk Automation Task';
            }
        });
    }

    function startPollingJobStatus() {
        if (jobPollInterval) clearInterval(jobPollInterval);

        const liveBadge = document.getElementById('live-target-badge');
        const liveImg = document.getElementById('live-preview-img');

        jobPollInterval = setInterval(async () => {
            if (!activeJobId) return;

            try {
                const res = await fetch(`/api/upload/job/${activeJobId}`);
                const job = await res.json();

                if (jobStatusBadge) {
                    jobStatusBadge.innerText = job.status;
                    jobStatusBadge.className = `badge badge-${job.status.toLowerCase()}`;
                }

                if (jobProgressBar) jobProgressBar.style.width = `${job.percent}%`;
                if (jobProgressText) jobProgressText.innerText = `${job.percent}% Completed`;
                if (jobCountsText) jobCountsText.innerText = `${job.completed} / ${job.total}`;

                if (liveBadge) {
                    if (job.current_site) {
                        liveBadge.innerText = `[${job.current_tier || 'Active'}] ${job.current_site}`;
                    } else if (job.status === 'COMPLETED') {
                        liveBadge.innerText = 'Completed';
                    }
                }

                // Refresh live preview screenshot
                if (liveImg) {
                    liveImg.src = `/static/live_preview.jpg?t=${Date.now()}`;
                }

                // Update Terminal Output
                if (terminalWindow) {
                    terminalWindow.innerHTML = '';
                    (job.logs || []).forEach(log => {
                        const p = document.createElement('p');
                        p.innerText = log;
                        terminalWindow.appendChild(p);
                    });
                    terminalWindow.scrollTop = terminalWindow.scrollHeight;
                }

                if (job.status === 'COMPLETED' || job.status === 'FAILED') {
                    clearInterval(jobPollInterval);
                    if (btnStartBatch) {
                        btnStartBatch.disabled = false;
                        btnStartBatch.innerHTML = '<i class="fa-solid fa-rocket"></i> Launch Bulk Automation Task';
                    }

                    // Show Results Table
                    if (job.results && Object.keys(job.results).length > 0) {
                        if (jobResultsSummary) jobResultsSummary.classList.remove('hidden');
                        if (resultsTableBody) {
                            resultsTableBody.innerHTML = '';
                            for (const [site, url] of Object.entries(job.results)) {
                                const tr = document.createElement('tr');
                                tr.innerHTML = `
                                    <td>${site}</td>
                                    <td class="link-cell"><a href="${url}" target="_blank">${url}</a></td>
                                `;
                                resultsTableBody.appendChild(tr);
                            }
                        }
                    }

                    // Reload tracker data so Excel table and Dashboard stay updated
                    loadTrackerData();
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 1000);
    }

    // ------------------------------------------------------------------------
    // 8. Render Excel Tracker Table
    // ------------------------------------------------------------------------
    const searchSitusInput = document.getElementById('search-situs');
    const filterCategorySelect = document.getElementById('filter-category');

    function renderExcelTable() {
        const thead = document.getElementById('excel-table-head');
        const tbody = document.getElementById('excel-table-body');

        if (!thead || !tbody) return;

        thead.innerHTML = '';
        tbody.innerHTML = '';

        const headers = trackerData.headers || [];
        const campaigns = trackerData.campaigns || [];
        const rows = trackerData.rows || [];

        const inspectorMap = {};
        (inspectorData.results || []).forEach(r => inspectorMap[r.situs] = r);

        // Build Table Header
        let trHead = '<tr><th>#</th><th>Target Site</th><th>Category</th><th>Tier</th>';
        campaigns.forEach(c => {
            trHead += `<th>${c}</th>`;
        });
        trHead += '</tr>';
        thead.innerHTML = trHead;

        // Apply Filters
        const searchQuery = searchSitusInput ? searchSitusInput.value.toLowerCase().trim() : '';
        const selectedCat = filterCategorySelect ? filterCategorySelect.value : 'ALL';

        const filteredRows = rows.filter(r => {
            const matchesSearch = !searchQuery || r.situs.toLowerCase().includes(searchQuery);
            const matchesCat = selectedCat === "ALL" || r.category === selectedCat;
            return matchesSearch && matchesCat;
        });

        // Build Table Body
        filteredRows.forEach((r, idx) => {
            const siteInfo = inspectorMap[r.situs] || {};
            let tierBadgeClass = 'badge-mudah';
            let tierDot = '🟢';
            if (siteInfo.tier === 'Sedang') { tierBadgeClass = 'badge-sedang'; tierDot = '🟡'; }
            if (siteInfo.tier === 'Sulit') { tierBadgeClass = 'badge-sulit'; tierDot = '🔴'; }

            const tr = document.createElement('tr');
            let tdHtml = `
                <td>${idx + 1}</td>
                <td><strong>${r.situs}</strong></td>
                <td><span class="btn-chip">${r.category}</span></td>
                <td><span class="badge ${tierBadgeClass}">${tierDot} ${siteInfo.tier || 'Sedang'}</span></td>
            `;

            campaigns.forEach(c => {
                const linkVal = r.campaigns[c] || '';
                if (linkVal) {
                    tdHtml += `<td class="link-cell" title="${linkVal}"><a href="${linkVal}" target="_blank">${linkVal}</a></td>`;
                } else {
                    tdHtml += `<td class="text-muted">-</td>`;
                }
            });

            tr.innerHTML = tdHtml;
            tbody.appendChild(tr);
        });
    }

    if (searchSitusInput) searchSitusInput.addEventListener('input', renderExcelTable);
    if (filterCategorySelect) filterCategorySelect.addEventListener('change', renderExcelTable);

    // ------------------------------------------------------------------------
    // 9. Add Campaign Column Modal
    // ------------------------------------------------------------------------
    const modalAddCampaign = document.getElementById('modal-add-campaign');
    const btnAddCampaignModal = document.getElementById('btn-add-campaign-modal');
    const btnAddCampaignBar = document.getElementById('btn-add-campaign-bar');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnCancelModal = document.getElementById('btn-cancel-modal');
    const btnSubmitCampaign = document.getElementById('btn-submit-campaign');
    const newCampaignNameInput = document.getElementById('new-campaign-name');

    const showModal = () => { if (modalAddCampaign) modalAddCampaign.classList.remove('hidden'); };
    const hideModal = () => {
        if (modalAddCampaign) modalAddCampaign.classList.add('hidden');
        if (newCampaignNameInput) newCampaignNameInput.value = '';
    };

    if (btnAddCampaignModal) btnAddCampaignModal.addEventListener('click', showModal);
    if (btnAddCampaignBar) btnAddCampaignBar.addEventListener('click', showModal);
    if (btnCloseModal) btnCloseModal.addEventListener('click', hideModal);
    if (btnCancelModal) btnCancelModal.addEventListener('click', hideModal);

    if (btnSubmitCampaign) {
        btnSubmitCampaign.addEventListener('click', async () => {
            const name = newCampaignNameInput ? newCampaignNameInput.value.trim() : '';
            if (!name) {
                alert("Please enter campaign name!");
                return;
            }

            try {
                const res = await fetch('/api/tracker/campaign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });

                const result = await res.json();
                if (result.status === 'success') {
                    hideModal();
                    loadTrackerData();
                } else {
                    alert("Error: " + result.message);
                }
            } catch (err) {
                alert("Failed to add campaign: " + err.message);
            }
        });
    }

    // ------------------------------------------------------------------------
    // 10. Link Health Audit Verifier
    // ------------------------------------------------------------------------
    function renderAuditCampaignSelect() {
        const select = document.getElementById('audit-campaign-select');
        if (!select) return;
        select.innerHTML = '<option value="">All Campaigns</option>';
        (trackerData.campaigns || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.innerText = c;
            select.appendChild(opt);
        });
    }

    const btnRunAudit = document.getElementById('btn-run-audit');
    const auditSummaryBadges = document.getElementById('audit-summary-badges');
    const badgeAlive = document.getElementById('badge-alive');
    const badgeDead = document.getElementById('badge-dead');
    const badgeRate = document.getElementById('badge-rate');
    const auditTableBody = document.getElementById('audit-table-body');

    if (btnRunAudit) {
        btnRunAudit.addEventListener('click', async () => {
            const selectedCampaign = document.getElementById('audit-campaign-select') ? document.getElementById('audit-campaign-select').value : '';

            btnRunAudit.disabled = true;
            btnRunAudit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Auditing Links...';
            if (auditTableBody) auditTableBody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fa-solid fa-spinner fa-spin"></i> Checking HTTP status codes concurrently...</td></tr>';

            try {
                const res = await fetch('/api/verify-links', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ campaign_name: selectedCampaign })
                });

                const result = await res.json();
                if (result.status === 'success') {
                    pollAuditStatus(result.task_id);
                }
            } catch (err) {
                alert("Audit start failed: " + err.message);
                btnRunAudit.disabled = false;
                btnRunAudit.innerHTML = '<i class="fa-solid fa-stethoscope"></i> Run Link Health Check';
            }
        });
    }

    function pollAuditStatus(taskId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/verify-status/${taskId}`);
                const task = await res.json();

                if (task.status === 'COMPLETED') {
                    clearInterval(interval);
                    if (btnRunAudit) {
                        btnRunAudit.disabled = false;
                        btnRunAudit.innerHTML = '<i class="fa-solid fa-stethoscope"></i> Run Link Health Check';
                    }

                    const data = task.result;
                    if (badgeAlive) badgeAlive.innerText = `Active: ${data.alive_count}`;
                    if (badgeDead) badgeDead.innerText = `Broken: ${data.dead_count}`;
                    if (badgeRate) badgeRate.innerText = `Health Rate: ${data.success_rate}%`;
                    if (auditSummaryBadges) auditSummaryBadges.classList.remove('hidden');

                    if (auditTableBody) {
                        auditTableBody.innerHTML = '';
                        (data.results || []).forEach(r => {
                            const tr = document.createElement('tr');
                            const statusBadgeClass = r.is_alive ? 'badge-success' : 'badge-danger';
                            tr.innerHTML = `
                                <td>${r.situs}</td>
                                <td>${r.campaign}</td>
                                <td class="link-cell"><a href="${r.url}" target="_blank">${r.url}</a></td>
                                <td><code>${r.status_code || '-'}</code></td>
                                <td><span class="badge ${statusBadgeClass}">${r.status}</span></td>
                            `;
                            auditTableBody.appendChild(tr);
                        });
                    }
                }
            } catch (err) {
                console.error("Audit status poll error:", err);
            }
        }, 1000);
    }

    // ==========================================
    // MASS AUDIT LOGIC (Tab Audit Info)
    // ==========================================
    let auditPollInterval = null;

    let auditBtn = document.getElementById('btn-run-audit');
    if (auditBtn) {
        auditBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/audit/run', { method: 'POST' });
                const data = await response.json();
                if (data.status === 'success') {
                    startAuditPolling();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (err) {
                console.error(err);
                alert('Gagal menjalankan mass audit.');
            }
        });
    }

    function startAuditPolling() {
        if (auditPollInterval) clearInterval(auditPollInterval);
        fetchAuditData(); // Fetch immediately
        auditPollInterval = setInterval(fetchAuditData, 2000);
    }

    async function fetchAuditData() {
        try {
            const response = await fetch('/api/audit/data');
            const data = await response.json();
            
            if (data.status === 'success' && data.data) {
                const state = data.data;
                
                // Update stats
                const elProgress = document.getElementById('audit-stat-progress');
                if(elProgress) elProgress.textContent = `${state.progress.completed} / ${state.progress.total}`;
                
                const elReady = document.getElementById('audit-stat-ready');
                if(elReady) elReady.textContent = state.stats.READY;
                
                const elNyasar = document.getElementById('audit-stat-nyasar');
                if(elNyasar) elNyasar.textContent = state.stats.NYASAR;
                
                const elLogin = document.getElementById('audit-stat-login');
                if(elLogin) elLogin.textContent = state.stats.LOGIN_REQUIRED;
                
                // Update table
                const tbody = document.getElementById('audit-results-tbody');
                if (tbody) {
                    if (state.results.length === 0) {
                        if (state.is_running) {
                            tbody.innerHTML = `<tr><td colspan="3" class="text-center"><i class="fa-solid fa-spinner fa-spin"></i> Memulai pemindaian...</td></tr>`;
                        } else {
                            tbody.innerHTML = `<tr><td colspan="3" class="text-center">Belum ada data audit. Klik "Run Mass Audit" untuk memulai.</td></tr>`;
                        }
                    } else {
                        tbody.innerHTML = '';
                        state.results.slice().reverse().forEach(row => {
                            let statusBadge = `<span class="badge" style="background:#4b5563; color:white;">${row.status}</span>`;
                            if (row.status === 'READY') statusBadge = `<span class="badge" style="background:#22c55e; color:white;">READY</span>`;
                            else if (row.status === 'NYASAR') statusBadge = `<span class="badge" style="background:#eab308; color:black;">NYASAR</span>`;
                            else if (row.status === 'LOGIN_REQUIRED') statusBadge = `<span class="badge" style="background:#ef4444; color:white;">LOGIN WALL</span>`;
                            
                            let routedBadge = row.routed ? ` <span class="badge" style="background:#3b82f6; color:white; font-size:10px;">Auto-Routed</span>` : '';
                            
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td>
                                    <strong>${row.situs}</strong><br>
                                    <small class="text-muted"><a href="${row.target_url}" target="_blank">${row.target_url}</a></small>${routedBadge}
                                </td>
                                <td>${statusBadge}</td>
                                <td>${row.msg}</td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }
                }
                
                if (auditBtn) {
                    auditBtn.disabled = state.is_running;
                    auditBtn.innerHTML = state.is_running ? '<i class="fa-solid fa-spinner fa-spin"></i> Auditing...' : '<i class="fa-solid fa-play"></i> Run Mass Audit';
                }
                
                if (!state.is_running && state.progress.total > 0 && state.progress.completed >= state.progress.total) {
                    clearInterval(auditPollInterval);
                }
            }
        } catch (err) {
            console.error('Error fetching audit data:', err);
        }
    }

    // Auto-load audit data on load
    fetchAuditData();

    // Initialize App Data
    loadTrackerData();
    loadInspectorData();
    loadKnowledgeData();
});
