def extract_teams(team_html):
    return team_html[0].find('p', class_="ds-capitalize").text, team_html[1].find('p', class_="ds-capitalize").text