"""Security utilities for Deep Agent AGI."""


def mask_api_key(api_key: str, prefix_len: int = 8, suffix_len: int = 4) -> str:
    """
    Mask an API key for safe logging.

    Shows prefix and suffix of key, masks the middle. Handles edge cases
    for short keys to avoid exposing too much information.

    Args:
        api_key: The API key to mask
        prefix_len: Number of characters to show at start (default: 8)
        suffix_len: Number of characters to show at end (default: 4)

    Returns:
        Masked API key string (e.g., "sk-abc12...xyz9" or "***" for short keys)

    Examples:
        >>> mask_api_key("sk-proj-1234567890abcdefghij")
        'sk-proj-1...ghij'

        >>> mask_api_key("short")
        '***'

        >>> mask_api_key("lsv2_abcdefghijklmnop")
        'lsv2_abc...mnop'
    """
    api_key_len = len(api_key)

    # For keys longer than prefix_len + suffix_len, show prefix...suffix
    if api_key_len > prefix_len + suffix_len:
        return f"{api_key[:prefix_len]}...{api_key[-suffix_len:]}"

    # For keys longer than just prefix_len, show partial prefix with masking
    elif api_key_len > prefix_len:
        return f"{api_key[:prefix_len//2]}...***"

    # For very short keys, mask completely
    else:
        return "***"
