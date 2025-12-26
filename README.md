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
├── app/
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
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup

### Prerequisites

- Python 3.10+
- Neo4j database (running on `bolt://localhost:7687`)
- FAISS indexes and metadata files (in `data/` folder)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/clinical-trials-matcher.git
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
   Create a `.env` file in the project root (or set environment variables):
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password_here
   NEO4J_DATABASE=database
   ```

5. **Ensure FAISS data is present**
   - Place `faiss_inclusion.index`, `faiss_exclusion.index`, and `faiss_metadata.csv` in the `data/` folder

## Running the Application

### Backend (FastAPI)

Start the FastAPI server:
```bash
cd "Clinical Trials"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`
- API endpoint: `POST http://localhost:8000/match-trials`
- Docs: `http://localhost:8000/docs`

### Frontend (Static UI)

Serve the frontend on a different port:
```bash
cd "Clinical Trials\app\static"
python -m http.server 8001
```

Then open in your browser: `http://localhost:8001/index.html`

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

## Performance Notes

- **Initialization**: Model and FAISS indexes are loaded on first request (can take 30+ seconds)
- **Subsequent requests**: Cached in memory for faster responses
- **Neo4j**: Connection pooling recommended for production
- **FAISS**: Optimized for semantic similarity at scale

## Future Improvements

- [ ] Implement model/index caching at startup
- [ ] Add pagination for large result sets
- [ ] Support for more clinical parameters
- [ ] Integration with real clinical trial databases (ClinicalTrials.gov)
- [ ] Mobile app (React Native or Flutter)
- [ ] Advanced filtering UI
- [ ] Result export (PDF, CSV)

## Security Notes

⚠️ **Important**: 
- Never commit `.env` files with credentials
- Store Neo4j credentials in environment variables, not in code
- Use HTTPS in production
- Implement authentication/authorization for production deployments
- Keep sensitive patient data encrypted

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add your feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

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
