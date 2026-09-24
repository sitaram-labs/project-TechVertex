# 🌱 Surplus-to-Shelter: Real-Time Food Rescue Routing Engine

> **Built for AmiHacks Track A (Social Impact / NGO)**  
> *Connecting urban food surplus to local shelters within critical safety windows.*

---

## 📌 Problem Statement
Over **1.3 billion tons** of food are wasted globally every year, while millions of urban shelter residents experience food insecurity. A key challenge is that prepared food from caterers, bakeries, and corporate dining facilities has a short shelf-life safety window (**2–6 hours**). Traditional manual coordination is too slow, causing good meals to end up in landfills.

---

## 🚀 The Solution
**Surplus-to-Shelter** is a real-time geo-spatial matching and dispatch engine designed to rescue surplus meals before they spoil. 

### Key Features
1. 🗺️ **Live Urban Dispatch Map:** Interactive Google Maps dark-mode tracking real-time locations of Donors, Shelters, and Active Delivery Volunteers.
2. ⚡ **Smart Matching Algorithm:** Uses the **Haversine Distance Formula** combined with real-time urgency scoring (shelf-life, fridge availability, and current shelter capacity).
3. 🏠 **Shelter Capacity Dashboard:** Shelters manage meal intake capacity and claim incoming donations with a single click.
4. 🚚 **Driver Rescue Dispatch:** Volunteer drivers view active routes, claim dispatch tasks, and mark deliveries complete.
5. 📈 **ESG & Sustainability Analytics:** Calculates food weight saved, total servings delivered, financial tax value saved, and CO₂e emissions prevented ($1 \text{ kg food} = 1.9 \text{ kg } CO_2e$).
6. ⚡ **Hackathon Stream Demo Mode:** Inject simulated live food events instantly to demo algorithm execution to judges.

---

## 🛠️ Tech Stack
* **Backend:** Python 3.x, Flask, RESTful API, python-dotenv
* **Frontend:** HTML5, Modern CSS3 (Glassmorphism & CSS Variables), Vanilla JS (ES6+)
* **Mapping:** Google Maps JavaScript API (Dark Theme, SVG Markers, InfoWindows, Route Polylines)

---

## 🏃 How to Run the App

1. **Clone the repo & enter project directory:**
   ```bash
   cd "project TechVertex"
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and set your Google Maps API Key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```env
   GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key_here
   ```

4. **Start the Flask server:**
   ```bash
   python app.py
   ```

4. **Open in Browser:**
   Go to [`http://127.0.0.1:5000`](http://127.0.0.1:5000)

---

## 📽️ Demo Pitch Script (2-Minute Hackathon Presentation)

1. **[0:00 - 0:30] Hook & Problem:** Introduce the issue of food waste vs. hunger in urban areas and why time-sensitivity (2-6 hours) breaks traditional manual logistics.
2. **[0:30 - 1:15] Live Demo:** 
   * Click **`⚡ Hackathon Stream Demo`** to show live simulation.
   * Watch the map fly smoothly to the new donor pin and display a toast alert.
   * Click **`⚡ Find Match`** on active food posting to showcase the distance & capacity scoring algorithm.
   * Select a shelter and show the dashed yellow route vector appear live on the map.
3. **[1:15 - 1:45] Impact Dashboard:** Switch to **ESG Impact** tab to show live carbon & tax savings.
4. **[1:45 - 2:00] Conclusion:** Future scope (IoT cold-chain tracking, scale across cities).
