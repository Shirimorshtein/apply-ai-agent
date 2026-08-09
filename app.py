import io, os, re, urllib.parse
import pandas as pd
import requests
import streamlit as st
from pypdf import PdfReader
from docx import Document

st.set_page_config(page_title="Resume Job Agent", page_icon="🎯", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1200px;padding-top:2rem}.hero{padding:1.5rem;border-radius:18px;background:linear-gradient(135deg,#0f172a,#1d4ed8);color:white;margin-bottom:1rem}.card{padding:1rem;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.score{font-size:1.7rem;font-weight:800;color:#1d4ed8}.muted{color:#64748b}
</style>
<div class="hero"><h1>Resume Job Agent</h1><p>Upload a resume, discover relevant roles by location, rank matches, and prepare applications for human review.</p></div>
""", unsafe_allow_html=True)

SKILLS = ["python","java","scala","spring boot","sql","kafka","flink","spark","airflow","aws","azure","gcp","kubernetes","docker","ci/cd","microservices","distributed systems","cassandra","elasticsearch","redis","machine learning","engineering management","team lead"]

def extract_text(upload):
    data=upload.getvalue()
    if upload.name.lower().endswith(".pdf"):
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    if upload.name.lower().endswith(".docx"):
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")

def profile(text):
    low=text.lower()
    skills=[s for s in SKILLS if s in low]
    titles=[]
    for t in ["Engineering Manager","Platform Engineering Manager","Data Engineering Manager","Data Platform Lead","Staff Data Engineer","Principal Data Engineer","Senior Data Engineer","Streaming Data Architect","Backend Engineering Manager"]:
        if any(k in low for k in t.lower().split()): titles.append(t)
    years=max([int(x) for x in re.findall(r"(\d{1,2})\+? years",low)] or [0])
    return skills, list(dict.fromkeys(titles))[:7], years

def match(job, skills, titles, location):
    text=(str(job.get("title",""))+" "+str(job.get("description",""))).lower()
    hits=[s for s in skills if s in text]
    role=max([len(set(t.lower().split()) & set(str(job.get("title","")).lower().split()))/max(1,len(t.split())) for t in titles] or [0])
    loc=1 if location.lower() in str(job.get("location","")).lower() or "remote" in str(job.get("location","")).lower() else 0
    score=round(100*(.55*min(1,len(hits)/max(3,min(8,len(skills) or 3)))+.35*role+.10*loc))
    return score,hits

def adzuna(app_id,key,query,location,country,pages=1):
    jobs=[]
    for page in range(1,pages+1):
        url=f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
        r=requests.get(url,params={"app_id":app_id,"app_key":key,"what":query,"where":location,"results_per_page":25,"content-type":"application/json"},timeout=20)
        r.raise_for_status()
        for x in r.json().get("results",[]):
            jobs.append({"title":x.get("title",""),"company":(x.get("company") or {}).get("display_name",""),"location":(x.get("location") or {}).get("display_name",""),"description":x.get("description",""),"url":x.get("redirect_url","")})
    return jobs

with st.sidebar:
    st.header("Search settings")
    location=st.text_input("Preferred location","Tel Aviv, Israel")
    country=st.selectbox("Adzuna country market",["gb","us","ca","au","de","fr","nl","pl","at","nz","za"],index=0,help="Choose a supported Adzuna market. For Israel, use LinkedIn search or import a CSV.")
    remote=st.checkbox("Include remote",True)
    threshold=st.slider("Minimum match",0,100,55)
    st.divider()
    st.caption("LinkedIn remains review-and-submit only. This app does not log in, scrape, or auto-submit.")

resume=st.file_uploader("Upload resume",type=["pdf","docx","txt"])
if not resume:
    st.info("Start by uploading a PDF, DOCX, or TXT resume.")
    st.stop()
text=extract_text(resume)
skills,titles,years=profile(text)

c1,c2,c3=st.columns(3)
c1.metric("Detected skills",len(skills)); c2.metric("Target roles",len(titles)); c3.metric("Years signal",f"{years}+" if years else "Not detected")
with st.expander("Review extracted profile",expanded=True):
    skills=st.multiselect("Skills",SKILLS,default=skills)
    titles=st.text_area("Target roles, one per line","\n".join(titles or ["Engineering Manager","Data Engineering Manager","Data Platform Lead"])).splitlines()

st.subheader("Find jobs")
tab1,tab2,tab3=st.tabs(["Job API","Import CSV","LinkedIn search"])
jobs=[]
with tab1:
    st.write("Use your Adzuna developer credentials to retrieve job postings through its API.")
    a,b=st.columns(2); app_id=a.text_input("Adzuna App ID",type="password"); key=b.text_input("Adzuna App Key",type="password")
    query=st.text_input("Search query",titles[0] if titles else "engineering manager")
    if st.button("Search jobs",type="primary"):
        try: st.session_state.jobs=adzuna(app_id,key,query,location,country,2)
        except Exception as e: st.error(f"Job search failed: {e}")
with tab2:
    template=pd.DataFrame([{"title":"Data Platform Lead","company":"Example","location":"Tel Aviv","description":"Lead Kafka, Flink and Kubernetes platform teams","url":"https://example.com/job"}])
    st.download_button("Download CSV template",template.to_csv(index=False),"jobs_template.csv")
    csv=st.file_uploader("Upload jobs CSV",type="csv",key="jobs")
    if csv is not None: st.session_state.jobs=pd.read_csv(csv).fillna("").to_dict("records")
with tab3:
    q=urllib.parse.quote_plus(" OR ".join(f'"{t.strip()}"' for t in titles[:4] if t.strip()))
    loc=urllib.parse.quote_plus(location)
    li=f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"
    st.link_button("Open matching LinkedIn search",li,use_container_width=True)
    st.caption("Review listings and submit applications yourself in LinkedIn.")

jobs=st.session_state.get("jobs",[])
if jobs:
    ranked=[]
    for j in jobs:
        score,hits=match(j,skills,titles,location)
        j={**j,"score":score,"matched_skills":", ".join(hits)}
        ranked.append(j)
    ranked=sorted([j for j in ranked if j["score"]>=threshold],key=lambda x:x["score"],reverse=True)
    st.subheader(f"Application queue ({len(ranked)})")
    for i,j in enumerate(ranked):
        with st.container(border=True):
            a,b=st.columns([1,5])
            a.markdown(f'<div class="score">{j["score"]}%</div><div class="muted">match</div>',unsafe_allow_html=True)
            b.markdown(f"### {j['title']}\n**{j['company']}** · {j['location']}")
            b.caption("Matched: "+(j["matched_skills"] or "role and location signals"))
            summary=f"Experienced engineering leader with strengths in {j['matched_skills'] or ', '.join(skills[:5])}, aligned to the {j['title']} opportunity at {j['company']}."
            with st.expander("Application package"):
                st.text_area("Tailored summary",summary,key=f"s{i}")
                st.text_area("Cover note",f"Dear Hiring Team,\n\nI am interested in the {j['title']} role at {j['company']}. My background includes {j['matched_skills'] or ', '.join(skills[:5])}. I would welcome the opportunity to discuss how my experience can contribute to your team.\n\nBest regards",key=f"c{i}",height=180)
                st.download_button("Download resume",resume.getvalue(),file_name=resume.name,key=f"d{i}")
            if j.get("url"): b.link_button("Open job and apply",j["url"])
    st.download_button("Export queue",pd.DataFrame(ranked).to_csv(index=False),"application_queue.csv")
