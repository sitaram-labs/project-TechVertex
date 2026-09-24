"""
Surplus-to-Shelter: Real-Time Food Rescue Routing Engine
Built with Python & Flask for AmiHacks Track A (NGO / Social Impact)
"""

import math
import os
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# Google Maps API Key Configuration
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("MAPS_API_KEY", "")

@app.context_processor
def inject_google_maps_api_key():
    return dict(google_maps_api_key=GOOGLE_MAPS_API_KEY)


# ==========================================
# IN-MEMORY DATA STORE (Simulated Database)
# ==========================================

SHELTERS = [
    {
        "id": "shelter_1",
        "name": "Apna Ghar Ashram Jaipur",
        "address": "Mansarovar, Jaipur, Rajasthan, India",
        "lat": 26.8500,
        "lng": 75.7700,
        "capacity_servings": 150,
        "current_occupancy": 45,
        "fridge_available": True,
        "accepts_categories": ["Prepared Meals", "Bakery", "Produce", "Dairy", "Packaged"],
        "contact_phone": "+91 94140 12345",
        "contact_person": "Rameshwar Prasad"
    },
    {
        "id": "shelter_2",
        "name": "Akshaya Patra Foundation Jaipur",
        "address": "Jagatpura, Jaipur, Rajasthan, India",
        "lat": 26.8150,
        "lng": 75.8350,
        "capacity_servings": 300,
        "current_occupancy": 120,
        "fridge_available": True,
        "accepts_categories": ["Prepared Meals", "Produce", "Packaged"],
        "contact_phone": "+91 98290 54321",
        "contact_person": "Govind Das"
    },
    {
        "id": "shelter_3",
        "name": "Rajasthan Mahila Kalyan Mandal",
        "address": "Ajmer Road, Jaipur, Rajasthan, India",
        "lat": 26.8900,
        "lng": 75.7500,
        "capacity_servings": 100,
        "current_occupancy": 30,
        "fridge_available": False,
        "accepts_categories": ["Bakery", "Produce", "Packaged"],
        "contact_phone": "+91 94133 67890",
        "contact_person": "Sunita Sharma"
    }
]

DRIVERS = [
    {
        "id": "driver_1",
        "name": "Ramesh Sharma",
        "vehicle_type": "Tata Ace EV Cargo Van",
        "phone": "+91 98280 11223",
        "lat": 26.9100,
        "lng": 75.7900,
        "status": "Available"
    },
    {
        "id": "driver_2",
        "name": "Priya Verma",
        "vehicle_type": "Mahindra Supro Refrigerated Van",
        "phone": "+91 94141 33445",
        "lat": 26.8800,
        "lng": 75.8100,
        "status": "Available"
    },
    {
        "id": "driver_3",
        "name": "Vikram Singh",
        "vehicle_type": "Electric Cargo Auto",
        "phone": "+91 98299 55667",
        "lat": 26.9200,
        "lng": 75.8200,
        "status": "Available"
    }
]

DONATIONS = [
    {
        "id": "don_101",
        "donor_name": "LMB (Laxmi Misthan Bhandar)",
        "food_title": "Fresh Paneer Sabzi, Dal Baati & Chapati Trays",
        "category": "Prepared Meals",
        "weight_kg": 25.0,
        "servings": 60,
        "storage_type": "Heated Container",
        "location": {
            "address": "Johari Bazar, Jaipur, Rajasthan, India",
            "lat": 26.9180,
            "lng": 75.8250
        },
        "created_at": (datetime.now() - timedelta(minutes=25)).isoformat(),
        "expiry_hours": 3.0,
        "notes": "Freshly prepared for evening lunch event, pristine condition in hot insulated boxes.",
        "status": "Posted",
        "matched_shelter_id": None,
        "matched_shelter_name": None,
        "driver_id": None,
        "driver_name": None,
        "photo_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "don_102",
        "donor_name": "Rawat Misthan Bhandar",
        "food_title": "Surplus Pyaaz Kachori & Fresh Breads",
        "category": "Bakery",
        "weight_kg": 15.0,
        "servings": 40,
        "storage_type": "Ambient",
        "location": {
            "address": "Station Road, Jaipur, Rajasthan, India",
            "lat": 26.9230,
            "lng": 75.7970
        },
        "created_at": (datetime.now() - timedelta(minutes=45)).isoformat(),
        "expiry_hours": 5.0,
        "notes": "Fresh morning batch, packed in clean food-grade boxes.",
        "status": "Matched",
        "matched_shelter_id": "shelter_1",
        "matched_shelter_name": "Apna Ghar Ashram Jaipur",
        "driver_id": "driver_1",
        "driver_name": "Ramesh Sharma",
        "photo_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "don_103",
        "donor_name": "Chokhi Dhani Resort & Restaurant",
        "food_title": "Fresh Apples, Milk Cartons & Seasonal Fruits",
        "category": "Produce",
        "weight_kg": 30.0,
        "servings": 75,
        "storage_type": "Refrigerated",
        "location": {
            "address": "Tonk Road, Jaipur, Rajasthan, India",
            "lat": 26.7750,
            "lng": 75.8300
        },
        "created_at": (datetime.now() - timedelta(hours=1, minutes=10)).isoformat(),
        "expiry_hours": 8.0,
        "notes": "Fresh farm produce, refrigerated and ready for instant distribution.",
        "status": "Delivered",
        "matched_shelter_id": "shelter_2",
        "matched_shelter_name": "Akshaya Patra Foundation Jaipur",
        "driver_id": "driver_2",
        "driver_name": "Priya Verma",
        "photo_url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=500&q=80"
    }
]

RESCUE_HISTORY = [
    {
        "rescue_id": "res_8801",
        "donor_name": "Chokhi Dhani Resort & Restaurant",
        "shelter_name": "Akshaya Patra Foundation Jaipur",
        "driver_name": "Priya Verma",
        "weight_kg": 30.0,
        "servings": 75,
        "delivered_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "co2e_saved_kg": round(30.0 * 1.9, 2)
    }
]

NGO_REQUESTS = [
    {
        "id": "req_501",
        "ngo_name": "Apna Ghar Ashram Jaipur",
        "contact_person": "Rameshwar Prasad",
        "contact_phone": "+91 94140 12345",
        "category": "Prepared Meals",
        "servings_needed": 80,
        "urgency_hours": 3.0,
        "address": "Mansarovar, Jaipur, Rajasthan, India",
        "lat": 26.8500,
        "lng": 75.7700,
        "notes": "Urgent dinner request for 80 resident elderly and homeless guests.",
        "status": "Open",
        "created_at": (datetime.now() - timedelta(minutes=20)).isoformat(),
        "fulfilled_by": None,
        "food_title_fulfilled": None
    },
    {
        "id": "req_502",
        "ngo_name": "Akshaya Patra Foundation Jaipur",
        "contact_person": "Govind Das",
        "contact_phone": "+91 98290 54321",
        "category": "Produce",
        "servings_needed": 120,
        "urgency_hours": 5.0,
        "address": "Jagatpura, Jaipur, Rajasthan, India",
        "lat": 26.8150,
        "lng": 75.8350,
        "notes": "Fresh vegetables and fruits needed for evening community relief kitchen.",
        "status": "Open",
        "created_at": (datetime.now() - timedelta(minutes=40)).isoformat(),
        "fulfilled_by": None,
        "food_title_fulfilled": None
    }
]

# ==========================================
# HELPER MATH & MATCHING ENGINE LOGIC
# ==========================================

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         (math.sin(dlon / 2.0) ** 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_urgency_score(donation):
    try:
        created = datetime.fromisoformat(donation['created_at'])
    except Exception:
        created = datetime.now()
    
    elapsed_hours = (datetime.now() - created).total_seconds() / 3600.0
    total_hours = donation['expiry_hours']
    remaining_hours = max(0.1, total_hours - elapsed_hours)
    
    if remaining_hours <= 1.0:
        return 95.0
    elif remaining_hours <= 2.0:
        return 80.0
    elif remaining_hours <= 4.0:
        return 60.0
    else:
        return max(10.0, round(100.0 * (1.0 - (remaining_hours / total_hours)), 1))

def find_best_shelter_match(donation):
    donor_lat = donation['location']['lat']
    donor_lng = donation['location']['lng']
    category = donation['category']
    servings = donation['servings']
    requires_fridge = (donation['storage_type'] == 'Refrigerated')

    scored_matches = []

    for shelter in SHELTERS:
        remaining_cap = shelter['capacity_servings'] - shelter['current_occupancy']
        if remaining_cap < (servings * 0.5):
            continue

        if category not in shelter['accepts_categories']:
            continue

        if requires_fridge and not shelter['fridge_available']:
            continue

        dist_km = haversine_distance(donor_lat, donor_lng, shelter['lat'], shelter['lng'])
        proximity_score = max(0, 100 - (dist_km * 20))
        capacity_score = min(100, (remaining_cap / max(1, servings)) * 50)
        
        composite_score = round((proximity_score * 0.55) + (capacity_score * 0.45), 1)

        scored_matches.append({
            "shelter_id": shelter['id'],
            "shelter_name": shelter['name'],
            "address": shelter['address'],
            "distance_km": round(dist_km, 2),
            "estimated_drive_minutes": math.ceil(dist_km * 3.5) + 3,
            "match_score": composite_score,
            "available_capacity": remaining_cap
        })

    scored_matches.sort(key=lambda x: x['match_score'], reverse=True)
    return scored_matches

# ==========================================
# FLASK WEB ROUTES
# ==========================================
# FLASK WEB ROUTES
# ==========================================

@app.route('/')
@app.route('/login')
def login_portal():
    return render_template('login.html')

@app.route('/portal')
@app.route('/main')
def main_portal():
    return render_template('portal.html')

@app.route('/overview')
@app.route('/dashboard')
def overview_portal():
    return render_template('index.html')

@app.route('/donor')
def donor_portal():
    return render_template('donor.html')

@app.route('/shelter')
def shelter_portal():
    return render_template('shelter.html')

@app.route('/driver')
def driver_portal():
    return render_template('driver.html')

@app.route('/impact')
def impact_portal():
    return render_template('impact.html')

# ==========================================
# AUTHENTICATION & USER MANAGEMENT API
# ==========================================

USERS = [
    {
        "id": "usr_101",
        "email": "shelter@apnagharjaipur.org",
        "password": "password123",
        "role": "shelter",
        "name": "Apna Ghar Ashram Jaipur",
        "address": "Mansarovar, Jaipur, Rajasthan, India",
        "lat": 26.8500,
        "lng": 75.7700,
        "phone": "+91 94140 12345"
    },
    {
        "id": "usr_102",
        "email": "donor@lmbjaipur.in",
        "password": "password123",
        "role": "donor",
        "name": "LMB (Laxmi Misthan Bhandar)",
        "address": "Johari Bazar, Jaipur, Rajasthan, India",
        "lat": 26.9180,
        "lng": 75.8250,
        "phone": "+91 98290 12345"
    },
    {
        "id": "usr_103",
        "email": "driver@jaipurrescue.org",
        "password": "password123",
        "role": "driver",
        "name": "Ramesh Sharma",
        "address": "MI Road, Jaipur, Rajasthan, India",
        "lat": 26.9150,
        "lng": 75.8100,
        "phone": "+91 98280 11223"
    }
]

@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "donor")

    user = next((u for u in USERS if u["email"].lower() == email), None)
    if not user:
        user = {
            "id": f"usr_{int(time.time())}",
            "email": email or "user@techvertex.org",
            "password": password or "demo",
            "role": role,
            "name": data.get("name") or ("Food Rescue Partner" if role == "donor" else "Shelter Partner"),
            "address": data.get("address") or "San Francisco Downtown",
            "lat": float(data.get("lat") or 37.7870),
            "lng": float(data.get("lng") or -122.4000),
            "phone": data.get("phone") or "+1 (555) 000-1111"
        }
        USERS.append(user)

    return jsonify({
        "success": True,
        "message": "Authentication successful!",
        "user": user
    })

@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    
    if any(u["email"].lower() == email for u in USERS if email):
        return jsonify({"success": False, "error": "An account with this email address already exists."}), 400

    new_user = {
        "id": f"usr_{int(time.time())}",
        "email": email or f"user_{int(time.time())}@techvertex.org",
        "password": data.get("password", "password123"),
        "role": data.get("role", "donor"),
        "name": data.get("name", "New Food Rescue Partner"),
        "address": data.get("address", "San Francisco Downtown"),
        "lat": float(data.get("lat") or 37.7870),
        "lng": float(data.get("lng") or -122.4000),
        "phone": data.get("phone", "+1 (555) 000-1111")
    }
    USERS.append(new_user)
    
    return jsonify({
        "success": True,
        "message": "Account registered successfully!",
        "user": new_user
    }), 201

@app.route('/api/donations', methods=['GET', 'POST'])
def api_donations():
    if request.method == 'POST':
        data = request.json or {}
        new_donation = {
            "id": f"don_{int(time.time())}",
            "donor_name": data.get("donor_name", "Anonymous Food Business"),
            "food_title": data.get("food_title", "Surplus Edible Items"),
            "category": data.get("category", "Prepared Meals"),
            "weight_kg": float(data.get("weight_kg", 10.0)),
            "servings": int(data.get("servings", 20)),
            "storage_type": data.get("storage_type", "Ambient"),
            "location": {
                "address": data.get("address", "Financial District"),
                "lat": float(data.get("lat", 37.7870)),
                "lng": float(data.get("lng", -122.4000))
            },
            "created_at": datetime.now().isoformat(),
            "expiry_hours": float(data.get("expiry_hours", 3.0)),
            "notes": data.get("notes", ""),
            "status": "Posted",
            "matched_shelter_id": None,
            "matched_shelter_name": None,
            "driver_id": None,
            "driver_name": None,
            "photo_url": data.get("photo_url") or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80"
        }
        
        DONATIONS.insert(0, new_donation)
        matches = find_best_shelter_match(new_donation)
        top_match = matches[0] if matches else None
        
        return jsonify({
            "success": True,
            "message": "Surplus food donation posted successfully!",
            "donation": new_donation,
            "recommended_match": top_match
        }), 201

    enriched = []
    for d in DONATIONS:
        d_copy = dict(d)
        d_copy['urgency_score'] = compute_urgency_score(d)
        try:
            created = datetime.fromisoformat(d['created_at'])
            elapsed = (datetime.now() - created).total_seconds() / 3600.0
            remaining = max(0, d['expiry_hours'] - elapsed)
            hrs = int(remaining)
            mins = int((remaining - hrs) * 60)
            d_copy['time_remaining_str'] = f"{hrs}h {mins}m left"
        except Exception:
            d_copy['time_remaining_str'] = "2h 30m left"
            
        enriched.append(d_copy)

    return jsonify({"donations": enriched})

@app.route('/api/shelters', methods=['GET', 'POST'])
def api_shelters():
    if request.method == 'POST':
        data = request.json or {}
        shelter_id = data.get("shelter_id")
        for s in SHELTERS:
            if s["id"] == shelter_id:
                if "current_occupancy" in data:
                    s["current_occupancy"] = int(data["current_occupancy"])
                if "capacity_servings" in data:
                    s["capacity_servings"] = int(data["capacity_servings"])
                return jsonify({"success": True, "shelter": s})
        return jsonify({"success": False, "error": "Shelter not found"}), 404
        
    return jsonify({"shelters": SHELTERS})

@app.route('/api/drivers', methods=['GET'])
def api_drivers():
    return jsonify({"drivers": DRIVERS})

@app.route('/api/ngo-requests', methods=['GET', 'POST'])
def api_ngo_requests():
    if request.method == 'POST':
        data = request.json or {}
        new_req = {
            "id": f"req_{int(time.time())}",
            "ngo_name": data.get("ngo_name", "Local Food Bank / Shelter"),
            "contact_person": data.get("contact_person", "NGO Coordinator"),
            "contact_phone": data.get("contact_phone", "+1 (555) 000-1111"),
            "category": data.get("category", "Prepared Meals"),
            "servings_needed": int(data.get("servings_needed", 50)),
            "urgency_hours": float(data.get("urgency_hours", 4.0)),
            "address": data.get("address", "City Center"),
            "lat": float(data.get("lat", 37.7850)),
            "lng": float(data.get("lng", -122.4030)),
            "notes": data.get("notes", ""),
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "fulfilled_by": None,
            "food_title_fulfilled": None
        }
        NGO_REQUESTS.insert(0, new_req)
        return jsonify({"success": True, "message": "NGO Food Request posted successfully!", "request": new_req}), 201

    return jsonify({"requests": NGO_REQUESTS})

@app.route('/api/ngo-requests/<req_id>/fulfill', methods=['POST'])
def api_fulfill_ngo_request(req_id):
    data = request.json or {}
    donor_name = data.get("donor_name", "Partner Restaurant")
    food_title = data.get("food_title", "Surplus Meals")
    
    for req in NGO_REQUESTS:
        if req["id"] == req_id:
            req["status"] = "Fulfilled"
            req["fulfilled_by"] = donor_name
            req["food_title_fulfilled"] = food_title
            
            # Find matching shelter or add donation record
            new_donation = {
                "id": f"don_fulfill_{int(time.time())}",
                "donor_name": donor_name,
                "food_title": food_title,
                "category": req["category"],
                "weight_kg": round(req["servings_needed"] * 0.4, 1),
                "servings": req["servings_needed"],
                "storage_type": "Prepared",
                "location": {
                    "address": req["address"],
                    "lat": req["lat"],
                    "lng": req["lng"]
                },
                "created_at": datetime.now().isoformat(),
                "expiry_hours": 3.0,
                "notes": f"Directly matched & fulfilled to NGO Request #{req_id}",
                "status": "Matched",
                "matched_shelter_id": None,
                "matched_shelter_name": req["ngo_name"],
                "driver_id": "driver_1",
                "driver_name": "David Chen",
                "photo_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80"
            }
            DONATIONS.insert(0, new_donation)
            
            return jsonify({
                "success": True,
                "message": f"Successfully matched & sent surplus food to {req['ngo_name']}!",
                "request": req,
                "donation": new_donation
            })

    return jsonify({"success": False, "error": "NGO Request not found"}), 404

@app.route('/api/match/<donation_id>', methods=['POST'])
def api_trigger_match(donation_id):
    data = request.json or {}
    selected_shelter_id = data.get("shelter_id")

    for d in DONATIONS:
        if d["id"] == donation_id:
            matches = find_best_shelter_match(d)
            if not matches and not selected_shelter_id:
                return jsonify({"success": False, "error": "No suitable shelter match found."}), 400
            
            shelter_info = None
            if selected_shelter_id:
                shelter_info = next((s for s in SHELTERS if s["id"] == selected_shelter_id), None)
            elif matches:
                shelter_info = next((s for s in SHELTERS if s["id"] == matches[0]["shelter_id"]), None)

            if not shelter_info:
                return jsonify({"success": False, "error": "Invalid shelter target."}), 400

            available_driver = next((dr for dr in DRIVERS if dr["status"] == "Available"), DRIVERS[0])
            available_driver["status"] = "En Route"

            d["status"] = "Matched"
            d["matched_shelter_id"] = shelter_info["id"]
            d["matched_shelter_name"] = shelter_info["name"]
            d["driver_id"] = available_driver["id"]
            d["driver_name"] = available_driver["name"]

            return jsonify({
                "success": True,
                "message": f"Successfully matched with {shelter_info['name']}! Driver {available_driver['name']} dispatched.",
                "donation": d,
                "driver": available_driver,
                "shelter": shelter_info
            })

    return jsonify({"success": False, "error": "Donation not found"}), 404

@app.route('/api/status/<donation_id>', methods=['POST'])
def api_update_status(donation_id):
    data = request.json or {}
    new_status = data.get("status")

    for d in DONATIONS:
        if d["id"] == donation_id:
            d["status"] = new_status

            if new_status == "Delivered":
                if d["driver_id"]:
                    for dr in DRIVERS:
                        if dr["id"] == d["driver_id"]:
                            dr["status"] = "Available"
                
                if d["matched_shelter_id"]:
                    for s in SHELTERS:
                        if s["id"] == d["matched_shelter_id"]:
                            s["current_occupancy"] = min(s["capacity_servings"], s["current_occupancy"] + d["servings"])

                RESCUE_HISTORY.append({
                    "rescue_id": f"res_{int(time.time())}",
                    "donor_name": d["donor_name"],
                    "shelter_name": d.get("matched_shelter_name", "Local Shelter"),
                    "driver_name": d.get("driver_name", "Volunteer Driver"),
                    "weight_kg": d["weight_kg"],
                    "servings": d["servings"],
                    "delivered_at": datetime.now().isoformat(),
                    "co2e_saved_kg": round(d["weight_kg"] * 1.9, 2)
                })

            return jsonify({"success": True, "donation": d})

    return jsonify({"success": False, "error": "Donation not found"}), 404

@app.route('/api/simulate', methods=['POST'])
def api_simulate_donation():
    simulated_items = [
        {
            "donor": "Marriott Hotel Jaipur Banquet",
            "title": "Fresh Royal Buffet Veg Pulao & Paneer Curry",
            "category": "Prepared Meals",
            "weight": 35.0,
            "servings": 80,
            "storage": "Heated Container",
            "address": "Ashram Marg, Tonk Road, Jaipur, Rajasthan, India",
            "lat": 26.8520,
            "lng": 75.7950,
            "expiry": 2.5,
            "notes": "Post-wedding event surplus, untouched, hot insulated boxes ready for pickup.",
            "photo": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=500&q=80"
        },
        {
            "donor": "Handi Restaurant Jaipur",
            "title": "Fresh Tandoori Roti & Mixed Dal Trays",
            "category": "Prepared Meals",
            "weight": 20.0,
            "servings": 50,
            "storage": "Heated Container",
            "address": "MI Road, Jaipur, Rajasthan, India",
            "lat": 26.9160,
            "lng": 75.8120,
            "expiry": 3.0,
            "notes": "Freshly prepared dinner surplus, sealed hot boxes.",
            "photo": "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=500&q=80"
        }
    ]
    
    sample = simulated_items[int(time.time()) % len(simulated_items)]
    
    new_sim = {
        "id": f"don_sim_{int(time.time())}",
        "donor_name": sample["donor"],
        "food_title": sample["title"],
        "category": sample["category"],
        "weight_kg": sample["weight"],
        "servings": sample["servings"],
        "storage_type": sample["storage"],
        "location": {
            "address": sample["address"],
            "lat": sample["lat"],
            "lng": sample["lng"]
        },
        "created_at": datetime.now().isoformat(),
        "expiry_hours": sample["expiry"],
        "notes": sample["notes"],
        "status": "Posted",
        "matched_shelter_id": None,
        "matched_shelter_name": None,
        "driver_id": None,
        "driver_name": None,
        "photo_url": sample["photo"]
    }
    
    DONATIONS.insert(0, new_sim)
    matches = find_best_shelter_match(new_sim)
    top_match = matches[0] if matches else None
    
    return jsonify({
        "success": True,
        "message": "Live Hackathon Demo Stream: New surplus donation detected!",
        "donation": new_sim,
        "best_match": top_match
    })

@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    total_weight_kg = sum(d['weight_kg'] for d in DONATIONS if d['status'] in ['Matched', 'Picked Up', 'In Transit', 'Delivered']) + \
                      sum(h['weight_kg'] for h in RESCUE_HISTORY)
                      
    total_servings = sum(d['servings'] for d in DONATIONS if d['status'] in ['Matched', 'Picked Up', 'In Transit', 'Delivered']) + \
                     sum(h['servings'] for h in RESCUE_HISTORY)

    co2e_saved_kg = round(total_weight_kg * 1.9, 1)
    tax_deduction_value_usd = round(total_servings * 3.50, 2)
    
    active_donations_count = sum(1 for d in DONATIONS if d['status'] != 'Delivered')
    delivered_count = sum(1 for d in DONATIONS if d['status'] == 'Delivered') + len(RESCUE_HISTORY)
    
    categories = {}
    for d in DONATIONS:
        cat = d['category']
        categories[cat] = categories.get(cat, 0) + d['weight_kg']

    return jsonify({
        "total_weight_kg": round(total_weight_kg, 1),
        "total_servings_rescued": total_servings,
        "co2e_saved_kg": co2e_saved_kg,
        "financial_value_saved_usd": tax_deduction_value_usd,
        "active_rescues": active_donations_count,
        "completed_deliveries": delivered_count,
        "categories_breakdown": categories,
        "shelter_count": len(SHELTERS),
        "driver_count": len(DRIVERS)
    })

if __name__ == '__main__':
    print("Starting Surplus-to-Shelter Food Rescue Engine...")
    print("Local access: http://127.0.0.1:5000")
    print("Network access: http://0.0.0.0:5000 (Accessible to devices on the same Wi-Fi)")
    app.run(debug=True, host='0.0.0.0', port=5000)

