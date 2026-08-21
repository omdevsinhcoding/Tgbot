"""
IMAP Scanner — scans IMAP accounts for Netflix emails.
Ported from the original monolithic bot code.
Supports multi-IMAP accounts per user (from DB).
"""

import re
import ssl
import imaplib
from typing import Optional, List, Tuple
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header
from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup


@dataclass
class EmailHit:
    subject: str
    sender: str
    date: str
    link: str


# ═══════════════════════════════════════════════
# EMAIL PARSING HELPERS
# ═══════════════════════════════════════════════

def decode_mime_header(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = ""
    for p, enc in parts:
        if isinstance(p, bytes):
            out += p.decode(enc or "utf-8", errors="ignore")
        else:
            out += str(p)
    return out


def sender_allowed(sender: str, allow_rules: List[str]) -> bool:
    s = (sender or "").lower()
    for rule in allow_rules:
        r = rule.lower().strip()
        if not r:
            continue
        if r.startswith("@"):
            if r in s:
                return True
        else:
            if r in s:
                return True
    return False


def subject_matches(subject: str, subject_rules: List[str]) -> bool:
    s = (subject or "").lower()
    for rule in subject_rules:
        r = rule.lower().strip()
        if r and r in s:
            return True
    return False


def normalize_google_redirect(u: str) -> str:
    try:
        p = urlparse(u)
        if "google." in p.netloc and p.path.startswith("/url"):
            qs = parse_qs(p.query)
            real_list = qs.get("q", [""])
            if real_list:
                real = unquote(real_list[0])
                return real if real else u
    except Exception:
        pass
    return u


def extract_links_from_html(html_body: str) -> List[str]:
    links = []
    try:
        soup = BeautifulSoup(html_body, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].replace("&amp;", "&")
            links.append(normalize_google_redirect(href))
    except Exception:
        for m in re.findall(r'href="([^"]+)"', html_body or ""):
            m = m.replace("&amp;", "&")
            links.append(normalize_google_redirect(m))
    return links


def get_message_bodies(msg) -> Tuple[str, str]:
    text_plain, text_html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", "")).lower()
            if "attachment" in disp:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                content = payload.decode(charset, errors="ignore")
            except Exception:
                content = payload.decode("utf-8", errors="ignore")
            if ctype == "text/plain":
                text_plain += content
            elif ctype == "text/html":
                text_html += content
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                content = payload.decode(charset, errors="ignore")
            except Exception:
                content = payload.decode("utf-8", errors="ignore")
            if msg.get_content_type() == "text/html":
                text_html = content
            else:
                text_plain = content
    return text_plain, text_html


def find_matching_link(links: List[str], mode: str, html_content: str = "") -> Optional[str]:
    blocked_patterns = [
        "/browse", "/password", "/ManageAccountAccess", "notificationsettings",
        "PrivacyPolicy", "TermsOfUse", "/help",
        "URL_LOGO", "URL_HELP", "URL_EMAIL", "URL_CORP_INFO",
        "URL_COMM_SETTINGS", "URL_TERMS", "URL_PRIVACY", "URL_SRC", "lkid=URL_",
    ]

    cleaned = []
    for u in links:
        u = normalize_google_redirect(u).replace("&amp;", "&")
        cleaned.append(u)

    # Button-based priority
    if html_content:
        button_text = "Get code" if mode == "temp" else "Yes, this was me"
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for a in soup.find_all("a"):
                if a.string and button_text.lower() in a.string.lower():
                    href = a.get("href", "")
                    if not href:
                        continue
                    href = normalize_google_redirect(href.replace("&amp;", "&"))
                    if "netflix.com" in href:
                        ok = False
                        if mode == "temp" and ("nftoken=" in href or "messageGuid=" in href):
                            ok = True
                        if mode == "household" and ("nftoken=" in href):
                            ok = True
                        if ok and not any(bad.lower() in href.lower() for bad in blocked_patterns):
                            return href
        except Exception:
            pass

    if mode == "temp":
        for u in cleaned:
            if "travel/verify" in u and ("nftoken=" in u or "messageGuid=" in u):
                if not any(bad.lower() in u.lower() for bad in blocked_patterns):
                    return u

    if mode == "household":
        for u in cleaned:
            if "update-primary-location" in u and "nftoken=" in u:
                if not any(bad.lower() in u.lower() for bad in blocked_patterns):
                    return u

    for u in cleaned:
        if "netflix.com" in u and ("nftoken=" in u or "messageGuid=" in u):
            if not any(bad.lower() in u.lower() for bad in blocked_patterns):
                return u

    return None


def mask_token_in_url(url: str) -> str:
    try:
        p = urlparse(url)
        qs = parse_qs(p.query)
        if "nftoken" in qs and qs["nftoken"]:
            tok = qs["nftoken"][0]
            masked = tok[:8] + "..." + tok[-4:] if len(tok) > 12 else tok[:4] + "..."
            qs["nftoken"] = [masked]
            base = f"{p.scheme}://{p.netloc}{p.path}"
            parts = []
            for k, vals in qs.items():
                for v in vals:
                    parts.append(f"{k}={v}")
            return base + ("?" + "&".join(parts) if parts else "")
    except Exception:
        pass
    return url


# ═══════════════════════════════════════════════
# IMAP SCAN — CORE FUNCTION
# ═══════════════════════════════════════════════

def imap_scan_last10_unseen(
    email: str,
    password: str,
    host: str,
    port: int,
    mode: str,
    sender_rules: List[str],
    subject_rules: List[str],
) -> Tuple[Optional[EmailHit], str]:
    """
    Scan last 10 UNSEEN emails from an IMAP account.
    mode: "household" or "temp"
    Returns: (EmailHit or None, status_message)
    """
    if not email or not password:
        return None, "IMAP credentials not configured."

    try:
        ctx = ssl.create_default_context()
        mbox = imaplib.IMAP4_SSL(host, port, ssl_context=ctx)
        mbox.login(email, password)
        mbox.select("INBOX")

        typ, data = mbox.search(None, "UNSEEN")
        if typ != "OK":
            mbox.logout()
            return None, "Failed to search inbox."

        ids = data[0].split()
        if not ids:
            mbox.logout()
            return None, "No unread emails."

        ids = ids[-10:][::-1]  # newest first

        for msg_id in ids:
            typ, msg_data = mbox.fetch(msg_id, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue

            raw = msg_data[0][1]
            msg = message_from_bytes(raw)

            subject = decode_mime_header(msg.get("Subject", ""))
            sender = decode_mime_header(msg.get("From", ""))
            date = decode_mime_header(msg.get("Date", ""))

            if not sender_allowed(sender, sender_rules):
                continue
            if not subject_matches(subject, subject_rules):
                continue

            plain, html = get_message_bodies(msg)
            links = []
            if html:
                links.extend(extract_links_from_html(html))
            if plain:
                links.extend(re.findall(r"https?://\S+", plain))

            links = [re.sub(r"[)\]>,.]+$", "", x) for x in links]

            found = find_matching_link(links, mode, html_content=html)
            if found:
                try:
                    mbox.store(msg_id, "+FLAGS", "(\\Seen)")
                except Exception:
                    pass
                mbox.logout()
                return EmailHit(subject=subject, sender=sender, date=date, link=found), "OK"

        mbox.logout()
        return None, "No matching email in last 10 unread."

    except imaplib.IMAP4.error as e:
        return None, f"IMAP error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"
