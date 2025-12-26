document.getElementById('submitBtn').addEventListener('click', async (e) => {
  e.preventDefault();

  const apiUrl = (document.getElementById('apiUrl').value || '').trim();
  if (!apiUrl) {
    alert('Please enter the API URL');
    return;
  }

  const ageVal = document.getElementById('age').value;
  const genderVal = document.getElementById('gender').value;
  const bmiVal = document.getElementById('bmi').value;
  const hba1cVal = document.getElementById('hba1c').value;
  const pregnantVal = document.getElementById('pregnant').checked;
  const clinical = document.getElementById('clinical').value;

  // Build the JSON payload — top_k is always 10
  const payload = {
    age: ageVal ? Number(ageVal) : undefined,
    gender: genderVal || undefined,
    bmi: bmiVal ? Number(bmiVal) : undefined,
    hba1c: hba1cVal ? Number(hba1cVal) : undefined,
    pregnant: pregnantVal,
    clinical_context: clinical || undefined,
    top_k: 10
  };

  const resultsContainer = document.getElementById('resultsContainer');
  const resultsCount = document.getElementById('resultsCount');
  const submitBtn = document.getElementById('submitBtn');

  // Show loading state
  submitBtn.disabled = true;
  submitBtn.textContent = 'Searching...';
  resultsContainer.innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <p>Finding matching clinical trials...</p>
    </div>
  `;

  try {
    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();

    // Display results
    if (data.top_trial) {
      const trials = [data.top_trial, ...(data.other_trials || [])];
      resultsCount.textContent = trials.length;

      resultsContainer.innerHTML = trials.map((trial, idx) => {
        const score = trial.inclusion_score;
        const scorePercent = (score * 100).toFixed(1);
        const label = idx === 0 ? 'Top Match' : `${idx + 1}.`;
        const nctUrl = `https://clinicaltrials.gov/study/${trial.nct_id}`;
        
        return `
          <div class="trial-card">
            <div class="trial-header">
              <span class="trial-id"><a href="${nctUrl}" target="_blank" rel="noopener noreferrer">${label}: ${trial.nct_id}</a></span>
              <span class="match-score">${scorePercent}% Match</span>
            </div>
            <div class="trial-info">
              <strong>Inclusion Score:</strong> ${scorePercent}% | 
              <strong>Exclusion Score:</strong> ${(trial.exclusion_score * 100).toFixed(1)}%
            </div>
            ${idx === 0 && data.explanation ? `<div class="trial-info"><strong>Recommendation:</strong><br>${data.explanation}</div>` : ''}
          </div>
        `;
      }).join('');
    } else if (data.message) {
      resultsCount.textContent = '0';
      resultsContainer.innerHTML = `
        <div class="empty-state">
          <h3>${data.message}</h3>
          <p>Try adjusting the patient criteria</p>
        </div>
      `;
    } else {
      resultsCount.textContent = '0';
      resultsContainer.innerHTML = `
        <div class="error-message">
          <strong>Unexpected response format</strong>
        </div>
      `;
    }
  } catch (err) {
    resultsCount.textContent = '0';
    resultsContainer.innerHTML = `
      <div class="error-message">
        <strong>Error:</strong> ${err.message}
      </div>
      <div class="empty-state">
        <h3>Unable to load results</h3>
        <p>Make sure the API server is running at the specified URL</p>
      </div>
    `;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Find Matching Trials';
  }
});

document.getElementById('clearBtn').addEventListener('click', () => {
  document.getElementById('apiUrl').value = '';
  document.getElementById('age').value = '';
  document.getElementById('gender').value = '';
  document.getElementById('bmi').value = '';
  document.getElementById('hba1c').value = '';
  document.getElementById('pregnant').checked = false;
  document.getElementById('clinical').value = '';
  document.getElementById('resultsCount').textContent = '0';
  document.getElementById('resultsContainer').innerHTML = `
    <div class="empty-state">
      <h3>Enter patient details to find matching trials</h3>
      <p>Fill out the form and click "Find Matching Trials"</p>
    </div>
  `;
});