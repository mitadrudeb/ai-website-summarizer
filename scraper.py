from bs4 import BeautifulSoup
import requests

# Standard browser headers to prevent basic scraping blocks
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_website_contents(url: str, max_chars: int = 2500) -> str:
    """
    Fetch the title and cleaned text contents of the website at the given url.
    Truncates to max_chars as a sensible context limit for 1B LLM models.
    """
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching webpage: {e}"

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    if soup.body:
        # Strip out non-content HTML elements
        for irrelevant in soup.body(["script", "style", "img", "input", "noscript", "svg", "footer", "header"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""

    combined = f"Title: {title}\n\nContent:\n{text}"
    return combined[:max_chars]


def fetch_website_links(url: str) -> list:
    """
    Return all valid links on the website at the given url.
    """
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link and link.startswith("http")]
