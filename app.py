"""
Surplus-to-Shelter: Real-Time Food Rescue Routing Engine
Built with Python & Flask for AmiHacks Track A (NGO / Social Impact)
"""

import math
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==========================================
# IN-MEMORY DATA STORE (Simulated Database)
# ==========================================

SHELTERS = [
    {
        "id": "shelter_1",
        "name": "Hope Haven Community Kitchen",
        "address": "452 Mission Street, Downtown",
        "lat": 37.7885,
        "lng": -122.4012,
        "capacity_servings": 120,
        "current_occupancy": 35,
        "fridge_available": True,
        "accepts_categories": ["Prepared Meals", "Bakery", "Produce", "Dairy", "Packaged"],
        "contact_phone": "+1 (555) 234-5678",
        "contact_person": "Sarah Jenkins"
    },
    {
        "id": "shelter_2",
        "name": "St. Vincent Rescue & Shelter",
        "address": "890 Howard St, South of Market",
        "lat": 37.7812,
        "lng": -122.4056,
        "capacity_servings": 200,
        "current_occupancy": 110,
        "fridge_available": True,
        "accepts_categories": ["Prepared Meals", "Produce", "Packaged"],
        "contact_phone": "+1 (555) 876-5432",
        "contact_person": "Marcus Vance"
    },
    {
        "id": "shelter_3",
        "name": "Grace Youth Horizon Center",
        "address": "1201 Pine St, Nob Hill",
        "lat": 37.7901,
        "lng": -122.4140,
        "capacity_servings": 75,
        "current_occupancy": 20,
        "fridge_available": False,
        "accepts_categories": ["Bakery", "Produce", "Packaged"],
        "contact_phone": "+1 (555) 345-6789",
        "contact_person": "Elena Rostova"
    }
]

DRIVERS = [
    {
        "id": "driver_1",
        "name": "David Chen",
        "vehicle_type": "Electric Cargo Van",
        "phone": "+1 (555) 444-1122",
        "lat": 37.7850,
        "lng": -122.4030,
        "status": "Available"
    },
    {
        "id": "driver_2",
        "name": "Maria Santos",
        "vehicle_type": "Hatchback (Refrigerated Box)",
        "phone": "+1 (555) 444-3344",
        "lat": 37.7890,
        "lng": -122.4100,
        "status": "Available"
    },
    {
        "id": "driver_3",
        "name": "Alex Johnson",
        "vehicle_type": "Bicycle Cargo Trailer",
        "phone": "+1 (555) 444-5566",
        "lat": 37.7820,
        "lng": -122.3980,
        "status": "Available"
    }
]

DONATIONS = [
    {
        "id": "don_101",
        "donor_name": "TechVertex Main Cafeteria",
        "food_title": "Tray-Sealed Lasagna & Salad Trays",
        "category": "Prepared Meals",
        "weight_kg": 18.5,
        "servings": 45,
        "storage_type": "Heated Container",
        "location": {
            "address": "500 Howard St, Suite 300",
            "lat": 37.7892,
            "lng": -122.3985
        },
        "created_at": (datetime.now() - timedelta(minutes=25)).isoformat(),
        "expiry_hours": 2.5,
        "notes": "Freshly prepared for corporate lunch event, pristine condition.",
        "status": "Posted",
        "matched_shelter_id": None,
        "matched_shelter_name": None,
        "driver_id": None,
        "driver_name": None,
        "photo_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "don_102",
        "donor_name": "Artisan Bakery & Co.",
        "food_title": "Surplus Sourdough & Croissants",
        "category": "Bakery",
        "weight_kg": 12.0,
        "servings": 30,
        "storage_type": "Ambient",
        "location": {
            "address": "780 Market St",
            "lat": 37.7865,
            "lng": -122.4045
        },
        "created_at": (datetime.now() - timedelta(minutes=45)).isoformat(),
        "expiry_hours": 5.0,
        "notes": "Baked this morning, packed in clean eco-bags.",
        "status": "Matched",
        "matched_shelter_id": "shelter_1",
        "matched_shelter_name": "Hope Haven Community Kitchen",
        "driver_id": "driver_1",
        "driver_name": "David Chen",
        "photo_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "don_103",
        "donor_name": "GreenGrocer Organic Market",
        "food_title": "Fresh Apples, Oranges & Leafy Greens",
        "category": "Produce",
        "weight_kg": 25.0,
        "servings": 60,
        "storage_type": "Refrigerated",
        "location": {
            "address": "325 4th St",
            "lat": 37.7830,
            "lng": -122.4010
        },
        "created_at": (datetime.now() - timedelta(hours=1, minutes=10)).isoformat(),
        "expiry_hours": 8.0,
        "notes": "Slight cosmetic flaws, 100% ripe and high nutritional value.",
        "status": "Delivered",
        "matched_shelter_id": "shelter_2",
        "matched_shelter_name": "St. Vincent Rescue & Shelter",
        "driver_id": "driver_2",
        "driver_name": "Maria Santos",
        "photo_url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=500&q=80"
    }
]

RESCUE_HISTORY = [
    {
        "rescue_id": "res_8801",
        "donor_name": "GreenGrocer Organic Market",
        "shelter_name": "St. Vincent Rescue & Shelter",
        "driver_name": "Maria Santos",
        "weight_kg": 25.0,
        "servings": 60,
        "delivered_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "co2e_saved_kg": round(25.0 * 1.9, 2)
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

@app.route('/')
def index():
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
# REST API ENDPOINTS FOR LEAFLET MAP & JS
# ==========================================

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
            "donor": "Grand Hyatt Hotel Banquet Hall",
            "title": "Fresh Buffet Roast Chicken & Grilled Veggies",
            "category": "Prepared Meals",
            "weight": 32.0,
            "servings": 75,
            "storage": "Heated Container",
            "address": "345 Stockton St",
            "lat": 37.7898,
            "lng": -122.4068,
            "expiry": 2.0,
            "notes": "Post-event surplus, untouched, insulated hot boxes ready for instant loading.",
            "photo": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=500&q=80"
        },
        {
            "donor": "Whole Foods Market Market St",
            "title": "Chilled Organic Yogurt & Fresh Milk Cartons",
            "category": "Dairy",
            "weight": 14.5,
            "servings": 35,
            "storage": "Refrigerated",
            "address": "1760 Market St",
            "lat": 37.7720,
            "lng": -122.4230,
            "expiry": 4.0,
            "notes": "Inventory overstock, sell-by date tomorrow, perfectly fresh cold chain intact.",
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

