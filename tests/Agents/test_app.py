import pytest
from code.utils import is_valid_github_repo

@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/user/repo", True),
        ("https://github.com/user-name/repo_name", True),
        ("https://github.com/user123/repo123", True),
        ("https://github.com/user/repo/", True),

        # ❌ invalid cases
        ("http://github.com/user/repo", False),
        ("https://github.com/user", False),
        ("https://github.com/user/repo/issues", False),
        ("github.com/user/repo", False),
        ("https://notgithub.com/user/repo", False),
        ("", False),
        (None, False),
        ("https://github.com/user/repo.git", False),
    ]
)

def test_is_valid_github_repo(url, expected):
    assert is_valid_github_repo(url) == expected
