import streamlit as st
import os                                                                                                                                                                                            
from dotenv import load_dotenv
import google.generativeai as genai
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Access the API key
api_key = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=api_key)
model = genai.GenerativeModel('models/gemini-pro')

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
        elif "abandoned" in record:
            df_filtered.at[index, "Match Result"] = "Abandoned"
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
