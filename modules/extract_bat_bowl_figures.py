import requests
from bs4 import BeautifulSoup

def extract_bat_bowl_figures(href_link):
    innings = []

    href_link = f'https://www.espncricinfo.com{href_link}'
    
    response = requests.get(href_link)
    if response.status_code != 200:
        return innings
    
    scorecard_soup = BeautifulSoup(response.content, 'html.parser')
    divs_with_class_ds_mt_3 = scorecard_soup.findAll('div', class_='ds-mt-3')
    
    for div_class in divs_with_class_ds_mt_3:
        divs_with_class_ds_mt_2 = div_class.findAll('div', class_='ds-mt-2')
        for sub_div in divs_with_class_ds_mt_2:
            score_tables = sub_div.findAll('table')
            if len(score_tables) < 2:
                continue
            bat_table = score_tables[0]
            bowl_table = score_tables[1]

            # Batting data
            batting_score_body = bat_table.find('tbody')
            if not batting_score_body:
                continue
            rows = batting_score_body.findAll('tr', class_=lambda x: x != 'ds-hidden')

            if rows and rows[-2].find('td').text.split(" ")[0] == "Did":
                del rows[-2]
            
            batting = []

            for tr in rows[:-3]:
                player = {}
                score_data = tr.findAll('td')
                for index, td in enumerate(score_data):
                    match index:
                        case 0:
                            player["name"] = td.text.replace('\xa0', '')
                        case 1:
                            player["dismissal"] = td.text
                        case 2:
                            player["runs"] = td.text
                        case 3:
                            player["balls"] = td.text
                        case 4:
                            continue
                        case 5:
                            player["fours"] = td.text
                        case 6:
                            player["sixes"] = td.text
                        case 7:
                            player["strike_rate"] = td.text
                batting.append(player)

            innings.append(batting)

            for index, tr in enumerate(rows[-3:]):
                score_data = tr.findAll('td')
                match index:
                    case 0:
                        result = {}
                        extras_tuple = score_data[1].text
                        extras_tuple = extras_tuple.replace("(", "").replace(")", "")
                        extras_tuple = extras_tuple.split(',')
            
                        for item in extras_tuple:
                            if item == "":
                                result = 0
                            else:
                                key, value = item.split()  # Split each item by space
                                result[key] = int(value)

                        innings.append(result)
            
                    case 2:
                        fall_of_wickets_text = score_data[0].text
                        
                        pattern = re.compile(r'(\d+-\d+)\s*\(([^)]+),\s*([\d.]+ ov)\)')
                        matches = pattern.findall(fall_of_wickets_text)
                        
                        fall_of_wickets_list = [[match[0], f'({match[1]}, {match[2]})'] for match in matches]
                        innings.append(fall_of_wickets_list)

            # Bowling Data
            bowling_figures_body = bowl_table.find('tbody')
            if not bowling_figures_body:
                continue
            rows = bowling_figures_body.findAll('tr', class_=lambda x: x != 'ds-hidden')

            bowling = []

            for tr in rows:
                player = {}
                score_data = tr.findAll('td')
                for index, td in enumerate(score_data):
                    match index:
                        case 0:
                            player["name"] = td.text.replace('\xa0', '')
                        case 1:
                            player["overs"] = td.text
                        case 2:
                            player["maiden"] = td.text
                        case 3:
                            player["runs"] = td.text
                        case 4:
                            player["wicket"] = td.text
                        case 5:
                            player["economy"] = td.text
                        case 6:
                            player["0s"] = td.text
                        case 7:
                            player["4s"] = td.text
                        case 8:
                            player["6s"] = td.text
                        case 9:
                            player["WD"] = td.text
                        case 10:
                            player["NB"] = td.text
                bowling.append(player)

            innings.append(bowling)
            
    return innings