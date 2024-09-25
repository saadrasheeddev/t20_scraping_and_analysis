import streamlit as st
from modules.fetch_data_from_url import fetch_data_from_url
from modules.show_dashboard import show_dashboard

# Add custom professional CSS for aesthetics
def add_custom_css():
    st.markdown("""
        <style>
            /* General layout and body */
            body {
                background-color: #f5f7fa;
                color: #333333;
                font-family: 'Roboto', sans-serif;
            }

            /* Container for padding and margin */
            .main-container {
                padding: 40px;
                margin: auto;
                width: 80%;
                max-width: 1100px;
                background-color: #ffffff;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }

            /* Title Styling */
            .title {
                color: #003f5c;
                font-size: 2.5rem;
                font-weight: 700;
                text-align: center;
                margin-bottom: 20px;
            }

            /* Subtitle and headers */
            .subheader {
                font-size: 1.25rem;
                color: #665191;
                margin-bottom: 20px;
            }

            /* Text area styling */
            textarea {
                border-radius: 8px;
                border: 1px solid #dddddd;
                padding: 15px;
                width: 100%;
                font-size: 1rem;
                background-color: #f9fafc;
            }

            /* Buttons */
            .stButton button {
                background-color: #003f5c;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 1rem;
                font-weight: bold;
                margin-top: 20px;
                transition: background-color 0.3s ease;
            }

            .stButton button:hover {
                background-color: #2f4b7c;
            }

            .stButton button:disabled {
                background-color: #cccccc;
                color: #666666;
            }

            /* Spinner styling */
            .stSpinner {
                font-size: 1.1rem;
                margin-top: 15px;
            }

            /* Dashboard back button */
            .stButton button.back-button {
                background-color: #d62728;
                color: #ffffff;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 1rem;
            }

            .stButton button.back-button:hover {
                background-color: #c12522;
            }

            /* Column and card layout */
            .column-card {
                padding: 20px;
                margin: 15px 0;
                background-color: #f1f1f1;
                border-radius: 8px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
            }

            /* Table data styling */
            .data-table {
                margin-top: 20px;
                border-radius: 8px;
                overflow: hidden;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th, td {
                padding: 12px;
                border: 1px solid #dddddd;
                text-align: left;
            }

            th {
                background-color: #2f4b7c;
                color: #ffffff;
            }

            td {
                background-color: #f9fafc;
            }

            /* For a responsive layout */
            @media screen and (max-width: 768px) {
                .main-container {
                    width: 95%;
                }

                .title {
                    font-size: 2rem;
                }

                textarea {
                    font-size: 0.9rem;
                }

                .stButton button {
                    font-size: 0.9rem;
                    padding: 10px 25px;
                }
            }

        </style>
    """, unsafe_allow_html=True)

# Define the main function
def main():
    # Add the custom CSS for professional design
    add_custom_css()

    # Initialize session state for buttons and dashboard view
    if 'data_extracted' not in st.session_state:
        st.session_state.data_extracted = False
    if 'show_dashboard' not in st.session_state:
        st.session_state.show_dashboard = False

    with st.container():
        # st.markdown("<div class='main-container'>", unsafe_allow_html=True)

        if not st.session_state.show_dashboard:
            st.markdown("<h1 class='title'>Extract Cricket Tournament Data</h1>", unsafe_allow_html=True)

            st.markdown("""
                <h3 class='subheader'>
                    Enter the URL of a tournament's fixtures and results page from ESPNCricinfo to extract and analyze the data.
                </h3>
            """, unsafe_allow_html=True)

            url_input = st.text_area(
                "Enter the URL of Fixtures and Results (e.g., https://www.espncricinfo.com/series/icc-world-twenty20-2007-08-286109/match-schedule-fixtures-and-results):")

            col1, col2 = st.columns([3, 1])

            with col1:
                if st.button("Extract Data"):
                    st.subheader(f"Extracting Data from {url_input}.")
                    with st.spinner('Extracting data... It may take 2-3 minutes'):
                        st.session_state.data = fetch_data_from_url(url_input)
                        st.write(st.session_state.data)
                        st.session_state.data_extracted = True

                if st.session_state.data_extracted:
                    st.markdown("<div class='column-card'>", unsafe_allow_html=True)
                    st.write(st.session_state.data)
                    st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                if st.session_state.data_extracted:
                    if st.button("See Analytics Dashboard"):
                        st.session_state.show_dashboard = True
                        st.rerun()
                else:
                    st.button("See Analytics Dashboard", disabled=True)
        else:
            st.markdown("<h1 class='title'>Dashboard</h1>", unsafe_allow_html=True)

            if st.button("Back", key="back_button", args=("Back")):
                st.session_state.show_dashboard = False
                st.rerun()

            show_dashboard(st.session_state.data)

        # st.markdown("</div>", unsafe_allow_html=True)

# Run the app
if __name__ == '__main__':
    main()

