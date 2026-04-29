def normalize_proxy(value: str | None) -> str | None:
    """
    Accepts proxy values like:
    - "212.113.107.128:36613"
    - "http://212.113.107.128:36613"
    - "http://user:pass@host:port"
    Returns normalized URL or None.
    """
    if value is None:
        return None

    v = value.strip()
    if not v:
        return None

    lowered = v.lower()
    if lowered in {"none", "off", "disable", "disabled", "0"}:
        return None

    if "://" not in v:
        v = "http://" + v
    return v

