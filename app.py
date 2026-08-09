import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Apply AI Agent", layout="wide")
st.title("Apply AI Agent")
st.caption("Scores jobs, prepares tailored material, and builds a human-review queue. It does not scrape or auto-submit on LinkedIn.")

DEFAULT_PROFILE = {
    "name": "Ben Vainberg",
    "target_roles": ["Engineering Manager", "Platform Engineering Manager", "Data Engineering Manager", "Data Platform Lead", "Staff Data Engineer", "Principal Data Engineer", "Streaming Data Architect"],
    "skills": ["Scala", "Java", "Spring Boot", "SQL", "Apache Kafka", "Apache Flink", "Apache Spark", "Cassandra", "Elasticsearch", "Redis", "Airflow", "AWS", "Azure", "Kubernetes", "Docker", "CI/CD", "Distributed Systems", "Microservices", "Engineering Management"]
}

def tokens(value):
    return set(re.findall(r"[a-z0-9+#.]+", str(value).lower()))

def score_job(title, description, profile):
    text = f"{title} {description}".lower()
    hits = [skill for skill in profile["skills"] if skill.lower() in text]
    title_tokens = tokens(title)
    role_fit = max((len(title_tokens & tokens(role)) / max(1, len(tokens(role))) for role in profile["target_roles"]), default=0)
    skill_fit = min(1.0, len(hits) / 8)
    leadership = 1.0 if any(word in text for word in ["manager", "lead", "leadership", "manage a team"]) else 0.0
    return round(100 * (0.45 * role_fit + 0.45 * skill_fit + 0.10 * leadership)), hits

def tailored_summary(profile, title, company, hits):
    relevant = ", ".join(hits[:6]) or "distributed data platforms"
    return (f"Senior engineering and data-platform leader targeting the {title} role at {company}. "
            f"Brings hands-on experience in {relevant}, engineering management, cloud-native systems, and high-throughput data platforms. "
            "Led a batch-to-streaming transformation that reduced processing latency from about 40 minutes to about 1 minute.")

def cover_letter(profile, title, company, hits):
    relevant = ", ".join(hits[:7]) or "distributed systems and data platforms"
    return f"""Dear Hiring Team,

I am interested in the {title} role at {company}. My background combines engineering leadership with hands-on experience across {relevant}. I have led multidisciplinary teams, modernized data platforms, and delivered resilient backend services and public APIs.

A relevant example is leading a transition from legacy batch processing to a low-latency streaming architecture using Scala, Apache Flink, and Apache Kafka, reducing processing latency from about 40 minutes to about 1 minute. I would welcome the opportunity to discuss how this experience can support your team.

Best regards,
{profile['name']}"""

st.sidebar.header("Candidate profile")
name = st.sidebar.text_input("Name", DEFAULT_PROFILE["name"])
target = st.sidebar.text_area("Target roles, one per line", "\n".join(DEFAULT_PROFILE["target_roles"]))
skills = st.sidebar.text_area("Skills, comma-separated", ", ".join(DEFAULT_PROFILE["skills"]))
profile = {"name": name, "target_roles": [x.strip() for x in target.splitlines() if x.strip()], "skills": [x.strip() for x in skills.split(",") if x.strip()]}

st.subheader("1. Add jobs")
st.write("Upload a CSV with columns `title`, `company`, `description`, and optionally `url`. Copy descriptions only from sources you are allowed to use.")
upload = st.file_uploader("Jobs CSV", type="csv")
example = pd.DataFrame([{"title":"Data Platform Engineering Manager","company":"Example Co","description":"Lead a team building Kafka and Flink services on Kubernetes and AWS.","url":"https://example.com/job"}])
st.download_button("Download CSV template", example.to_csv(index=False), "jobs_template.csv", "text/csv")

if upload:
    df = pd.read_csv(upload).fillna("")
    if not {"title", "company", "description"}.issubset(df.columns):
        st.error("CSV must include title, company, and description.")
        st.stop()
    rows = []
    for _, row in df.iterrows():
        score, hits = score_job(row["title"], row["description"], profile)
        item = row.to_dict()
        item.update({"match_score": score, "matched_skills": ", ".join(hits), "review_status": "Review", "tailored_summary": tailored_summary(profile, row["title"], row["company"], hits), "cover_letter": cover_letter(profile, row["title"], row["company"], hits)})
        rows.append(item)
    output = pd.DataFrame(rows).sort_values("match_score", ascending=False)
    st.subheader("2. Review queue")
    threshold = st.slider("Minimum match score", 0, 100, 65)
    filtered = output[output["match_score"] >= threshold]
    columns = [c for c in ["match_score", "title", "company", "matched_skills", "url", "review_status"] if c in filtered.columns]
    st.dataframe(filtered[columns], use_container_width=True)
    st.download_button("Download application queue", filtered.to_csv(index=False), "application_queue.csv", "text/csv")
    st.subheader("3. Tailored package")
    if len(filtered):
        choice = st.selectbox("Select job", filtered.index, format_func=lambda i: f"{filtered.loc[i, 'title']} at {filtered.loc[i, 'company']}")
        st.text_area("Tailored summary", filtered.loc[choice, "tailored_summary"], height=140)
        st.text_area("Cover letter", filtered.loc[choice, "cover_letter"], height=330)
        if filtered.loc[choice].get("url", ""):
            st.link_button("Open job and apply manually", filtered.loc[choice, "url"])
    else:
        st.info("No jobs meet the selected threshold.")
