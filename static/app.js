/**
 * SmartFileOrganizer - Frontend Application
 * Handles all UI interactions and API communication
 */

// API Base URL
const API_BASE = 'http://localhost:8001';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('SmartFileOrganizer UI loaded');
    checkServerStatus();
    loadPlans();
    setupEventListeners();
});

/**
 * Check if server is reachable
 */
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        
        if (response.ok) {
            const data = await response.json();
            updateStatusIndicator('online');
            console.log('Server status:', data);
        } else {
            updateStatusIndicator('offline');
        }
    } catch (error) {
        console.error('Server health check failed:', error);
        updateStatusIndicator('offline');
        showErrorMessage('Server not reachable. Please run install.sh to start the server.');
    }
}

/**
 * Update status indicator
 */
function updateStatusIndicator(status) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    
    dot.className = 'status-dot status-' + status;
    
    if (status === 'online') {
        text.textContent = '✅ Connected';
    } else if (status === 'offline') {
        text.textContent = '❌ Server offline';
    } else {
        text.textContent = '⏳ Checking...';
    }
}

/**
 * Auto-scan common folders
 */
async function autoScan() {
    showLoading('Scanning common folders (Downloads, Documents, Desktop, Pictures)...');
    
    try {
        const response = await fetch(`${API_BASE}/api/auto-scan`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Auto-scan result:', data);
        
        showSuccessMessage(data.message || `Scanned ${data.scanned} folders successfully!`);
        
        // Refresh plans list
        await loadPlans();
        
    } catch (error) {
        console.error('Auto-scan error:', error);
        showErrorMessage(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Manual scan of a specific folder
 */
async function manualScan(folderPath) {
    if (!folderPath || !folderPath.trim()) {
        showErrorMessage('Please enter a folder path');
        return;
    }
    
    const scanStartTime = Date.now();
    showLoading(`Scanning ${folderPath}...`);
    
    try {
        const response = await fetch(`${API_BASE}/api/plans`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                root_path: folderPath,
                dry_run: true,
                recursive: false
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const plan = await response.json();
        const scanDuration = Math.round((Date.now() - scanStartTime) / 1000);
        console.log('Scan result:', plan);
        
        // Log performance metric
        console.log(`Performance: Scanned ${plan.file_count} files in ${scanDuration}s (${plan.scan_duration_ms}ms server-side)`);
        
        if (plan.status === 'empty') {
            showSuccessMessage(plan.message || 'No files found to organize');
        } else {
            showSuccessMessage(
                `Scan complete! Found ${plan.file_count} files, ${plan.reclaimable_mb.toFixed(2)} MB reclaimable (${scanDuration}s)`
            );
        }
        
        // Refresh plans list
        await loadPlans();
        
    } catch (error) {
        console.error('Manual scan error:', error);
        showErrorMessage(`Error scanning folder: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Load all plans from API
 */
async function loadPlans() {
    try {
        const response = await fetch(`${API_BASE}/api/plans`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const plans = await response.json();
        console.log('Plans loaded:', plans.length);
        
        renderPlans(plans);
        
    } catch (error) {
        console.error('Load plans error:', error);
        // Don't show error on initial load, just log it
        if (document.getElementById('plans-container').children.length > 0) {
            showErrorMessage(`Error loading plans: ${error.message}`);
        }
    }
}

/**
 * Render plans to the UI
 */
function renderPlans(plans) {
    const container = document.getElementById('plans-container');
    container.innerHTML = '';
    
    if (!plans || plans.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📭</span>
                <p>No plans yet</p>
                <small>Click "Auto-Scan" above to get started!</small>
            </div>
        `;
        return;
    }
    
    // Sort plans by timestamp (newest first)
    plans.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    plans.forEach(plan => {
        const card = createPlanCard(plan);
        container.appendChild(card);
    });
}

/**
 * Create a plan card element
 */
function createPlanCard(plan) {
    const card = document.createElement('div');
    card.className = 'plan-card';
    card.setAttribute('data-plan-id', plan.id);
    
    // Format plan ID (first 8 characters)
    const shortId = plan.id.toString().substring(0, 8);
    
    // Format timestamp
    const timestamp = new Date(plan.timestamp).toLocaleString();
    
    // Create card structure
    const header = document.createElement('div');
    header.className = 'plan-header';
    header.innerHTML = `
        <span class="plan-id" title="${escapeHtml(plan.id)}">${escapeHtml(shortId)}</span>
        <span class="plan-status status-${escapeHtml(plan.status)}">${escapeHtml(plan.status)}</span>
    `;
    
    const info = document.createElement('div');
    info.className = 'plan-info';
    info.innerHTML = `
        <p><strong>📁 Folder:</strong> ${escapeHtml(plan.root_path)}</p>
        <p style="font-size: 0.8rem; color: #a0aec0;">Created: ${escapeHtml(timestamp)}</p>
    `;
    
    const metrics = document.createElement('div');
    metrics.className = 'plan-metrics';
    metrics.innerHTML = `
        <div class="metric">
            <span class="metric-label">Files</span>
            <span class="metric-value">📄 ${escapeHtml(plan.file_count.toString())}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Space</span>
            <span class="metric-value">💾 ${escapeHtml(plan.reclaimable_mb.toFixed(2))} MB</span>
        </div>
        <div class="metric">
            <span class="metric-label">Risk Level</span>
            <span class="metric-value risk-${escapeHtml(plan.risk_level.toLowerCase())}">⚠️ ${escapeHtml(plan.risk_level)}</span>
        </div>
    `;
    
    const actions = document.createElement('div');
    actions.className = 'plan-actions';
    
    // Create buttons with proper event listeners (not inline onclick)
    const approveBtn = document.createElement('button');
    approveBtn.className = 'btn-success';
    approveBtn.textContent = '✅ Approve';
    approveBtn.disabled = plan.status !== 'pending';
    approveBtn.addEventListener('click', () => approvePlan(plan.id));
    
    const executeBtn = document.createElement('button');
    executeBtn.className = 'btn-primary';
    executeBtn.textContent = '▶️ Execute';
    executeBtn.disabled = plan.status === 'executed' || plan.status === 'rolled_back';
    executeBtn.addEventListener('click', () => executePlan(plan.id));
    
    const rollbackBtn = document.createElement('button');
    rollbackBtn.className = 'btn-warning';
    rollbackBtn.textContent = '↩️ Rollback';
    rollbackBtn.disabled = plan.status !== 'executed';
    rollbackBtn.addEventListener('click', () => rollbackPlan(plan.id));
    
    actions.appendChild(approveBtn);
    actions.appendChild(executeBtn);
    actions.appendChild(rollbackBtn);
    
    // Assemble card
    card.appendChild(header);
    card.appendChild(info);
    card.appendChild(metrics);
    card.appendChild(actions);
    
    return card;
}

/**
 * Approve a plan
 */
async function approvePlan(planId) {
    if (!confirm('Approve this organization plan?')) {
        return;
    }
    
    showLoading('Approving plan...');
    
    try {
        const response = await fetch(`${API_BASE}/api/plans/${planId}/approve`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Approve result:', result);
        
        showSuccessMessage('Plan approved!');
        
        // Refresh plans
        await loadPlans();
        
    } catch (error) {
        console.error('Approve error:', error);
        showErrorMessage(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Execute a plan
 */
async function executePlan(planId) {
    if (!confirm('Execute this plan? Files will be moved!')) {
        return;
    }
    
    showLoading('Executing plan... This may take a moment.');
    
    try {
        const response = await fetch(`${API_BASE}/api/plans/${planId}/execute`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Execute result:', result);
        
        showSuccessMessage(`Plan executed! Moved ${result.files_moved || 0} files`);
        
        // Refresh plans
        await loadPlans();
        
    } catch (error) {
        console.error('Execute error:', error);
        showErrorMessage(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Rollback a plan
 */
async function rollbackPlan(planId) {
    if (!confirm('Rollback this plan? This will undo the file moves.')) {
        return;
    }
    
    showLoading('Rolling back plan...');
    
    try {
        const response = await fetch(`${API_BASE}/api/plans/${planId}/rollback`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Rollback result:', result);
        
        showSuccessMessage(`Plan rolled back successfully! Restored ${result.files_restored || 0} files`);
        
        // Refresh plans
        await loadPlans();
        
    } catch (error) {
        console.error('Rollback error:', error);
        showErrorMessage(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Show loading overlay
 */
function showLoading(message) {
    const overlay = document.getElementById('loading-overlay');
    const messageEl = document.getElementById('loading-message');
    messageEl.textContent = message || 'Loading...';
    overlay.classList.remove('hidden');
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('hidden');
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    showToast(message, 'success');
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    showToast(message, 'error');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close" aria-label="Close notification">×</button>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Close button handler
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        toast.classList.add('toast-hiding');
        setTimeout(() => toast.remove(), 300);
    });
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('toast-hiding');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('toast-visible');
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Auto-scan button
    const autoScanBtn = document.getElementById('auto-scan-btn');
    if (autoScanBtn) {
        autoScanBtn.addEventListener('click', autoScan);
    }
    
    // Manual scan button
    const scanBtn = document.getElementById('scan-btn');
    if (scanBtn) {
        scanBtn.addEventListener('click', () => {
            const path = document.getElementById('folder-path').value;
            manualScan(path);
        });
    }
    
    // Allow Enter key in folder path input
    const folderPathInput = document.getElementById('folder-path');
    if (folderPathInput) {
        folderPathInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const path = folderPathInput.value;
                manualScan(path);
            }
        });
    }
    
    // Refresh plans button
    const refreshBtn = document.getElementById('refresh-plans-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadPlans);
    }
    
    // Quick folder chips
    const chips = document.querySelectorAll('.folder-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', (e) => {
            const folder = e.target.dataset.folder;
            
            // Construct path based on OS
            const home = getHomePath();
            const fullPath = `${home}/${folder}`;
            
            // Set input value
            const input = document.getElementById('folder-path');
            if (input) {
                input.value = fullPath;
            }
            
            // Trigger scan
            manualScan(fullPath);
        });
    });
}

/**
 * Get home directory path based on OS
 */
function getHomePath() {
    // Try to detect OS from user agent
    const platform = navigator.platform.toLowerCase();
    
    if (platform.includes('win')) {
        // Windows - use typical path
        return 'C:\\Users\\' + (getUsername() || 'YourName');
    } else {
        // Unix-like (Linux, macOS)
        return '~';
    }
}

/**
 * Try to get username (not reliable, fallback to generic)
 */
function getUsername() {
    // This is a placeholder - browser can't reliably get username
    // Server should expand ~ to actual home directory
    return null;
}

/**
 * Load and display performance metrics (observability)
 */
async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics`);
        
        if (!response.ok) {
            console.warn('Metrics not available');
            return;
        }
        
        const metrics = await response.json();
        console.log('Performance Metrics:', metrics);
        
        // Display in console for now (future: dashboard)
        console.table({
            'Total Scans': metrics.scans_total,
            'Avg Files/Scan': metrics.avg_files_per_scan,
            'Plans Created': metrics.plans_created,
            'Plans Approved': metrics.plans_approved,
            'Plans Rolled Back': metrics.plans_rolled_back,
            'Total Files Organized': metrics.files_organized_total
        });
        
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

// Load metrics on page load (for observability)
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadMetrics, 2000); // Load after 2 seconds
});
