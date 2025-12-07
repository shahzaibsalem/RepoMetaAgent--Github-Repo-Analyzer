import streamlit as st
from PIL import Image
import time
import json 
from app import run_assembly_line_analysis
import streamlit.components.v1 as components


# ------------------------------
# PAGE STYLE
# ------------------------------
PAGE_CSS = """
<style>
/* Import a modern, techy font */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap');

/* Base Streamlit overrides */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Base App Style */
.stApp {
    background: linear-gradient(145deg, #0f0c29, #2b1c43, #150f3b); /* Darker, richer background */
    color: #f0f0ff; /* Light, slightly bluish text */
    font-family: 'Rajdhani', sans-serif; /* Techy font for body text */
}

/* Glowing Title - Now with Orbitron Font and Continuous Gradient Fill */
.big-title {
    font-size: 4rem;
    font-weight: 700;
    text-align: center;
    text-transform: uppercase;
    
    /* Dashing Font */
    font-family: 'Orbitron', sans-serif;
    
    /* Continuous Gradient Text Effect */
    background-image: linear-gradient(90deg, #ff00c3, #00eaff, #ff00c3, #00eaff); /* Seamlessly repeating gradient */
    background-size: 200% 100%; /* Twice the width for animation */
    -webkit-background-clip: text;
    
    /* Text Shadow Glow */
    text-shadow: 0 0 3px #00eaff, 0 0 4px #ff00c3, 0 0 6px #00eaff;
    animation: pulseGlow 5s infinite alternate ease-in-out, moveGradient 10s linear infinite;
    letter-spacing: 7px; /* Increased letter spacing */
    padding-top: 20px;
}

/* Pulse/Breathing Glow Animation */
@keyframes pulseGlow {
    0% { opacity: 1; text-shadow: 0 0 2px #00eaff, 0 0 6px #ff00c3; }
    100% { opacity: 0.9; text-shadow: 0 0 4px #ff00c3, 0 0 6px #00eaff; }
}

/* Continuous Color Movement Animation */
@keyframes moveGradient {
    0% { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
}

.sub-text {
    text-align: center;
    font-size: 1.5rem;
    color: #99d9ea;
    # text-shadow: 0 0 #99d9ea;
    margin-top: 14px;
    margin-bottom: 40px;
}

/* Hero Icon Replacement */
.hero-icon-container {
    text-align: center;
    margin: 30px 0;
}
.hero-icon {
    font-size: 8rem;
    color: #00eaff;
    text-shadow: 0 0 10px #00eaff, 0 0 30px #00eaff, 0 0 10px rgba(0, 234, 255, 0.2);
    animation: rotateIcon 15s infinite linear;
    display: inline-block;
}

@keyframes rotateIcon {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Animated Button */
.stButton>button {
    background: #0f0c29;
    padding: 15px 40px;
    border-radius: 8px;
    color: #f0f0ff !important;
    border: 2px solid #00eaff;
    font-weight: 700;
    font-size: 20px;
    letter-spacing: 1px;
    box-shadow: 0 0 15px rgba(0, 234, 255, 0.5);
    transition: all 0.4s ease-in-out;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    margin-top: 40px;
    margin-bottom: 40px;
}

.stButton>button:hover {
    transform: translateY(-2px) scale(1.00);
    border-color: #ff00c3;
    box-shadow: 0 0 10px #ff00c3, 0 0 10px rgba(255, 0, 195, 0.2);
    color: white !important;
}

/* Styling for the custom input prompt box */
.info-prompt-box {
    text-align: center;
    padding: 20px;
    border-radius: 10px;
    background: rgba(0, 234, 255, 0.1); /* Light cyan background */
    border: 1px solid #00eaff;
    box-shadow: 0 0 10px #00eaff, 0 0 10px rgba(0, 234, 255, 0.1); /* Blue neon glow */
    color: #f0f0ff;
    font-size: 1.2rem;
    font-weight: 350;
    margin-top: 40px;
}


/* --- TEXT INPUT STYLING --- */
/* Target the actual input field for base styling */
.stTextInput > div > div > input {
    background-color: #1a1538; /* Dark interior for the input field */
    color: #f0f0ff;
    border: 2px solid #2b1c43; /* Subtle border matching the theme */
    border-radius: 8px;
    padding: 12px 15px;
    font-size: 1.1rem;
    box-shadow: none;
    transition: all 0.3s ease-in-out;
}

/* Focus state: Add neon glow */
.stTextInput > div > div > input:focus {
    border-color: #00eaff;
    box-shadow: 0 0 10px #00eaff, 0 0 20px rgba(0, 234, 255, 0.4);
    outline: none; /* Remove default outline */
}

/* Placeholder style */
.stTextInput > div > div > input::placeholder {
    color: #7d7d8e;
    font-style: italic;
}


/* Glowing Info Cards */
.info-card-container {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: space-around;
    margin: 40px 0;
}

.info-card {
    flex: 1 1 300px; /* Responsive size */
    max-width: 320px;
    padding: 25px;
    border-radius: 12px;
    background: rgba(15, 12, 41, 0.7); /* Semi-transparent background */
    border: 1px solid rgba(0, 234, 255, 0.2);
    box-shadow: 0 0 10px rgba(0, 234, 255, 0.4); /* Subtle glow */
    transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
    animation: float 4s infinite alternate ease-in-out; /* Subtle floating animation */
}

/* Custom glow for each card to cycle colors */
.info-card:nth-child(1) { animation-delay: 0s; }
.info-card:nth-child(2) { animation-delay: -0.8s; }
.info-card:nth-child(3) { animation-delay: -1.6s; }
.info-card:nth-child(4) { animation-delay: -2.4s; }
.info-card:nth-child(5) { animation-delay: -3.2s; }

.info-card:hover {
    transform: translateY(-8px) scale(1.03);
    box-shadow: 0 5px 40px rgba(255, 0, 195, 0.2); /* Stronger hover glow (magenta) */
    border-color: #ff00c3;
}

@keyframes float {
    0% { transform: translateY(0px); }
    100% { transform: translateY(-8px); }
}

.card-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #00eaff;
    margin-bottom: 10px;
}


/* --- FILE TREE STYLING (VS Code Look) --- */

.file-tree-container {
    background: #1e1e1e; /* VS Code dark background */
    color: #cccccc;
    padding: 15px;
    border-radius: 8px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 0.95rem;
    border: 1px solid rgba(255, 0, 195, 0.2); /* Magenta outline */
    box-shadow: 0 0 15px rgba(255, 0, 195, 0.2);
    overflow-x: auto;
}

.file-tree-list {
    list-style: none;
    padding-left: 0;
    margin: 0;
}

.file-tree-list .file-tree-list {
    padding-left: 20px; /* Indentation for nested items */
}

.tree-node {
    line-height: 1.8;
    white-space: nowrap;
}

.folder-name {
    color: #77b3ff; /* Blue folder color */
    font-weight: 600;
}

.file-name {
    color: #cccccc; /* Default file name color */
}

.icon-folder {
    color: #ffcc00; /* Yellow folder icon color */
    margin-right: 5px;
    font-size: 0.8em;
    display: inline-block;
    /* transform: rotate(90deg); Removed this to let st.expander handle open/close icon */
}

.icon-file {
    color: #ff00c3; /* Magenta file icon color (using # as placeholder) */
    margin-right: 5px;
    font-size: 0.9em;
}

/* --- END FILE TREE STYLING --- */


/* Result Cards - Solid, professional look */
.result-card-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #ff00c3; /* Magenta highlight */
    margin-top: 30px;
    margin-bottom: 10px;
    border-bottom: 2px solid rgba(255, 0, 195, 0.3);
    padding-bottom: 5px;
}

.result-card-content {
    padding: 20px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08); /* Lighter background for readability */
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 15px rgba(255, 0, 195, 0.2);
    white-space: pre-wrap;
    line-height: 1.6;
}

/* --- KEYWORD TAG STYLING --- */
.tag-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 0;
}

.tag-item {
    background-color: #00eaff; /* Cyan background for primary tags */
    color: #0f0c29; /* Dark text on bright background */
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 700;
    box-shadow: 0 0 10px rgba(0, 234, 255, 0.8); /* Stronger cyan glow */
    transition: all 0.2s ease-in-out;
    cursor: default;
    text-transform: uppercase;
}
.tag-item-secondary {
    background-color: #ff00c3; /* Magenta background for secondary tags */
    color: #0f0c29; 
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 700;
    box-shadow: 0 0 10px rgba(255, 0, 195, 0.8); /* Stronger magenta glow */
    transition: all 0.2s ease-in-out;
    cursor: default;
    text-transform: uppercase;
}

/* Custom styling for the JSON output box (must override Streamlit's style) */
.stJson {
    border: 1px solid #00eaff;
    box-shadow: 0 0 10px rgba(0, 234, 255, 0.5);
    border-radius: 8px;
    padding: 10px;
}
</style>
"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------

FILE_ICONS = {
    ".py": "🐍",
    ".md": "📄",
    ".html": "🌐",
    ".css": "🎨",
    ".js": "📜",
    ".png": "🖼️",
    ".jpg": "🖼️",
    ".jpeg": "🖼️",
    ".gif": "🎞️",
    ".pdf": "📕",
}

FOLDER_ICON = "📁"
FILE_ICON_DEFAULT = "📄"


if "is_analysis_running" not in st.session_state:
    st.session_state.is_analysis_running = False
    

def _render_keywords_html(keywords, tag_class='tag-item'):
    """Renders a list of keywords as HTML tags."""
    if isinstance(keywords, str):
        # Convert comma-separated string to a list
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    elif not isinstance(keywords, list):
        # Handle case where it's a single keyword string without commas
        keywords = [keywords]

    tags_html = "".join([f"<div class='{tag_class}'>{keyword.replace('-', ' ').title()}</div>" for keyword in keywords])
    return f"<div class='tag-container'>{tags_html}</div>"


def render_suggested_title(data):
    """Render suggested title (handles dict, list, JSON string, or plain text)."""
    import json

    if not data:
        return "<div class='title-box'>No title available</div>"

    # If JSON string → decode it
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            # It's just a plain title string
            return f"<div class='result-card-content'><b>{data}</b></div>"

    # If list → take first element
    if isinstance(data, list):
        data = data[0] if data else None

    # If dict → extract field
    if isinstance(data, dict):
        title = data.get("suggested_title") or list(data.values())[0]
    else:
        title = data

    # If list of words → join
    if isinstance(title, list):
        title = ", ".join(title)

    return f"<div class='result-card-content'><b>{title}</b></div>"


def render_github_topics(topics, tag_class='tag-item'):
    """Render GitHub topics as tags using existing UI style."""

    if not topics:
        return "<div class='tag-container'>No GitHub topics found.</div>"

    if isinstance(topics, str):
        topics = topics.replace('```json', '').replace('```JSON', '').strip()
        topics = topics.replace('```', '').strip()
        
        try:
            topics = json.loads(topics)
        except json.JSONDecodeError as e:

            return f"<div class='tag-container'><div class='{tag_class}'>Parsing Error: {str(e)}</div></div>"


    # --- DICTIONARY LOGIC ---
    if isinstance(topics, dict):
        # Extract the list of topics from the dictionary, using both casing
        topics = topics.get("GITHUB_TOPICS") or topics.get("github_topics")

    # Ensure final result is a list
    if not isinstance(topics, list):
        topics = []
        
    # Rest of the function for rendering tags
    tags_html = "".join(
        f"<div class='{tag_class}'>{topic.replace('-', ' ').title()}</div>"
        for topic in topics
        if topic
    )

    return f"<div class='tag-container'>{tags_html}</div>"


def render_seo_keywords(topics, tag_class='tag-item'):
    """Render SEO keywords as tags."""

    if not topics:
        return "<div class='tag-container'>No SEO keywords found.</div>"

    # --- CRITICAL CLEANING STEP HERE (from previous turns) ---
    if isinstance(topics, str):
        topics = topics.replace('```json', '').replace('```JSON', '').strip().replace('```', '').strip()
        try:
            topics = json.loads(topics)
        except json.JSONDecodeError:
            pass # Keep topics as string if parsing fails

    # --- DICTIONARY LOGIC ---
    if isinstance(topics, dict):
        # Extract the value (which is the comma-separated string)
        topics = topics.get("SEO_KEYWORDS") or topics.get("seo_keywords")

    # --- KEY FIX: CONVERT STRING TO LIST FOR TAGS ---
    if isinstance(topics, str):
        # Split the comma-separated string into a list of keywords
        topics = [k.strip() for k in topics.split(',') if k.strip()]
    elif not isinstance(topics, list):
        topics = []
        
    # Rest of the function for rendering tags
    tags_html = "".join(
        f"<div class='{tag_class}'>{topic.replace('-', ' ').title()}</div>"
        for topic in topics
        if topic
    )

    return f"<div class='tag-container'>{tags_html}</div>"


def render_seo_description(topics):
    """Render SEO description as a single block of text."""

    if not topics:
        return "<div class='result-card-content'>No SEO description found.</div>"

    # --- CRITICAL CLEANING STEP HERE (from previous turns) ---
    if isinstance(topics, str):
        topics = topics.replace('```json', '').replace('```JSON', '').strip().replace('```', '').strip()
        try:
            topics = json.loads(topics)
        except json.JSONDecodeError:
            pass # Keep topics as string if parsing fails

    # --- DICTIONARY LOGIC ---
    if isinstance(topics, dict):
        # Extract the description text string
        description_text = topics.get("SEO_DESCRIPTION") or topics.get("seo_description")
    else:
        # If input was the description string itself
        description_text = str(topics)
        
    # Final check and rendering
    if isinstance(description_text, str) and description_text.strip():
        # Render as plain text inside a div, not as a list of tags
        return f"<div class='result-card-content'><p>{description_text.strip()}</p></div>"
    else:
        return "<div class='result-card-content'>No SEO description found.</div>"


def render_file_tree(structure, level=0):
    """
    Recursively render a folder/file tree using Streamlit expanders.
    Folders become expanders, files become markdown lines with indentation.
    """
    indent = "&nbsp;&nbsp;" * (level * 2)  # HTML spaces for indentation

    for name, content in structure.items():
        is_folder = isinstance(content, dict)

        if is_folder:
            # Folder as an expander
            with st.expander(f"{indent}{FOLDER_ICON} **{name}**", expanded=(level==0)):
                render_file_tree(content, level=level+1)
        else:
            # File: add icon based on extension
            ext = "." + name.split(".")[-1] if "." in name else ""
            icon = FILE_ICONS.get(ext, FILE_ICON_DEFAULT)
            st.markdown(f"{indent}{icon} {name}", unsafe_allow_html=True)



def render_review_report(review_report_str):

    review_text = ""

    if isinstance(review_report_str, dict):
        review_text = review_report_str.get("review_report", "")

    elif isinstance(review_report_str, str):
        try:
            parsed = json.loads(review_report_str)
            if isinstance(parsed, dict) and "review_report" in parsed:
                review_text = parsed["review_report"]
            else:
                review_text = review_report_str
        except:
            # Not valid JSON → remove leading key manually
            if '"review_report":' in review_report_str:
                review_text = review_report_str.split('"review_report":', 1)[1]
            else:
                review_text = review_report_str

    review_text = review_text.strip().lstrip('{"').rstrip('"}').strip()

    return review_text



# ------------------------------
# HERO SECTION
# ------------------------------
st.markdown("<div class='big-title'>Repo-Meta-Agent</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-text'>AI-Powered Metadata • Tags • SEO • Review • Summary</div>", unsafe_allow_html=True)

# Animated Icon Replacement for the removed image
st.markdown("""
<div class='hero-icon-container'>
    <span class='hero-icon'>⚡</span>
</div>
""", unsafe_allow_html=True)

st.write("---")

# ------------------------------
# PROJECT INFORMATION CARDS (Glowing and Moving)
# ------------------------------
st.markdown("## The Power of AI-Driven Repository Analysis")
st.markdown("""
<div class='info-card-container'>
    <div class='info-card'>
        <div class='card-title'>Comprehensive Project Insight</div>
        <p>We perform deep semantic analysis across your entire repository, moving beyond the README to generate accurate project summaries, architectural overviews, and detailed documentation recommendations.</p>
    </div>
    <div class='info-card'>
        <div class='card-title'>Maximized Project Visibility</div>
        <p>Instantly receive optimized metadata, including high-impact titles, descriptions, and relevant keywords. Ensure your repository achieves maximum organic reach and discoverability across developer platforms.</p>
    </div>
    <div class='info-card'>
        <div class='card-title'>Expert Code Audit & Review</div>
        <p>Get a structured quality report highlighting potential security concerns, code complexity issues, and performance bottlenecks. We deliver the professional audit and actionable insights your project needs, instantly.</p>
    </div>
    <div class='info-card'>
        <div class='card-title'>Automated Stack Detection</div>
        <p>Immediately identify all programming languages, major frameworks, and external dependencies used. This provides a clear, high-level technology overview for rapid onboarding and assessment.</p>
    </div>
    <div class='info-card'>
        <div class='card-title'>Project Health Metrics</div>
        <p>Receive crucial metrics on repository health, including cyclomatic complexity scores, code churn rates, and suggested refactoring areas to improve long-term maintainability and reduce technical debt.</p>
    </div>
</div>
""", unsafe_allow_html=True)


st.write("---")

# ------------------------------
# INPUT SECTION
# ------------------------------
st.markdown("### 🔗 Enter GitHub Repository URL")
repo_url = st.text_input("", placeholder="https://github.com/username/repo", key="repo_input")
start_analysis = st.button("🔍 Analyze Repository" , disabled = st.session_state.is_analysis_running)
# ------------------------------
# EXECUTION & LOADING
# ------------------------------
if start_analysis and repo_url.strip():
    st.session_state.is_analysis_running = True
    with st.spinner("⚡ Initializing AI ..."):
        time.sleep(1)

    progress = st.progress(0, text="Loading...")
    
    steps = [
        "Fetching Repository Data...",
        "Parsing File Contents...",
        "Generating Core Metadata...",
        "Extracting SEO Keywords...",
        "Drafting Summaries...",
        "Running Expert Review Agent...",
        "Synthesizing Final Report..."
    ]

    for i, step in enumerate(steps):
        progress.progress((i + 1)/len(steps), text=f"✨ {step}")
        time.sleep(4)

    try:
        final_result = run_assembly_line_analysis(repo_url)
        st.success("✅ Repo Analysis Complete! Data Synthesized.")


        # ------------------------------
        # DISPLAY RESULTS
        # ------------------------------
        # 1. Project Summary
        # st.markdown("<div class='result-card-title'>📘 Project Summary</div>", unsafe_allow_html=True)
        # st.markdown(f"<div class='result-card-content'>{final_result['project_summary']}</div>", unsafe_allow_html=True)

        # 2. Missing Documentation / Improvements
        st.markdown("<div class='result-card-title'>📝 Missing Documentation / Improvements</div>", unsafe_allow_html=True)
        missing_docs = _render_keywords_html(final_result['missing_documentation'] , tag_class='tag-item-secondary')
        st.markdown(f"{missing_docs}", unsafe_allow_html=True)

        # 3. Existing GitHub Topics/Keywords (Cyan Tags)
        st.markdown("<div class='result-card-title'>🏷️ Existing Keywords</div>", unsafe_allow_html=True)
        Github_Topics = _render_keywords_html(final_result['github_keywords_extracted'], tag_class='tag-item')
        st.markdown(f"{Github_Topics}", unsafe_allow_html=True)

        # 4. Suggested Keywords for Repo 
        st.markdown("<div class='result-card-title'>🎯 Suggested Keywords for Repo</div>", unsafe_allow_html=True)
        suggested_keywords_html = _render_keywords_html(final_result['keywords'], tag_class='tag-item')
        st.markdown(f"{suggested_keywords_html}", unsafe_allow_html=True)

        # 5. Related GitHub Topic
        st.markdown("<div class='result-card-title'>🤝 Related GitHub Topics</div>", unsafe_allow_html=True)
        related_topics_html = render_github_topics(final_result['github_topics'] , tag_class='tag-item')
        st.markdown(f"{related_topics_html}", unsafe_allow_html=True)

        # 6. Suggested SEO Keywords
        st.markdown("<div class='result-card-title'>🏷️ Suggested SEO Keywords</div>", unsafe_allow_html=True)
        suggested_seo_keywords_html = render_seo_keywords(final_result['github_topics'], tag_class='tag-item')
        st.markdown(f"<div class='result-card-content'>{suggested_seo_keywords_html}</div>", unsafe_allow_html=True)

        # 7. Suggested Title
        st.markdown("<div class='result-card-title'>🎯 Suggested Title for Project</div>", unsafe_allow_html=True)
        suggested_title_html = render_suggested_title(final_result['suggested_title'])
        st.markdown(f"<div class='result-card-content'>{suggested_title_html}</div>", unsafe_allow_html=True)

        # 8. Suggested SEO Description
        st.markdown("<div class='result-card-title'>📝 Suggested SEO Description</div>", unsafe_allow_html=True)
        suggested_seo_description_html = render_seo_description(final_result['github_topics'])
        st.markdown(f"<div class='result-card-content'>{suggested_seo_description_html}</div>", unsafe_allow_html=True)
       
        # 9. Short Summary
        st.markdown("<div class='result-card-title'>📄 Short Summary (for Metadata)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-card-content'>{final_result['short_summary']}</div>", unsafe_allow_html=True)

        # 10. Long Summary
        st.markdown("<div class='result-card-title'>📰 Long Summary (for README)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-card-content'>{final_result['long_summary']}</div>", unsafe_allow_html=True)

        # 11. Expert Review Report
        st.markdown("<div class='result-card-title'>🧪 Expert Review Report</div>", unsafe_allow_html=True)
        review_report = render_review_report(final_result["review_report"])
        st.markdown(f"<div class='result-card-content'>{review_report}</div>", unsafe_allow_html=True)

        # 12. Analyzed File Structure (Now Collapsible)
        st.markdown("<div class='result-card-title'>🏗️ Analyzed File Structure</div>", unsafe_allow_html=True)
        
        # Use st.expander for the collapsible/coolapsible feature
        with st.expander("📂 Project File Structure", expanded=True):
         render_file_tree(final_result["file_structure"])

        st.session_state.is_analysis_running = False

    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        st.session_state.is_analysis_running = False

    finally:
       st.session_state.is_analysis_running = False

else:
    st.markdown("""
    <div class='info-prompt-box'>
        👆 Enter a repository URL above and press 'Analyze Repository' to start the AI workflow.
    </div>
    """, unsafe_allow_html=True)