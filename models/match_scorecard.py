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