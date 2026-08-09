# Resume Job Agent

Streamlit app that accepts a resume, extracts skills and role signals, discovers jobs by location through an authorized job API or CSV import, ranks matches, and prepares a human-reviewed application package.

## Safety and platform policy
The app does not log in to LinkedIn, scrape LinkedIn, or automatically submit applications. It creates a LinkedIn search link and lets the candidate review and submit.

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Job sources
- Adzuna API: obtain an App ID and App Key from the Adzuna developer portal.
- CSV import: columns `title`, `company`, `location`, `description`, `url`.
- LinkedIn: opens a search URL based on extracted target roles and preferred location.

## Privacy
Resume processing occurs in the running Streamlit session. Do not deploy publicly without authentication, secure secret storage, retention controls, and a privacy notice.

## Publish to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
gh auth login
gh repo create resume-job-agent --public --source=. --push
```

Alternatively, create a public repository named `resume-job-agent` on GitHub, then upload the files from this project folder.
