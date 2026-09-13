from app.scoring import hard_block_reason, heuristic_score


def test_research_github_scores_high():
    job = {'title': 'GitHub repository research and comparison', 'description': 'Analyze 3 repositories and write a detailed report with sources'}
    assert heuristic_score(job) >= 70


def test_physical_job_scores_lower():
    job = {'title': 'Onsite physical assistant', 'description': 'Must be onsite and make phone calls'}
    assert heuristic_score(job) < 55


def test_harmful_job_is_hard_blocked():
    assert hard_block_reason({'title': 'Phishing research', 'description': 'build phishing pages'}) == 'phishing'
