import hashlib
import os
import sys
import textwrap
from datetime import datetime, timezone

import requests
import smtplib
from email.message import EmailMessage

URL = "https://www.esma.europa.eu/sites/default/files/position_limits_publication.xlsx"
STATE_FILE = "last_hash.txt"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_prev_hash() -> str | None:
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        v = f.read().strip()
        return v or None


def save_hash(h: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(h + "\n")


def send_email(subject: str, body: str) -> None:
    smtp_user = os.environ["oray.gungor@gmail.com"]
    smtp_pass = os.environ["jgda opas tjmx krxs"]
    to_email = os.environ["oray.gungor@gmail.com"]

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.ehlo()
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)


def main() -> int:
    # Download file
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    data = r.content

    new_hash = sha256_bytes(data)
    prev_hash = load_prev_hash()

    now = datetime.now(timezone.utc).isoformat()
    last_modified = r.headers.get("Last-Modified", "")
    etag = r.headers.get("ETag", "")

    if prev_hash is None:
        # First run: store hash, don't email
        save_hash(new_hash)
        print(f"[{now}] First run. Stored hash: {new_hash}")
        return 0

    if new_hash == prev_hash:
        print(f"[{now}] No change. Hash: {new_hash}")
        return 0

    # Changed
    save_hash(new_hash)

    subject = "ESMA Excel changed: position_limits_publication.xlsx"
    body = textwrap.dedent(f"""\
    Change detected in ESMA XLSX.

    URL: {URL}
    Time (UTC): {now}
    Last-Modified: {last_modified}
    ETag: {etag}

    Previous hash: {prev_hash}
    New hash:      {new_hash}
    """)

    print(body)
    send_email(subject, body)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
