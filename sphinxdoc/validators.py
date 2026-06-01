import re
from django.core.exceptions import ValidationError

def validate_relative_path(value):
    """Validate whether ``value`` is a safe, relative path."""
    if not value:
        return

    # Instantly reject absolute paths (Linux/Mac or Windows)
    if value.startswith('/') or value.startswith('\\') or ':' in value:
        raise ValidationError(f"'{value}' must be a relative path, not an absolute path.")

    # Regex ensures valid directory/file names (rejects purely '.' or '..')
    regex = re.compile(r"^(?!\.\.?$)[a-zA-Z0-9.\-_]+$")
    
    # Split by forward or backward slash
    parts = re.split(r"[/\\]", value)
    
    for part in parts:
        part = part.strip()
        if not part:
            # Catches double slashes like 'a//b'
            raise ValidationError(f"'{value}' contains empty path segments.")
        if not regex.fullmatch(part):
            raise ValidationError(
                f"'{value}' contains invalid characters or illegal directory traversal dots (..)."
            )

def validate_repository_url(value):
    """Validate whether a repository URL is properly formatted and accessible."""
    if not value:
        return 
    
    # Imported locally to avoid circular dependencies during Django initialization
    from .services.git_manager import Repository 
    
    if not Repository.validate(value):
        raise ValidationError(
            f"'{value}' is an invalid repository URL. "
            "Must be a valid Git URL (HTTPS, SSH, or Git protocol)."
        )

def validate_branch_name(value):
    """Validate that a branch name follows strict Git naming conventions."""
    if not value:
        return 
    
    # Git branch name rules (simplified)
    invalid_patterns = [
        r'\.\.',           # No double dots
        r'^\.',            # Cannot start with dot
        r'\.$',            # Cannot end with dot
        r'@{',             # Cannot contain @{sequence}
        r'[~\^:?\*\[\]]',  # Cannot contain special characters
        r'\s',             # No whitespace
        r'\\',             # No backslashes
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, value):
            raise ValidationError(
                f"'{value}' is an invalid branch name. "
                "Cannot contain spaces, special characters, or start/end with dots."
            )
    
    if len(value) > 100:
        raise ValidationError(
            f"'{value}' is too long. Maximum 100 characters allowed for a branch name."
        )