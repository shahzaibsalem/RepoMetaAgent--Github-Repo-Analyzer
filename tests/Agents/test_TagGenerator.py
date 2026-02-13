from unittest.mock import patch
import spacy
import pytest
from unittest.mock import MagicMock
from code.Agents.MetaDataAgent.nodes.TagGenerator import make_llm_extractor_node
from code.Agents.MetaDataAgent.nodes.TagGenerator import make_gazetteer_tag_generator_node
from code.Agents.MetaDataAgent.nodes.TagGenerator import make_spacy_extractor_node
from code.Agents.MetaDataAgent.nodes.TagGenerator import assign_tag_types
from code.Agents.MetaDataAgent.nodes.TagGenerator import union_keywords_node

FAKE_GAZETTEER = {
    "Python": "language",
    "Docker": "tool",
    "Flask": "framework",
}


def test_make_llm_extractor_node(mock_groq_manager):
    mock_client = mock_groq_manager.get_client.return_value

    # Proper mocked LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='''
        {
            "tags": [
                {"name": "python"},
                {"name": "testing"},
                {"name": "unit-tests"}
            ]
        }
        '''))
    ]

    mock_client.chat.completions.create.return_value = mock_response

    node = make_llm_extractor_node(mock_groq_manager)

    state = {"readme_md": "sample readme text"}

    result = node(state)


    assert "llm_keywords" in result
    assert isinstance(result["llm_keywords"], list)
    assert result["llm_keywords"] == ["python", "testing", "unit-tests"]
    mock_client.chat.completions.create.assert_called_once()





# -------------------------------------------------
# 1. Basic extraction
# -------------------------------------------------
@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_basic(mock_loader):

    mock_loader.return_value = FAKE_GAZETTEER

    node = make_gazetteer_tag_generator_node()

    state = {
        "readme_md": "Built with Python and Docker."
    }

    result = node(state)

    assert result["gazetteer_keywords"] == [
        {"name": "python", "type": "language"},
        {"name": "docker", "type": "tool"},
    ]


# -------------------------------------------------
# 2. No match
# -------------------------------------------------
@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_no_match(mock_loader):

    mock_loader.return_value = FAKE_GAZETTEER

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": "Nothing here"})

    assert result["gazetteer_keywords"] == []


# -------------------------------------------------
# 3. Empty text
# -------------------------------------------------
@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_empty_text(mock_loader):

    mock_loader.return_value = FAKE_GAZETTEER

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": ""})

    assert result["gazetteer_keywords"] == []


# -------------------------------------------------
# 4. Deduplication
# -------------------------------------------------
@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_deduplicates(mock_loader):

    mock_loader.return_value = {"Python": "language"}

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": "Python python PYTHON"})

    assert result["gazetteer_keywords"] == [
        {"name": "python", "type": "language"}
    ]


# -------------------------------------------------
# 5. Case insensitive
# -------------------------------------------------
@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_case_insensitive(mock_loader):

    mock_loader.return_value = {"Docker": "tool"}

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": "docker DOCKER DoCkEr"})

    assert result["gazetteer_keywords"] == [
        {"name": "docker", "type": "tool"}
    ]


# -------------------------------------------------
# 6. Loader called once
# -------------------------------------------------
@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_loader_called_once(mock_loader):

    mock_loader.return_value = {}

    make_gazetteer_tag_generator_node()

    mock_loader.assert_called_once()




# -------------------------------------------------
# helper
# -------------------------------------------------

def has_model():
    try:
        spacy.load("en_core_web_sm")
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not has_model(), reason="SpaCy model not installed")


# -------------------------------------------------
# 1. basic extraction
# -------------------------------------------------

def test_basic_keyword_extraction():
    node = make_spacy_extractor_node()

    text = "This backend server is built with Python and Docker."

    result = node({"readme_md": text})
    keywords = result["spacy_keywords"]

    assert isinstance(keywords, list)
    assert len(keywords) > 0

    assert "python" in keywords
    assert "docker" in keywords
    assert "server" in keywords


# -------------------------------------------------
# 2. empty input
# -------------------------------------------------

def test_empty_text_returns_empty():
    node = make_spacy_extractor_node()

    result = node({"readme_md": ""})

    assert result["spacy_keywords"] == []


# -------------------------------------------------
# 3. duplicates removed
# -------------------------------------------------

def test_duplicates_removed():
    node = make_spacy_extractor_node()

    text = "Python Python Python backend backend server server"

    result = node({"readme_md": text})
    keywords = result["spacy_keywords"]

    assert len(keywords) == len(set(keywords))


# -------------------------------------------------
# 4. order sorted
# -------------------------------------------------

def test_keywords_are_sorted():
    node = make_spacy_extractor_node()

    text = "Docker Python backend server"

    result = node({"readme_md": text})
    keywords = result["spacy_keywords"]

    assert keywords == sorted(keywords)


# -------------------------------------------------
# 5. real-world README paragraph
# -------------------------------------------------

def test_real_readme_paragraph():
    node = make_spacy_extractor_node()

    text = """
    FastAPI microservice for GitHub repository analysis.
    Extracts metadata, generates tags, and deploys using Docker containers.
    """

    result = node({"readme_md": text})
    keywords = result["spacy_keywords"]

    expected_terms = ["docker", "metadata"]

    for term in expected_terms:
        assert term in keywords


# -------------------------------------------------
# 6. very large text (stress test)
# -------------------------------------------------

def test_large_text_does_not_crash():
    node = make_spacy_extractor_node()

    text = ("Python backend service. " * 2000)

    result = node({"readme_md": text})

    assert isinstance(result["spacy_keywords"], list)





# -------------------------------------------------
# 1. basic merge
# -------------------------------------------------

def test_basic_union():
    state = {
        "spacy_keywords": ["python", "backend"],
        "gazetteer_keywords": [{"name": "docker"}],
        "llm_keywords": ["api"]
    }

    result = union_keywords_node(state)

    assert result["union_list"] == ["api", "backend", "docker", "python"]


# -------------------------------------------------
# 2. duplicates across sources removed
# -------------------------------------------------

def test_duplicates_removed():
    state = {
        "spacy_keywords": ["python", "docker"],
        "gazetteer_keywords": [{"name": "python"}],
        "llm_keywords": ["DOCKER"]
    }

    result = union_keywords_node(state)

    assert result["union_list"] == ["docker", "python"]


# -------------------------------------------------
# 3. mixed types handled
# -------------------------------------------------

def test_mixed_types_and_invalid_items():
    state = {
        "spacy_keywords": ["python", 123, None],
        "gazetteer_keywords": [{"name": "docker"}, {"wrong": "x"}],
        "llm_keywords": [True, "api"]
    }

    result = union_keywords_node(state)

    assert "python" in result["union_list"]
    assert "docker" in result["union_list"]
    assert "api" in result["union_list"]


# -------------------------------------------------
# 5. empty input
# -------------------------------------------------

def test_empty_state():
    result = union_keywords_node({})

    assert result["union_list"] == []


# -------------------------------------------------
# 6. large stress input
# -------------------------------------------------

def test_large_scale():
    state = {
        "spacy_keywords": ["python"] * 1000,
        "gazetteer_keywords": [{"name": "docker"}] * 1000,
        "llm_keywords": ["api"] * 1000,
    }

    result = union_keywords_node(state)

    assert result["union_list"] == ["api", "docker", "python"]


# -------------------------------------------------
# 7. output contract
# -------------------------------------------------

def test_output_contract():
    state = {
        "spacy_keywords": ["Python"],
        "gazetteer_keywords": [{"name": "Docker"}],
        "llm_keywords": ["API"]
    }

    result = union_keywords_node(state)

    keywords = result["union_list"]

    assert isinstance(keywords, list)
    assert all(isinstance(k, str) for k in keywords)
    assert keywords == sorted(keywords)



import pytest
from unittest.mock import MagicMock
import json

@pytest.fixture
def mock_groq_client():
    """Return a mock Groq client with default behavior."""
    client = MagicMock()
    response_mock = MagicMock()
    response_mock.choices = [MagicMock()]
    response_mock.choices[0].message = MagicMock()
    response_mock.choices[0].message.content = json.dumps({
        "tags": [
            {"name": "python", "type": "language"},
            {"name": "docker", "type": "container"}
        ]
    })
    client.chat.completions.create = MagicMock(return_value=response_mock)
    return client

@pytest.fixture
def mock_groq_manager(mock_groq_client):
    """Return a mock GroqClientManager that returns the mock client."""
    mgr = MagicMock()
    mgr.get_client.return_value = mock_groq_client
    mgr.get_model.return_value = "dummy-model"
    return mgr

@pytest.fixture
def mock_config(monkeypatch):
    """Patch load_tag_type_assigner_config to return dummy config."""
    cfg = {
        "llm": "dummy-model",
        "role": "system-role",
        "instruction": "Assign types",
        "output_format": "{}",
        "output_constraints": "",
        "style_or_tone": "neutral",
        "goal": "test"
    }
    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tag_type_assigner_config",
        lambda path: cfg
    )
    return cfg

def test_assign_tag_types_normal(mock_groq_manager, mock_config):
    keywords = ["python", "docker"]
    result = assign_tag_types(keywords)
    assert isinstance(result, list)
    assert all("name" in t and "type" in t for t in result)
    assert result[0]["name"] == "python"

def test_assign_tag_types_malformed_json(mock_groq_manager, monkeypatch, mock_config):
    # Make LLM return invalid JSON
    def bad_json_client(path=None):
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message = MagicMock()
        response.choices[0].message.content = "not json"
        client.chat.completions.create = MagicMock(return_value=response)
        return client
    monkeypatch.setattr(mock_groq_manager, "get_client", lambda: bad_json_client())

    result = assign_tag_types(["python"])
    assert result == []

def test_assign_tag_types_empty_config(monkeypatch, mock_groq_manager):
    # Patch config loader to return None
    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tag_type_assigner_config",
        lambda path: None
    )
    result = assign_tag_types(["python"])
    assert result == []

def test_assign_tag_types_llm_returns_list(mock_groq_manager, monkeypatch, mock_config):
    # Make LLM return a list instead of dict
    def list_client(path=None):
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message = MagicMock()
        response.choices[0].message.content = json.dumps([
            {"name": "python", "type": "language"}
        ])
        client.chat.completions.create = MagicMock(return_value=response)
        return client
    monkeypatch.setattr(mock_groq_manager, "get_client", lambda: list_client())

    result = assign_tag_types(["python"])
    assert isinstance(result, list)
    assert result[0]["name"] == "python"
