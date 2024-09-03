import streamlit as st
import lchelper as lch
import textwrap
import openai
from openai import OpenAIError

def validate_openai_api_key(api_key):
    '''
    Validate the OpenAI API key by making a simple API call.
    '''
    try:
        openai.api_key = api_key   


        openai.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-3.5-turbo",
        )
        
        
        return True
    except openai.APIError:
        return False
    
st.title("YouTube Assistant")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Authentication form
if not st.session_state.logged_in:
    st.subheader("Login")
    api_key = st.text_input("OpenAI API Key", type="password")
    login_button = st.button("Login")

    if login_button:
        if validate_openai_api_key(api_key):
            st.session_state.logged_in = True
            st.session_state.api_key = api_key
            st.success("API Key verification successful, please click Login again to proceed")
        else:
            st.error("Invalid OpenAI API Key, please try again")
else:
    with st.sidebar:
        with st.form(key='my_form'):
            youtube_url = st.sidebar.text_area("What is the YouTube video URL?", max_chars=50)
            query = st.sidebar.text_area("Ask me about the video?", max_chars=100, key="query")
            language = st.selectbox("Select the language of the video and the response:", ["en", "es", "de"])
            submit_button = st.form_submit_button(label='Submit')       
        
    if submit_button and query and youtube_url:
        openai.api_key = st.session_state.api_key
        db = lch.create_vector_from_youtube_url(youtube_url, language)
        response, doc = lch.get_response_from_query(db, query, language)
        st.subheader("Answer:")
        st.markdown(textwrap.fill(response, width=80))
