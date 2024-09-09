import requests
from bs4 import BeautifulSoup

def extract_over_by_over_score(href_link):
    href_link = f'https://www.espncricinfo.com{href_link}'
    
    over_comparison_link = href_link.split('/')
    over_comparison_link[-1] = "match-overs-comparison"
    over_comparison_link = '/'.join(over_comparison_link)

    response = requests.get(over_comparison_link)
    if response.status_code != 200:
        return [], []
    
    over_comparison_soup = BeautifulSoup(response.content, 'html.parser')
    over_table = over_comparison_soup.find('table', class_="ds-table-fixed")
    if not over_table:
        return [], []

    table_rows = over_table.findAll('tr')
    rows = table_rows[1:]

    inning_1_overs = []
    inning_2_overs = []

    for row in rows:
        over = {}
        over["Over"] = row.findAll('td')[0].text
        if len(row.findAll('td')) > 2:
            team_1 = row.findAll('td')[1]
        else:
            continue
        if team_1.text == "-":
            continue
        score = team_1.find('div', class_="ds-pt-1").find('div', class_="ds-text-tight-m").find('div', class_="ds-text-typo").text
        over["Runs"] = score.split("(")[0].split("/")[0]
        over["Wickets"] = score.split("(")[0].split("/")[1]
        inning_1_overs.append(over)

    for row in rows:
        over = {}
        over["Over"] = row.findAll('td')[0].text
        if len(row.findAll('td')) > 2:
            team_2 = row.findAll('td')[2]
        else:
            continue
        if team_2.text == "-":
            continue
        score = team_2.find('div', class_="ds-pt-1").find('div', class_="ds-text-tight-m").find('div', class_="ds-text-typo").text
        over["Runs"] = score.split("(")[0].split("/")[0]
        over["Wickets"] = score.split("(")[0].split("/")[1]
        inning_2_overs.append(over)
        
    return inning_1_overs, inning_2_overs