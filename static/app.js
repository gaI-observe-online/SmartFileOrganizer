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
        console.log('Scan result:', plan);
        
        if (plan.status === 'empty') {
            showSuccessMessage(plan.message || 'No files found to organize');
        } else {
            showSuccessMessage(
                `Scan complete! Found ${plan.file_count} files, ${plan.reclaimable_mb.toFixed(2)} MB reclaimable`
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
    
    // Format plan ID (first 8 characters)
    const shortId = plan.id.toString().substring(0, 8);
    
    // Format timestamp
    const timestamp = new Date(plan.timestamp).toLocaleString();
    
    card.innerHTML = `
        <div class="plan-header">
            <span class="plan-id" title="${plan.id}">${shortId}</span>
            <span class="plan-status status-${plan.status}">${plan.status}</span>
        </div>
        <div class="plan-info">
            <p><strong>📁 Folder:</strong> ${escapeHtml(plan.root_path)}</p>
            <p style="font-size: 0.8rem; color: #a0aec0;">Created: ${timestamp}</p>
        </div>
        <div class="plan-metrics">
            <div class="metric">
                <span class="metric-label">Files</span>
                <span class="metric-value">📄 ${plan.file_count}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Space</span>
                <span class="metric-value">💾 ${plan.reclaimable_mb.toFixed(2)} MB</span>
            </div>
            <div class="metric">
                <span class="metric-label">Risk Level</span>
                <span class="metric-value risk-${plan.risk_level.toLowerCase()}">⚠️ ${plan.risk_level}</span>
            </div>
        </div>
        <div class="plan-actions">
            <button class="btn-success" onclick="approvePlan('${plan.id}')" ${plan.status !== 'pending' ? 'disabled' : ''}>
                ✅ Approve
            </button>
            <button class="btn-primary" onclick="executePlan('${plan.id}')" ${plan.status === 'executed' || plan.status === 'rolled_back' ? 'disabled' : ''}>
                ▶️ Execute
            </button>
            <button class="btn-warning" onclick="rollbackPlan('${plan.id}')" ${plan.status !== 'executed' ? 'disabled' : ''}>
                ↩️ Rollback
            </button>
        </div>
    `;
    
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
    alert('✅ ' + message);
    // TODO: Replace with toast notification in production
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    alert('❌ ' + message);
    // TODO: Replace with toast notification in production
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
