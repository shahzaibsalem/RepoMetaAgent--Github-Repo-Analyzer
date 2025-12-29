import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_groq_manager():
    mock_client = MagicMock()

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Mocked summary"
            )
        )
    ]

    mock_client.chat.completions.create.return_value = mock_response

    manager = MagicMock()
    manager.get_client.return_value = mock_client
    manager.get_model.return_value = "mock-model"

    return manager
