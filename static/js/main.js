/* 
  Surplus-to-Shelter: Real-Time Food Rescue Routing Engine
  Interactive Google Maps JS API, NGO Requests & Auth Engine
*/

let map = null;
let donorMarkers = {};
let shelterMarkers = {};
let ngoRequestMarkers = {};
let activePolyLines = [];
let activeInfoWindow = null;
let isMapInitialized = false;

let currentFeedTab = 'donations'; // 'donations' or 'ngo-requests'
let selectedRole = 'donor';

document.addEventListener('DOMContentLoaded', () => {
    initUserProfileNav();
    
    if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
        initMap();
    }
    loadDashboardData();
    
    const params = new URLSearchParams(window.location.search);
    if (params.get('open') === 'team-modal') {
        openModal('team-modal');
    } else if (params.get('open') === 'onboarding-modal') {
        openModal('onboarding-modal');
    }
    
    // Auto refresh every 6 seconds
    setInterval(loadDashboardData, 6000);
});

// User Profile & Saved Session Management
function getUserProfile() {
    try {
        const saved = localStorage.getItem('sts_user_profile');
        if (saved) return JSON.parse(saved);
    } catch (e) {}
    return {
        role: 'donor',
        name: 'TechVertex Kitchen',
        email: 'user@techvertex.org',
        address: 'Jaipur, Rajasthan, India',
        lat: 26.9180,
        lng: 75.8250
    };
}

function saveUserProfile(profile) {
    try {
        localStorage.setItem('sts_user_profile', JSON.stringify(profile));
    } catch (e) {}
    initUserProfileNav();
}

function initUserProfileNav() {
    const profile = getUserProfile();
    const navBadge = document.getElementById('nav-user-badge');
    if (navBadge) {
        let roleBadgeEmoji = '🍲';
        if (profile.role === 'shelter') roleBadgeEmoji = '🏠';
        if (profile.role === 'driver') roleBadgeEmoji = '🚚';

        navBadge.innerHTML = `
            <span>${roleBadgeEmoji} <b>${escapeHtml(profile.name)}</b></span>
            <span style="opacity:0.6; font-size:0.75rem;">(${profile.role.toUpperCase()})</span>
        `;
    }
}

// Location & Profile Setup Modal Handler
function completeWizard(event) {
    event.preventDefault();
    const roleElem = document.getElementById('wiz-role');
    const roleVal = roleElem ? roleElem.value : 'donor';

    const profile = {
        role: roleVal,
        name: document.getElementById('wiz-name').value || 'Food Rescue Partner',
        address: document.getElementById('wiz-address').value || 'Jaipur, Rajasthan, India',
        lat: 26.9124,
        lng: 75.7873
    };

    saveUserProfile(profile);
    closeModal('onboarding-modal');
    showToast('👋 Profile Updated!', `Saved profile as <b>${escapeHtml(profile.name)}</b> (${profile.role.toUpperCase()})`, 'emerald');
}

// Google Maps Auth Failure Handler
window.gm_authFailure = function() {
    const mapElement = document.getElementById('map');
    if (mapElement) {
        showMapErrorState(mapElement, "Invalid API Key or Billing Disabled");
    }
};

// Helper SVG Marker Icon Generator for Google Maps
function getSvgMarkerIcon(bgColor, emojiText) {
    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
        <circle cx="18" cy="18" r="15" fill="${bgColor}" stroke="#ffffff" stroke-width="2"/>
        <text x="18" y="23" font-size="16" text-anchor="middle" dominant-baseline="middle" fill="#ffffff">${emojiText}</text>
    </svg>`;
    return {
        url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg),
        scaledSize: new google.maps.Size(36, 36),
        anchor: new google.maps.Point(18, 18)
    };
}

// Initialize Google Map
window.initMap = function initMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    if (isMapInitialized && map) return;

    if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
        console.warn('Google Maps API script not loaded or API key missing.');
        showMapErrorState(mapElement);
        return;
    }

    const darkMapStyle = [
        { "elementType": "geometry", "stylers": [{ "color": "#181f2a" }] },
        { "elementType": "labels.text.fill", "stylers": [{ "color": "#94a3b8" }] },
        { "elementType": "labels.text.stroke", "stylers": [{ "color": "#0f172a" }] },
        { "featureType": "administrative.locality", "elementType": "labels.text.fill", "stylers": [{ "color": "#cbd5e1" }] },
        { "featureType": "poi", "elementType": "labels.text.fill", "stylers": [{ "color": "#10b981" }] },
        { "featureType": "poi.park", "elementType": "geometry", "stylers": [{ "color": "#112229" }] },
        { "featureType": "poi.park", "elementType": "labels.text.fill", "stylers": [{ "color": "#64748b" }] },
        { "featureType": "road", "elementType": "geometry", "stylers": [{ "color": "#1e293b" }] },
        { "featureType": "road", "elementType": "geometry.stroke", "stylers": [{ "color": "#0f172a" }] },
        { "featureType": "road", "elementType": "labels.text.fill", "stylers": [{ "color": "#94a3b8" }] },
        { "featureType": "road.highway", "elementType": "geometry", "stylers": [{ "color": "#334155" }] },
        { "featureType": "transit", "elementType": "geometry", "stylers": [{ "color": "#1e293b" }] },
        { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#0b131e" }] },
        { "featureType": "water", "elementType": "labels.text.fill", "stylers": [{ "color": "#475569" }] }
    ];

    try {
        map = new google.maps.Map(mapElement, {
            center: { lat: 26.9124, lng: 75.7873 },
            zoom: 13,
            styles: darkMapStyle,
            disableDefaultUI: false,
            zoomControl: true,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: true
        });
        isMapInitialized = true;
        loadDashboardData();
    } catch (e) {
        console.error("Failed to initialize Google Maps:", e);
        showMapErrorState(mapElement);
    }
};

function showMapErrorState(mapElement, message = "Configure GOOGLE_MAPS_API_KEY in your .env file") {
    mapElement.innerHTML = `
        <div style="display:flex; height:100%; min-height:350px; align-items:center; justify-content:center; flex-direction:column; background:#0f172a; color:#94a3b8; text-align:center; padding:1.5rem; border-radius:12px;">
            <span style="font-size:2.5rem; margin-bottom:0.5rem;">🗺️</span>
            <strong style="color:white; font-size:1.15rem; margin-bottom:0.5rem;">Google Maps Integration Active</strong>
            <p style="font-size:0.88rem; max-width:360px; line-height:1.5; color:#cbd5e1; margin-bottom:1rem;">
                ${escapeHtml(message)}
            </p>
            <span style="font-size:0.75rem; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); padding:0.4rem 0.8rem; border-radius:6px; color:#10b981;">
                Key variable: <code>GOOGLE_MAPS_API_KEY</code>
            </span>
        </div>`;
}

// Main Data Fetcher
async function loadDashboardData() {
    try {
        const [donationsRes, sheltersRes, driversRes, ngoReqsRes, analyticsRes] = await Promise.all([
            fetch('/api/donations').then(r => r.json()),
            fetch('/api/shelters').then(r => r.json()),
            fetch('/api/drivers').then(r => r.json()),
            fetch('/api/ngo-requests').then(r => r.json()),
            fetch('/api/analytics').then(r => r.json())
        ]);

        updateAnalyticsUI(analyticsRes);

        if (currentFeedTab === 'donations') {
            renderDonationsFeed(donationsRes.donations || []);
        } else {
            renderNgoRequestsFeed(ngoReqsRes.requests || []);
        }

        renderMapMarkers(
            donationsRes.donations || [],
            sheltersRes.shelters || [],
            driversRes.drivers || [],
            ngoReqsRes.requests || []
        );
    } catch (err) {
        console.error('Error fetching dashboard data:', err);
    }
}

// Switch Feed View Tab (Surplus Food vs NGO Requests)
function switchFeedTab(tabName) {
    currentFeedTab = tabName;
    const btnDonations = document.getElementById('tab-btn-donations');
    const btnNgo = document.getElementById('tab-btn-ngo');

    if (tabName === 'donations') {
        if (btnDonations) btnDonations.classList.add('active');
        if (btnNgo) btnNgo.classList.remove('active');
    } else {
        if (btnNgo) btnNgo.classList.add('active');
        if (btnDonations) btnDonations.classList.remove('active');
    }

    loadDashboardData();
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

// Render Live NGO Requests Feed
function renderNgoRequestsFeed(requests) {
    const feedContainer = document.getElementById('donations-feed');
    if (!feedContainer) return;

    if (requests.length === 0) {
        feedContainer.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:2rem;">No open NGO food requests right now.</p>';
        return;
    }

    let html = '';
    requests.forEach(r => {
        const isOpen = r.status === 'Open';
        
        html += `
        <div class="ngo-req-card">
            <div class="ngo-req-header">
                <span class="ngo-req-title">📋 ${escapeHtml(r.ngo_name)}</span>
                <span class="badge-status ${r.status}">${r.status}</span>
            </div>
            <div style="font-size:0.9rem; color:var(--primary); font-weight:600; margin-bottom:0.4rem;">
                Needs: ${r.servings_needed} servings of ${escapeHtml(r.category)}
            </div>
            <div class="ngo-req-meta">
                <span>📍 ${escapeHtml(r.address)}</span>
                <span>⏱️ Urgency: Within ${r.urgency_hours} hrs</span>
                <span>📞 ${escapeHtml(r.contact_person)}</span>
            </div>
            <p style="font-size:0.83rem; color:var(--text-muted); margin-bottom:0.75rem; background:rgba(0,0,0,0.2); padding:0.4rem 0.6rem; border-radius:6px;">
                "${escapeHtml(r.notes || 'Direct food request for community shelter guests.')}"
            </p>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.78rem; color:var(--text-dim);">Posted recently</span>
                ${isOpen ? `<button onclick="openFulfillNgoModal('${r.id}', '${escapeHtml(r.ngo_name)}', '${escapeHtml(r.category)}', ${r.servings_needed})" class="btn btn-primary btn-pulse" style="padding:0.35rem 0.75rem; font-size:0.82rem;">🍲 Fulfill with Surplus</button>` : `<span style="font-size:0.8rem; color:var(--primary);">✓ Fulfilled by ${escapeHtml(r.fulfilled_by || 'Restaurant')}</span>`}
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

// Render Interactive Google Maps Markers & Route Vectors
function renderMapMarkers(donations, shelters, drivers, ngoRequests = []) {
    if (!map || typeof google === 'undefined' || typeof google.maps === 'undefined') return;

    // Clear existing polylines
    activePolyLines.forEach(line => line.setMap(null));
    activePolyLines = [];

    const userProfile = getUserProfile();

    // Render Shelters (Purple House Icon)
    shelters.forEach(s => {
        if (!shelterMarkers[s.id]) {
            const icon = getSvgMarkerIcon('#8b5cf6', '🏠');

            const marker = new google.maps.Marker({
                position: { lat: s.lat, lng: s.lng },
                map: map,
                icon: icon,
                title: s.name
            });

            const contentString = `
                <div style="font-family:sans-serif; color:#0f172a; padding:4px;">
                    <strong style="color:#8b5cf6; font-size:14px;">${escapeHtml(s.name)}</strong><br>
                    <span>Capacity: ${s.current_occupancy}/${s.capacity_servings} meals</span><br>
                    <span>Fridge Available: ${s.fridge_available ? 'Yes ✅' : 'No ❌'}</span>
                </div>
            `;
            const infoWindow = new google.maps.InfoWindow({ content: contentString });

            marker.addListener('click', () => {
                if (activeInfoWindow) activeInfoWindow.close();
                infoWindow.open(map, marker);
                activeInfoWindow = infoWindow;
            });

            shelterMarkers[s.id] = { marker, infoWindow };
        }
    });

    // Render NGO Live Food Requests Pins (Glowing Blue Document Pins)
    ngoRequests.forEach(req => {
        if (!ngoRequestMarkers[req.id]) {
            const bg = req.status === 'Open' ? '#3b82f6' : '#64748b';
            const icon = getSvgMarkerIcon(bg, '📋');

            const marker = new google.maps.Marker({
                position: { lat: req.lat, lng: req.lng },
                map: map,
                icon: icon,
                title: req.ngo_name
            });

            const contentString = `
                <div style="font-family:sans-serif; color:#0f172a; padding:6px; max-width:240px;">
                    <strong style="color:#3b82f6; font-size:14px; display:block; margin-bottom:4px;">📋 ${escapeHtml(req.ngo_name)}</strong>
                    <span style="font-size:12px; color:#475569;">📍 ${escapeHtml(req.address)}</span><br>
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; color:#1d4ed8; font-weight:600; font-size:12px; padding:4px 8px; border-radius:4px; margin:6px 0;">
                        Needs: ${req.servings_needed} servings of ${escapeHtml(req.category)}
                    </div>
                    <span style="font-size:11px; color:#64748b;">Urgency: Within ${req.urgency_hours} hrs</span><br>
                    ${req.status === 'Open' ? `
                        <button onclick="openFulfillNgoModal('${req.id}', '${escapeHtml(req.ngo_name)}', '${escapeHtml(req.category)}', ${req.servings_needed})" 
                                style="margin-top:8px; width:100%; background:#10b981; color:white; border:none; padding:6px 12px; border-radius:6px; font-weight:600; cursor:pointer; font-size:12px;">
                            🍲 Fulfill Request with Surplus Food
                        </button>` : `
                        <div style="margin-top:6px; color:#10b981; font-weight:600; font-size:12px;">
                            ✓ Fulfilled by ${escapeHtml(req.fulfilled_by || 'Restaurant')}
                        </div>`}
                </div>
            `;
            const infoWindow = new google.maps.InfoWindow({ content: contentString });

            marker.addListener('click', () => {
                if (activeInfoWindow) activeInfoWindow.close();
                infoWindow.open(map, marker);
                activeInfoWindow = infoWindow;
            });

            ngoRequestMarkers[req.id] = { marker, infoWindow };
        }
    });

    // Render Donors & Food Surplus Pins
    donations.forEach(d => {
        const dLat = d.location.lat;
        const dLng = d.location.lng;

        if (!donorMarkers[d.id]) {
            const isUrgent = d.urgency_score >= 75;
            const bg = isUrgent ? '#f43f5e' : '#10b981';
            const icon = getSvgMarkerIcon(bg, '🍲');

            const marker = new google.maps.Marker({
                position: { lat: dLat, lng: dLng },
                map: map,
                icon: icon,
                title: d.donor_name
            });

            const contentString = `
                <div style="font-family:sans-serif; color:#0f172a; padding:4px;">
                    <strong style="color:#10b981; font-size:14px;">${escapeHtml(d.donor_name)}</strong><br>
                    <b>Item:</b> ${escapeHtml(d.food_title)}<br>
                    <b>Qty:</b> ${d.servings} servings (${d.weight_kg} kg)<br>
                    <b>Status:</b> ${d.status}
                </div>
            `;
            const infoWindow = new google.maps.InfoWindow({ content: contentString });

            marker.addListener('click', () => {
                if (activeInfoWindow) activeInfoWindow.close();
                infoWindow.open(map, marker);
                activeInfoWindow = infoWindow;
            });

            donorMarkers[d.id] = { marker, infoWindow };
        }

        // Draw connecting route vector if matched
        if (d.matched_shelter_id && (d.status === 'Matched' || d.status === 'In Transit')) {
            const targetShelter = shelters.find(s => s.id === d.matched_shelter_id);
            if (targetShelter) {
                const line = new google.maps.Polyline({
                    path: [
                        { lat: dLat, lng: dLng },
                        { lat: targetShelter.lat, lng: targetShelter.lng }
                    ],
                    geodesic: true,
                    strokeColor: '#f59e0b',
                    strokeOpacity: 0.85,
                    strokeWeight: 3,
                    map: map
                });
                activePolyLines.push(line);
            }
        }
    });
}

// Fulfill NGO Request Modal Launcher
function openFulfillNgoModal(reqId, ngoName, category, servings) {
    const profile = getUserProfile();
    const modal = document.getElementById('fulfill-ngo-modal');
    if (!modal) return;

    document.getElementById('fulfill-req-id').value = reqId;
    document.getElementById('fulfill-target-title').textContent = `Send Food to ${ngoName}`;
    document.getElementById('fulfill-target-meta').textContent = `Target request: ${servings} servings of ${category}`;
    document.getElementById('fulfill-donor-name').value = profile.name || 'TechVertex Kitchen';
    
    modal.classList.add('active');
}

async function handleFulfillSubmit(event) {
    event.preventDefault();
    const reqId = document.getElementById('fulfill-req-id').value;
    const donorName = document.getElementById('fulfill-donor-name').value;
    const foodTitle = document.getElementById('fulfill-food-title').value;

    try {
        const res = await fetch(`/api/ngo-requests/${reqId}/fulfill`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ donor_name: donorName, food_title: foodTitle })
        }).then(r => r.json());

        if (res.success) {
            closeModal('fulfill-ngo-modal');
            await loadDashboardData();
            showToast('🎉 NGO Request Fulfilled!', res.message || 'Surplus food matched & driver dispatched.', 'emerald');
        } else {
            showToast('⚠️ Error', res.error || 'Could not fulfill request', 'rose');
        }
    } catch (err) {
        showToast('⚠️ Error', 'Failed to send food fulfillment.', 'rose');
    }
}

// NGO Post Food Request Form Handler
async function handleNgoPostSubmit(event) {
    event.preventDefault();
    const profile = getUserProfile();

    const data = {
        ngo_name: document.getElementById('ngo-req-name').value || profile.name,
        contact_person: document.getElementById('ngo-req-person').value || 'NGO Coordinator',
        contact_phone: document.getElementById('ngo-req-phone').value || '+1 (555) 234-5678',
        category: document.getElementById('ngo-req-category').value,
        servings_needed: parseInt(document.getElementById('ngo-req-servings').value || 50),
        urgency_hours: parseFloat(document.getElementById('ngo-req-hours').value || 3.0),
        address: document.getElementById('ngo-req-address').value || profile.address,
        lat: parseFloat(document.getElementById('ngo-req-lat').value || profile.lat),
        lng: parseFloat(document.getElementById('ngo-req-lng').value || profile.lng),
        notes: document.getElementById('ngo-req-notes').value
    };

    try {
        const res = await fetch('/api/ngo-requests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(r => r.json());

        if (res.success) {
            closeModal('ngo-request-modal');
            switchFeedTab('ngo-requests');
            await loadDashboardData();
            
            // Pan map to new NGO request location
            if (map && res.request) {
                map.panTo({ lat: res.request.lat, lng: res.request.lng });
                map.setZoom(15);
            }
            
            showToast('📋 NGO Food Request Published!', 'Your request pin is now visible on Google Maps for nearby restaurants to fulfill.', 'purple');
        }
    } catch (err) {
        showToast('⚠️ Error', 'Failed to post NGO food request.', 'rose');
    }
}

// Step-Wise Onboarding Wizard Logic
function selectWizardRole(role) {
    selectedRole = role;
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
                map.panTo({ lat: res.donation.location.lat, lng: res.donation.location.lng });
                map.setZoom(15);
                
                // Open marker popup if available
                const item = donorMarkers[res.donation.id];
                if (item && item.infoWindow && item.marker) {
                    setTimeout(() => {
                        if (activeInfoWindow) activeInfoWindow.close();
                        item.infoWindow.open(map, item.marker);
                        activeInfoWindow = item.infoWindow;
                    }, 1300);
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
