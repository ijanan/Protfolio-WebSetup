import json
import re
import urllib.parse
import urllib.request

from django.db import transaction
from django.utils.text import slugify

from .models import Profile, Project


GITHUB_API_BASE = "https://api.github.com"
AUTO_SYNC_CACHE_SECONDS = 30 * 60


def parse_github_username(github_url: str) -> str | None:
    if not github_url:
        return None

    try:
        parsed = urllib.parse.urlparse(github_url)
    except Exception:
        return None

    if parsed.netloc and parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None

    path = (parsed.path or "").strip("/")
    if not path:
        return None

    parts = [part for part in path.split("/") if part]
    if not parts:
        return None

    username = parts[0]
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", username):
        return None

    return username


def get_profile_github_username(profile: Profile | None) -> str | None:
    return parse_github_username(profile.github_url if profile else "")


def infer_category(repo: dict, default_category: str) -> str:
    language = (repo.get("language") or "").strip().lower()
    name = (repo.get("name") or "").strip().lower()
    desc = (repo.get("description") or "").strip().lower()

    topics = repo.get("topics")
    if isinstance(topics, list):
        topics_text = " ".join(str(topic).lower() for topic in topics)
    else:
        topics_text = ""

    haystack = " ".join([name, desc, topics_text]).strip()

    def has_any(*keywords: str) -> bool:
        return any(keyword in haystack for keyword in keywords)

    if (
        has_any(
            "machine learning",
            "deep learning",
            "ml",
            "ai",
            "neural",
            "classification",
            "regression",
            "nlp",
            "computer vision",
            "pytorch",
            "tensorflow",
            "keras",
            "scikit",
            "scikit-learn",
        )
        or language in {"jupyter notebook"}
        and has_any("tensorflow", "pytorch", "keras", "scikit", "scikit-learn", "nlp")
    ):
        return "ml"

    if (
        has_any(
            "data analysis",
            "data analytics",
            "analysis",
            "analytics",
            "eda",
            "visualization",
            "dashboard",
            "power bi",
            "tableau",
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn",
            "sql",
        )
        or language in {"r", "jupyter notebook", "sql"}
    ):
        return "data"

    if (
        has_any(
            "android",
            "ios",
            "flutter",
            "react native",
            "kotlin",
            "swift",
            "mobile app",
            "app development",
        )
        or language in {"kotlin", "swift", "dart"}
    ):
        return "app"

    if (
        has_any(
            "web",
            "website",
            "portfolio",
            "frontend",
            "backend",
            "fullstack",
            "full-stack",
            "api",
            "django",
            "flask",
            "fastapi",
            "react",
            "next",
            "nextjs",
            "vue",
            "angular",
            "node",
            "express",
            "tailwind",
            "bootstrap",
        )
        or language in {"javascript", "typescript", "html", "css"}
    ):
        return "web"

    if has_any(
        "algorithm",
        "data structure",
        "dsa",
        "competitive programming",
        "problem solving",
        "coding challenge",
        "cli",
        "script",
        "automation",
    ):
        return "programming"

    return default_category


def github_request(url: str, token: str | None) -> tuple[int, dict, bytes]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "portfolio-site-github-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = getattr(resp, "status", 200)
        return status, dict(resp.headers.items()), resp.read()


def get_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None

    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            match = re.search(r"<([^>]+)>", part)
            if match:
                return match.group(1)
    return None


def unique_slug_from_title(title: str, *, fallback_suffix: str) -> str:
    base = slugify(title) or "project"
    candidate = base
    index = 2

    while Project.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{fallback_suffix}" if index == 2 else f"{base}-{fallback_suffix}-{index}"
        index += 1

    return candidate


def sync_github_projects(
    *,
    username: str,
    token: str | None = None,
    include_forks: bool = False,
    include_archived: bool = False,
    update_existing: bool = False,
    auto_category: bool = True,
    update_category: bool = False,
    default_category: str = "other",
    limit: int = 0,
) -> dict[str, int | str]:
    url = f"{GITHUB_API_BASE}/users/{urllib.parse.quote(username)}/repos?per_page=100&sort=updated"

    repos: list[dict] = []
    while url:
        status, headers, body = github_request(url, token)
        if status >= 400:
            raise RuntimeError(f"GitHub API error {status}: {body[:2000]!r}")

        page = json.loads(body.decode("utf-8"))
        if not isinstance(page, list):
            raise RuntimeError("Unexpected GitHub API response (expected list of repos).")

        repos.extend(page)
        if limit and len(repos) >= limit:
            repos = repos[:limit]
            break

        url = get_next_link(headers.get("Link"))

    created = 0
    updated = 0
    skipped = 0

    with transaction.atomic():
        for repo in repos:
            repo_id = repo.get("id")
            if not repo_id:
                skipped += 1
                continue

            if (not include_forks) and repo.get("fork"):
                skipped += 1
                continue

            if (not include_archived) and repo.get("archived"):
                skipped += 1
                continue

            defaults = {
                "title": (repo.get("name") or "Untitled").replace("-", " ").replace("_", " ").strip() or "Untitled",
                "short_description": (repo.get("description") or "No description provided.")[:300],
                "full_description": (repo.get("description") or "No description provided."),
                "category": infer_category(repo, default_category) if auto_category else default_category,
                "tech_stack": (repo.get("language") or "GitHub"),
                "github_url": repo.get("html_url") or "",
                "live_url": repo.get("homepage") or "",
            }

            project = Project.objects.filter(github_repo_id=repo_id).first()
            if project:
                # Never overwrite a project the user added/edited manually.
                # Only auto-update projects that GitHub sync originally created.
                if not project.synced_from_github:
                    skipped += 1
                    continue

                changed = False
                if project.github_url != defaults["github_url"]:
                    project.github_url = defaults["github_url"]
                    changed = True
                if project.live_url != defaults["live_url"]:
                    project.live_url = defaults["live_url"]
                    changed = True

                if update_existing:
                    fields = ["title", "short_description", "full_description", "tech_stack"]
                    if update_category:
                        fields.append("category")

                    for field in fields:
                        new_value = defaults[field]
                        if getattr(project, field) != new_value:
                            setattr(project, field, new_value)
                            changed = True

                if changed:
                    project.save()
                    updated += 1
                else:
                    skipped += 1
                continue

            Project.objects.create(
                github_repo_id=repo_id,
                synced_from_github=True,
                slug=unique_slug_from_title(defaults["title"], fallback_suffix=str(repo_id)),
                **defaults,
            )
            created += 1

    return {
        "username": username,
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }


def maybe_sync_github_projects(*, cache, profile: Profile | None, token: str | None = None) -> dict[str, int | str] | None:
    username = get_profile_github_username(profile)
    if not username:
        return None

    cache_key = f"github-sync:{username}"
    if cache.get(cache_key):
        return None

    result = sync_github_projects(
        username=username,
        token=token,
        update_existing=True,
        update_category=True,
    )
    cache.set(cache_key, True, AUTO_SYNC_CACHE_SECONDS)
    return result