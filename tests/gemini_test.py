import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
import google.generativeai as genai

# Assuming the above code is encapsulated in a function called check_team_win
def check_team_win(selected_team, record):
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro')

    result = model.generate_content(
        f"""
        In the statement below,
        Did {selected_team} win the match? If {selected_team} won the match,
        Return "True" 
        Statement: {record}
        Return: 
        """
    )

    result_text = result.text.replace(" ", "").replace("\n", "").replace("\t", "").lower()

    return result_text

class TestCheckTeamWin(unittest.TestCase):

    @patch('google.generativeai.GenerativeModel')
    def test_team_win_true(self, mock_model):
        # Mock the response from the API
        mock_result = MagicMock()
        mock_result.text = 'True'
        mock_model.return_value.generate_content.return_value = mock_result

        selected_team = 'Team A'
        record = 'Team A won the match by 5 wickets.'
        
        result = check_team_win(selected_team, record)
        self.assertEqual(result, 'true')  # Expected output after processing

    @patch('google.generativeai.GenerativeModel')
    def test_team_win_false(self, mock_model):
        # Mock the response from the API
        mock_result = MagicMock()
        mock_result.text = 'False'
        mock_model.return_value.generate_content.return_value = mock_result

        selected_team = 'Team A'
        record = 'Team B won the match by 5 wickets.'
        
        result = check_team_win(selected_team, record)
        self.assertEqual(result, 'false')  # Expected output after processing

    @patch('google.generativeai.GenerativeModel')
    def test_team_win_edge_case(self, mock_model):
        # Mock the response from the API
        mock_result = MagicMock()
        mock_result.text = 'True'
        mock_model.return_value.generate_content.return_value = mock_result

        selected_team = 'Team C'
        record = 'The match ended with Team C winning by 2 runs.'
        
        result = check_team_win(selected_team, record)
        self.assertEqual(result, 'true')  # Expected output after processing

if __name__ == '__main__':
    unittest.main()
