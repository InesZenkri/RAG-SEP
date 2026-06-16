"""GitLab team-management automations for scheduled pipelines."""

from __future__ import annotations

import argparse
import os
import smtplib
import ssl
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
STALE_MARKER = "<!-- sep-stale-issue-reminder -->"


@dataclass(frozen=True)
class Project:
    project_id: str
    name: str

    @property
    def label(self) -> str:
        return self.name.rsplit("/", maxsplit=1)[-1].strip()


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def gitlab_url() -> str:
    value = env(
        "GITLAB_URL",
        os.getenv("GITLAB_HOST", os.getenv("CI_SERVER_URL", "https://gitlab.com")),
    )
    if value.startswith(("http://", "https://")):
        return value.rstrip("/")
    return f"https://{value.rstrip('/')}"


def parse_gitlab_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def gitlab_request(
    session: requests.Session,
    method: str,
    base_url: str,
    path: str,
    **kwargs: Any,
) -> requests.Response:
    response = session.request(
        method,
        f"{base_url}/api/v4/{path.lstrip('/')}",
        timeout=30,
        **kwargs,
    )
    response.raise_for_status()
    return response


def gitlab_get(
    session: requests.Session,
    base_url: str,
    path: str,
    params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        response = gitlab_request(
            session,
            "GET",
            base_url,
            path,
            params={**(params or {}), "per_page": "100", "page": str(page)},
        )
        results.extend(response.json())
        next_page = response.headers.get("X-Next-Page")
        if not next_page:
            return results
        page = int(next_page)


def project_path(project_id: str) -> str:
    return requests.utils.quote(project_id, safe="")


def fetch_projects(
    session: requests.Session,
    base_url: str,
    project_ids: list[str],
) -> list[Project]:
    projects: list[Project] = []
    for project_id in project_ids:
        response = gitlab_request(session, "GET", base_url, f"projects/{project_path(project_id)}")
        data = response.json()
        projects.append(
            Project(
                project_id=project_id,
                name=str(data.get("name_with_namespace") or data.get("name") or project_id),
            )
        )
    return projects


def send_email(
    sender: str,
    recipients: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
) -> None:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    if cc:
        message["Cc"] = ", ".join(cc)
    message["Subject"] = subject
    message.set_content(body)

    host = env("SMTP_HOST")
    port = int(env("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_ssl = env("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    use_starttls = env("SMTP_USE_STARTTLS", "true").lower() in {"1", "true", "yes"}

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as smtp:
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(host, port) as smtp:
        if use_starttls:
            smtp.starttls(context=ssl.create_default_context())
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def fetch_open_issues(
    session: requests.Session,
    base_url: str,
    project: Project,
) -> list[dict[str, Any]]:
    return gitlab_get(
        session,
        base_url,
        f"projects/{project_path(project.project_id)}/issues",
        params={"state": "opened", "scope": "all"},
    )


def recent_stale_comment_exists(
    session: requests.Session,
    base_url: str,
    project: Project,
    issue_iid: int,
    cutoff: datetime,
) -> bool:
    notes = gitlab_get(
        session,
        base_url,
        f"projects/{project_path(project.project_id)}/issues/{issue_iid}/notes",
        params={"sort": "desc", "order_by": "created_at"},
    )
    for note in notes:
        if STALE_MARKER not in str(note.get("body", "")):
            continue
        created_at = parse_gitlab_time(str(note["created_at"]))
        if created_at >= cutoff:
            return True
    return False


def stale_comment_body(issue: dict[str, Any], stale_days: int) -> str:
    mentions = " ".join(f"@{assignee['username']}" for assignee in issue.get("assignees", []))
    mention_line = f"{mentions}\n\n" if mentions else ""
    return (
        f"{STALE_MARKER}\n"
        f"{mention_line}"
        f"This issue has had no activity for at least {stale_days} days.\n\n"
        "Please add a short status update, move the issue forward, or close it if it is done."
    )


def run_stale_comments(session: requests.Session, base_url: str, projects: list[Project]) -> int:
    stale_days = int(env("STALE_ISSUE_DAYS", "7"))
    dry_run = env("STALE_ISSUE_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    cutoff = datetime.now(UTC) - timedelta(days=stale_days)
    commented = 0

    for project in projects:
        for issue in fetch_open_issues(session, base_url, project):
            updated_at = parse_gitlab_time(str(issue["updated_at"]))
            if updated_at >= cutoff:
                continue
            issue_iid = int(issue["iid"])
            if recent_stale_comment_exists(session, base_url, project, issue_iid, cutoff):
                continue

            title = str(issue["title"])
            print(f"stale: [{project.name}] #{issue_iid} {title}")
            if not dry_run:
                gitlab_request(
                    session,
                    "POST",
                    base_url,
                    f"projects/{project_path(project.project_id)}/issues/{issue_iid}/notes",
                    data={"body": stale_comment_body(issue, stale_days)},
                )
            commented += 1

    action = "would comment on" if dry_run else "commented on"
    print(f"{action} {commented} stale issue(s).")
    return 0


def issue_line(project: Project, issue: dict[str, Any]) -> str:
    due = f" | due: {issue['due_date']}" if issue.get("due_date") else ""
    return f"- {project.label}: {issue['title']}{due}\n  URL: {issue['web_url']}"


def collect_digest(
    session: requests.Session,
    base_url: str,
    projects: list[Project],
) -> dict[str, list[str]]:
    issue_days = int(env("DIGEST_ISSUE_LOOKBACK_DAYS", "7"))
    commit_days = int(env("DIGEST_COMMIT_LOOKBACK_DAYS", "1"))
    due_days = int(env("DIGEST_DUE_WITHIN_DAYS", "14"))
    now = datetime.now(UTC)
    since_issues = (now - timedelta(days=issue_days)).isoformat()
    since_commits = (now - timedelta(days=commit_days)).isoformat()
    due_until = date.today() + timedelta(days=due_days)

    sections: dict[str, list[str]] = {
        "New issues": [],
        "Closed issues": [],
        "Commits pushed recently": [],
        "Upcoming due dates": [],
    }

    for project in projects:
        new_issues = gitlab_get(
            session,
            base_url,
            f"projects/{project_path(project.project_id)}/issues",
            params={"state": "opened", "scope": "all", "created_after": since_issues},
        )
        sections["New issues"].extend(issue_line(project, issue) for issue in new_issues)

        closed_issues = gitlab_get(
            session,
            base_url,
            f"projects/{project_path(project.project_id)}/issues",
            params={"state": "closed", "scope": "all", "updated_after": since_issues},
        )
        sections["Closed issues"].extend(issue_line(project, issue) for issue in closed_issues)

        commits = gitlab_get(
            session,
            base_url,
            f"projects/{project_path(project.project_id)}/repository/commits",
            params={"since": since_commits},
        )
        for commit in commits:
            title = str(commit.get("title") or commit.get("message", "")).splitlines()[0]
            author = commit.get("author_name", "unknown")
            sections["Commits pushed recently"].append(
                f"- {project.label}: {title} ({author})\n  URL: {commit['web_url']}"
            )

        for issue in fetch_open_issues(session, base_url, project):
            due_date = issue.get("due_date")
            if not due_date:
                continue
            parsed_due = date.fromisoformat(str(due_date))
            if date.today() <= parsed_due <= due_until:
                sections["Upcoming due dates"].append(issue_line(project, issue))

    return sections


def build_digest_body(sections: dict[str, list[str]]) -> str:
    new_count = len(sections["New issues"])
    closed_count = len(sections["Closed issues"])
    commit_count = len(sections["Commits pushed recently"])
    due_count = len(sections["Upcoming due dates"])

    lines = [
        "Hi team,",
        "",
        "Here is the weekly SEP GitLab digest.",
        "",
        "Summary",
        "-------",
        f"- {new_count} new issue(s)",
        f"- {closed_count} closed issue(s)",
        f"- {commit_count} recent commit(s)",
        f"- {due_count} upcoming due date(s)",
        "",
    ]
    for title, items in sections.items():
        lines.extend([f"{title} ({len(items)})", "-" * (len(title) + len(str(len(items))) + 3)])
        if items:
            lines.extend(items)
        else:
            lines.append("- Nothing to report.")
        lines.append("")
    lines.append("Generated automatically by the GitLab team-management schedule.")
    return "\n".join(lines)


def run_digest(session: requests.Session, base_url: str, projects: list[Project]) -> int:
    recipients = split_csv(env("TEAM_DIGEST_RECIPIENTS"))
    cc = split_csv(os.getenv("TEAM_DIGEST_CC"))
    sender = env("REMINDER_EMAIL_FROM")
    subject = env("TEAM_DIGEST_SUBJECT", "[SEP GitLab digest]")
    dry_run = env("TEAM_DIGEST_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    body = build_digest_body(collect_digest(session, base_url, projects))

    if dry_run:
        print(body)
        return 0

    send_email(sender, recipients, subject, body, cc=cc)
    print(f"Sent weekly digest to {len(recipients)} recipient(s), cc {len(cc)} recipient(s).")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["stale-comments", "weekly-digest"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(os.getenv("REMINDER_ENV_FILE", ROOT / ".env.gitlab")))

    base_url = gitlab_url()
    project_ids = split_csv(env("REMINDER_PROJECT_IDS", os.getenv("CI_PROJECT_ID")))
    session = requests.Session()
    session.headers.update({"PRIVATE-TOKEN": env("GITLAB_TOKEN")})
    projects = fetch_projects(session, base_url, project_ids)

    if args.command == "stale-comments":
        return run_stale_comments(session, base_url, projects)
    return run_digest(session, base_url, projects)


if __name__ == "__main__":
    raise SystemExit(main())
