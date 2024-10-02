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
# api_key = os.getenv('GEMINI_API_KEY')
api_key = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=api_key)
model = genai.GenerativeModel('models/gemini-pro')

def dashboard_css():
    # Custom CSS to improve the look and feel
    st.markdown("""
    <style>
        .stApp {
            
            color: #1e1e1e;
        }
        .stSelectbox, .stButton>button {
            background-color: #ffffff;
            color: #1e1e1e;
            border-radius: 5px;
            border: 1px solid #d1d5db;
        }
        .stSelectbox:hover, .stButton>button:hover {
            border-color: #6e7681;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
                
        .stPlotlyChart {
            
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
                
        .stats-container {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .stat-box {
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            text-align: center;
            width: 32%;
            transition: transform 0.3s ease-in-out;
        }
        .stat-box:hover {
            transform: translateY(-5px);
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 16px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
                
        .st-emotion-cache-13ln4jf{
            max-width: 80%;    
        }
    </style>
    """, unsafe_allow_html=True)

def show_dashboard(df):

    dashboard_css()

    st.title("T20 World Cup Analysis Dashboard")

    teams = sorted(set(df["Team Bat First"]).union(set(df["Team Bat Second"])))
    selected_team = st.selectbox("Select a team to analyze", teams)

    st.header(f"Analysis for {selected_team}")

    # Data processing (same as before)
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

    # Win-Loss Ratio
    result_ratio = df_filtered["Match Result"].value_counts()
    
    col1, col2 = st.columns(2)

    with col1:
        fig_pie = go.Figure(data=[go.Pie(
            labels=result_ratio.index, 
            values=result_ratio.values,
            hole=.3,
            marker=dict(colors=['#3498db', '#e74c3c', '#f39c12', '#95a5a6'])
        )])
        fig_pie.update_layout(
            title=f"Win-Loss Ratio of {selected_team}",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        result_counts = df_filtered["Match Result"].value_counts()
        fig_bar = go.Figure([go.Bar(
            x=result_counts.index, 
            y=result_counts.values,
            marker_color=['#3498db', '#e74c3c', '#f39c12', '#95a5a6']
        )])
        fig_bar.update_layout(
            title="Match Results",
            xaxis_title="Result",
            yaxis_title="Number of Matches"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Batting First vs Batting Second Analysis
    df_won = df_filtered[df_filtered["Match Result"] == "Won"]
    df_lost = df_filtered[df_filtered["Match Result"] == "Lost"]

    wins_bat_first = df_won["Team Bat First"].value_counts().get(selected_team, 0)
    wins_bat_second = df_won["Team Bat Second"].value_counts().get(selected_team, 0)
    losses_bat_first = df_lost["Team Bat First"].value_counts().get(selected_team, 0)
    losses_bat_second = df_lost["Team Bat Second"].value_counts().get(selected_team, 0)

    fig_batting = make_subplots(rows=1, cols=2, subplot_titles=("Wins", "Losses"))

    fig_batting.add_trace(go.Bar(
        x=["Batting First", "Batting Second"],
        y=[wins_bat_first, wins_bat_second],
        marker_color=['#3498db', '#2ecc71'],
        name='Wins'
    ), row=1, col=1)

    fig_batting.add_trace(go.Bar(
        x=["Batting First", "Batting Second"],
        y=[losses_bat_first, losses_bat_second],
        marker_color=['#e74c3c', '#f39c12'],
        name='Losses'
    ), row=1, col=2)

    fig_batting.update_layout(
        height=400,
        title_text="Batting First vs Batting Second Analysis",
        showlegend=False
    )

    st.plotly_chart(fig_batting, use_container_width=True)

    # Team Statistics
    st.header("Team Statistics")

    df_filtered["1st Innings Score"] = df_filtered["1st Innings Score"].str.split(")").str.get(1).fillna(df_filtered["1st Innings Score"])
    df_filtered["2nd Innings Score"] = df_filtered["2nd Innings Score"].str.split(")").str.get(1).fillna(df_filtered["2nd Innings Score"])

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

    average_score = int(df_filtered[f"{selected_team}'s Score"].mean())
    highest_score = max(team_score)
    lowest_score = min(team_score)

    st.markdown(f"""
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-value">{average_score}</div>
                <div class="stat-label">Average Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{highest_score}</div>
                <div class="stat-label">Highest Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{lowest_score}</div>
                <div class="stat-label">Lowest Score</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Power Play Analysis
    st.header("Power Play Analysis")

    team_pp_score = []
    team_pp_conceded = []

    for index, match in df_filtered.iterrows():
        pp_score = {}
        pp_conceded = {}
        
        if match["Team Bat First"] == selected_team:
            if match["Over by Over Score (1st Innings)"]:
                data_list = json.loads(match["Over by Over Score (1st Innings)"].replace("'", "\""))
                pp_score["Power Play Score"] = data_list[5]["Runs"]
                pp_score["Wickets Lost"] = data_list[5]["Wickets"]
                pp_score[f"{selected_team} Inning"] = "1st"
                pp_score["Opponent"] = match["Team Bat Second"]
                pp_score["Result"] = match["Match Result"]
                team_pp_score.append(pp_score)

            if match["Over by Over Score (2nd Innings)"]:
                data_list = json.loads(match["Over by Over Score (2nd Innings)"].replace("'", "\""))
                pp_conceded["Power Play Score Conceded"] = data_list[5]["Runs"]
                pp_conceded["Opponent Inning"] = "2nd"
                pp_conceded["Wickets Gained"] = data_list[5]["Wickets"]
                team_pp_conceded.append(pp_conceded)
        else:
            if match["Over by Over Score (2nd Innings)"]:
                data_list = json.loads(match["Over by Over Score (2nd Innings)"].replace("'", "\""))
                pp_score["Power Play Score"] = data_list[5]["Runs"]
                pp_score[f"{selected_team} Inning"] = "2nd"
                pp_score["Opponent"] = match["Team Bat First"]
                pp_score["Wickets Lost"] = data_list[5]["Wickets"]
                pp_score["Result"] = match["Match Result"]
                team_pp_score.append(pp_score)
            
            if match["Over by Over Score (1st Innings)"]:
                data_list = json.loads(match["Over by Over Score (1st Innings)"].replace("'", "\""))
                pp_conceded["Power Play Score Conceded"] = data_list[5]["Runs"]
                pp_conceded["Wickets Gained"] = data_list[5]["Wickets"]
                pp_conceded["Opponent Inning"] = "1st"
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
        
        trace1 = go.Bar(
            x=[i for i in index],
            y=df['Power Play Score'],
            name='Runs Scored in Power Play',
            marker=dict(color='#3498db')
        )
        
        trace2 = go.Bar(
            x=[i + bar_width for i in index],
            y=df['Power Play Score Conceded'],
            name='Runs Conceded in Power Play',
            marker=dict(color='#e74c3c')
        )
        
        layout = go.Layout(
            title=title,
            xaxis=dict(
                title='Opponent',
                tickvals=[i + bar_width / 2 for i in index],
                ticktext=df['Opponent'],
                tickangle=45
            ),
            yaxis=dict(
                title='Runs in Power Play'
            ),
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        annotations = []
        for i, (scored, conceded) in enumerate(zip(df['Power Play Score'], df['Power Play Score Conceded'])):
            annotations.append(dict(
                x=i,
                y=scored,
                text=str(scored),
                xanchor='center',
                yanchor='bottom',
                showarrow=False,
                font=dict(color='white', size=10, family='Arial')
            ))
            annotations.append(dict(
                x=i + bar_width,
                y=conceded,
                text=str(conceded),
                xanchor='center',
                yanchor='bottom',
                showarrow=False,
                font=dict(color='white', size=10, family='Arial')
            ))
        
        layout['annotations'] = annotations
        
        fig = go.Figure(data=[trace1, trace2], layout=layout)
        st.plotly_chart(fig, use_container_width=True)

    bat_first_won = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "1st") & (combined_pp_df["Result"] == "Won"))]

    pp_plot(bat_first_won, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat First & Match Won)")

    bat_second_won = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "2nd") & (combined_pp_df["Result"] == "Won"))]

    pp_plot(bat_second_won, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat Second & Match Won)")

    bat_first_lost = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "1st") & (combined_pp_df["Result"] == "Lost"))]

    pp_plot(bat_first_lost, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat First & Match Lost)")

    bat_second_lost = combined_pp_df[((combined_pp_df[f"{selected_team} Inning"] == "2nd") & (combined_pp_df["Result"] == "Lost"))]

    pp_plot(bat_second_lost, f"Runs Scored VS Runs Conceded in Power Play when ({selected_team} Bat Second & Match Lost)")
