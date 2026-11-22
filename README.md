# ✦ Atmosphere Diary // ArtTech
> **An Interactive 3D Spatial Memory Atlas & Multimodal Emotional Journal**  
> Transform 2D photographs, feelings, dates, and music into walkable **3D Gaussian Splat (`.PLY`)** worlds pinned onto an interactive 3D Earth Globe.

---

## 🧑‍⚖️ Quick Start Guide

You can evaluate **Atmosphere Diary** in two ways: **instantly in your browser** via our live Vercel deployment, or **locally** to test uploading new 3D `.ply` files to disk.

### 🚀 1. Explore the Live Web App (Zero Setup)
Open the live Vercel deployment link at the top of this repository:

* **Step 1 — Enter a 3D Gaussian Splat Memory:**
  * Look at the **Memory Archive** sidebar on the left.
  * Entries marked with **`🧊`** contain full **Apple ML-SHARP 3D Gaussian Splat (`.ply`)** scenes. Click any memory (e.g., *Cool Forest* or *A Quiet Moment Remembered*) to enter the 3D world.
* **Step 2 — Move Around Inside the 3D Photograph:**
  * **🖱️ Left-Click + Drag:** Orbit camera angle.
  * **🖱️ Right-Click + Drag:** Pan camera position.
  * **🖱️ Scroll Wheel:** Zoom in and out.
  * **⌨️ `W` `A` `S` `D` Keys:** Walk forward (`W`), backward (`S`), left (`A`), and right (`D`) inside the 3D scene.
* **Step 3 — Spin the 3D Earth Globe:**
  * Click **`🌍 Open 3D Earth Globe`** in the left sidebar (or `← Earth Globe` from inside a 3D scene).
  * Drag to rotate the 3D NASA Earth and hover over any **Red Teardrop Map Pin** to inspect the location, date, title, and importance rating (`★ 1/5` to `★ 5/5`).
  * **Click any red pin** on the globe to teleport directly into that memory's 3D world.
* **Step 4 — Music & Mood Player:**
  * Each memory includes an attached song that plays in the bottom-right liquid-glass vinyl player with a live animated equalizer.
  * On the home bubble (`+ New Day Entry`), you can search any song or artist in the **`🔍 Search any song or artist...`** bar and click **`Find`**—even without logging into a Spotify account!

---

### 🧪 2. Test Creating a New 3D Memory (Using Our Pre-Built `.PLY` Models)
We have included ready-to-use raw 2D photographs and their generated ML-SHARP 3D `.ply` files right inside this repository so judges can test the creation flow:

1. Download a sample photo from **[`assets/images/`](./assets/images)** and a sample 3D Gaussian Splat from **[`assets/3d_models/`](./assets/3d_models)** (or grab any `photo_...` and `model_....ply` from **[`memories/`](./memories)**).
2. *(Recommended for full file saving)* Clone and run the app locally (takes 30 seconds):
   ```bash
   git clone [https://github.com/shoev052011-source/3D-Memory.git](https://github.com/shoev052011-source/3D-Memory.git)
   cd 3D-Memory
   pip install -r requirements.txt
   python -m uvicorn server:app --reload
   Open http://127.0.0.1:8000 in your browser.
3. Inside the center Wobbly Liquid-Glass Bubble:

📍 Location: Type any city or country (e.g., Almaty, Tokyo, Berlin, New York).

📅 Date & ★ Importance: Pick a date and select an importance level (1/5 to 5/5 Core).

➕ Attach Media: Click the + button on the left of the main prompt bar:

Click 📷 1. Upload Photo and select your .jpg / .png image.

Click 🧊 2. Attach 3D (.PLY / .GLB) and select your .ply 3D Gaussian Splat file.

💭 Feeling & 🎵 Music: Type how the day felt, pick a song from the dropdown (or search any artist), and click the Up Arrow (↑) → Create 3D World.

Your new 3D memory will immediately render and pin itself to the 3D Earth Globe!

🧠 How We Built It (Tech Stack & Pipeline)
1. 2D-to-3D AI Reconstruction (Apple ML-SHARP)
We used Apple ML-SHARP (sharp predict -i input_photos -o output_splats) to perform monocular 3D view synthesis on single 2D photographs.

Within seconds on a local GPU/CPU, ML-SHARP predicts a metric-scale 3D Gaussian Splat (.ply) containing over 1,000,000 3D Gaussians with color, opacity, and covariance.

If a user uploads only a 2D photo without a .ply file, our engine automatically falls back to a real-time luminance depth-map displacement shader that sculpts the 2D photo into a walkable 3D relief biome.

2. Real-Time WebGL 3D Engine (Three.js + GaussianSplats3D)
3D Gaussian Splatting in the Browser: Powered by @mkkellogg/gaussian-splats-3d and Three.js (r160) with custom WASD first-person horizontal plane navigation.

Interactive 3D Earth Atlas: Built with NASA high-resolution Earth diffuse, normal, and specular maps (earth_atmos_2048.jpg), custom 2D canvas-generated Teardrop Location Pin 3D billboard sprites, raycasting hover tooltips, and an anti-overlap spiral coordinate spreader so multiple memories in the same city never hide each other.

3. VisionOS / iPadOS Liquid-Glass UX
60 FPS GPU-Accelerated Wobbly Glass Bubble: Built with multi-layered radial gradients, specular inner shadows, and hardware-composited scale3d keyframe physics.

iPadOS Magnetic Cursor Tracking: Every pill and circular button uses requestAnimationFrame-throttled pointer physics to magnetically pull toward the user's cursor.

4. Multimodal Audio & AI Sentiment Backend (FastAPI)
FastAPI + Static CDN Architecture: Lightweight Python backend handling geocoding (OpenStreetMap Nominatim + instant offline coordinate dictionary), metadata persistence, and music search.

Spotify OAuth 2.0 + Universal iTunes Fallback: Supports linking personal Spotify accounts while providing zero-login instant 30-second audio previews for any song query worldwide.

LLM Mood Analysis (Llama 3.2 via Ollama): Generates poetic memory titles and mood-matched hex color palettes from diary text, complete with an instant offline fallback.
3D-Memory/
├── index.html          # 3D WebGL App: Liquid-Glass UI, 3D Earth Globe & ML-SHARP .PLY Splat Viewer
├── server.py           # FastAPI Backend: Memory creation, Geocoding, Spotify OAuth & Archive API
├── assets/             # Raw showcase files for judges to inspect or download for testing
│   ├── images/         # Original 2D input photographs (.jpg / .png)
│   └── 3d_models/      # Generated ML-SHARP 3D Gaussian Splats (.ply)
├── memories/           # Active 3D Memory Database (Loaded automatically into Sidebar & Earth Globe)
│   └── <Memory_Name>/  # Contains photo, model_.ply, and metadata.json (coords, date, song, mood)
├── requirements.txt    # Python dependencies for local & Vercel serverless deployment
├── vercel.json         # Vercel static CDN routing (streams 60MB+ .ply files directly from Edge CDN)
└── README.md           # Project documentation & judge instructions