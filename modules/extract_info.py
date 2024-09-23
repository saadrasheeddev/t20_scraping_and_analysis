from .find_date import find_date
from .extract_teams import extract_teams
from .extract_scores import extract_scores
from .extract_bat_bowl_figures import extract_bat_bowl_figures
from .extract_over_by_over_score import extract_over_by_over_score

from models import MatchScorecard

def extract_info(html_content, index):
    match_date = find_date(html_content, index)
    
    match_venue = html_content[index].find('div', class_='ds-text-typo-mid3')
    if not match_venue:
        return None
    
    text_content = match_venue.get_text(separator=' ', strip=True)
    location = text_content.split('•')[1].strip().split(',')[0]
    match_no = text_content.split('•')[0].strip().split(',')[0]
    
    team_1, team_2 = extract_teams(html_content[index].findAll('div', class_='ci-team-score'))

    print(team_1, "VS", team_2)

    score_1, score_2 = extract_scores(html_content[index].findAll('div', class_='ci-team-score'))
    
    result = html_content[index].find('p', class_='ds-line-clamp-2').text if html_content[index].find('p', class_='ds-line-clamp-2') else "Result not found"
    
    href_link = html_content[index].find('div', class_='ds-px-4').find('a').get('href') if html_content[index].find('div', class_='ds-px-4') and html_content[index].find('a') else ""
    if not href_link:
        return None
    
    scorecard = extract_bat_bowl_figures(href_link)
    inning_1_score, inning_2_score = extract_over_by_over_score(href_link)
    
    record = MatchScorecard(location, match_no, team_1, score_1, team_2, score_2, result)
    
    if len(scorecard) == 8:
        record.add_batting_details(team_1, scorecard[0], scorecard[1], scorecard[2], inning_1_score)
        record.add_batting_details(team_2, scorecard[4], scorecard[5], scorecard[6], inning_2_score)
        record.add_bowling_details(team_1, scorecard[7])
        record.add_bowling_details(team_2, scorecard[3])
    
    return record