# Clinical Trials Matcher

A web application that matches patients with eligible clinical trials based on their medical profile using semantic search and Neo4j graph filtering.

## Features

- **Patient Profile Matching**: Match patients against clinical trials using age, gender, BMI, HbA1c, pregnancy status, and clinical context
- **Semantic Search**: AI-powered inclusion/exclusion criteria matching using sentence transformers
- **Hard Constraint Filtering**: Neo4j-based graph database for fast eligibility filtering
- **FAISS Indexing**: Vector similarity search for inclusion and exclusion criteria
- **Modern UI**: Clean, responsive web interface for easy patient data entry
- **RESTful API**: FastAPI backend with CORS support

## Project Structure

```
Clinical Trials/
├── app/                     # FastAPI backend + Frontend
│   ├── main.py              # FastAPI application entry point
│   ├── retrieve_id.py       # Core trial retrieval logic
│   ├── schemas.py           # Pydantic models
│   ├── static/              # Frontend files
│   │   ├── index.html       # UI (two-column form + results)
│   │   ├── app.js           # Frontend logic
│   │   └── README.md        # Frontend documentation
│   └── __init__.py
├── data/                    # FAISS indexes and metadata
│   ├── faiss_inclusion.index
│   ├── faiss_exclusion.index
│   └── faiss_metadata.csv
├── src/                     # Source data and utilities
├── evaluation/              # Evaluation scripts and results
├── screenshots/             # Documentation screenshots
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── results.md              # Results and demonstrations
└── LICENSE                 # MIT License
```

## Code Workflow

This section explains how data flows through the application from user input to results display.

### Step-by-Step Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INTERFACE (Frontend - app.js)                       │
├─────────────────────────────────────────────────────────────┤
│ • User fills form (age, gender, BMI, HbA1c, pregnant, etc)  │
│ • User clicks "Find Matching Trials" button                 │
│ • Form validation runs                                      │
│ • JSON payload created with patient data                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ POST request with JSON
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. API ENDPOINT (Backend - main.py)                         │
├─────────────────────────────────────────────────────────────┤
│ • FastAPI receives POST /match-trials request               │
│ • Pydantic validates request body against PatientInput      │
│ • CORS headers verified (allows localhost:8001)             │
│ • Calls retrieve_trials_dual() with patient parameters      │
└──────────────────────┬──────────────────────────────────────┘
                       │ Patient data
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. NEO4J HARD FILTERING (retrieve_id.py)                    │
├─────────────────────────────────────────────────────────────┤
│ • get_eligible_trials_from_graph() runs Neo4j query         │
│ • Filters trials by:                                        │
│   - Age range constraints (min_age ≤ patient_age ≤ max_age) │
│   - BMI range constraints (if specified)                    │
│   - HbA1c range constraints (if specified)                  │
│   - Pregnancy status allowance                              │
│ • Returns list of ~100-500 eligible trial IDs               │
│ • ~95% of trials filtered out at this stage                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ Eligible trial IDs
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. SEMANTIC SEARCH - INCLUSION CRITERIA (retrieve_id.py)    │
├─────────────────────────────────────────────────────────────┤
│ • build_query() creates semantic search string:             │
│   - Combines: age + gender + clinical_context               │
│   - Example: "45 year old male heart patient diabetes"      │
│ • Model loads (S-BioBERT) - 30-45s on first request         │
│ • Query converted to embedding vector (768 dimensions)      │
│ • FAISS searches faiss_inclusion.index for similar vectors  │
│ • Returns top ~10,000 trial-criterion matches with scores   │
│ • Score = semantic similarity (0.0 to 1.0)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Trial IDs + inclusion scores
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. SEMANTIC SEARCH - EXCLUSION CRITERIA (retrieve_id.py)    │
├─────────────────────────────────────────────────────────────┤
│ • Same query used to search faiss_exclusion.index           │
│ • Finds trials with exclusion criteria matching patient     │
│ • Returns scores (higher = more risky to patient)           │
│ • Trials filtered if exclusion_score too high               │
└──────────────────────┬──────────────────────────────────────┘
                       │ Trial IDs + both scores
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. RANKING & FILTERING (retrieve_id.py)                     │
├─────────────────────────────────────────────────────────────┤
│ • fetch_trial_constraints() gets each trial's metadata      │
│ • Combined score = inclusion_score - (exclusion_score * w)  │
│ • Trials ranked by combined score (descending)              │
│ • Top 10 trials selected (configurable via top_k)           │
│ • fetch_trial_constraints() retrieves trial details         │
└──────────────────────┬──────────────────────────────────────┘
                       │ Top 10 trials with scores
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. EXPLANATION GENERATION (retrieve_id.py)                  │
├─────────────────────────────────────────────────────────────┤
│ • explain_trial_recommendation() called for top match       │
│ • Generates human-readable text explaining:                 │
│   - Why age criteria match                                  │
│   - Why BMI/HbA1c criteria match                            │
│   - Why clinical context is relevant                        │
│   - Similarity score percentage                             │
│ • Example: "Patient age (45) satisfies trial age (18-65)..."│
└──────────────────────┬──────────────────────────────────────┘
                       │ JSON response with trials + explanations
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. API RESPONSE (Backend - main.py)                         │
├─────────────────────────────────────────────────────────────┤
│ Returns JSON:                                               │
│ {                                                           │
│   "top_trial": { nct_id, inclusion_score, exclusion_score },| 
│   "explanation": "Human readable text...",                  │
│   "other_trials": [ {...}, {...}, {...} ]                   │
│ }                                                           │
│ • Response sent back to frontend                            │
│ • Execution time: 2-5 seconds (after model cached)          │
└──────────────────────┬──────────────────────────────────────┘
                       │ JSON with results
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. FRONTEND RENDERING (app.js)                              │
├─────────────────────────────────────────────────────────────┤
│ • JavaScript parses JSON response                           │
│ • Creates HTML trial cards dynamically:                     │
│   - Trial rank (Top Match / 2. / 3. etc)                    │
│   - NCT ID as clickable link                                │
│   - Green match score badge                                 │
│   - Inclusion/exclusion percentages                         │
│   - Recommendation text (for top match)                     │
│ • Updates results counter ("10 trials matched")             │
│ • Displays loading spinner during request                   │
│ • Error handling for failed requests                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTML cards rendered in browser
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. USER INTERACTION (Browser)                              │
├─────────────────────────────────────────────────────────────┤
│ • User sees trial results displayed in right panel          │
│ • User clicks NCT ID link → Opens ClinicalTrials.gov        │
│ • User scrolls to see more trials                           │
│ • User can click "Clear Form" → Reset for new query         │
└─────────────────────────────────────────────────────────────┘
```


### Key Technologies in Action

- **Neo4j**: Boolean constraint filtering (very fast, eliminates 95% of trials)
- **Sentence Transformers (S-BioBERT)**: Converts medical text to embeddings (768-dim vectors)
- **FAISS**: Vector similarity search (finds semantically similar inclusion/exclusion criteria)
- **FastAPI**: HTTP server with automatic validation and CORS support
- **Vanilla JavaScript**: Lightweight frontend with no dependencies

## Architecture

### Backend Components

1. **retrieve_id.py**
   - `retrieve_trials_dual()`: Main function for trial retrieval
   - `get_eligible_trials_from_graph()`: Neo4j-based hard filtering
   - `explain_trial_recommendation()`: Generates human-readable explanations
   - `fetch_trial_constraints()`: Fetches trial constraints from Neo4j

2. **main.py**
   - FastAPI application setup
   - CORS middleware configuration
   - `/match-trials` endpoint

3. **schemas.py**
   - Pydantic `PatientInput` model for request validation

### Frontend Components

1. **index.html**
   - Two-column responsive layout
   - Form card for patient data entry
   - Results card for trial display
   - Modern gradient design

2. **app.js**
   - Form submission handling
   - API communication
   - Result rendering with cards and scores
   - Loading and error states

## Getting Started

### Prerequisites

- Python 3.10+
- Neo4j database (running on `bolt://localhost:7687`)
- FAISS indexes and metadata files (in `data/` folder)

### Installation & Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/vansh23106-sudo/clinical-trials-matcher.git
   cd "Clinical Trials"
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password_here
   NEO4J_DATABASE=database
   ```

5. **Ensure FAISS data is present**
   - Place `faiss_inclusion.index`, `faiss_exclusion.index`, and `faiss_metadata.csv` in the `data/` folder

6. **Start the backend (FastAPI)**
   ```bash
   cd "Clinical Trials"
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   API available at: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

7. **Start the frontend (in another terminal)**
   ```bash
   cd "Clinical Trials\app\static"
   python -m http.server 8001
   ```
   Open in browser: `http://localhost:8001/index.html`

### Using the Application

1. **Fill Patient Information**
   - Enter age, gender, BMI, HbA1c
   - Check pregnancy status if applicable
   - Add clinical context notes

2. **Click "Find Matching Trials"**
   - Wait for results (loading indicator shown)
   - Review top match first
   - Explore other options below

3. **Click NCT ID**
   - Opens trial on ClinicalTrials.gov
   - Get full protocol, contact info, and status
   - Register as interested participant

## API Usage

### Request

**Endpoint:** `POST /match-trials`

**Request Body:**
```json
{
  "age": 45,
  "gender": "Male",
  "bmi": 28.0,
  "hba1c": 7.1,
  "pregnant": false,
  "clinical_context": "Heart patient. Newly diagnosed. No prior insulin therapy.",
  "top_k": 10
}
```

**Field Descriptions:**
- `age` (int): Patient age in years
- `gender` (string): "Male", "Female", or "Other"
- `bmi` (float, optional): Body Mass Index
- `hba1c` (float, optional): Glycated hemoglobin level
- `pregnant` (bool): Pregnancy status
- `clinical_context` (string, optional): Additional clinical notes
- `top_k` (int, default 10): Number of results to return

### Response

```json
{
  "top_trial": {
    "nct_id": "NCT06243536",
    "inclusion_score": 0.615,
    "exclusion_score": 0.213
  },
  "explanation": "This trial was recommended because the patient's age (45) satisfies the trial's age criteria (18.0–65.0), BMI (28.0) lies within the allowed range (28.0–None), HbA1c (7.1) is compatible with the trial requirements (7.0–None), pregnancy is not allowed and the patient is not pregnant, the inclusion criteria is semantically similar (similarity score 0.62).",
  "other_trials": [
    {
      "nct_id": "NCT01941290",
      "inclusion_score": 0.602,
      "exclusion_score": 0.153
    },
    ...
  ]
}
```


## Security Notes

**Important**: 
- Never commit `.env` files with credentials
- Store Neo4j credentials in environment variables, not in code
- Use HTTPS in production
- Implement authentication/authorization for production deployments
- Keep sensitive patient data encrypted


## License

This project is licensed under the MIT License — see LICENSE file for details.

## Support

For issues, questions, or feedback, please open an issue on GitHub or contact the maintainers.

## Authors

- Vansh Mehta

## Acknowledgments

- FAISS (Facebook AI Similarity Search) for vector indexing
- Sentence Transformers for semantic search
- Neo4j for graph database capabilities
- FastAPI for the modern web framework
- Clinical trial data sources
