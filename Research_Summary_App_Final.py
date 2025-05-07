import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import pandas as pd
import os
import openai

# ---------------------- CONFIG ----------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
S2_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_URL = "http://export.arxiv.org/api/query"

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="UB Research Assistant", layout="wide")

# ---------------------- UB BRAND STYLES ----------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 85%;
    }
    .ub-header {
        background-color: #005bbb;
        padding: 1.5rem 2rem;
        border-radius: 6px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .ub-header h1 {
        font-size: 28px;
        margin: 0;
    }
    .ub-header p {
        margin-top: 6px;
        font-size: 16px;
        font-weight: 400;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 500;
        padding: 10px 16px;
    }
    .paper-container {
        background-color: #f6faff;
        padding: 20px;
        margin-bottom: 25px;
        border: 1px solid #c3d7f1;
        border-left: 4px solid #005bbb;
        border-radius: 8px;
    }
    .paper-title {
        font-size: 18px;
        font-weight: 600;
        color: #003366;
        margin-bottom: 8px;
    }
    .paper-meta {
        color: #444;
        font-size: 14px;
        margin-bottom: 10px;
    }
    .paper-abstract {
        color: #333;
        font-size: 15px;
        margin-bottom: 10px;
    }
    .relevance-box {
        background-color: #e9efff;
        padding: 10px 15px;
        font-size: 14px;
        border-left: 4px solid #005bbb;
        border-radius: 4px;
        margin-top: 10px;
    }
    .sidebar-content {
        background-color: #f5f8fc;
        padding: 20px;
        border-left: 4px solid #005bbb;
        border-radius: 6px;
        margin-bottom: 2rem;
        font-size: 15px;
        line-height: 1.5;
    }
    .sidebar-header {
        font-weight: 600;
        color: #003366;
        font-size: 17px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------- HEADER ----------------------
st.markdown("""
    <div class="ub-header">
        <h1>UB Research Assistant</h1>
        <p>The UB way to research smarter</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------- SIDEBAR ----------------------
with st.sidebar:
    st.markdown("""
        <div class="sidebar-content">
            <div class="sidebar-header">About This Assistant</div>
            <p>
                This tool acts as a personalized research assistant to students, faculty and researchers
                <ul>
                    <li>Summarize recent papers</li>
                    <li>Explore UB faculty research</li>
                    <li>Find collaboration opportunities</li>
                </ul>
            </p>
            <div class="sidebar-header">Quick Links</div>
            <p>
                <a href="https://www.buffalo.edu/" target="_blank">UB Homepage</a><br>
                <a href="https://library.buffalo.edu/" target="_blank">UB Libraries</a><br>
                <a href="https://csed.buffalo.edu/" target="_blank">Dept. of Computer Science</a>
            </p>
            <div class="sidebar-header">Feedback</div>
            <p>We'd love to hear from you!</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("feedback_form"):
        name = st.text_input("Please enter your name")
        email = st.text_input("Email")
        feedback_text = st.text_area("Your Feedback", height=100)
        submitted = st.form_submit_button("Submit")

        if submitted and name.strip() and feedback_text.strip() and email.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = pd.DataFrame([[timestamp,name.strip(), email.strip(), feedback_text.strip()]],
                                     columns=["Timestamp","Name","Email", "Feedback"])
            file_path = "feedback_log.csv"
            if os.path.exists(file_path):
                existing = pd.read_csv(file_path)
                updated = pd.concat([existing, new_entry], ignore_index=True)
            else:
                updated = new_entry
            updated.to_csv(file_path, index=False)
            st.success("✅ Thank you! Your feedback has been saved.")

# ---------------------- UTILS ----------------------
@st.cache_data
def load_ub_papers():
    with open("ub_papers.json", "r") as f:
        return json.load(f)

import openai

def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following abstract in 2 simple sentences."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message["content"].strip()


def get_relevance_reason(paper, keyword):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Given this paper and the keyword '{keyword}', explain in one line why it is relevant.\n\nTitle: {paper['title']}\nAbstract: {paper['abstract']}"}],
            temperature=0.3
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"(Error: {str(e)})"

def fetch_semantic_scholar(query):
    res = requests.get(S2_URL, params={
        "query": query,
        "fields": "title,abstract,url,authors,year",
        "limit": 5
    })
    return [
        {
            "title": p["title"],
            "abstract": p.get("abstract", ""),
            "url": p.get("url", ""),
            "authors": ", ".join([author["name"] for author in p.get("authors", [])]),
            "year": p.get("year", "N/A")
        } for p in res.json().get("data", []) if p.get("abstract")
    ]

def fetch_arxiv(query):
    url = f"{ARXIV_URL}?search_query=all:{query}&start=0&max_results=3"
    res = requests.get(url)
    root = ET.fromstring(res.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    papers = []
    for entry in root.findall('atom:entry', ns):
        authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
        published = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else "N/A"
        year = published[:4] if published != "N/A" else "N/A"
        papers.append({
            "title": entry.find('atom:title', ns).text.strip(),
            "abstract": entry.find('atom:summary', ns).text.strip(),
            "url": entry.find('atom:id', ns).text.strip(),
            "authors": ", ".join(authors),
            "year": year
        })
    return papers

# ---------------------- MAIN TABS ----------------------
summary_tab, ub_tab, collab_tab = st.tabs(["Summary", "UB Database", "Collaboration Finder"])

with summary_tab:
    st.markdown("### Research Summarizer")
    topic = st.text_input("Enter a keyword to fetch and summarize papers")

    if topic:
        st.info("Fetching papers from Semantic Scholar and arXiv...")
        papers = fetch_semantic_scholar(topic) + fetch_arxiv(topic)

        for paper in papers:
            summary = summarize_text(paper['abstract'])
            st.markdown(f"""
                <div class="paper-container">
                    <div class="paper-title">{paper['title']}</div>
                    <div class="paper-meta">
                        Authors: {paper['authors']}<br>
                        Year: {paper['year']}<br>
                        <a href="{paper['url']}" target="_blank">View Full Paper</a>
                    </div>
                    <details><summary>Abstract</summary>
                    <p class="paper-abstract">{paper['abstract']}</p>
                    </details>
                    <div class="relevance-box"><b>AI Summary:</b> {summary}</div>
                </div>
            """, unsafe_allow_html=True)

with ub_tab:
    st.markdown("### UB Research Paper Archive")
    keyword = st.text_input("Enter a research keyword", key="ub_search")

    if keyword:
        ub_papers = load_ub_papers()
        filtered = []

        with st.spinner("Finding relevant UB papers..."):
            for paper in ub_papers:
                if keyword.lower() in paper['title'].lower() or keyword.lower() in paper['abstract'].lower():
                    explanation = get_relevance_reason(paper, keyword)
                    paper["reason"] = explanation
                    filtered.append(paper)

        if filtered:
            for paper in filtered:
                st.markdown(f"""
                    <div class="paper-container">
                        <div class="paper-title">{paper['title']}</div>
                        <div class="paper-meta">
                            Authors: {', '.join(paper['authors'])}<br>
                            Department: {paper['department']}<br>
                            Email: {paper['email']}<br>
                            Year: {paper['year']}<br>
                            <a href="{paper['link']}" target="_blank">View Full Paper</a>
                        </div>
                        <div class="paper-abstract">{paper['abstract']}</div>
                        <div class="relevance-box"><b>Why Relevant:</b> {paper['reason']}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No matching papers found.")

with collab_tab:
    st.markdown("### UB Professor Collaboration Finder")
    keyword = st.text_input("Enter a research keyword", key="collab_input")

    if keyword:
        ub_papers = load_ub_papers()
        results = [p for p in ub_papers if keyword.lower() in p["title"].lower() or keyword.lower() in p["abstract"].lower()]
        if results:
            for paper in results:
                explanation = get_relevance_reason(paper, keyword)
                st.markdown(f"""
                    <div class="paper-container">
                        <div class="paper-title">{paper['title']}</div>
                        <div class="paper-meta">
                            Authors: {', '.join(paper['authors'])}<br>
                            Department: {paper['department']}<br>
                            Email: {paper['email']}<br>
                            <a href="{paper['link']}" target="_blank">View Full Paper</a>
                        </div>
                        <div class="relevance-box"><b>Why Relevant:</b> {explanation}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No matching faculty found.")
