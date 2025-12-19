import re


# Pre-compile regex pattern to avoid repeated compilation
_NON_ALNUM_PATTERN = re.compile(r'[^A-Z0-9]+')


def format_ids(ids):
    """
    Format a list of ID strings by:
    - Skipping None values
    - Stripping whitespace
    - Converting to uppercase
    - Collapsing runs of non-alphanumeric characters to a single hyphen
    - Preserving order and duplicates
    
    Args:
        ids: List of strings or None values
        
    Returns:
        List of formatted ID strings
        
    Performance optimizations:
    - Pre-compiled regex pattern (avoids O(n) regex compilation overhead)
    - Reduced temporary string allocations
    - More efficient iteration
    """
    result = []
    for id_val in ids:
        if id_val is None:
            continue
        # Chain operations to reduce intermediate allocations
        # Strip whitespace and convert to uppercase
        cleaned = id_val.strip().upper()
        # Use pre-compiled pattern for substitution
        cleaned = _NON_ALNUM_PATTERN.sub('-', cleaned)
        result.append(cleaned)
    return result
