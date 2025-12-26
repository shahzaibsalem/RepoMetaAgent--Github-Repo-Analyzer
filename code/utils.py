import re
from typing import Optional

def is_valid_github_repo(url: Optional[str]) -> bool:
    # 1. Handle None or empty strings immediately
    if not url or not isinstance(url, str):
        return False
    
    # 2. Updated Pattern:
    # (?!.*\.git/?$) is a negative lookahead that says: 
    # "Don't match if the string ends in .git or .git/"
    pattern = r"^https://github\.com/[A-Za-z0-9_.-]+/(?![A-Za-z0-9_.-]+\.git/?$)[A-Za-z0-9_.-]+/?$"
    
    # Alternative simpler approach:
    # Check regex normally, then manually exclude .git
    standard_pattern = r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$"
    
    if bool(re.match(standard_pattern, url)):
        return not url.rstrip('/').endswith('.git')
        
    return False