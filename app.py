import streamlit as st
from modules import fetch_data_from_url, show_dashboard

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
