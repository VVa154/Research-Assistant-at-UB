# UB Research Assistant

**UB Research Assistant** is an AI-powered research assistant designed for the University at Buffalo community. It helps students and faculty discover, summarize, and explore relevant academic research using generative AI.

## 🚀 Features
- 🔍 Summarize research papers from Semantic Scholar and arXiv
- 📚 Search and view UB faculty-authored research papers
- 🤝 Find UB faculty for potential research collaboration
- ✍️ Collect feedback from users

## 🧠 Powered By
- Streamlit
- Python
- Ollama (local LLM – replace with OpenAI for cloud)
- pandas, requests

## 📁 Files
- `ub_research_assistant.py` – Main Streamlit app
- `ub_papers.json` – Sample UB research paper database
- `requirements.txt` – Python dependencies

## 🌐 Deployment
To deploy using Streamlit Cloud:
1. Fork or clone this repo
2. Push to a public GitHub repository
3. Visit [streamlit.io/cloud](https://streamlit.io/cloud)
4. Connect your GitHub and deploy!

> **Note:** For public deployment, replace Ollama (localhost) with a hosted model like OpenAI.

## 📝 Feedback
Feedback is saved locally in `feedback_log.csv`. Use Google Sheets or a database for cloud-safe storage.

---

© 2025 University at Buffalo – This is an academic prototype project.
