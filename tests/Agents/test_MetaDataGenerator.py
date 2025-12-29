import json
from code.Agents.MetaDataAgent.nodes.MetaDataGenerator import generate_title_short_summary
from code.Agents.MetaDataAgent.nodes.MetaDataGenerator import generate_long_summary
from code.Agents.MetaDataAgent.nodes.MetaDataGenerator import generate_topics_seo
from code.Agents.MetaDataAgent.nodes.MetaDataGenerator import generate_suggested_title

def test_generate_title_short_summary(mock_groq_manager):
    node = generate_title_short_summary(mock_groq_manager)

    state = {
        "readme_md": "This is a sample README file for testing purposes. It contains information about the project. The project aims to demonstrate unit testing in Python. The README should be concise and informative. It provides an overview of the project's features and usage."
    }

    result = node(state)
    assert "short_summary" in result
    assert isinstance(result["short_summary"], str)
    assert len(result["short_summary"]) > 0
    assert result["short_summary"].count('.') < 5 
    assert result["short_summary"] == "Mocked summary"
    client = mock_groq_manager.get_client.return_value
    client.chat.completions.create.assert_called_once()


def test_generate_long_summary(mock_groq_manager):
    node = generate_long_summary(mock_groq_manager)

    state = {
        "readme_md": "This is a sample README file for testing purposes. It contains information about the project. The project aims to demonstrate unit testing in Python. The README should be concise and informative. It provides an overview of the project's features and usage."
    }

    result = node(state)
    assert "long_summary" in result
    assert isinstance(result["long_summary"], str)
    assert len(result["long_summary"]) > 0
    assert result["long_summary"].count('.') < 7
    assert result["long_summary"] == "Mocked summary"
    client = mock_groq_manager.get_client.return_value
    client.chat.completions.create.assert_called_once()

def test_generate_topics_seo(mock_groq_manager):
    node = generate_topics_seo(mock_groq_manager)

    state = {
        "readme_md": "This is a sample README file for testing purposes. It contains information about the project. The project aims to demonstrate unit testing in Python. The README should be concise and informative. It provides an overview of the project's features and usage."
    }

    result = node(state)

    assert "github_topics" in result
    assert isinstance(result["github_topics"], str)

    output = result["github_topics"]
    
    expected_topics = ["seo_keywords", "seo_description", "seo_title"]

    for topic in expected_topics:
        assert helper_checker(output, topic), f"Missing or empty topic: {topic}"
  
    # assert result["github_topics"] == "Mocked Summary"
    client = mock_groq_manager.get_client.return_value
    client.chat.completions.create.assert_called_once()


def test_generate_suggested_title(mock_groq_manager):
    node = generate_suggested_title(mock_groq_manager)

    state = {
        "readme_md": "This is a sample README file for testing purposes. It contains information about the project. The project aims to demonstrate unit testing in Python. The README should be concise and informative. It provides an overview of the project's features and usage."
    }

    result = node(state)
    assert "suggested_title" in result
    assert isinstance(result["suggested_title"], str)
    assert len(result["suggested_title"]) > 0
    assert result["suggested_title"] == "Mocked summary"
    client = mock_groq_manager.get_client.return_value
    client.chat.completions.create.assert_called_once()



def helper_checker(topics , expected_topic):
    if not topics:
        return False
    if isinstance(topics, str):
        topics = topics.replace('```json', '').replace('```JSON', '').strip().replace('```', '').strip()
        try:
            topics = json.loads(topics)
        except json.JSONDecodeError:
            pass 

    expected_topic = expected_topic.lower()
    if isinstance(topics, dict):
        description_text = topics.get(expected_topic)
    else:
        description_text = str(topics)

    if isinstance(description_text, str) and description_text.strip():

        return True
    else:
        return False
