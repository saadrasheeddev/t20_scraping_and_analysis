import requests
from bs4 import BeautifulSoup
import pandas as pd

import extract_info

def fetch_data_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    divs_with_class_ds_p_0 = soup.find('div', class_='ds-p-0')
    if not divs_with_class_ds_p_0:
        return []
    
    divs_with_class_ds_p_4 = divs_with_class_ds_p_0.findAll('div', class_='ds-p-4')
    
    records = []

    for i in range(len(divs_with_class_ds_p_4)):
        record = extract_info(divs_with_class_ds_p_4, i)
        if record:
            records.append(record)

    records_for_df = []

    for record in records:

        records_for_df.append([
        record.match_no,
        record.venue,
        record.team_bat_first,
        record.first_innings_score,
        record.team_bat_second,
        record.second_innings_score,
        record.result,
        str(record.batting.get(record.team_bat_first, {}).get('players', '')),
        str(record.batting.get(record.team_bat_first, {}).get('over_by_over_score', '')),
        str(record.batting.get(record.team_bat_first, {}).get('extras', '')),
        str(record.batting.get(record.team_bat_first, {}).get('fall_of_wickets', '')),
        str(record.batting.get(record.team_bat_second, {}).get('bowling', '')),
        str(record.batting.get(record.team_bat_second, {}).get('players', '')),
        str(record.batting.get(record.team_bat_second, {}).get('over_by_over_score', '')),
        str(record.batting.get(record.team_bat_second, {}).get('extras', '')),
        str(record.batting.get(record.team_bat_second, {}).get('fall_of_wickets', '')),
        str(record.batting.get(record.team_bat_first, {}).get('bowling', ''))
    ])

    df_cols = ["Match Number", "Venue", "Team Bat First", "1st Innings Score", "Team Bat Second", "2nd Innings Score", "Result", "Scores - Players (Team Bat First)", "Over by Over Score (1st Innings)", "Extras (Team Bat First)", "Fall of Wickets (Team Bat First)", "Bowling (Team Bowling First)", "Scores - Players (Team Bat Second)", "Over by Over Score (2nd Innings)", "Extras (Team Bat Second)", "Fall of Wickets (Team Bat Second)", "Bowling (Team Bowling Second)"]

    df = pd.DataFrame(records_for_df, columns=df_cols)

    return df