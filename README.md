## 📂 Repository Structure
```text
arttech-diary/
├── index.html          # Main 3D WebGL application, Earth Globe, Splat Viewer & Liquid-Glass UI
├── server.py           # FastAPI backend (Memory API, Spotify OAuth, Geocoding, Archive reader)
├── assets/             # Raw showcase source files for judges to inspect or test uploading
│   ├── images/         # Original 2D input photographs (.jpg / .png)
│   └── 3d_models/      # ML-SHARP generated 3D Gaussian Splats (.ply) & 3D meshes (.glb)
├── memories/           # Active app database (Saved 3D memories loaded into the Sidebar & Earth Globe)
├── requirements.txt    # Python dependencies for local & Vercel serverless execution
├── vercel.json         # Vercel static CDN & FastAPI serverless routing configuration
└── README.md           # Project documentation & judge instructions

**4. Important GitHub 100 MB File Limit Check**
Before running `git add .` and `git push`, check the file size of your `.ply` files:
* Each ML-SHARP `.ply` file is roughly **60–65 MB**.
* GitHub allows files under **100 MB** (it will show a yellow warning for files between 50 MB and 100 MB, which is fine and still pushes).
* However, if you duplicate the exact same 63 MB `.ply` file in both `memories/` and `assets/3d_models/` across 4–5 photos, your total `git push` will exceed 500 MB and Vercel may reject the bundle size.
* **Best Practice:** Keep **1 sample `.ply` file** (and all your 2D photos) inside `assets/`, and keep your **2–3 best finished memories** inside `memories/`.

<ElicitationsGroup message="If you run into any issues while pushing your 3D models to GitHub or deploying to Vercel:">
  <Elicitation label="GitHub file size error" query="Git rejected my push because the .ply files are too large. How do I fix this?"/>
  <Elicitation label="Models not loading on Vercel" query="I deployed to Vercel, the UI loads, but the 3D .ply models give a 404 error. How do I fix vercel.json?"/>
</ElicitationsGroup>