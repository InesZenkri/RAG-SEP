"""Send reminder emails to GitLab issue assignees.

Designed for GitLab scheduled pipelines. Configure with environment variables;
see `.env.example` for the required CI/CD variables.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import smtplib
import ssl
import sys
from collections import defaultdict
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Issue:
    project_name: str
    title: str
    web_url: str
    due_date: str | None
    labels: list[str]
    assignees: list[dict[str, Any]]


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


def gitlab_get(
    session: requests.Session,
    base_url: str,
    path: str,
    params: dict[str, str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        response = session.get(
            f"{base_url.rstrip('/')}/api/v4/{path.lstrip('/')}",
            params={**params, "per_page": "100", "page": str(page)},
            timeout=30,
        )
        response.raise_for_status()
        results.extend(response.json())

        next_page = response.headers.get("X-Next-Page")
        if not next_page:
            return results
        page = int(next_page)


def fetch_project_name(session: requests.Session, base_url: str, project_id: str) -> str:
    response = session.get(
        f"{base_url.rstrip('/')}/api/v4/projects/{requests.utils.quote(project_id, safe='')}",
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return str(data.get("name_with_namespace") or data.get("name") or project_id)


def fetch_open_issues(
    session: requests.Session,
    base_url: str,
    project_id: str,
    project_name: str,
    labels: list[str],
) -> list[Issue]:
    params = {"state": "opened", "scope": "all"}
    if labels:
        params["labels"] = ",".join(labels)

    raw_issues = gitlab_get(
        session=session,
        base_url=base_url,
        path=f"projects/{requests.utils.quote(project_id, safe='')}/issues",
        params=params,
    )
    issues: list[Issue] = []
    for raw_issue in raw_issues:
        assignees = raw_issue.get("assignees") or []
        if not assignees:
            continue
        issues.append(
            Issue(
                project_name=project_name,
                title=str(raw_issue["title"]),
                web_url=str(raw_issue["web_url"]),
                due_date=raw_issue.get("due_date"),
                labels=list(raw_issue.get("labels") or []),
                assignees=assignees,
            )
        )
    return issues


def assignee_email(assignee: dict[str, Any], domain: str | None) -> str | None:
    public_email = assignee.get("public_email") or assignee.get("email")
    if public_email:
        return str(public_email)
    if domain:
        username = str(assignee["username"])
        return f"{username}@{domain}"
    return None


def group_by_assignee(issues: list[Issue], fallback_domain: str | None) -> dict[str, list[Issue]]:
    grouped: dict[str, list[Issue]] = defaultdict(list)
    missing: list[str] = []

    for issue in issues:
        for assignee in issue.assignees:
            email = assignee_email(assignee, fallback_domain)
            if email:
                grouped[email].append(issue)
            else:
                missing.append(str(assignee.get("username") or assignee.get("name") or "unknown"))

    for username in sorted(set(missing)):
        print(f"warning: no email address available for assignee {username}", file=sys.stderr)

    return grouped


def build_message(
    sender: str,
    recipient: str,
    issues: list[Issue],
    subject_prefix: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = f"{subject_prefix} {len(issues)} open GitLab issue(s)"

    lines = [
        "Hi,",
        "",
        "this is an automatic reminder for your currently assigned open GitLab issues:",
        "",
    ]
    sorted_issues = sorted(
        issues,
        key=lambda item: (item.project_name, item.due_date or "", item.title),
    )
    for issue in sorted_issues:
        due = f" | due: {issue.due_date}" if issue.due_date else ""
        labels = f" | labels: {', '.join(issue.labels)}" if issue.labels else ""
        lines.append(f"- [{issue.project_name}] {issue.title}{due}{labels}")
        lines.append(f"  {issue.web_url}")
    lines.extend(["", "Please update or close the issues when you have made progress.", ""])

    message.set_content("\n".join(lines))
    return message


def send_messages(messages: list[EmailMessage]) -> None:
    host = env("SMTP_HOST")
    port = int(env("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_ssl = env("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    use_starttls = env("SMTP_USE_STARTTLS", "true").lower() in {"1", "true", "yes"}

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as smtp:
            if username and password:
                smtp.login(username, password)
            for message in messages:
                smtp.send_message(message)
        return

    with smtplib.SMTP(host, port) as smtp:
        if use_starttls:
            smtp.starttls(context=ssl.create_default_context())
        if username and password:
            smtp.login(username, password)
        for message in messages:
            smtp.send_message(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=env("REMINDER_DRY_RUN", "false").lower() in {"1", "true", "yes"},
        help="Print recipients and issue counts without sending email.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(os.getenv("REMINDER_ENV_FILE", ROOT / ".env.gitlab")))

    gitlab_url = env(
        "GITLAB_URL",
        os.getenv("GITLAB_HOST", os.getenv("CI_SERVER_URL", "https://gitlab.com")),
    )
    project_ids = split_csv(env("REMINDER_PROJECT_IDS", os.getenv("CI_PROJECT_ID")))
    labels = split_csv(os.getenv("REMINDER_LABELS"))
    sender = env("REMINDER_EMAIL_FROM")
    fallback_domain = os.getenv("REMINDER_EMAIL_DOMAIN")
    subject_prefix = env("REMINDER_SUBJECT_PREFIX", "[GitLab reminder]")

    session = requests.Session()
    session.headers.update({"PRIVATE-TOKEN": env("GITLAB_TOKEN")})

    issues: list[Issue] = []
    for project_id in project_ids:
        project_name = fetch_project_name(session, gitlab_url, project_id)
        project_issues = fetch_open_issues(session, gitlab_url, project_id, project_name, labels)
        print(f"{project_name}: found {len(project_issues)} assigned open issue(s)")
        issues.extend(project_issues)

    grouped = group_by_assignee(issues, fallback_domain)
    messages = [
        build_message(
            sender=sender,
            recipient=recipient,
            issues=recipient_issues,
            subject_prefix=subject_prefix,
        )
        for recipient, recipient_issues in sorted(grouped.items())
    ]

    if args.dry_run:
        for recipient, recipient_issues in sorted(grouped.items()):
            print(f"dry-run: would email {recipient} about {len(recipient_issues)} issue(s)")
        return 0

    if not messages:
        print("No assigned open issues found. No emails sent.")
        return 0

    send_messages(messages)
    print(f"Sent {len(messages)} reminder email(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
