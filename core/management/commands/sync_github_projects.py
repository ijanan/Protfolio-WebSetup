import json
import os
import re
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from core.models import Profile, Project
from core.github_sync import get_profile_github_username, sync_github_projects


GITHUB_API_BASE = "https://api.github.com"


def _infer_category(repo: dict, default_category: str) -> str:
    """Infer portfolio category from GitHub repo metadata.

    Heuristic-based to keep it simple and explainable:
    - ML: ML/AI keywords or common ML libraries.
    - Data: analysis/visualization/dashboard keywords or data-focused languages.
    - App: mobile/app keywords and ecosystems.
    - Web: web frameworks/front-end languages/keywords.
    - Programming: algorithm/problem-solving/CLI utilities.
    - Otherwise: default_category.
    """

    language = (repo.get("language") or "").strip().lower()
    name = (repo.get("name") or "").strip().lower()
    desc = (repo.get("description") or "").strip().lower()

    topics = repo.get("topics")
    if isinstance(topics, list):
        topics_text = " ".join(str(t).lower() for t in topics)
    else:
        topics_text = ""

    haystack = " ".join([name, desc, topics_text]).strip()

    def has_any(*keywords: str) -> bool:
        return any(k in haystack for k in keywords)

    # Machine Learning
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

    # Data Analysis
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

    # App Development
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

    # Web Development
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

    # Programming / DSA / utilities
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


def _parse_github_username(github_url: str) -> str | None:
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

    # Accept both profile and repo URLs; first segment is username.
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None

    username = parts[0]
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", username):
        return None

    return username


def _github_request(url: str, token: str | None) -> tuple[int, dict, bytes]:
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
        resp_headers = dict(resp.headers.items())
        body = resp.read()
        return status, resp_headers, body


def _get_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None

    # Link header format: <url>; rel="next", <url>; rel="last"
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            m = re.search(r"<([^>]+)>", part)
            if m:
                return m.group(1)
    return None


def _unique_slug_from_title(title: str, *, fallback_suffix: str) -> str:
    base = slugify(title) or "project"
    candidate = base
    i = 2

    while Project.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{fallback_suffix}" if i == 2 else f"{base}-{fallback_suffix}-{i}"
        i += 1

    return candidate


class Command(BaseCommand):
    help = "Sync public GitHub repositories into Project entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help="GitHub username. If omitted, inferred from Profile.github_url.",
        )
        parser.add_argument(
            "--token",
            help="GitHub API token. If omitted, reads from env var GITHUB_TOKEN.",
        )
        parser.add_argument(
            "--include-forks",
            action="store_true",
            help="Include forked repositories (default: skip forks).",
        )
        parser.add_argument(
            "--include-archived",
            action="store_true",
            help="Include archived repositories (default: skip archived).",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing projects matched by github_repo_id (default: only create new).",
        )
        parser.add_argument(
            "--auto-category",
            action="store_true",
            default=True,
            help="Auto-infer category from repo language/keywords (default: enabled).",
        )
        parser.add_argument(
            "--no-auto-category",
            action="store_false",
            dest="auto_category",
            help="Disable category inference and always use --default-category for new repos.",
        )
        parser.add_argument(
            "--update-category",
            action="store_true",
            help="When used with --update-existing, also update category via inference.",
        )
        parser.add_argument(
            "--default-category",
            choices=[c for c, _ in Project.CATEGORY_CHOICES],
            default="other",
            help="Category to use for new synced projects.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of repos to sync (0 = no limit).",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        token = options.get("token") or os.getenv("GITHUB_TOKEN")
        include_forks = bool(options.get("include_forks"))
        include_archived = bool(options.get("include_archived"))
        update_existing = bool(options.get("update_existing"))
        auto_category = bool(options.get("auto_category"))
        update_category = bool(options.get("update_category"))
        default_category = options.get("default_category")
        limit = int(options.get("limit") or 0)

        if not username:
            profile = Profile.objects.first()
            username = get_profile_github_username(profile)

        if not username:
            raise CommandError(
                "GitHub username not provided and could not be inferred. "
                "Pass --username YOURNAME or set Profile.github_url to your GitHub profile URL."
            )

        try:
            result = sync_github_projects(
                username=username,
                token=token,
                include_forks=include_forks,
                include_archived=include_archived,
                update_existing=update_existing,
                auto_category=auto_category,
                update_category=update_category,
                default_category=default_category,
                limit=limit,
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"GitHub sync complete for '{result['username']}': created={result['created']}, updated={result['updated']}, skipped={result['skipped']}"
            )
        )
