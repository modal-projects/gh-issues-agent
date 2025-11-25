# GitHub Issues Agent

This demo shows how to create an agent in Modal that scrapes a set of URLs,
extracts all Github repository links, and posts a Github Issue to each of them.

To run this example, you'll need a Github token and a Modal account.

1. `pip install modal` and `modal setup`, to create a Modal account.
2. Create a Github token at the [developer settings].
3. Save this token as Modal Secret called `github`: `modal secret create github GITHUB_TOKEN=<token-value>` https://modal.com/secrets.
4. Run it! `modal run -m create_action::ete_demo --sample-repository-url=<URL>` - will post to a sample repository.
5. Scale up: `modal run -m create_action` - to scrape 250+ sample papers in parallel.
