from unittest.mock import patch
import json
import spacy
import pytest
from unittest.mock import MagicMock
from code.Agents.MetaDataAgent.nodes.TagGenerator import make_llm_extractor_node, make_selector_node
from code.Agents.MetaDataAgent.nodes.TagGenerator import make_gazetteer_tag_generator_node
from code.Agents.MetaDataAgent.nodes.TagGenerator import make_spacy_extractor_node
from code.Agents.MetaDataAgent.nodes.TagGenerator import assign_tag_types
from code.Agents.MetaDataAgent.nodes.TagGenerator import union_keywords_node

FAKE_GAZETTEER = {
    "Python": "language",
    "Docker": "tool",
    "Flask": "framework",
}



# -------------------------------------------------
# Tests for llm node
# -------------------------------------------------


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
# Tests for gazetteer node
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

@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_no_match(mock_loader):

    mock_loader.return_value = FAKE_GAZETTEER

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": "Nothing here"})

    assert result["gazetteer_keywords"] == []


@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_empty_text(mock_loader):

    mock_loader.return_value = FAKE_GAZETTEER

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": ""})

    assert result["gazetteer_keywords"] == []


@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_deduplicates(mock_loader):

    mock_loader.return_value = {"Python": "language"}

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": "Python python PYTHON"})

    assert result["gazetteer_keywords"] == [
        {"name": "python", "type": "language"}
    ]

@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_gazetteer_case_insensitive(mock_loader):

    mock_loader.return_value = {"Docker": "tool"}

    node = make_gazetteer_tag_generator_node()

    result = node({"readme_md": "docker DOCKER DoCkEr"})

    assert result["gazetteer_keywords"] == [
        {"name": "docker", "type": "tool"}
    ]


@patch("code.Agents.MetaDataAgent.nodes.TagGenerator.load_gazetteer_data")
def test_loader_called_once(mock_loader):

    mock_loader.return_value = {}

    make_gazetteer_tag_generator_node()

    mock_loader.assert_called_once()




# -------------------------------------------------
# Tests for spacy node
# -------------------------------------------------

def has_model():
    try:
        spacy.load("en_core_web_sm")
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not has_model(), reason="SpaCy model not installed")


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


def test_empty_text_returns_empty():
    node = make_spacy_extractor_node()

    result = node({"readme_md": ""})

    assert result["spacy_keywords"] == []


def test_duplicates_removed():
    node = make_spacy_extractor_node()

    text = "Python Python Python backend backend server server"

    result = node({"readme_md": text})
    keywords = result["spacy_keywords"]

    assert len(keywords) == len(set(keywords))


def test_keywords_are_sorted():
    node = make_spacy_extractor_node()

    text = "Docker Python backend server"

    result = node({"readme_md": text})
    keywords = result["spacy_keywords"]

    assert keywords == sorted(keywords)


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


def test_large_text_does_not_crash():
    node = make_spacy_extractor_node()

    text = ("Python backend service. " * 2000)

    result = node({"readme_md": text})

    assert isinstance(result["spacy_keywords"], list)




# -------------------------------------------------
# Tests for union node
# -------------------------------------------------

def test_basic_union():
    state = {
        "spacy_keywords": ["python", "backend"],
        "gazetteer_keywords": [{"name": "docker"}],
        "llm_keywords": ["api"]
    }

    result = union_keywords_node(state)

    assert result["union_list"] == ["api", "backend", "docker", "python"]


def test_duplicates_removed():
    state = {
        "spacy_keywords": ["python", "docker"],
        "gazetteer_keywords": [{"name": "python"}],
        "llm_keywords": ["DOCKER"]
    }

    result = union_keywords_node(state)

    assert result["union_list"] == ["docker", "python"]


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


def test_empty_state():
    result = union_keywords_node({})

    assert result["union_list"] == []


def test_large_scale():
    state = {
        "spacy_keywords": ["python"] * 1000,
        "gazetteer_keywords": [{"name": "docker"}] * 1000,
        "llm_keywords": ["api"] * 1000,
    }

    result = union_keywords_node(state)

    assert result["union_list"] == ["api", "docker", "python"]


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




# -------------------------------------------------
# Tests for tag type assignment node
# -------------------------------------------------

@pytest.fixture
def dummy_config():
    return {
        "llm": "dummy-model",
        "role": "system-role",
        "instruction": "Assign types",
        "output_format": "{}",
        "output_constraints": "",
        "style_or_tone": "neutral",
        "goal": "test"
    }


def make_client_with_response(content: str):
    """
    Returns a mock Groq client whose .create()
    returns content exactly as provided.
    """
    client = MagicMock()

    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content

    client.chat.completions.create.return_value = resp
    return client


def test_assign_tag_types_normal(monkeypatch, dummy_config):
    """Happy path → dict with 'tags'"""

    # mock config loader
    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tag_type_assigner_config",
        lambda _: dummy_config
    )

    # mock groq manager
    manager = MagicMock()
    manager.get_client.return_value = make_client_with_response(
        json.dumps({
            "tags": [
                {"name": "python", "type": "language"},
                {"name": "docker", "type": "tool"}
            ]
        })
    )

    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.GroqClientManager",
        lambda model=None: manager
    )

    result = assign_tag_types(["python", "docker"])

    assert result == [
        {"name": "python", "type": "language"},
        {"name": "docker", "type": "tool"}
    ]


def test_assign_tag_types_llm_returns_list(monkeypatch, dummy_config):
    """LLM returns list instead of dict → still valid"""

    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tag_type_assigner_config",
        lambda _: dummy_config
    )

    manager = MagicMock()
    manager.get_client.return_value = make_client_with_response(
        json.dumps([
            {"name": "python", "type": "language"}
        ])
    )

    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.GroqClientManager",
        lambda model=None: manager
    )

    result = assign_tag_types(["python"])

    assert result == [{"name": "python", "type": "language"}]


def test_assign_tag_types_malformed_json(monkeypatch, dummy_config):
    """Broken JSON → should safely return []"""

    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tag_type_assigner_config",
        lambda _: dummy_config
    )

    manager = MagicMock()
    manager.get_client.return_value = make_client_with_response("not json")

    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.GroqClientManager",
        lambda model=None: manager
    )

    result = assign_tag_types(["python"])

    assert result == []


def test_assign_tag_types_empty_config(monkeypatch):
    """No config → early return"""

    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tag_type_assigner_config",
        lambda _: None
    )

    result = assign_tag_types(["python"])

    assert result == []





# -------------------------------------------------
# Tests for selector node
# -------------------------------------------------

def fake_manager(content: str):
    """Creates manager whose LLM returns `content`"""
    manager = MagicMock()

    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content

    client = MagicMock()
    client.chat.completions.create.return_value = resp

    manager.get_client.return_value = client
    manager.get_model.return_value = "dummy-model"

    return manager


@pytest.fixture
def selector_config(monkeypatch):
    monkeypatch.setattr(
        "code.Agents.MetaDataAgent.nodes.TagGenerator.load_tags_selector_config",
        lambda _: {
            "prompt_config": {
                "role": "curator",
                "instruction": "select best tags",
                "output_format": '[{"name":"Tag","type":"Type"}]'
            },
            "max_tags": 5
        }
    )



@pytest.mark.parametrize(
    "llm_output, union_list, expected",
    [
        (
            json.dumps([
                {"name": "Python", "type": "language"},
                {"name": "Docker", "type": "tool"}
            ]),
            ["python", "docker"],
            ["python", "docker"],
        ),

        # dict with tags
        (
            json.dumps({"tags": [{"name": "FastAPI", "type": "framework"}]}),
            ["fastapi"],
            ["fastapi"],
        ),

        # wrapped code block
        (
            "```json\n[{\"name\":\"Redis\",\"type\":\"db\"}]\n```",
            ["redis"],
            ["redis"],
        ),

        # uppercase → lowercase
        (
            json.dumps([{"name": "PYTHON"}]),
            ["python"],
            ["python"],
        ),

        # whitespace trimmed
        (
            json.dumps([{"name": "  docker  "}]),
            ["docker"],
            ["docker"],
        ),

        # duplicates preserved (node does not dedupe)
        (
            json.dumps([{"name": "python"}, {"name": "python"}]),
            ["python"],
            ["python", "python"],
        ),

        # short names removed
        (
            json.dumps([{"name": "ai"}, {"name": "docker"}]),
            ["ai", "docker"],
            ["docker"],
        ),

        # missing name
        (
            json.dumps([{"type": "tool"}]),
            ["docker"],
            [],
        ),

        # empty name
        (
            json.dumps([{"name": ""}]),
            [""],
            [],
        ),

        # non-dict items
        (
            json.dumps(["python", 123, None]),
            ["python"],
            [],
        ),


        # malformed JSON
        (
            "not json",
            ["python"],
            [],
        ),

        # empty string
        (
            "",
            ["python"],
            [],
        ),

        # wrong JSON shape
        (
            json.dumps({"unexpected": "format"}),
            ["python"],
            [],
        ),

        # empty list from LLM
        (
            json.dumps([]),
            ["python"],
            [],
        ),

        # dict with empty tags
        (
            json.dumps({"tags": []}),
            ["python"],
            [],
        ),

        # empty union → early exit
        (
            json.dumps([{"name": "python"}]),
            [],
            [],
        ),

        # many candidates
        (
            json.dumps([{"name": f"tag{i}"} for i in range(10)]),
            [f"tag{i}" for i in range(10)],
            [f"tag{i}" for i in range(10)],
        ),
    ],
)
def test_selector_node_param(selector_config, llm_output, union_list, expected):
    manager = fake_manager(llm_output)
    node = make_selector_node(manager)

    state = {
        "union_list": union_list,
        "summaries": {"readme.md": "dummy text"},
    }

    result = node(state)

    assert result["keywords"] == expected
