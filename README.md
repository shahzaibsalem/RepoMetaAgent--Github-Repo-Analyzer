# RepoMetaAgent

### Multi-Agent GitHub Repository Intelligence System

RepoMetaAgent is a deterministic multi-agent system that analyzes any public GitHub repository and converts it into structured, machine-readable intelligence.

Given a repository URL, the system generates:

- Repository title  
- Short and long summaries  
- Keywords and tags  
- Metadata and classification  
- Code review insights  
- Improvement recommendations  
- Documentation gap analysis  
- Unified JSON output  


## 🚀 Why This Project Matters

Understanding a repository manually is slow and inconsistent.

Most tools:
- Rely only on README files  
- Miss structural insights  
- Produce shallow summaries  
- Lack standard output formats  

RepoMetaAgent solves this by using a multi-agent pipeline to perform deep, structured analysis across the entire repository.

This makes it useful for:
- Developer tools  
- AI agents needing repository context  
- Search and indexing systems  
- Documentation automation  
- Repository quality evaluation  


## 🧠 Key Features

- Multi-agent architecture (not a single LLM prompt)  
- Deterministic pipeline using DAG orchestration  
- Structured JSON output  
- Multi-source keyword extraction (LLM + NLP + Gazetteer)  
- Automated code review and recommendations  
- Missing documentation detection  
- Scalable and modular design  


## 🏗 Architecture Overview

The system is built using LangGraph for orchestration and Groq for fast LLM inference.

### Pipeline Flow

    Repository URL
          ↓
    Repo Analyzer Agent
          ↓
    Metadata Agent
          ↓
    Tag Generator Agent
          ↓
    Review & Improvement Agent
          ↓
    Final JSON Output

Each agent operates on a shared structured state, ensuring consistency and reproducibility.


## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/shahzaibsalem/RepoMetaAgent--Github-Repo-Analyzer
```
```bash
cd RepoMetaAgent--Github-Repo-Analyzer
```
---

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**
```bash
venv\Scripts\activate
```

**macOS/Linux**
```bash
source venv/bin/activate
```


### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Set API Key

```bash
export GROQ_API_KEY="your_api_key_here"
```


## ▶️ Usage

Run the full pipeline:

```bash
python code/app.py
```


## 🎥 Live Demo

Click below to watch RepoMetaAgent in action:

[![RepoMetaAgent Demo](https://img.youtube.com/vi/cYkiVOm7qkQ/0.jpg)](https://www.youtube.com/watch?v=cYkiVOm7qkQ)


## 📤 What the Output Will Be

The system generates a structured JSON intelligence bundle containing:

- Repository title and summaries  
- Extracted keywords and tags  
- Structured metadata and classification  
- Code review insights  
- Improvement recommendations  
- Missing documentation analysis  
- Repository structure details  

This output is designed for:
- AI agent consumption  
- Dashboard visualization  
- Search indexing  
- Documentation generation systems  


## 🧪 Testing & Reliability

The system is validated through:

- Unit testing for each agent  
- Integration testing for state transitions  
- End-to-end pipeline testing  
- Schema validation (strict JSON outputs)  
- Failure testing (invalid repositories, missing files)  

This ensures consistent, production-ready results.


## 🔐 Security Considerations

- `.env` files are excluded via `.gitignore`  
- Static analysis only (no code execution)  
- Input validation for repository URLs  
- Prompt injection mitigation  
- Structured JSON output enforcement  


## ⚠️ Limitations

- Large repositories increase processing time  
- Binary files are ignored  
- Requires Groq API access  
- No dynamic code execution  


## 🛣 Roadmap

- Static code analysis integration  
- UML diagram generation  
- Repository similarity search  
- Security vulnerability scanning  
- Advanced scoring metrics  


## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.


## 🎯 Conclusion

RepoMetaAgent transforms GitHub repositories into structured intelligence through a deterministic multi-agent architecture. It enables scalable repository understanding, automated documentation, and AI-ready metadata generation, making it a strong foundation for next-generation developer tools and intelligent systems.
