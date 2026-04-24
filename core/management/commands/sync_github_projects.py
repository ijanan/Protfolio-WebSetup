import json
import os
import re
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from core.models import Profile, Project


GITHUB_API_BASE = "https://api.github.com"


def _infer_category(repo: dict, default_category: str) -> str:
    """Infer portfolio category from GitHub repo metadata.

    Heuristic-based to keep it simple and explainable:
    - ML: ML/AI keywords or common ML libraries.
    - Data: analysis/visualization/dashboard keywords or data-focused languages.
    - Web: web frameworks/front-end languages/keywords.
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

    # Programming
    if (
        has_any(
            "algorithm",
            "data structure",
            "competitive programming",
            "problem solving",
            "leetcode",
            "codeforces",
            "hackerrank",
        )
        or language in {"c", "c++", "java", "go", "rust"}
    ):
        return "programming"

    # Tools & Frameworks
    if has_any("automation", "devops", "ci/cd", "docker", "kubernetes", "terraform", "ansible"):
        return "tools"

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
            username = _parse_github_username(profile.github_url if profile else "")

        if not username:
            raise CommandError(
                "GitHub username not provided and could not be inferred. "
                "Pass --username YOURNAME or set Profile.github_url to your GitHub profile URL."
            )

        url = f"{GITHUB_API_BASE}/users/{urllib.parse.quote(username)}/repos?per_page=100&sort=updated"

        repos: list[dict] = []
        while url:
            status, headers, body = _github_request(url, token)
            if status >= 400:
                raise CommandError(f"GitHub API error {status}: {body[:2000]!r}")

            try:
                page = json.loads(body.decode("utf-8"))
            except Exception as e:
                raise CommandError(f"Could not parse GitHub API response JSON: {e}")

            if not isinstance(page, list):
                raise CommandError("Unexpected GitHub API response (expected list of repos).")

            repos.extend(page)
            if limit and len(repos) >= limit:
                repos = repos[:limit]
                break

            url = _get_next_link(headers.get("Link"))

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
                    "category": _infer_category(repo, default_category) if auto_category else default_category,
                    "tech_stack": (repo.get("language") or "GitHub"),
                    "github_url": repo.get("html_url") or "",
                    "live_url": repo.get("homepage") or "",
                }

                project = Project.objects.filter(github_repo_id=repo_id).first()
                if project:
                    # Always keep URLs in sync; optionally update the rest.
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
                            new_val = defaults[field]
                            if getattr(project, field) != new_val:
                                setattr(project, field, new_val)
                                changed = True

                        # Keep slug consistent if title changed and slug was auto-generated originally.
                        # We won't auto-change slugs because it can break existing URLs.

                    if changed:
                        project.save()
                        updated += 1
                    else:
                        skipped += 1
                    continue

                # Create new project.
                title = defaults["title"]
                slug = _unique_slug_from_title(title, fallback_suffix=str(repo_id))

                Project.objects.create(
                    github_repo_id=repo_id,
                    slug=slug,
                    **defaults,
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"GitHub sync complete for '{username}': created={created}, updated={updated}, skipped={skipped}"
            )
        )
