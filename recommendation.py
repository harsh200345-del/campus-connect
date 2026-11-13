import re
from datetime import datetime, date

def clean_skills(skills_str):
    """Normalize comma/semicolon/space-separated skill strings into a clean list of lowercased tokens."""
    if not skills_str:
        return []
    # Split by comma or semicolon or slashes
    tokens = re.split(r'[,;/|]+', skills_str)
    cleaned = []
    for t in tokens:
        item = t.strip().lower()
        if item:
            cleaned.append(item)
    return cleaned

def calculate_match_score(student, opportunity):
    """
    Calculates a personalized recommendation score (0-100%) for a student and an opportunity.
    
    Weights:
    - Branch Match: 30 points (Full match or 'All')
    - Year Match:   20 points (Full match or 'All')
    - Skills Match: 50 points (Weighted overlap of required skills)
    """
    total_score = 0
    matched_skills = []

    stu_branch = (student.get('branch') or '').strip().lower()
    stu_year = (student.get('year') or '').strip().lower()
    stu_skills = clean_skills(student.get('skills', ''))

    opp_branch = (opportunity.get('eligibility_branch') or 'All').strip().lower()
    opp_year = (opportunity.get('eligibility_year') or 'All').strip().lower()
    opp_skills = clean_skills(opportunity.get('required_skills', ''))

    # 1. Branch Match (30 pts)
    branch_matched = False
    if opp_branch == 'all' or opp_branch == stu_branch or stu_branch in opp_branch:
        total_score += 30
        branch_matched = True

    # 2. Year Match (20 pts)
    year_matched = False
    if opp_year == 'all' or opp_year == stu_year or stu_year in opp_year:
        total_score += 20
        year_matched = True

    # 3. Skills Match (50 pts)
    if opp_skills:
        for os in opp_skills:
            for ss in stu_skills:
                # Direct match or substring match (e.g. 'web' in 'web development')
                if os == ss or (len(os) > 3 and os in ss) or (len(ss) > 3 and ss in os):
                    matched_skills.append(os.title())
                    break
        
        # Deduplicate matched skills
        matched_skills = list(dict.fromkeys(matched_skills))
        
        # Calculate overlap fraction
        ratio = len(matched_skills) / len(opp_skills)
        skill_score = int(ratio * 50)
        total_score += min(skill_score, 50)
    else:
        # If opportunity doesn't specify skills (e.g., general scholarship or competition)
        if branch_matched and year_matched:
            total_score += 40
        else:
            total_score += 20

    # Ensure score is within [0, 100]
    total_score = min(max(total_score, 10), 100)

    # Deadline status badge calculation
    deadline_info = get_deadline_status(opportunity.get('deadline'))

    return {
        'score': total_score,
        'matched_skills': matched_skills,
        'deadline_info': deadline_info
    }

def get_deadline_status(deadline_str):
    """Computes human-friendly deadline alert info."""
    if not deadline_str:
        return {'status': 'none', 'text': 'No deadline', 'badge_class': 'secondary', 'days': 999}
    
    try:
        if isinstance(deadline_str, str):
            deadline_date = datetime.strptime(deadline_str[:10], '%Y-%m-%d').date()
        else:
            deadline_date = deadline_str
        
        today = date.today()
        delta = (deadline_date - today).days

        if delta < 0:
            return {'status': 'expired', 'text': f'Closed ({abs(delta)}d ago)', 'badge_class': 'dark', 'days': delta}
        elif delta == 0:
            return {'status': 'urgent', 'text': '⚠️ Closes Today!', 'badge_class': 'danger', 'days': 0}
        elif delta == 1:
            return {'status': 'urgent', 'text': '⚠️ Closes Tomorrow!', 'badge_class': 'danger', 'days': 1}
        elif delta <= 3:
            return {'status': 'urgent', 'text': f'⚠️ Closes in {delta} days', 'badge_class': 'danger', 'days': delta}
        elif delta <= 7:
            return {'status': 'warning', 'text': f'🔔 {delta} days left', 'badge_class': 'warning text-dark', 'days': delta}
        else:
            return {'status': 'normal', 'text': f'📅 {delta} days left', 'badge_class': 'info text-dark', 'days': delta}
    except Exception:
        return {'status': 'none', 'text': str(deadline_str), 'badge_class': 'secondary', 'days': 999}

def rank_opportunities_for_student(student, opportunities_list):
    """Ranks and annotates opportunities for a specific student."""
    ranked = []
    for opp in opportunities_list:
        opp_dict = dict(opp)
        metrics = calculate_match_score(student, opp_dict)
        opp_dict['match_score'] = metrics['score']
        opp_dict['matched_skills'] = metrics['matched_skills']
        opp_dict['deadline_info'] = metrics['deadline_info']
        ranked.append(opp_dict)
    
    # Sort primarily by match score descending, then by remaining days ascending
    ranked.sort(key=lambda x: (-x['match_score'], x['deadline_info']['days']))
    return ranked
