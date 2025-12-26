# Results & Demonstrations

## Project Overview

Clinical Trials Matcher is an AI-powered web application that matches patients with eligible clinical trials based on their medical profile. This document showcases the application's user interface, input handling, and results output.

---

## Table of Contents

1. [User Interface](#user-interface)
2. [Sample Input](#sample-input)
3. [Results Output](#results-output)

---

## User Interface

The application features a modern, responsive two-column layout with a clean gradient design.

### UI Design

The left panel contains the patient information form with fields for:
- **API URL Configuration** — Easy endpoint configuration
- **Age** — Patient age in years
- **Gender** — Dropdown selection (Male, Female, Other)
- **BMI** — Body Mass Index (optional)
- **HbA1c Level** — Glycated hemoglobin percentage (optional)
- **Pregnancy Status** — Checkbox for pregnancy
- **Clinical Context** — Text area for additional clinical notes

The right panel displays matching trial results with:
- Results counter showing total matches
- Trial cards with NCT IDs (clickable links to ClinicalTrials.gov)
- Match scores (inclusion & exclusion percentages)
- AI-generated recommendations explaining why a trial matches

### Screenshot

![Clinical Trials Matcher UI - Two Column Layout with Form and Results Panel](./screenshots/01-ui-interface.png)

*The application features a modern responsive two-column layout with purple gradient background. Left panel shows patient information form with fields for API URL, Age, Gender, BMI, HbA1c, Pregnancy Status, and Clinical Context. Right panel displays matching trial results with a counter badge showing number of matches.*

---

## Sample Input

### Example Patient Profile

A typical patient query includes:

- **Age:** 45 years
- **Gender:** Male
- **BMI:** 28.0 kg/m²
- **HbA1c:** 7.1%
- **Pregnancy Status:** Not pregnant
- **Clinical Context:** "Heart patient. Newly diagnosed. No prior insulin therapy."

### How It Works

1. User fills in the patient information form
2. Clicks "Find Matching Trials"
3. The system performs:
   - Hard filtering via Neo4j graph database (age, BMI, HbA1c constraints)
   - Semantic similarity search using FAISS indexes
   - Exclusion criteria filtering to remove ineligible trials
4. Results appear instantly with top matches first

### Screenshot

![Clinical Trials Matcher - Sample Patient Input Form](./screenshots/02-sample-input.png)

*Example patient profile filled in the form:*
- *Age: 66 years*
- *Gender: Male*
- *BMI: 27 kg/m²*
- *HbA1c: 8.2%*
- *Pregnancy Status: Not pregnant (unchecked)*
- *Clinical Context: "Heart Patient. Newly diagnosed patient. No prior insulin therapy."*
- *API endpoint configured and ready to query*

---

## Results Output

The application matches patients with eligible clinical trials and displays them with match scores and AI-generated recommendations.

### First Output Screenshot

![Clinical Trials Matcher - Results Output with Top Match and Additional Trials](./screenshots/03-output-results.png)

### Second Output Screenshot

![Clinical Trials Matcher - Extended Results List Continuation](./screenshots/04-output-results-extended.png)
