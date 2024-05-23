import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyAYSaidaY8gNQpKZe56TXpOvaaaC9nETGs"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-pro')

class MatchScorecard:
    def __init__(self, venue, match_no, team_bat_first, first_innings_score, team_bat_second, second_innings_score, result):
        self.match_no = match_no
        self.venue = venue
        self.team_bat_first = team_bat_first
        self.first_innings_score = first_innings_score
        self.team_bat_second = team_bat_second
        self.second_innings_score = second_innings_score
        self.result = result
        self.batting = {}
        
    def __str__(self):
        return f"Match No: {self.match_no}\nVenue: {self.venue}\nTeam Batting First: {self.team_bat_first}\n1st Innings Score: {self.first_innings_score}\nTeam Batting Second: {self.team_bat_second}\n2nd Innings Score: {self.second_innings_score}\nResult: {self.result}"
    
    def add_batting_details(self, team, players, extras, fall_of_wickets, inning_score):
        self.batting[team] = {
            'players': players,
            'extras': extras,
            'over_by_over_score': inning_score,
            'fall_of_wickets': fall_of_wickets,
            'bowling': {}
        }
    
    def add_bowling_details(self, team, bowlers):
        self.batting[team]['bowling'] = bowlers

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

def find_date(html_content, index):
    for i in range(3):
        date_div = html_content[index].find('div', class_='ds-w-24')
        if date_div:
            date = date_div.text
            if date:
                return date
        index -= 1
    return "Date not found"

def extract_teams(team_html):
    return team_html[0].find('p', class_="ds-capitalize").text, team_html[1].find('p', class_="ds-capitalize").text

def extract_scores(team_html):
    score_1_div = team_html[0].find('div', class_="ds-text-compact-s")
    score_2_div = team_html[1].find('div', class_="ds-text-compact-s")
    
    score_1 = score_1_div.text if score_1_div else "0"
    score_2 = score_2_div.text if score_2_div else "0"
    
    return score_1, score_2

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
        team_1 = row.findAll('td')[1]
        if team_1.text == "-":
            continue
        score = team_1.find('div', class_="ds-pt-1").find('div', class_="ds-text-tight-m").find('div', class_="ds-text-typo").text
        over["Runs"] = score.split("(")[0].split("/")[0]
        over["Wickets"] = score.split("(")[0].split("/")[1]
        inning_1_overs.append(over)

    for row in rows:
        over = {}
        over["Over"] = row.findAll('td')[0].text
        team_2 = row.findAll('td')[2]
        if team_2.text == "-":
            continue
        score = team_2.find('div', class_="ds-pt-1").find('div', class_="ds-text-tight-m").find('div', class_="ds-text-typo").text
        over["Runs"] = score.split("(")[0].split("/")[0]
        over["Wickets"] = score.split("(")[0].split("/")[1]
        inning_2_overs.append(over)
        
    return inning_1_overs, inning_2_overs

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

def show_dashboard(df):

    teams = sorted(set(df["Team Bat First"]).union(set(df["Team Bat Second"])))
    selected_team = st.selectbox("Select a team to analyze", teams)

    # Let's Extract Exact match result from the "Result" column
    # Currently "Result" column values look like this "Pakistan won by 51 runs"
    # With respect to Pakistan team let's make another column with short string of "Won", "Lost" or "Tied"

    df_filtered = df[(df["Team Bat First"] == selected_team) | (df["Team Bat Second"] == selected_team)]

    df_filtered = df_filtered.reset_index(drop=True)

    df_filtered["Match Result"] = ""

    for index, record in enumerate(df_filtered["Result"]):

        result = model.generate_content(
            f"""
            In the statement below,
            Did {selected_team} won the match? if {selected_team} won the match,
            Return "True" 
            
            Statement: {record}
            Return: 
            """
        )

        result_text = result.text.replace(" ", "").replace("\n", "").replace("\t", "")

        result_text = result_text.lower()

        print(result_text)

        if selected_team in record or result_text == "true":
            df_filtered.at[index, "Match Result"] = "Won"
        elif "tied" in record:
            df_filtered.at[index, "Match Result"] = "Tied"
        elif "No result" in record:
            df_filtered.at[index, "Match Result"] = "No Result"
        else:
            df_filtered.at[index, "Match Result"] = "Lost"

    # Let's extract win-lost ratio of team throughout T20 world cup matches
    result_ratio = df_filtered["Match Result"].value_counts()

    # Create a Plotly pie chart for the win-loss ratio
    fig = go.Figure(data=[go.Pie(labels=result_ratio.index, values=result_ratio.values)])
    fig.update_layout(title=f"Win-Loss Ratio of {selected_team} Team in T20 World Cup Matches")

    # Display the pie chart
    st.plotly_chart(fig)

    # Let's visualize number of matches according to their results in a bar chart
    result_counts = df_filtered["Match Result"].value_counts()
    fig_bar = go.Figure([go.Bar(x=result_counts.index, y=result_counts.values)])
    fig_bar.update_layout(title="Number of Matches (Won | Lost | Tied)", xaxis_title="Match Result", yaxis_title="Number of Matches")

    # Display the bar chart
    st.plotly_chart(fig_bar)

    # Subsetting dataframe with only matches that were won by Selected Team
    df_won = df_filtered[df_filtered["Match Result"] == "Won"]

    # Extracting number of matches won by Selected Team while batting first

    number_of_wins_bat_first = df_won["Team Bat First"].value_counts()
    number_of_wins_bat_first = number_of_wins_bat_first[number_of_wins_bat_first.index == selected_team]
    
    # Extracting number of matches won by Selected Team while batting second

    number_of_wins_bat_second = df_won["Team Bat Second"].value_counts()
    number_of_wins_bat_second = number_of_wins_bat_second[number_of_wins_bat_second.index == selected_team]

    # Subsetting dataframe with only matches that were lost by Selected Team
    df_lost = df_filtered[df_filtered["Match Result"] == "Lost"]

    # Extracting number of matches lost by Selected Team while batting first

    number_of_loss_bat_first = df_lost["Team Bat First"].value_counts()
    number_of_loss_bat_first = number_of_loss_bat_first[number_of_loss_bat_first.index == selected_team]

    # Extracting number of matches lost by Selected Team while batting second

    number_of_loss_bat_second = df_lost["Team Bat Second"].value_counts()
    number_of_loss_bat_second = number_of_loss_bat_second[number_of_loss_bat_second.index == selected_team]

    # Define the palettes
    win_palette = ['#1f77b4', '#ff7f0e']  # replace with your actual palette
    loss_palette = ['#d62728', '#2ca02c']  # replace with your actual palette

    # Create subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Number of Wins (Bat First vs Bat Second)", "Number of Losses (Bat First vs Bat Second)"))

    def get_value(data):
        if data.empty:
            return 0
        else:
            return data[0]

    number_of_wins_bat_first = get_value(number_of_wins_bat_first)
    number_of_wins_bat_second = get_value(number_of_wins_bat_second)
    number_of_loss_bat_first = get_value(number_of_loss_bat_first)
    number_of_loss_bat_second = get_value(number_of_loss_bat_second)

    # Add the bar plots for wins
    fig.add_trace(go.Bar(
        x=["Bat First", "Bat Second"],
        y=[number_of_wins_bat_first, number_of_wins_bat_second],
        marker_color=win_palette,
        name='Wins'
    ), row=1, col=1)

    # Add the bar plots for losses
    fig.add_trace(go.Bar(
        x=["Bat First", "Bat Second"],
        y=[number_of_loss_bat_first, number_of_loss_bat_second],
        marker_color=loss_palette,
        name='Losses'
    ), row=1, col=2)

    # Update the layout
    fig.update_layout(
        height=500, 
        width=800, 
        title_text="Match Outcomes: Bat First vs Bat Second",
        showlegend=False
    )

    # Update y-axis titles
    fig.update_yaxes(title_text="Number of Matches Won", row=1, col=1)
    fig.update_yaxes(title_text="Number of Matches Lost", row=1, col=2)

    # Display the bar chart
    st.plotly_chart(fig)

    # Extracting Score from the score string
    # Originally score of 1st inning string looked like this "120/5" but one of scores is "(18/18 ov) 118/5"
    # We want "118/5"

    df_filtered["1st Innings Score"] = df_filtered["1st Innings Score"].str.split(")").str.get(1).fillna(df_filtered["1st Innings Score"])

    # Originally score of 2nd inning string looked like this "(20 ov, T:142) 141/7"
    # We want "141/7"

    df_filtered["2nd Innings Score"] = df_filtered["2nd Innings Score"].str.split(")").str.get(1).fillna(df_filtered["2nd Innings Score"])

    # Extract Selected Team Scores

    team_score = []

    for index, match in df_filtered.iterrows():

        if match["Team Bat First"] == selected_team:
            if "/" in str(match["1st Innings Score"]):
                team_score.append(int(match["1st Innings Score"].split("/")[0]))
            else:
                team_score.append(int(match["1st Innings Score"]))
        elif match["Team Bat Second"] == selected_team:
            if "/" in str(match["2nd Innings Score"]):
                team_score.append(int(match["2nd Innings Score"].split("/")[0]))
            else:
                team_score.append(int(match["2nd Innings Score"]))

    df_filtered[f"{selected_team}'s Score"] = team_score

    # Assuming df is your DataFrame and "Pakistan's Score" is a column in it
    average_score = int(df_filtered[f"{selected_team}'s Score"].mean())

    # Create a Plotly figure
    fig = go.Figure()

    # Add a scatter plot (invisible) to define the layout
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(size=0)
    ))

    # Add an annotation for the average score
    fig.add_annotation(
        text=f"Average Score: {average_score}",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=20, color="RoyalBlue"),
        align='center',
        bordercolor='black',
        borderwidth=2,
        borderpad=4,
        bgcolor='white',
        opacity=0.8
    )

    # Update the layout to adjust the size and hide axes
    fig.update_layout(
        height=100,
        width=300,
        paper_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    # Show the plot
    st.plotly_chart(fig)

    team_pp_score = []
    team_pp_conceded = []

    for index, match in df_filtered.iterrows():

        pp_score = {}
        pp_conceded = {}
        
        if match["Team Bat First"] == selected_team:

            if not match["Over by Over Score (1st Innings)"] == "":
            
                # Remove single quotes and convert to valid JSON format
                data_string = match["Over by Over Score (1st Innings)"].replace("'", "\"")

                # Convert the string to a list of dictionaries
                data_list = json.loads(data_string)
                
                pp_score["Power Play Score"] = data_list[5]["Runs"]
                pp_score["Wickets Lost"] = data_list[5]["Wickets"]
                pp_score[f"{selected_team} Inning"] = "1st"
                pp_score["Opponent"] = match["Team Bat Second"]
                pp_score["Result"] = match["Match Result"]
                pp_score[f"Target to Achieve by {selected_team}"] = 0

                team_pp_score.append(pp_score)

            if not match["Over by Over Score (2nd Innings)"] == "":

                # Remove single quotes and convert to valid JSON format
                data_string = match["Over by Over Score (2nd Innings)"].replace("'", "\"")

                # Convert the string to a list of dictionaries
                data_list = json.loads(data_string)

                pp_conceded["Power Play Score Conceded"] = data_list[5]["Runs"]
                pp_conceded["Opponent Inning"] = "2nd"
                pp_conceded["Wickets Gained"] = data_list[5]["Wickets"] 
                pp_conceded["Target to Achieve By Opponent"] = int(match["1st Innings Score"].split("/")[0]) + 1
                
                team_pp_conceded.append(pp_conceded)
            
        else:
            
            if not match["Over by Over Score (2nd Innings)"] == "":

                # Remove single quotes and convert to valid JSON format
                data_string = match["Over by Over Score (2nd Innings)"].replace("'", "\"")

                # Convert the string to a list of dictionaries
                data_list = json.loads(data_string)
                
                pp_score["Power Play Score"] = data_list[5]["Runs"]
                pp_score[f"{selected_team} Inning"] = "2nd"
                pp_score["Opponent"] = match["Team Bat First"]
                pp_score["Wickets Lost"] = data_list[5]["Wickets"]
                pp_score["Result"] = match["Match Result"]
                pp_score[f"Target to Achieve by {selected_team}"] = int(match["1st Innings Score"].split("/")[0]) + 1

                team_pp_score.append(pp_score)
            
            if not match["Over by Over Score (1st Innings)"] == "":

                # Remove single quotes and convert to valid JSON format
                data_string = match["Over by Over Score (1st Innings)"].replace("'", "\"")

                # Convert the string to a list of dictionaries
                data_list = json.loads(data_string)

                pp_conceded["Power Play Score Conceded"] = data_list[5]["Runs"]
                pp_conceded["Wickets Gained"] = data_list[5]["Wickets"]
                pp_conceded["Opponent Inning"] = "1st"
                pp_conceded["Target to Achieve By Opponent"] = 0
                
                team_pp_conceded.append(pp_conceded)

    df_pp_score = pd.DataFrame(team_pp_score)
    df_pp_conceded = pd.DataFrame(team_pp_conceded)

    df_pp_score["Power Play Score"] = df_pp_score["Power Play Score"].astype(int)
    df_pp_score["Wickets Lost"] = df_pp_score["Wickets Lost"].astype(int)

    df_pp_conceded["Power Play Score Conceded"] = df_pp_conceded["Power Play Score Conceded"].astype(int)
    df_pp_conceded["Wickets Gained"] = df_pp_conceded["Wickets Gained"].astype(int)

    combined_pp_df = pd.concat([df_pp_score, df_pp_conceded], axis=1)

    def pp_plot(df, title):
        bar_width = 0.35
        index = list(range(len(df['Opponent'])))
        
        # Creating the traces
        trace1 = go.Bar(
            x=[i for i in index],
            y=df['Power Play Score'],
            name='Runs Scored in Power Play',
            marker=dict(color='blue')
        )
        
        trace2 = go.Bar(
            x=[i + bar_width for i in index],
            y=df['Power Play Score Conceded'],
            name='Runs Conceded in Power Play',
            marker=dict(color='red')
        )
        
        # Creating the layout
        layout = go.Layout(
            title=title,
            xaxis=dict(
                title='Opponent',
                tickvals=[i + bar_width / 2 for i in index],
                ticktext=df['Opponent'],
                tickangle=90
            ),
            yaxis=dict(
                title='Runs in Power Play'
            ),
            barmode='group'
        )
        
        # Adding values on top of each bar
        annotations = []
        for i, (scored, conceded) in enumerate(zip(df['Power Play Score'], df['Power Play Score Conceded'])):
            annotations.append(dict(
                x=i,
                y=scored,
                text=str(scored),
                xanchor='center',
                yanchor='bottom',
                showarrow=False,
                font=dict(color='gray', size=12, family='Arial')
            ))
            annotations.append(dict(
                x=i + bar_width,
                y=conceded,
                text=str(conceded),
                xanchor='center',
                yanchor='bottom',
                showarrow=False,
                font=dict(color='gray', size=12, family='Arial')
            ))
        
        layout['annotations'] = annotations
        
        # Creating the figure
        fig = go.Figure(data=[trace1, trace2], layout=layout)
        # Show the plot
        st.plotly_chart(fig)

    bat_first_won = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "1st") & (combined_pp_df["Result"] == "Won"))]

    pp_plot(bat_first_won, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat First & Match Won)")

    bat_second_won = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "2nd") & (combined_pp_df["Result"] == "Won"))]

    pp_plot(bat_second_won, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat Second & Match Won)")

    bat_first_lost = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "1st") & (combined_pp_df["Result"] == "Lost"))]

    pp_plot(bat_first_lost, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat First & Match Lost)")

    bat_second_lost = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "2nd") & (combined_pp_df["Result"] == "Lost"))]

    pp_plot(bat_second_lost, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat Second & Match Lost)")

# Define the main function
def main():

    # Initialize session state for the button
    if 'data_extracted' not in st.session_state:
        st.session_state.data_extracted = False
    if 'show_dashboard' not in st.session_state:
        st.session_state.show_dashboard = False

    if not st.session_state.show_dashboard:

        st.title("Extract any Cricket Tournament Data from ESPNCricinfo")
    
        url_input = st.text_area("Enter URL of Fixtures and Results of Tournament. Eg (https://www.espncricinfo.com/series/icc-world-twenty20-2007-08-286109/match-schedule-fixtures-and-results):")

        col1, col2 = st.columns([3, 1])
        
        with col1:

            if st.button("Extract Data"):
                st.subheader(f"Extracting Data from {url_input}.")
                with st.spinner('Extracting data... It may take 2-3 minutes'):
                    st.session_state.data = fetch_data_from_url(url_input)
                    st.write(st.session_state.data)
                    st.session_state.data_extracted = True

            if st.session_state.data_extracted:
                st.write(st.session_state.data)
        
        with col2:
            if st.session_state.data_extracted:
                if st.button("See Analytics Dashboard"):
                    st.session_state.show_dashboard = True
                    st.rerun()
            else:
                st.button("See Analytics Dashboard", disabled=True)
    else:
        st.title("Dashboard")

        if st.button("Back"):
            st.session_state.show_dashboard = False
            st.rerun()
        
        show_dashboard(st.session_state.data)



if __name__ == "__main__":
    main()
