# Apply AI Agent

A local, human-in-the-loop job application assistant tailored to Ben Vainberg's resume.

## Features
- Imports jobs from CSV.
- Scores fit against target titles and skills.
- Generates a tailored summary and cover letter.
- Produces a review queue and opens the original link for manual submission.

It intentionally does not scrape LinkedIn, control an account, bypass access controls, or automatically submit applications.

## Run
1. Install Python 3.10+.
2. Run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.

Required CSV columns: `title`, `company`, `description`. Optional: `url`.

Review every generated statement, obtain Ben's consent, and keep all candidate details accurate.
