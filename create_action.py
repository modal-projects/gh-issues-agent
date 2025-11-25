import modal
from typing import List, Optional

app = modal.App("github-actions-example")


image = modal.Image.debian_slim().uv_pip_install("requests", "PyPDF2")


@app.cls(image=image, secrets=[modal.Secret.from_name("github")])
class GithubIssueAgent:
    @modal.method()
    def extract_gh_links(self, url) -> List[str]:
        """Extract all GitHub links from a PDF URL"""
        import re
        import urllib.request
        import io
        from PyPDF2 import PdfReader

        # Download the PDF
        response = urllib.request.urlopen(url)
        pdf_data = response.read()

        # Parse PDF and extract text
        pdf_file = io.BytesIO(pdf_data)
        pdf_reader = PdfReader(pdf_file)

        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Find all GitHub URLs in the text
        # Pattern matches various GitHub URL formats
        github_pattern = r"https?://github\.com/[^\s\)\]\>,]+"
        links = re.findall(github_pattern, text)

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links

    @modal.method()
    def parse_gh_config(self, url: str) -> Optional[tuple[str, str]]:
        import re

        # https://github.com/modal-projects/gh-actions-issue
        # Extract owner and repo from GitHub URL
        pattern = r"github\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, url)

        if match:
            owner = match.group(1)
            repo = match.group(2)
            # Clean up repo name (remove trailing slashes, .git, etc.)
            repo = repo.rstrip("/").replace(".git", "")
            return (owner, repo)

        return None

    @modal.method()
    def check_hugging_face_weights(self) -> bool:
        # huggingface.co/minimaxai/minimax-m1-80k
        # TODO: implement

        return False

    @modal.method()
    def post_gh_issue(self, gh_owner: str, gh_repo: str):
        import os
        import requests

        gh_token = os.environ.get("GITHUB_TOKEN")

        ISSUE_TITLE = "Share your model weights with the community 🚀"
        ISSUE_BODY = """
        👋 Hello from the Hugging Face Team!

        Your repo includes a model, but we couldn’t find its weights on Hugging Face.  
        Publishing them helps your work reach a wider audience, boosts reproducibility, and enables developers worldwide to build on your research.

        You can easily upload your model here:  
        https://huggingface.co/docs/hub/en/models-uploading

        Thanks for contributing to an open and collaborative ML ecosystem!  
        — The Hugging Face Team
        """

        url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/issues"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {gh_token}",
            "X-GitHub-Api-Version": "2022-11-28",  # current stable version header
        }

        payload = {
            "title": ISSUE_TITLE,
            "body": ISSUE_BODY,
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            issue = response.json()
            issue_url = issue["html_url"]
            print(f"Issue created: {issue_url}")
            return {"success": True, "url": issue_url}
        else:
            print(f"Failed to create issue: {response.status_code}")
            print(response.text)
            return {"success": True}


@app.function(image=image)
def ete_demo(
    sample_repository_url: str = "https://github.com/modal-projects/gh-issues-agent",
):
    """Sample ETE demo flow - uses sample paper urls and overrides for testing"""
    paper_urls = [
        "https://proceedings.neurips.cc/paper_files/paper/2024/file/71c3451f6cd6a4f82bb822db25cea4fd-Paper-Conference.pdf"
    ]
    agent = GithubIssueAgent()

    extracted_urls = agent.extract_gh_links.map(
        paper_urls, return_exceptions=True, wrap_returned_exceptions=False
    )
    extracted_urls = [url for url_list in extracted_urls for url in url_list]
    print(f"Extracted {len(extracted_urls)} urls")
    print(extracted_urls)

    ## Override for testing
    extracted_urls = [sample_repository_url]
    print(f"Overriding with {', '.join(extracted_urls)}")

    github_configs = agent.parse_gh_config.map(
        extracted_urls, return_exceptions=True, wrap_returned_exceptions=False
    )
    results = agent.post_gh_issue.starmap(
        github_configs, return_exceptions=True, wrap_returned_exceptions=False
    )
    total_success = 0
    total_failure = 0
    urls = []
    for r in results:
        if r["success"]:
            total_success += 1
            urls.append(r["url"])
        else:
            total_failure += 1
    print("Results posted to Github. URLs:")
    print("\n".join(urls))
    print(f"\nTotal success: {total_success}, total failures: {total_failure}")


@app.local_entrypoint()
def scrape_many():
    with open("/paper_urls.txt", "r") as f:
        paper_urls = [line.strip() for line in f.readlines()]

    agent = GithubIssueAgent()

    print(paper_urls)

    extracted_urls = agent.extract_gh_links.map(
        paper_urls, return_exceptions=True, wrap_returned_exceptions=False
    )
    # Flatten list of lists to a single list
    extracted_urls = [url for url_list in extracted_urls for url in url_list]
    print(f"Extracted {len(extracted_urls)} urls")
    print(extracted_urls)
