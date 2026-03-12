import streamlit as st
import pdfplumber
from collections import Counter
import re
import pandas as pd

# Optional OpenAI import
try:
    from openai import OpenAI
    client = OpenAI(api_key="YOUR_API_KEY_HERE")
except:
    client = None

# -----------------------------
# Functions
# -----------------------------
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def resume_statistics(resume_text):
    return len(resume_text.split())

skills = [
    "python", "machine learning", "data analysis", "sql",
    "deep learning", "nlp", "tensorflow", "pandas",
    "java", "cloud computing"
]

def detect_skills(resume_text):
    resume_text = resume_text.lower()
    return [skill for skill in skills if skill in resume_text]

def missing_skills(found):
    return [skill for skill in skills if skill not in found]

def extract_keywords(job_description):
    words = re.findall(r'\b[a-zA-Z]+\b', job_description.lower())
    stopwords = [
        "the","is","and","to","for","in","a","of","with","on",
        "we","are","looking","candidate","should","have","will",
        "team","our","all"
    ]
    filtered = [word for word in words if word not in stopwords]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(10)]

def calculate_ats_score(resume_text, job_description):
    resume_text = resume_text.lower()
    job_words = extract_keywords(job_description)
    match_count = sum(1 for word in job_words if word in resume_text)
    score = (match_count / len(job_words)) * 100 if job_words else 0
    return round(score, 2)

def keyword_match(resume_text, keywords):
    resume_text = resume_text.lower()
    matched = [word for word in keywords if word in resume_text]
    missing = [word for word in keywords if word not in resume_text]
    return matched, missing

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
    # Fallback suggestions
    suggestions = []
    words = resume_text.lower()
    if len(words.split()) < 350:
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
# Streamlit UI (Final Dashboard)
# -----------------------------
st.set_page_config(page_title="AI Resume Dashboard", page_icon="📊", layout="wide")
st.title("📊 AI-Powered ATS Resume Dashboard")

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

    # -----------------------------
    # Resume Overview
    # -----------------------------
    st.subheader("Resume Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Word Count", word_count)
    with col2:
        st.metric("ATS Score", f"{score}%")
    with col3:
        if score >= 80:
            st.success("Excellent Match")
        elif score >= 60:
            st.info("Good Match")
        else:
            st.warning("Needs Improvement")
    st.progress(score / 100)

    # -----------------------------
    # Expandable Sections
    # -----------------------------
    with st.expander("🔑 Job Keywords Analysis"):
        st.write("**Top Keywords from Job Description:**")
        st.write(keywords)
        st.write("**Matched Keywords:**", matched_kw)
        st.write("**Missing Keywords:**", missing_kw)

    with st.expander("🛠 Skills Analysis"):
        st.write("**Detected Skills:**", detected)
        st.write("**Missing Skills:**", missing)
        st.write("⚠ Things You Should Add:")
        combined_missing = [{"item": kw, "type": "keyword"} for kw in missing_kw] + \
                           [{"item": skill, "type": "skill"} for skill in missing]
        if combined_missing:
            for item in combined_missing:
                if item["type"] == "keyword":
                    st.markdown(f"• 🔑 <span title='Job Keyword' style='color:blue'>{item['item']}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"• ⚡ <span title='Skill' style='color:orange'>{item['item']}</span>", unsafe_allow_html=True)
        else:
            st.success("Your resume already contains all key skills and job keywords!")

    # -----------------------------
    # Interactive Charts
    # -----------------------------
    st.subheader("Skill & Keyword Visualization")
    skill_chart_data = pd.DataFrame({
        "Category": ["Detected Skills", "Missing Skills"],
        "Count": [len(detected), len(missing)],
        "Items": [", ".join(detected), ", ".join(missing)]
    })
    keyword_chart_data = pd.DataFrame({
        "Category": ["Matched Keywords", "Missing Keywords"],
        "Count": [len(matched_kw), len(missing_kw)],
        "Items": [", ".join(matched_kw), ", ".join(missing_kw)]
    })

    st.write("**Skills Overview:**")
    st.bar_chart(skill_chart_data.set_index("Category")["Count"])
    selected_skill = st.radio("Select skill category to view details", ["Detected Skills", "Missing Skills"])
    st.table(pd.DataFrame({"Skills": skill_chart_data.loc[skill_chart_data['Category']==selected_skill, "Items"].values[0].split(", ")}))

    st.write("**Job Keywords Overview:**")
    st.bar_chart(keyword_chart_data.set_index("Category")["Count"])
    selected_kw = st.radio("Select keyword category to view details", ["Matched Keywords", "Missing Keywords"])
    st.table(pd.DataFrame({"Keywords": keyword_chart_data.loc[keyword_chart_data['Category']==selected_kw, "Items"].values[0].split(", ")}))

    # -----------------------------
    # AI Resume Suggestions
    # -----------------------------
    with st.expander("💡 AI Resume Improvement Suggestions"):
        with st.spinner("Generating AI suggestions..."):
            suggestions = generate_resume_suggestions(resume_text, job_description)
            st.markdown(suggestions)