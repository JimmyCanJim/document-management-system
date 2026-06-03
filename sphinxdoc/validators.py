import re
from django.core.exceptions import ValidationError


def validate_relative_path(value):

    """Validates that any given string is a safe, relative file or directory path. This makes sure that the path does not point to an absolute path.

    Args:
        value (str): The directory or file path to validate.

    Raises:
        ValidationError: If the path is absolute.
        ValidationError: If the path contains empty segments.
        ValidationError: If the path contains invalid characters.
    """

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
    
    """Validates that a correctly formatted Git repository URL that is accessable

    Args:
        value (str): The Git repository URL to validate.

    Raises:
        ValidationError: If the URL does not match known Git URL formats.
    """
    
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
    
    """Validates that a string is a safe and strictly formatted Git branch name.
    Args:
        value (str): The Git branch name to validate.

    Raises:
        ValidationError: If the Git branch name contains illegal characters.
        ValidationError: If  the Git branch name is too long.
    """    

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