// Event Analytics Dashboard - Enterprise Script v3.0
// Features: Theme toggle, search, sort, animations, export

let analysisData = null;
let charts = {};
let sortDirection = {};

// Professional color palette matching the new CSS design system
const chartColors = {
    primary: 'rgba(99, 102, 241, 0.9)',      // Brand indigo
    secondary: 'rgba(139, 92, 246, 0.9)',    // Brand purple
    tertiary: 'rgba(59, 130, 246, 0.9)',     // Brand blue
    quaternary: 'rgba(168, 85, 247, 0.9)',   // Violet
    success: 'rgba(34, 197, 94, 0.9)',       // Success green
    warning: 'rgba(245, 158, 11, 0.9)',      // Warning amber
    danger: 'rgba(239, 68, 68, 0.9)',        // Danger red
    neutral: 'rgba(113, 113, 122, 0.6)',     // Zinc
    palette: [
        'rgba(99, 102, 241, 0.85)',
        'rgba(139, 92, 246, 0.85)',
        'rgba(59, 130, 246, 0.85)',
        'rgba(168, 85, 247, 0.85)',
        'rgba(34, 197, 94, 0.85)',
        'rgba(245, 158, 11, 0.85)',
        'rgba(236, 72, 153, 0.85)',
        'rgba(20, 184, 166, 0.85)'
    ]
};

// Chart.js global defaults for dark theme
Chart.defaults.color = '#a1a1aa';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard v3.0 Loading...');
    loadAnalysisResults();
});

function animateCounter(element, target, duration, prefix, suffix) {
    duration = duration || 1000;
    prefix = prefix || '';
    suffix = suffix || '';
    var start = 0;
    var startTime = performance.now();
    
    function update(currentTime) {
        var elapsed = currentTime - startTime;
        var progress = Math.min(elapsed / duration, 1);
        var easeProgress = 1 - Math.pow(1 - progress, 3);
        var current = Math.floor(start + (target - start) * easeProgress);
        element.textContent = prefix + current.toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

async function loadAnalysisResults() {
    try {
        var response = await fetch('data/analysis_results.json');
        if (!response.ok) {
            hideLoadingOverlay();
            showInstructions();
            return;
        }
        
        analysisData = await response.json();
        console.log('Data loaded', analysisData);
        
        updateOrgInfo(analysisData.org_name);
        updateExecutiveSummary(analysisData.data_summary);
        updateQuickStats(analysisData.data_summary);
        updateHeaderStats(analysisData.data_summary);
        updateFinancialKPIs(analysisData.data_summary);
        updateInsights(analysisData.ai_insights);
        createCharts(analysisData.data_summary);
        updatePredictions(analysisData.predictions);
        updateEventsTable(analysisData.data_summary.events);
        updateDemographics(analysisData.demographics);
        updateYoYComparison(analysisData.data_summary.events);
        updateFooter(analysisData);
        updateTimestamp(analysisData.timestamp);
        
        hideLoadingOverlay();
    } catch (error) {
        console.error('Error:', error);
        hideLoadingOverlay();
        showInstructions();
    }
}

function hideLoadingOverlay() {
    var overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('hidden');
}

function showInstructions() {
    document.getElementById('aiInsights').innerHTML = '<div class="loading"><div class="spinner"></div><p>No data found. Run: python src/analyzer.py</p></div>';
    document.getElementById('executiveSummary').textContent = 'Run analysis to generate insights';
}

function updateOrgInfo(orgName) {
    if (orgName) {
        document.getElementById('orgName').textContent = orgName;
        document.title = orgName + ' | Event Analytics';
    }
}

function updateExecutiveSummary(summary) {
    var best = summary.best_performing_event || 'N/A';
    var text = summary.total_events + ' events analyzed with ' + summary.total_attendees.toLocaleString() + ' attendees. ';
    text += 'Overall rate: ' + summary.attendance_rate.toFixed(1) + '%. ';
    text += 'Top performer: ' + best + ' (' + summary.best_conversion_rate.toFixed(1) + '%).';
    document.getElementById('executiveSummary').textContent = text;
}

function updateQuickStats(summary) {
    animateCounter(document.getElementById('quickEvents'), summary.total_events, 800);
    animateCounter(document.getElementById('quickAttendees'), summary.total_attendees, 1200);
    document.getElementById('quickRate').textContent = summary.attendance_rate.toFixed(1) + '%';
    document.getElementById('rateBar').style.width = summary.attendance_rate + '%';
    if (summary.total_budget) {
        document.getElementById('quickBudget').textContent = formatCurrency(summary.total_budget);
    }
}

function updateHeaderStats(summary) {
    animateCounter(document.getElementById('totalEvents'), summary.total_events, 800);
    animateCounter(document.getElementById('totalAttendees'), summary.total_attendees, 1200);
    animateCounter(document.getElementById('avgAttendance'), Math.round(summary.avg_attendance), 1000);
    animateCounter(document.getElementById('attendanceRate'), Math.round(summary.attendance_rate), 1000, '', '%');
    
    var progressBar = document.getElementById('attendanceProgress');
    if (progressBar) progressBar.style.width = summary.attendance_rate + '%';
    
    if (summary.date_range) document.getElementById('dateRange').textContent = summary.date_range;
}

function updateFinancialKPIs(summary) {
    if (summary.total_budget) {
        document.getElementById('financialKpis').style.display = 'grid';
        document.getElementById('totalBudget').textContent = formatCurrency(summary.total_budget);
        document.getElementById('costPerAttendee').textContent = formatCurrency(summary.cost_per_attendee);
        document.getElementById('avgBudgetEvent').textContent = formatCurrency(summary.avg_budget_per_event);
    }
    if (summary.best_performing_event) {
        document.getElementById('bestEvent').textContent = summary.best_performing_event;
    }
}

function formatCurrency(amount) {
    if (amount >= 1000) return '$' + (amount / 1000).toFixed(1) + 'K';
    return '$' + amount.toFixed(0);
}

function updateInsights(insights) {
    var html = insights
        .replace(/\*\*(.*?)\*\*/g, '<strong>\</strong>')
        .replace(/### (.*)/g, '<h4>\</h4>')
        .replace(/## (.*)/g, '<h3>\</h3>')
        .replace(/# (.*)/g, '<h2>\</h2>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n- /g, '</li><li>');
    html = '<p>' + html + '</p>';
    document.getElementById('aiInsights').innerHTML = html;
}

function toggleInsights() {
    var card = document.getElementById('aiInsights');
    var btn = document.getElementById('insightsToggle');
    card.classList.toggle('collapsed');
    var icon = btn.querySelector('i');
    icon.className = card.classList.contains('collapsed') ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
}

function toggleTheme() {
    var html = document.documentElement;
    var btn = document.getElementById('themeBtn');
    var icon = btn.querySelector('i');
    if (html.getAttribute('data-theme') === 'light') {
        html.setAttribute('data-theme', 'dark');
        icon.className = 'fas fa-moon';
    } else {
        html.setAttribute('data-theme', 'light');
        icon.className = 'fas fa-sun';
    }
}

function refreshDashboard() {
    var btn = document.getElementById('refreshBtn');
    btn.querySelector('i').classList.add('fa-spin');
    setTimeout(function() {
        location.reload();
    }, 500);
}

function scrollToInsights() {
    document.getElementById('insightsSection').scrollIntoView({ behavior: 'smooth' });
}

function createCharts(summary) {
    createEventTypeChart(summary);
    createAttendanceTimeChart(summary);
    createExpectedVsActualChart(summary);
    createAttendanceRateChart(summary);
}

function createEventTypeChart(summary) {
    var ctx = document.getElementById('eventTypeChart').getContext('2d');
    var types = Object.keys(summary.event_types);
    var counts = Object.values(summary.event_types);
    charts.eventType = new Chart(ctx, {
        type: 'bar',
        data: { labels: types, datasets: [{ data: counts, backgroundColor: chartColors.palette.slice(0, types.length), borderRadius: 6 }] },
        options: { responsive: true, plugins: { legend: { display: false } }, animation: { duration: 1000 }, scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.5)' } }, x: { ticks: { color: '#94a3b8' }, grid: { display: false } } } }
    });
}

function createAttendanceTimeChart(summary) {
    var ctx = document.getElementById('attendanceTimeChart').getContext('2d');
    var events = summary.events.slice().sort(function(a, b) { return new Date(a.date) - new Date(b.date); });
    charts.attendanceTime = new Chart(ctx, {
        type: 'line',
        data: { labels: events.map(function(e) { return e.name; }), datasets: [{ label: 'Attendance', data: events.map(function(e) { return e.actual; }), borderColor: 'rgba(59,130,246,1)', backgroundColor: 'rgba(59,130,246,0.1)', tension: 0.4, fill: true, borderWidth: 3, pointRadius: 6 }] },
        options: { responsive: true, animation: { duration: 1200 }, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { maxRotation: 45, color: '#94a3b8' }, grid: { display: false } }, y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.5)' } } } }
    });
}

function createExpectedVsActualChart(summary) {
    var ctx = document.getElementById('expectedVsActualChart').getContext('2d');
    var events = summary.events.slice(0, 10);
    charts.expectedVsActual = new Chart(ctx, {
        type: 'bar',
        data: { labels: events.map(function(e) { return e.name; }), datasets: [{ label: 'Expected', data: events.map(function(e) { return e.expected; }), backgroundColor: chartColors.neutral, borderRadius: 4 }, { label: 'Actual', data: events.map(function(e) { return e.actual; }), backgroundColor: chartColors.success, borderRadius: 4 }] },
        options: { responsive: true, animation: { duration: 1000 }, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { x: { ticks: { maxRotation: 45, color: '#94a3b8' }, grid: { display: false } }, y: { beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.5)' } } } }
    });
}

function createAttendanceRateChart(summary) {
    var ctx = document.getElementById('attendanceRateChart').getContext('2d');
    var events = summary.events.slice().sort(function(a, b) { return b.attendance_rate - a.attendance_rate; });
    var colors = events.map(function(e) { return e.attendance_rate >= 85 ? chartColors.success : e.attendance_rate >= 75 ? chartColors.warning : chartColors.quaternary; });
    charts.attendanceRate = new Chart(ctx, {
        type: 'bar',
        data: { labels: events.map(function(e) { return e.name; }), datasets: [{ data: events.map(function(e) { return e.attendance_rate; }), backgroundColor: colors, borderRadius: 6 }] },
        options: { indexAxis: 'y', responsive: true, animation: { duration: 1000 }, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.5)' } }, y: { ticks: { color: '#94a3b8' }, grid: { display: false } } } }
    });
}

function updateDemographics(demographics) {
    if (!demographics || Object.keys(demographics).length === 0) return;
    document.getElementById('demographicsSection').style.display = 'block';
    var ctx = document.getElementById('demographicsChart').getContext('2d');
    var labels = Object.keys(demographics);
    var values = Object.values(demographics);
    charts.demographics = new Chart(ctx, {
        type: 'doughnut',
        data: { labels: labels, datasets: [{ data: values, backgroundColor: chartColors.palette, borderWidth: 2, borderColor: '#1e293b' }] },
        options: { responsive: true, animation: { duration: 1200 }, plugins: { legend: { position: 'right', labels: { color: '#94a3b8', padding: 15 } } } }
    });
    var total = values.reduce(function(a, b) { return a + b; }, 0);
    var html = '<div class="demo-stats-grid">';
    labels.forEach(function(label, i) {
        var pct = ((values[i] / total) * 100).toFixed(1);
        html += '<div class="demo-stat-card"><div class="demo-stat-label">' + label + '</div><div class="demo-stat-value">' + values[i].toLocaleString() + '</div><div class="demo-stat-pct">' + pct + '%</div></div>';
    });
    html += '</div>';
    document.getElementById('demographicsStats').innerHTML = html;
}

function updateYoYComparison(events) {
    if (!events || events.length < 2) return;
    
    // Find recurring events (same base name, different years)
    var eventGroups = {};
    events.forEach(function(event) {
        // Extract base name by removing year patterns like "2024", "2025", "'24", "'25"
        var baseName = event.name.replace(/\s*(20\d{2}|'\d{2})\s*$/i, '').trim();
        if (!eventGroups[baseName]) eventGroups[baseName] = [];
        eventGroups[baseName].push(event);
    });
    
    // Filter to only recurring events (2+ occurrences)
    var comparisons = [];
    for (var name in eventGroups) {
        if (eventGroups[name].length >= 2) {
            // Sort by date
            var sorted = eventGroups[name].sort(function(a, b) {
                return new Date(a.date) - new Date(b.date);
            });
            // Compare most recent to previous
            comparisons.push({
                name: name,
                old: sorted[sorted.length - 2],
                new: sorted[sorted.length - 1]
            });
        }
    }
    
    if (comparisons.length === 0) return;
    
    // Show the section
    document.getElementById('yoySection').style.display = 'block';
    
    var html = '';
    comparisons.forEach(function(comp) {
        var oldYear = new Date(comp.old.date).getFullYear();
        var newYear = new Date(comp.new.date).getFullYear();
        
        // Calculate changes
        var attChange = comp.new.actual - comp.old.actual;
        var attPct = ((attChange / comp.old.actual) * 100).toFixed(1);
        var attClass = attChange > 0 ? 'positive' : attChange < 0 ? 'negative' : 'neutral';
        var attIcon = attChange > 0 ? 'arrow-up' : attChange < 0 ? 'arrow-down' : 'minus';
        
        var rateChange = (comp.new.attendance_rate - comp.old.attendance_rate).toFixed(1);
        var rateClass = parseFloat(rateChange) > 0 ? 'positive' : parseFloat(rateChange) < 0 ? 'negative' : 'neutral';
        var rateIcon = parseFloat(rateChange) > 0 ? 'arrow-up' : parseFloat(rateChange) < 0 ? 'arrow-down' : 'minus';
        
        html += '<div class="yoy-card">';
        html += '<div class="yoy-event-name"><i class="fas fa-repeat"></i> ' + comp.name + '</div>';
        html += '<div class="yoy-metrics">';
        
        // Attendance comparison
        html += '<div class="yoy-metric">';
        html += '<span class="yoy-metric-label">Attendance</span>';
        html += '<div class="yoy-metric-values">';
        html += '<span class="yoy-old">' + oldYear + ': ' + comp.old.actual + '</span>';
        html += '<span class="yoy-arrow"><i class="fas fa-arrow-right"></i></span>';
        html += '<span class="yoy-new">' + newYear + ': ' + comp.new.actual + '</span>';
        html += '<span class="yoy-change ' + attClass + '"><i class="fas fa-' + attIcon + '"></i> ' + (attChange > 0 ? '+' : '') + attPct + '%</span>';
        html += '</div></div>';
        
        // Rate comparison
        html += '<div class="yoy-metric">';
        html += '<span class="yoy-metric-label">Conversion Rate</span>';
        html += '<div class="yoy-metric-values">';
        html += '<span class="yoy-old">' + comp.old.attendance_rate.toFixed(1) + '%</span>';
        html += '<span class="yoy-arrow"><i class="fas fa-arrow-right"></i></span>';
        html += '<span class="yoy-new">' + comp.new.attendance_rate.toFixed(1) + '%</span>';
        html += '<span class="yoy-change ' + rateClass + '"><i class="fas fa-' + rateIcon + '"></i> ' + (parseFloat(rateChange) > 0 ? '+' : '') + rateChange + 'pp</span>';
        html += '</div></div>';
        
        // Highlight
        html += '<div class="yoy-highlight">';
        html += '<div class="yoy-highlight-label">Year-over-Year Growth</div>';
        html += '<div class="yoy-highlight-value">' + (attChange > 0 ? '+' : '') + attChange + ' attendees</div>';
        html += '</div>';
        
        html += '</div></div>';
    });
    
    document.getElementById('yoyCards').innerHTML = html;
}

function updatePredictions(predictions) {
    var grid = document.getElementById('predictionsGrid');
    if (!predictions || Object.keys(predictions).length === 0) {
        grid.innerHTML = '<p class="loading">No predictions available</p>';
        return;
    }
    var html = '';
    for (var eventType in predictions) {
        var data = predictions[eventType];
        html += '<div class="prediction-card"><h4>' + eventType + '</h4>';
        html += '<div class="prediction-stat">Predicted: <strong>' + Math.round(data.avg_attendance) + '</strong></div>';
        html += '<div class="prediction-stat">Rate: <strong>' + data.attendance_rate.toFixed(1) + '%</strong></div>';
        if (data.avg_cost_per_attendee) html += '<div class="prediction-stat">Cost: <strong>$' + data.avg_cost_per_attendee.toFixed(2) + '</strong></div>';
        html += '<div class="prediction-meta">Based on ' + data.sample_size + ' events</div></div>';
    }
    grid.innerHTML = html;
}

function updateEventsTable(events) {
    var tbody = document.getElementById('eventsTableBody');
    if (!events || events.length === 0) return;
    var sorted = events.slice().sort(function(a, b) { return new Date(b.date) - new Date(a.date); });
    var html = '';
    sorted.forEach(function(event) {
        var rateClass = event.attendance_rate >= 85 ? 'rate-high' : event.attendance_rate >= 75 ? 'rate-mid' : 'rate-low';
        var date = new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        html += '<tr><td class="event-name">' + event.name + '</td><td>' + date + '</td><td><span class="event-type-badge">' + event.type + '</span></td><td>' + event.expected.toLocaleString() + '</td><td>' + event.actual.toLocaleString() + '</td><td><span class="rate-badge ' + rateClass + '">' + event.attendance_rate.toFixed(1) + '%</span></td></tr>';
    });
    tbody.innerHTML = html;
    document.getElementById('tableInfo').textContent = 'Showing ' + sorted.length + ' events';
}

function updateFooter(data) {
    document.getElementById('footerEvents').textContent = data.data_summary.total_events;
    document.getElementById('footerAttendees').textContent = data.data_summary.total_attendees.toLocaleString();
}

function updateTimestamp(timestamp) {
    var date = new Date(timestamp);
    document.getElementById('lastUpdated').textContent = date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function filterTable() {
    var input = document.getElementById('tableSearch').value.toLowerCase();
    var rows = document.querySelectorAll('#eventsTableBody tr');
    var visible = 0;
    rows.forEach(function(row) {
        var text = row.textContent.toLowerCase();
        if (text.indexOf(input) > -1) {
            row.style.display = '';
            visible++;
        } else {
            row.style.display = 'none';
        }
    });
    document.getElementById('tableInfo').textContent = 'Showing ' + visible + ' of ' + rows.length + ' events';
}

function sortTable(colIndex) {
    var table = document.getElementById('eventsTable');
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    sortDirection[colIndex] = !sortDirection[colIndex];
    rows.sort(function(a, b) {
        var aVal = a.cells[colIndex].textContent.trim();
        var bVal = b.cells[colIndex].textContent.trim();
        if (colIndex === 3 || colIndex === 4) {
            aVal = parseInt(aVal.replace(/,/g, ''));
            bVal = parseInt(bVal.replace(/,/g, ''));
        } else if (colIndex === 5) {
            aVal = parseFloat(aVal);
            bVal = parseFloat(bVal);
        }
        if (sortDirection[colIndex]) return aVal > bVal ? 1 : -1;
        return aVal < bVal ? 1 : -1;
    });
    rows.forEach(function(row) { tbody.appendChild(row); });
}

function exportData() {
    if (!analysisData) { alert('No data'); return; }
    var blob = new Blob([JSON.stringify(analysisData, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'analytics_' + new Date().toISOString().split('T')[0] + '.json';
    a.click();
    URL.revokeObjectURL(url);
}

function exportTableCSV() {
    if (!analysisData) { alert('No data'); return; }
    var events = analysisData.data_summary.events;
    var csv = 'Event,Date,Type,Expected,Actual,Rate\n';
    events.forEach(function(e) {
        csv += '"' + e.name + '",' + e.date + ',"' + e.type + '",' + e.expected + ',' + e.actual + ',' + e.attendance_rate.toFixed(1) + '%\n';
    });
    var blob = new Blob([csv], { type: 'text/csv' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'events_' + new Date().toISOString().split('T')[0] + '.csv';
    a.click();
    URL.revokeObjectURL(url);
}
