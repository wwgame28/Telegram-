import re
from typing import Any

GOOD = {
    'research': 18, 'analysis': 18, 'analyze': 18, 'report': 16, 'summary': 12,
    'github': 20, 'repository': 14, 'compare': 14, 'website': 12, 'web': 8,
    'documentation': 10, 'technical': 8, 'market research': 16, 'audit': 12,
    'исслед': 18, 'анализ': 18, 'отчет': 16, 'отчёт': 16, 'сравн': 14, 'сайт': 12,
}
BAD = {
    'call': -18, 'phone': -18, 'physical': -25, 'onsite': -30, 'video edit': -20,
    'photoshop': -18, 'legal advice': -35, 'medical diagnosis': -40, 'adult': -50,
    'casino': -40, 'gambling': -40, 'hack account': -70, 'credential': -45,
    'malware': -70, 'phishing': -70, 'bypass authentication': -70, 'impersonat': -50,
    'send money': -45, 'trade crypto': -45, 'investment advice': -35,
}


def flatten_job(job: dict[str, Any]) -> str:
    return ' '.join(str(job.get(k, '')) for k in ('title', 'description', 'skills', 'success_criteria')).lower()


def heuristic_score(job: dict[str, Any]) -> int:
    text = flatten_job(job)
    score = 30
    for key, pts in GOOD.items():
        if key in text:
            score += pts
    for key, pts in BAD.items():
        if key in text:
            score += pts
    urls = re.findall(r'https?://\S+', text)
    if urls:
        score += min(10, len(urls) * 3)
    if len(text) > 250:
        score += 5
    if len(text) < 40:
        score -= 10
    return max(0, min(100, score))


def hard_block_reason(job: dict[str, Any]) -> str:
    text = flatten_job(job)
    blocked = {
        'hack account': 'account compromise', 'phishing': 'phishing', 'malware': 'malware',
        'credential theft': 'credential theft', 'medical diagnosis': 'medical diagnosis',
        'legal advice': 'legal advice', 'casino': 'gambling', 'gambling': 'gambling',
        'impersonate': 'impersonation', 'bypass authentication': 'auth bypass',
    }
    for needle, reason in blocked.items():
        if needle in text:
            return reason
    return ''
