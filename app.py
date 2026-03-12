import streamlit as st
import pdfplumber
from collections import Counter
import re
import pandas as pd
import os

# -----------------------------
# Optional OpenAI import
# -----------------------------
try:
    from openai import OpenAI
    # Use Streamlit Secrets for API key
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
except:
    client = None

# -----------------------------
# Extract text from PDF
# -----------------------------
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# -----------------------------
# Resume statistics
# -----------------------------
def resume_statistics(resume_text):
    words = resume_text.split()
    return len(words)

# -----------------------------
# Skills database
# -----------------------------
skills = [
    "python", "machine learning", "data analysis", "sql",
    "deep learning", "nlp", "tensorflow", "pandas", "java",
    "cloud computing"
]

# -----------------------------
# Detect skills
# -----------------------------
def detect_skills(resume_text):
    resume_text = resume_text.lower()
    found = [skill for skill in skills if skill in resume_text]
    return found

# -----------------------------
# Missing skills
# -----------------------------
def missing_skills(found):
    return [skill for skill in skills if skill not in found]

# -----------------------------
# Extract job keywords
# -----------------------------
def extract_keywords(job_description):
    words = re.findall(r'\b[a-zA-Z]+\b', job_description.lower())
    stopwords = ["the","is","and","to","for","in","a","of","with","on",
                 "we","are","looking","candidate","should","have","will",
                 "team","our","all"]
    filtered = [word for word in words if word not in stopwords]
    counts = Counter(filtered)
    keywords = [word for word, count in counts.most_common(10)]
    return keywords

# -----------------------------
# ATS Score
# -----------------------------
def calculate_ats_score(resume_text, job_description):
    resume_text = resume_text.lower()
    job_words = extract_keywords(job_description)
    match_count = sum(1 for word in job_words if word in resume_text)
    score = (match_count / len(job_words)) * 100 if job_words else 0
    return round(score, 2)

# -----------------------------
# Keyword match analysis
# -----------------------------
def keyword_match(resume_text, keywords):
    resume_text = resume_text.lower()
    matched = [word for word in keywords if word in resume_text]
    missing = [word for word in keywords if word not in resume_text]
    return matched, missing

# -----------------------------
# Resume Suggestions
# -----------------------------
def generate_resume_suggestions(resume_text, job_description):
    if client:
        try:
            prompt = f"""
You are a professional resume reviewer.
Analyze the resume and job description.
Give exactly 5 bullet suggestions to improve the resume.

Resume:
{resume_text[:600]}

Job Description:
{job_description[:400]}
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            return response.choices[0].message.content
        except:
            pass

    # Free fallback
    suggestions = []
    words = resume_text.lower()
    if len(resume_text.split()) < 350:
        suggestions.append("• Increase resume length by adding more project details.")
    if "project" not in words:
        suggestions.append("• Add a projects section to showcase practical work.")
    if "experience" not in words:
        suggestions.append("• Include internships or real-world experience if available.")
    if "python" not in words:
        suggestions.append("• Highlight programming languages like Python.")
    if "machine learning" not in words:
        suggestions.append("• Mention machine learning or AI related work.")
    if "skills" not in words:
        suggestions.append("• Add a clear skills section for better ATS compatibility.")
    if len(suggestions) == 0:
        suggestions.append("• Your resume already aligns well. Add measurable achievements to strengthen it.")
    return "\n".join(suggestions)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI Resume Dashboard", layout="wide")
st.title("AI-Powered ATS Resume Analyzer")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
job_description = st.text_area("Paste Job Description")

if uploaded_file and job_description:
    resume_text = extract_text(uploaded_file)
    word_count = resume_statistics(resume_text)
    detected = detect_skills(resume_text)
    missing = missing_skills(detected)
    keywords = extract_keywords(job_description)
    score = calculate_ats_score(resume_text, job_description)
    matched_kw, missing_kw = keyword_match(resume_text, keywords)

    # Resume Statistics
    st.subheader("Resume Statistics")
    st.write("Total Words in Resume:", word_count)
    if word_count < 300:
        st.warning("Resume might be too short.")
    elif word_count > 800:
        st.warning("Resume might be too long.")
    else:
        st.success("Resume length looks good.")

    # ATS Score
    st.subheader("ATS Resume Score")
    st.progress(score / 100)
    st.write(f"{score}% match with job description")
    if score < 40:
        st.error("Low ATS compatibility. Add more job-related keywords.")
    elif score < 70:
        st.warning("Moderate ATS compatibility. Improve alignment.")
    else:
        st.success("Strong ATS compatibility.")

    # Keywords
    st.subheader("Important Job Keywords")
    st.write(keywords)

    # Recommended Skills to Add
    st.subheader("Top Skills You Should Add")
    if missing_kw:
        for skill in missing_kw[:5]:
            st.write(f"• {skill}")
    else:
        st.success("Your resume already contains most important job keywords!")

    # Keyword Match
    st.subheader("Matched Keywords")
    st.success(matched_kw)
    st.subheader("Missing Keywords")
    st.error(missing_kw)

    # Skills
    st.subheader("Detected Skills")
    st.write(detected)
    st.subheader("Skills You Should Consider Adding")
    st.write(missing)

    # Skill Visualization
    skill_data = {"Category": ["Detected Skills", "Missing Skills"], "Count": [len(detected), len(missing)]}
    df = pd.DataFrame(skill_data)
    st.subheader("Skill Match Visualization")
    st.bar_chart(df.set_index("Category"))

    # Suggestions
    with st.spinner("Generating AI suggestions..."):
        suggestions = generate_resume_suggestions(resume_text, job_description)
    st.subheader("AI Resume Improvement Suggestions")
    st.markdown(suggestions)