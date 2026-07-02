console.log("SentinelMind Dashboard loaded");

async function fetchDashboardData() {
    const totalEl = document.getElementById("stat-total");
    const criticalEl = document.getElementById("stat-critical");
    const highEl = document.getElementById("stat-high");
    const mediumEl = document.getElementById("stat-medium");
    const lowEl = document.getElementById("stat-low");
    const tbodyEl = document.getElementById("incidents-tbody");

    try {
        const response = await fetch("http://127.0.0.1:8000/incidents");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 1. Update Metrics
        if (data.stats) {
            totalEl.textContent = data.stats.total || 0;
            criticalEl.textContent = data.stats.critical || 0;
            highEl.textContent = data.stats.high || 0;
            mediumEl.textContent = data.stats.medium || 0;
            lowEl.textContent = data.stats.low || 0;
        }

        // 2. Render Incident Table Rows
        tbodyEl.innerHTML = "";

        if (!data.incidents || data.incidents.length === 0) {
            tbodyEl.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: var(--text-muted);">
                        No incidents logged.
                    </td>
                </tr>
            `;
            return;
        }

        data.incidents.forEach(incident => {
            const tr = document.createElement("tr");

            // Format severity class name
            const severityClass = incident.severity ? incident.severity.toLowerCase() : "low";

            tr.innerHTML = `
                <td style="font-family: var(--font-mono); color: var(--text-muted); font-size: 0.8rem;">
                    #${incident.id}
                </td>
                <td style="font-weight: 500; color: var(--text-primary);">
                    ${escapeHtml(incident.title)}
                </td>
                <td style="color: var(--text-secondary);">
                    ${escapeHtml(incident.system || '—')}
                </td>
                <td style="color: var(--text-secondary);">
                    ${escapeHtml(incident.category || '—')}
                </td>
                <td>
                    <span class="severity-badge severity-${severityClass}">
                        ${escapeHtml(incident.severity || 'Low')}
                    </span>
                </td>
            `;

            tbodyEl.appendChild(tr);
        });

    } catch (err) {
        console.error("Error fetching dashboard data:", err);
        tbodyEl.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; color: #ff6b6b; font-weight: 500;">
                    Failed to fetch dashboard data. Make sure the backend server is running.
                </td>
            </tr>
        `;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Fetch data on page load
document.addEventListener("DOMContentLoaded", fetchDashboardData);

async function searchMemory() {
    const queryInput = document.getElementById("search-query");
    const searchBtn = document.getElementById("search-btn");
    const resultsContainer = document.getElementById("search-results");

    const query = queryInput.value.trim();
    if (!query) {
        resultsContainer.innerHTML = `
            <p style="text-align: center; color: #ff6b6b; font-size: 0.85rem; padding: 1rem 0;">
                Please enter a search query.
            </p>
        `;
        return;
    }

    // Set loading state
    queryInput.disabled = true;
    searchBtn.disabled = true;
    searchBtn.textContent = "Searching...";
    resultsContainer.innerHTML = `
        <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; padding: 1rem 0;">
            ⏳ Searching organizational memory...
        </p>
    `;

    try {
        const response = await fetch(`http://127.0.0.1:8000/incident/similar?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.count === 0) {
            resultsContainer.innerHTML = `
                <p style="text-align: center; color: var(--text-muted); font-size: 0.85rem; padding: 1rem 0;">
                    No similar incidents found in organizational memory.
                </p>
            `;
            return;
        }

        let html = `
            <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem; font-weight: 500;">
                Found ${data.count} similar incident${data.count === 1 ? '' : 's'}:
            </p>
        `;

        data.incidents.forEach(incident => {
            const severityClass = incident.severity ? incident.severity.toLowerCase() : "low";
            const recommendationHtml = incident.recommendation ? `
                <div class="recommendation" style="margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-primary); border-left: 2px solid var(--accent); padding-left: 10px; background: rgba(255, 255, 255, 0.02);">
                    <span style="font-weight: 600; text-transform: uppercase; font-size: 0.7rem; color: var(--text-muted); display: block; margin-bottom: 0.25rem;">Recommendation</span>
                    ${escapeHtml(incident.recommendation)}
                </div>
            ` : '';

            const systemHtml = incident.system ? `
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.25rem;">
                    <b>Affected System:</b> ${escapeHtml(incident.system)}
                </p>
            ` : '';

            html += `
                <div class="memory-card" style="margin-bottom: 1rem; animation: fadeUp 0.3s ease-out both;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; gap: 1rem;">
                        <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin: 0;">
                            ${escapeHtml(incident.title)}
                        </h4>
                        <span class="severity-badge severity-${severityClass}">
                            ${escapeHtml(incident.severity || 'Low')}
                        </span>
                    </div>
                    ${systemHtml}
                    <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem; line-height: 1.5;">
                        ${escapeHtml(incident.description)}
                    </p>
                    ${recommendationHtml}
                </div>
            `;
        });

        resultsContainer.innerHTML = html;

    } catch (err) {
        console.error("Error searching memory:", err);
        resultsContainer.innerHTML = `
            <p style="text-align: center; color: #ff6b6b; font-size: 0.85rem; padding: 1rem 0; font-weight: 500;">
                Failed to search organizational memory. Make sure the backend server is running.
            </p>
        `;
    } finally {
        queryInput.disabled = false;
        searchBtn.disabled = false;
        searchBtn.textContent = "Search ⌕";
    }
}

