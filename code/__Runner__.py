import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.let_it_rain import rain
from streamlit_extras.animated_title import animated_title
from streamlit_extras.badges import badge
from PIL import Image
import time

# ------------------------------
# Import Your Main Graph System
# ------------------------------
from app import run_assembly_line_analysis


# ================================
# 🌈 STYLING & ANIMATIONS
# ================================
PAGE_CSS = """
<style>
body {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    background-attachment: fixed;
    color: white !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.big-title {
    font-size: 4rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #00eaff, #ff00c3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sub-text {
    text-align: center;
    font-size: 1.3rem;
    color: #cfcfcf;
    margin-top: -15px;
}

.input-box {
    padding: 20px;
    border-radius: 15px;
    border: 2px solid #4e54c8;
    background: rgba(255,255,255,0.07);
    color: white !important;
}

.stButton>button {
    background: linear-gradient(90deg, #ff00c3, #00eaff);
    padding: 12px 30px;
    border-radius: 30px;
    color: black !important;
    border: none;
    font-weight: 700;
    font-size: 18px;
    transition: 0.4s;
}

.stButton>button:hover {
    transform: scale(1.05);
    background: linear-gradient(90deg, #00eaff, #ff00c3);
    cursor: pointer;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.2);
    margin-bottom: 20px;
}
</style>
"""

st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ================================
# 🎬 HERO SECTION
# ================================
animated_title("🚀 RepoMetaAgent")

st.markdown("<div class='big-title'>Smart AI Repo Analyzer</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-text'>AI-Powered Metadata • Tags • SEO • Review • Summary</div>", unsafe_allow_html=True)

badge(type="github", name="RepoMetaAgent")

# Picture section
st.image("https://i.ibb.co/8zHxVJz/ai-analyze.png", width=450)

st.write("---")

# ================================
# 📝 INPUT SECTION
# ================================
st.markdown("### 🔗 Enter GitHub Repository URL")

repo_url = st.text_input("", placeholder="https://github.com/username/repo", key="repo_input")

start_analysis = st.button("🔍 Analyze Repository")

# ================================
# ⏳ EXECUTION & LOADING
# ================================
if start_analysis and repo_url.strip():

    with st.spinner("⚡ Initializing AI Graphs..."):
        time.sleep(1)

    progress = st.progress(0, text="Loading...")

    steps = [
        "Fetching Repository...",
        "Reading Files...",
        "Generating Metadata...",
        "Extracting Keywords...",
        "Creating SEO Data...",
        "Running Reviewer Agent...",
        "Finalizing Report..."
    ]

    for i, step in enumerate(steps):
        progress.progress((i + 1) / len(steps), text=f"✨ {step}")
        time.sleep(1)

    # Call your backend
    final_result = run_assembly_line_analysis(repo_url)

    st.success("✅ Repo Analysis Complete!")

    st.write("---")
    rain(
        emoji="✨",
        font_size=20,
        falling_speed=3,
        animation_length="infinite"
    )

    # ================================
    # 📊 DISPLAY RESULTS
    # ================================
    st.markdown("## 📘 Project Summary")
    st.markdown(f"<div class='card'>{final_result['project_summary']}</div>", unsafe_allow_html=True)

    st.markdown("## 📝 Missing Documentation")
    st.markdown(f"<div class='card'>{final_result['missing_documentation']}</div>", unsafe_allow_html=True)

    st.markdown("## 🏷️ Keywords")
    st.markdown(f"<div class='card'>{final_result['keywords']}</div>", unsafe_allow_html=True)

    st.markdown("## 🏗️ File Structure")
    st.json(final_result["file_structure"])

    st.markdown("## 🎯 Suggested Title")
    st.markdown(f"<div class='card'><b>{final_result['suggested_title']}</b></div>", unsafe_allow_html=True)

    st.markdown("## 📄 Short Summary")
    st.markdown(f"<div class='card'>{final_result['short_summary']}</div>", unsafe_allow_html=True)

    st.markdown("## 📰 Long Summary")
    st.markdown(f"<div class='card'>{final_result['long_summary']}</div>", unsafe_allow_html=True)

    st.markdown("## 🧪 Review Report")
    st.markdown(f"<div class='card'>{final_result['review_report']}</div>", unsafe_allow_html=True)

else:
    st.info("👆 Enter a repository URL above to begin analysis.")

