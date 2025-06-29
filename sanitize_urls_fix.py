import re

def clean_asset_urls(assets):
    """
    Remove malformed, non-URL values or extensions such as .log, .bak, .swp, .tmp,
    numeric error headers like '404 -', and junk like .rar, .tar, etc.
    """
    cleaned = []
    seen = set()
    for url in assets:
        if not isinstance(url, str):
            continue
        url = url.strip()

        # Remove leading numeric codes like "404 - ... https://..."
        url = re.sub(r"^\d{3}\s*-\s*", "", url)
        url = re.sub(r"^\d{3}.*?(https?://)", r"\1", url)

        if not url or url in seen:
            continue

        # Exclude malformed or non-production URLs
        if any(ext in url.lower() for ext in [
            ".log", ".bak", ".swp", ".tmp", ".txt", ".rar", ".zip", ".sql",
            ".tar", ".gz", ".7z", ".old", ".py", ".rb", ".conf", ".xml", "localhost", "127.0.0.1"
        ]):
            continue

        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", url):
            continue

        cleaned.append(url)
        seen.add(url)
    return cleaned

# Test block (you can remove in prod)
if __name__ == "__main__":
    raw_assets = [
        "404 - https://example.com/old",
        "https://example.com/valid",
        "403 -   983B - /jsp.old",
        "https://404",
        "https://example.com/file.log",
        "https://example.com/valid2"
    ]
    clean = clean_asset_urls(raw_assets)
    for url in clean:
        print(url)
