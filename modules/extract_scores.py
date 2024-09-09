def extract_scores(team_html):
    score_1_div = team_html[0].find('div', class_="ds-text-compact-s")
    score_2_div = team_html[1].find('div', class_="ds-text-compact-s")
    
    score_1 = score_1_div.text if score_1_div else "0"
    score_2 = score_2_div.text if score_2_div else "0"
    
    return score_1, score_2