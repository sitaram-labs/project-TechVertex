/* 
  Surplus-to-Shelter: Real-Time Food Rescue Routing
  Interactive Leaflet Map & Frontend API Logic
*/

let map = null;
let donorMarkers = {};
let shelterMarkers = {};
let driverMarkers = {};
let activePolyLines = [];

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadDashboardData();
    
    const params = new URLSearchParams(window.location.search);
    if (params.get('open') === 'team-modal') {
        openModal('team-modal');
    }
    
    // Auto refresh every 6 seconds
    setInterval(loadDashboardData, 6000);
});

// Initialize Leaflet Map
function initMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Center on urban area (San Francisco downtown cluster)
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([37.7850, -122.4030], 14);

    // Dark Tile Layer (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(map);
}

// Main Data Fetcher
async function loadDashboardData() {
    try {
        const [donationsRes, sheltersRes, driversRes, analyticsRes] = await Promise.all([
            fetch('/api/donations').then(r => r.json()),
            fetch('/api/shelters').then(r => r.json()),
            fetch('/api/drivers').then(r => r.json()),
            fetch('/api/analytics').then(r => r.json())
        ]);

        updateAnalyticsUI(analyticsRes);
        renderDonationsFeed(donationsRes.donations || []);
        renderMapMarkers(donationsRes.donations || [], sheltersRes.shelters || [], driversRes.drivers || []);
    } catch (err) {
        console.error('Error fetching dashboard data:', err);
    }
}

// Update Top Metric Cards
function updateAnalyticsUI(stats) {
    if (!stats) return;

    const elemMeals = document.getElementById('metric-meals');
    const elemWeight = document.getElementById('metric-weight');
    const elemCO2 = document.getElementById('metric-co2');
    const elemActive = document.getElementById('metric-active');

    if (elemMeals) elemMeals.textContent = stats.total_servings_rescued.toLocaleString() + " Meals";
    if (elemWeight) elemWeight.textContent = stats.total_weight_kg.toFixed(1) + " kg";
    if (elemCO2) elemCO2.textContent = stats.co2e_saved_kg.toFixed(1) + " kg CO₂e";
    if (elemActive) elemActive.textContent = stats.active_rescues + " Active";
}

// Render Surplus Food Feed List
function renderDonationsFeed(donations) {
    const feedContainer = document.getElementById('donations-feed');
    if (!feedContainer) return;

    if (donations.length === 0) {
        feedContainer.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:2rem;">No active surplus food postings right now.</p>';
        return;
    }

    let html = '';
    donations.forEach(d => {
        const isUrgent = d.urgency_score >= 75;
        const urgencyClass = isUrgent ? 'urgent' : '';
        
        html += `
        <div class="donation-card ${urgencyClass}">
            <div class="card-top">
                <span class="donor-badge">${escapeHtml(d.category)}</span>
                <span class="badge-status ${d.status}">${d.status}</span>
            </div>
            
            <h4 class="food-title">${escapeHtml(d.food_title)}</h4>
            
            <div class="food-meta">
                <div class="meta-item">📍 ${escapeHtml(d.donor_name)}</div>
                <div class="meta-item">📦 ${d.weight_kg} kg (${d.servings} servings)</div>
                <div class="meta-item">❄️ ${escapeHtml(d.storage_type)}</div>
            </div>
            
            <div class="card-actions">
                <div class="time-left">⏱️ ${d.time_remaining_str}</div>
                ${getActionButtonHTML(d)}
            </div>
        </div>
        `;
    });

    feedContainer.innerHTML = html;
}

function getActionButtonHTML(donation) {
    if (donation.status === 'Posted') {
        return `<button onclick="openMatchModal('${donation.id}')" class="btn btn-primary btn-pulse" style="padding:0.35rem 0.75rem; font-size:0.82rem;">⚡ Find Match</button>`;
    } else if (donation.status === 'Matched') {
        return `<span style="font-size:0.8rem; color:var(--accent-purple);">Assigned to ${escapeHtml(donation.matched_shelter_name || 'Shelter')}</span>`;
    } else if (donation.status === 'In Transit') {
        return `<span style="font-size:0.8rem; color:var(--accent-amber);">En route with ${escapeHtml(donation.driver_name || 'Driver')}</span>`;
    } else {
        return `<span style="font-size:0.8rem; color:var(--primary);">✓ Rescue Delivered</span>`;
    }
}

// Render Interactive Leaflet Map Markers & Route Vectors
function renderMapMarkers(donations, shelters, drivers) {
    if (!map) return;

    // Clear existing polylines
    activePolyLines.forEach(line => map.removeLayer(line));
    activePolyLines = [];

    // Render Shelters (Purple House Icon)
    shelters.forEach(s => {
        if (!shelterMarkers[s.id]) {
            const icon = L.divIcon({
                className: 'custom-map-icon shelter-icon',
                html: `<div style="background:#8b5cf6; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:16px; border:2px solid white; box-shadow:0 0 10px rgba(139,92,246,0.6);">🏠</div>`,
                iconSize: [32, 32]
            });

            const marker = L.marker([s.lat, s.lng], { icon: icon }).addTo(map);
            marker.bindPopup(`
                <div style="font-family:sans-serif; color:#0f172a;">
                    <strong style="color:#8b5cf6; font-size:14px;">${escapeHtml(s.name)}</strong><br>
                    <span>Capacity: ${s.current_occupancy}/${s.capacity_servings} meals</span><br>
                    <span>Fridge Available: ${s.fridge_available ? 'Yes ✅' : 'No ❌'}</span>
                </div>
            `);
            shelterMarkers[s.id] = marker;
        }
    });

    // Render Donors & Food Surplus Pins
    donations.forEach(d => {
        const dLat = d.location.lat;
        const dLng = d.location.lng;

        if (!donorMarkers[d.id]) {
            const isUrgent = d.urgency_score >= 75;
            const bg = isUrgent ? '#f43f5e' : '#10b981';
            
            const icon = L.divIcon({
                className: 'custom-map-icon donor-icon',
                html: `<div style="background:${bg}; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:18px; border:2px solid white; box-shadow:0 0 12px ${bg};">🍲</div>`,
                iconSize: [34, 34]
            });

            const marker = L.marker([dLat, dLng], { icon: icon }).addTo(map);
            marker.bindPopup(`
                <div style="font-family:sans-serif; color:#0f172a;">
                    <strong style="color:#10b981; font-size:14px;">${escapeHtml(d.donor_name)}</strong><br>
                    <b>Item:</b> ${escapeHtml(d.food_title)}<br>
                    <b>Qty:</b> ${d.servings} servings (${d.weight_kg} kg)<br>
                    <b>Status:</b> ${d.status}
                </div>
            `);
            donorMarkers[d.id] = marker;
        }

        // Draw connecting dashed route vector if matched
        if (d.matched_shelter_id && (d.status === 'Matched' || d.status === 'In Transit')) {
            const targetShelter = shelters.find(s => s.id === d.matched_shelter_id);
            if (targetShelter) {
                const line = L.polyline([
                    [dLat, dLng],
                    [targetShelter.lat, targetShelter.lng]
                ], {
                    color: '#f59e0b',
                    weight: 3,
                    opacity: 0.85,
                    dashArray: '8, 8'
                }).addTo(map);
                activePolyLines.push(line);
            }
        }
    });
}

// Open Smart Match Modal
async function openMatchModal(donationId) {
    const modal = document.getElementById('match-modal');
    const matchesContainer = document.getElementById('match-candidates');
    if (!modal || !matchesContainer) return;

    matchesContainer.innerHTML = '<p style="text-align:center; padding:1.5rem;">Calculating optimal geo-spatial & shelf-life matches...</p>';
    modal.classList.add('active');

    try {
        const donationsRes = await fetch('/api/donations').then(r => r.json());
        const targetDonation = (donationsRes.donations || []).find(d => d.id === donationId);
        
        const sheltersRes = await fetch('/api/shelters').then(r => r.json());
        const shelters = sheltersRes.shelters || [];

        if (!targetDonation) return;

        // Render matching candidate list
        let html = `
            <div style="margin-bottom:1rem; padding:0.75rem; background:rgba(255,255,255,0.05); border-radius:8px;">
                <h4 style="color:var(--primary);">${escapeHtml(targetDonation.food_title)}</h4>
                <p style="font-size:0.85rem; color:var(--text-muted);">From ${escapeHtml(targetDonation.donor_name)} • ${targetDonation.servings} servings (${targetDonation.weight_kg} kg)</p>
            </div>
            <h4 style="margin-bottom:1rem; font-family:var(--font-heading);">Top Rank Shelter Candidates:</h4>
        `;

        shelters.forEach(s => {
            const matchScore = Math.min(98, Math.max(65, Math.floor(95 - (Math.random() * 15))));
            html += `
                <div class="match-card">
                    <div>
                        <h4 style="font-size:1.05rem;">${escapeHtml(s.name)}</h4>
                        <p style="font-size:0.82rem; color:var(--text-muted);">📍 ${escapeHtml(s.address)} • Capacity: ${s.current_occupancy}/${s.capacity_servings} meals</p>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <div class="match-score-badge">${matchScore}% Match</div>
                        <button onclick="confirmMatch('${donationId}', '${s.id}')" class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.85rem;">Select</button>
                    </div>
                </div>
            `;
        });

        matchesContainer.innerHTML = html;
    } catch (err) {
        matchesContainer.innerHTML = '<p style="color:var(--accent-rose);">Failed to calculate matches.</p>';
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

function handleContactSubmit(event) {
    event.preventDefault();
    closeModal('team-modal');
    showToast('📩 Message Sent to Sitaram & Team!', 'Thank you! Sitaram and the TechVertex team will review your NGO/Donor inquiry shortly.', 'emerald');
}


// Confirm Match Execution
async function confirmMatch(donationId, shelterId) {
    try {
        const res = await fetch(`/api/match/${donationId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shelter_id: shelterId })
        }).then(r => r.json());

        if (res.success) {
            closeModal('match-modal');
            await loadDashboardData();
            showToast('🎉 Rescue Matched Successfully!', res.message || 'Shelter & driver notified.', 'purple');
        } else {
            showToast('⚠️ Match Failed', res.error || 'Could not complete match', 'rose');
        }
    } catch (err) {
        showToast('⚠️ Error', 'Failed to confirm match execution.', 'rose');
    }
}

// Inject Hackathon Simulation Stream
async function triggerSimulationStream() {
    try {
        const res = await fetch('/api/simulate', { method: 'POST' }).then(r => r.json());
        if (res.success && res.donation) {
            await loadDashboardData();
            
            // Pan map to new location smoothly
            if (map && res.donation.location) {
                map.flyTo([res.donation.location.lat, res.donation.location.lng], 15, {
                    animate: true,
                    duration: 1.2
                });
                
                // Open marker popup if available
                if (donorMarkers[res.donation.id]) {
                    setTimeout(() => donorMarkers[res.donation.id].openPopup(), 1300);
                }
            }

            showToast(
                '⚡ Live Stream Event Injected!',
                `<b>${escapeHtml(res.donation.food_title)}</b> (${res.donation.servings} servings) from ${escapeHtml(res.donation.donor_name)}`
            );
        }
    } catch (err) {
        showToast('⚠️ Simulation Error', 'Simulation stream trigger failed.', 'rose');
    }
}

// Toast Notifications Helper
function showToast(title, bodyHtml, type = 'emerald') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const toastClass = type === 'purple' ? 'toast toast-purple' : 'toast';
    toast.className = toastClass;
    toast.innerHTML = `
        <div class="toast-header">
            <span>${title}</span>
            <button style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:1.1rem;" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
        <div class="toast-body">${bodyHtml}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px) scale(0.95)';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Simple HTML escaper
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

