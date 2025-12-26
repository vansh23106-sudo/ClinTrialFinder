Simple UI for Clinical Trials retrieval

Files:
- `index.html` — minimal form for Age, Gender, BMI, HbA1c, Clinical Context and API URL
- `app.js` — small JS that sends a JSON POST to the configured API URL

How to use locally:

1. Open the page directly (file://) — most browsers restrict `fetch` from `file://` origins, so POST requests may fail.

2. Recommended: serve the folder with a minimal local server and open in browser.

Windows (cmd.exe):

```cmd
cd "c:\Users\Vansh Mehta\C++\Clinical Trials\app\static"
python -m http.server 8001
```

Then open `http://localhost:8001/index.html` in your browser.

Default API URL field is empty — set it to your running backend, e.g. `http://localhost:8000/retrieve` and press Submit.

Notes:
- The page is intentionally simple and standalone; it does not modify any existing project files.
- Payload keys: `age`, `gender`, `bmi`, `hba1c`, `clinical_context`, optional `top_k`.
- Keep your API running and reachable from the browser (CORS may be required on the API). If your API is on a different host/port, ensure CORS is allowed on the server or use a local proxy.
