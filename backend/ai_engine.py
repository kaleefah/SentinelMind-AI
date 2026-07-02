import os
import json

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ── KEYWORD FALLBACK ──────────────────────────────────────────────────────────

def _keyword_fallback(description: str) -> dict:
    desc = description.lower()

    if "ransomware" in desc or "encrypt" in desc:
        return {
            "category": "Ransomware",
            "severity": "Critical",
            "recommendation": (
                "Immediately isolate all affected systems from the network. "
                "Engage your Incident Response team and preserve forensic evidence. "
                "Restore from the latest clean offline backup. "
                "Do not pay the ransom without legal counsel."
            ),
            "risk_score": 94,
        }
    if "phishing" in desc or ("email" in desc and ("suspicious" in desc or "link" in desc or "click" in desc)):
        return {
            "category": "Social Engineering",
            "severity": "Medium",
            "recommendation": (
                "Block the sender domain and any linked URLs immediately. "
                "Reset credentials for users who interacted with the email. "
                "Issue a company-wide phishing alert and enforce DMARC/DKIM. "
                "Run a targeted security awareness session."
            ),
            "risk_score": 45,
        }
    if "login" in desc or "password" in desc or "credential" in desc or "brute" in desc:
        return {
            "category": "Credential Attack",
            "severity": "High",
            "recommendation": (
                "Force immediate password reset for all affected accounts. "
                "Enable multi-factor authentication on all entry points. "
                "Block the offending IP range at the firewall. "
                "Review all successful logins from the same period."
            ),
            "risk_score": 68,
        }
    if "malware" in desc or "trojan" in desc or "virus" in desc or "backdoor" in desc:
        return {
            "category": "Malware",
            "severity": "High",
            "recommendation": (
                "Isolate the infected system immediately. "
                "Run a full forensic scan and analyse network traffic for C2 communication. "
                "Re-image the workstation from a clean baseline. "
                "Change all credentials that may have been exposed."
            ),
            "risk_score": 78,
        }
    if "sql" in desc or "injection" in desc:
        return {
            "category": "SQL Injection",
            "severity": "High",
            "recommendation": (
                "Patch input validation deficiencies immediately. "
                "Rotate all database credentials. "
                "Audit access logs for signs of data exfiltration. "
                "Update WAF rules and apply parameterised query patterns."
            ),
            "risk_score": 76,
        }
    if "ddos" in desc or "denial" in desc or "flood" in desc:
        return {
            "category": "DDoS",
            "severity": "Medium",
            "recommendation": (
                "Activate DDoS mitigation rules on your CDN/WAF. "
                "Implement rate-limiting at the API gateway. "
                "Contact upstream ISP for traffic scrubbing assistance."
            ),
            "risk_score": 55,
        }
    if ("data" in desc and ("breach" in desc or "leak" in desc or "exfil" in desc)) or "pii" in desc:
        return {
            "category": "Data Breach",
            "severity": "Critical",
            "recommendation": (
                "Isolate affected systems and revoke access tokens immediately. "
                "Preserve all logs for forensic investigation. "
                "Notify your Data Protection Officer — GDPR breach notification may be required within 72 hours. "
                "Engage legal counsel."
            ),
            "risk_score": 91,
        }
    if "insider" in desc or "employee" in desc and ("download" in desc or "unauthor" in desc):
        return {
            "category": "Insider Threat",
            "severity": "Critical",
            "recommendation": (
                "Revoke the employee's access tokens and credentials immediately. "
                "Preserve all activity logs for HR and legal. "
                "Notify your DPO if personal data is involved. "
                "Conduct a full audit of data accessed."
            ),
            "risk_score": 88,
        }

    return {
        "category": "General Incident",
        "severity": "Low",
        "recommendation": "Investigate manually, document all findings, and escalate if further indicators of compromise are discovered.",
        "risk_score": 20,
    }


# ── LLM CALL (OPENROUTER) ─────────────────────────────────────────────────────

def analyze_incident(description: str) -> dict:
    api_key = os.getenv("LLM_API_KEY", "")
    model   = os.getenv("LLM_MODEL", "openai/gpt-4.1-mini")

    if not api_key or not _HAS_REQUESTS:
        return _keyword_fallback(description)

    try:
        resp = _requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization":  f"Bearer {api_key}",
                "Content-Type":   "application/json",
                "HTTP-Referer":   "https://sentinelmind.ai",
                "X-Title":        "SentinelMind AI",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert cybersecurity AI analyst. "
                            "Analyse the incident description and respond ONLY with a single valid JSON object — "
                            "no markdown, no explanation, no code fences. "
                            "The JSON must have exactly these keys:\n"
                            "  \"category\": one of [Social Engineering, Credential Attack, Malware, Ransomware, "
                            "SQL Injection, DDoS, Data Breach, Insider Threat, General Incident]\n"
                            "  \"severity\": exactly one of [Critical, High, Medium, Low]\n"
                            "  \"recommendation\": 3-5 sentences of specific, actionable remediation steps\n"
                            "  \"risk_score\": integer 0-100 reflecting the overall threat level"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Incident Description:\n{description}",
                    },
                ],
                "temperature": 0.2,
                "max_tokens":  400,
            },
            timeout=18,
        )

        if resp.status_code == 200:
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            # Strip code fences if the model added them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            required = {"category", "severity", "recommendation", "risk_score"}
            if required.issubset(result.keys()):
                # Clamp risk_score to 0-100
                result["risk_score"] = max(0, min(100, int(result["risk_score"])))
                return result

    except Exception:
        pass

    return _keyword_fallback(description)


# ── CHAT WITH MEMORY ──────────────────────────────────────────────────────────

def chat_with_memory(message: str, incident_context: str) -> str:
    api_key = os.getenv("LLM_API_KEY", "")
    model   = os.getenv("LLM_MODEL", "openai/gpt-4.1-mini")

    if not api_key or not _HAS_REQUESTS:
        return (
            "AI chat is unavailable — no API key configured. "
            "Set LLM_API_KEY in your .env file to enable this feature."
        )

    try:
        resp = _requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization":  f"Bearer {api_key}",
                "Content-Type":   "application/json",
                "HTTP-Referer":   "https://sentinelmind.ai",
                "X-Title":        "SentinelMind AI",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are SentinelMind, an expert AI cybersecurity assistant embedded in a SOC platform. "
                            "You have access to the organisation's full incident history shown below. "
                            "Answer the analyst's question concisely and professionally. "
                            "When referencing past incidents, cite their titles explicitly. "
                            "If no matching incidents exist, say so clearly and give general best-practice advice. "
                            "Keep responses under 200 words."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Incident Memory:\n{incident_context}\n\n"
                            f"Analyst Question: {message}"
                        ),
                    },
                ],
                "temperature": 0.35,
                "max_tokens":  500,
            },
            timeout=22,
        )

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception:
        pass

    return "Unable to reach the AI service. Please check your connection and try again."