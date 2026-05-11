"""GitHub API utilities for fetching repository metadata."""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


@dataclass
class RepoInfo:
    """Basic repository metadata from GitHub API."""

    full_name: str
    description: str | None
    stars: int
    forks: int
    url: str


def get_repo_info(
    owner: str,
    repo: str,
    token: str | None = None,
) -> RepoInfo:
    """Fetch basic metadata for a GitHub repository.

    Args:
        owner: Repository owner (user or organization).
        repo: Repository name.
        token: Optional GitHub personal access token for higher rate limits.

    Returns:
        RepoInfo dataclass with star count, fork count, and description.

    Raises:
        httpx.HTTPStatusError: If the API returns a non-2xx status code.
        httpx.TimeoutException: If the request exceeds the timeout.
        httpx.RequestError: For other network-level errors.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            info = RepoInfo(
                full_name=data["full_name"],
                description=data.get("description"),
                stars=data["stargazers_count"],
                forks=data["forks_count"],
                url=data["html_url"],
            )
            logger.info(
                "Fetched repo info: %s (stars=%d, forks=%d)",
                info.full_name,
                info.stars,
                info.forks,
            )
            return info

        except (httpx.TimeoutException, httpx.RequestError) as exc:
            last_exc = exc
            logger.warning(
                "Attempt %d/%d failed for %s/%s: %s",
                attempt,
                MAX_RETRIES,
                owner,
                repo,
                exc,
            )

    raise last_exc  # type: ignore[misc]
