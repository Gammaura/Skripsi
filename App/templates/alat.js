let selectedFile = null;

function handleFileSelect(e) {
    const files = e.target.files;
    if (files && files[0]) {
        selectedFile = files[0];
        const fileInfo = document.getElementById('file-info');
        fileInfo.style.display = 'inline-flex';
        
        const sizeMB = (selectedFile.size / (1024 * 1024)).toFixed(1);
        const isVercel = window.location.hostname.includes("vercel.app");

        if (isVercel && selectedFile.size > 4.5 * 1024 * 1024) {
            fileInfo.className = 'file-pill';
            fileInfo.style.background = '#fee2e2';
            fileInfo.style.color = '#991b1b';
            fileInfo.style.border = '1px solid #f87171';
            fileInfo.innerHTML = `⚠️ ${selectedFile.name} &nbsp;•&nbsp; ${sizeMB} MB (Melebihi limit Vercel 4.5 MB)`;
            document.getElementById('dz-title').innerText = selectedFile.name;
            document.getElementById('dz-subtitle').innerHTML = `<span style="color: #b91c1c; font-weight: 600;">Ukuran berkas (${sizeMB} MB) melebihi batas upload Vercel Serverless (maks 4.5 MB). Silakan kompres gambar di Word terlebih dahulu atau gunakan server lokal.</span>`;
            document.getElementById('btn-process').disabled = true;
            return;
        }

        fileInfo.className = 'file-pill';
        fileInfo.style.background = '';
        fileInfo.style.color = '';
        fileInfo.style.border = '';
        fileInfo.innerHTML = `${selectedFile.name} &nbsp;•&nbsp; ${(selectedFile.size/1024).toFixed(1)} KB`;
        document.getElementById('dz-title').innerText = selectedFile.name;
        document.getElementById('dz-subtitle').innerText = "Berkas terpilih. Klik tombol 'Mulai Rapikan Dokumen' di bawah untuk memproses.";
        document.getElementById('btn-process').disabled = false;
    }
}

// Drag & Drop Listeners
const dz = document.getElementById('dropzone');
if (dz) {
    ['dragenter', 'dragover'].forEach(eventName => {
        dz.addEventListener(eventName, (e) => {
            e.preventDefault();
            dz.classList.add('dragover');
        }, false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dz.addEventListener(eventName, (e) => {
            e.preventDefault();
            dz.classList.remove('dragover');
        }, false);
    });
    dz.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files[0]) {
            document.getElementById('file-input').files = dt.files;
            handleFileSelect({ target: { files: dt.files } });
        }
    }, false);
}

async function processDocument() {
    if (!selectedFile) return;

    const isVercel = window.location.hostname.includes("vercel.app");
    if (isVercel && selectedFile.size > 4.5 * 1024 * 1024) {
        alert(`Ukuran berkas (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB) melebihi batas upload Vercel Serverless (maksimal 4.5 MB).\n\nSolusi:\n1. Buka berkas di Word, pilih gambar > Picture Format > Compress Pictures.\n2. Atau jalankan Asdoku di server lokal (localhost:8000) tanpa batas ukuran.`);
        return;
    }

    const btn = document.getElementById('btn-process');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const resultsArea = document.getElementById('results-area');

    btn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline';

    // Reset Agents UI Status
    setAgentStatus(1, "running");
    setAgentStatus(2, "idle");
    setAgentStatus(3, "idle");

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        // Step 1: Inspector UI simulation
        await new Promise(r => setTimeout(r, 400));
        setAgentStatus(1, "done");
        setAgentStatus(2, "running");

        // Step 2: Critic UI simulation
        await new Promise(r => setTimeout(r, 400));
        setAgentStatus(2, "done");
        setAgentStatus(3, "running");

        const response = await fetch('/api/format', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errMsg = "Gagal memproses dokumen";
            if (response.status === 413) {
                errMsg = `Ukuran berkas (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB) melebihi batas maksimal Vercel Serverless (4.5 MB). Silakan kompres gambar di dokumen Word atau gunakan server lokal.`;
            } else {
                try {
                    const err = await response.json();
                    errMsg = err.detail || errMsg;
                } catch (e) {
                    const rawText = await response.text();
                    errMsg = rawText || `HTTP ${response.status}: ${response.statusText}`;
                }
            }
            throw new Error(errMsg);
        }

        const data = await response.json();

                // All Agents Done
                setAgentStatus(1, "done");
                setAgentStatus(2, "done");
                setAgentStatus(3, "done");

                // Populate Stats Metrics
                document.getElementById('stat-time').innerText = `${data.elapsed_time || 0}s`;
                document.getElementById('stat-paras').innerText = data.total_paragraphs || 0;
                document.getElementById('stat-corrections').innerText = data.total_corrections || 0;
                document.getElementById('stat-chapters').innerText = `${(data.approved_chapters || []).length} Bab`;
                document.getElementById('stat-sqa').innerText = `${data.sqa_score || 100}%`;

                // Update SQA Badge
                const sqaBadge = document.getElementById('badge-sqa-status');
                const defectsCount = (data.sqa_defects || []).length;
                if (data.sqa_status === "PASS") {
                    sqaBadge.className = "pill-badge badge-emerald";
                    sqaBadge.innerText = `PASS 100% (Iterasi ${data.sqa_tier2_iterations || 1})`;
                } else {
                    sqaBadge.className = "pill-badge badge-pink";
                    sqaBadge.innerText = `SCORE ${data.sqa_score || 100}% (${defectsCount} Defect)`;
                }

                // Update Download Link
                const dlBtn = document.getElementById('btn-download');
                dlBtn.href = `/api/download/${encodeURIComponent(data.output_filename || '')}`;
                document.getElementById('out-filename-label').innerText = data.output_filename || 'hasil_skripsi.docx';

                // Populate Corrections Log Table
                const tbody = document.getElementById('corrections-tbody');
                tbody.innerHTML = '';
                if (data.corrections_log && data.corrections_log.length > 0) {
                    data.corrections_log.slice(0, 50).forEach(c => {
                        const tr = document.createElement('tr');
                        const pIdx = c.idx !== undefined ? c.idx : (c.para_id !== undefined ? c.para_id : '-');
                        const origPred = c.agent1_pred || c.original_pred || '-';
                        const corrTo = c.corrected_to || c.corrected_label || '-';
                        tr.innerHTML = `
                            <td style="font-family: 'JetBrains Mono'; font-weight: 600; color: var(--text-muted);">P[${escapeHtml(pIdx)}]</td>
                            <td style="color: var(--text-heading); font-weight: 500;">"${escapeHtml(c.text || '')}"</td>
                            <td><span style="background: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">${escapeHtml(origPred)}</span></td>
                            <td><span style="background: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">${escapeHtml(corrTo)}</span></td>
                            <td style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(c.reason || '')}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--emerald-text); font-weight: 600; padding: 1rem;">Sempurna! Agent 1 berhasil memprediksi seluruh struktur dengan 0 anomali.</td></tr>`;
                }

                renderReviewQueue(data.review_queue || []);

                resultsArea.style.display = 'block';
                resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });

            } catch (err) {
                alert("Terjadi kesalahan: " + err.message);
                setAgentStatus(1, "idle");
                setAgentStatus(2, "idle");
                setAgentStatus(3, "idle");
            } finally {
                btn.disabled = false;
                btnText.style.display = 'inline';
                btnSpinner.style.display = 'none';
            }
        }

        const LABEL_OPTIONS = [
            "BODY_PARAGRAPH", "SUB_BAB", "JUDUL_BAB", "FRONTMATTER_TITLE", "COVER_METADATA",
            "CAPTION_GAMBAR", "CAPTION_TABEL", "DAFTAR_PUSTAKA_ITEM", "LAINNYA"
        ];

        function escapeHtml(value) {
            return String(value).replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
        }

        function renderReviewQueue(queue) {
            const card = document.getElementById('review-card');
            const tbody = document.getElementById('review-tbody');
            tbody.innerHTML = '';
            card.style.display = queue.length ? 'block' : 'none';
            document.getElementById('review-count-badge').innerText = `${queue.length} Paragraf`;

            queue.forEach(q => {
                const tr = document.createElement('tr');
                const options = LABEL_OPTIONS.map(label =>
                    `<option value="${label}" ${label === q.predicted_label ? 'selected' : ''}>${label}</option>`).join('');
                tr.innerHTML = `
                    <td style="font-family: 'JetBrains Mono'; font-weight: 600; color: var(--text-muted);">P[${escapeHtml(q.idx)}]</td>
                    <td style="color: var(--text-heading); font-weight: 500;">"${escapeHtml(q.text)}"</td>
                    <td style="font-size: 0.72rem;"><b>${escapeHtml(q.predicted_label)}</b><br>
                        <span style="color: var(--text-muted);">yakin ${Math.round(q.confidence * 100)}%</span></td>
                    <td><select class="review-select" style="width: 100%; font-size: 0.72rem; padding: 3px;">${options}</select></td>
                    <td><button type="button" class="pill-badge badge-blue" style="border: none; cursor: pointer;">Simpan</button></td>
                `;
                const btn = tr.querySelector('button');
                btn.addEventListener('click', () => submitReview(q, tr.querySelector('select').value, btn));
                tbody.appendChild(tr);
            });
        }

        async function submitReview(q, label, btn) {
            btn.disabled = true;
            const form = new FormData();
            form.append('paragraph_idx', q.idx);
            form.append('paragraph_text', q.text);
            form.append('correct_label', label);
            form.append('review_id', q.review_id);
            try {
                const res = await fetch('/api/active-learning/feedback', { method: 'POST', body: form });
                const body = await res.json();
                if (!res.ok) throw new Error(body.detail || 'Gagal menyimpan label');
                btn.innerText = 'Tersimpan';
                btn.className = 'pill-badge badge-emerald';
            } catch (err) {
                btn.disabled = false;
                alert(err.message);
            }
        }

        function setAgentStatus(agentNum, status) {
            const card = document.getElementById(`card-agent-${agentNum}`);
            const badge = document.getElementById(`badge-agent-${agentNum}`);

            card.classList.remove("active", "done");
            badge.className = "agent-status-badge";

            if (status === "idle") {
                badge.classList.add("status-idle");
                badge.innerText = "Idle";
            } else if (status === "running") {
                card.classList.add("active");
                badge.classList.add("status-running");
                badge.innerText = "Running...";
            } else if (status === "done") {
                card.classList.add("done");
                badge.classList.add("status-done");
                badge.innerText = "Approved";
            }
        }