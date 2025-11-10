import streamlit as st

st.set_page_config(page_title="Unified MCP Flask + Streamlit Client")

st.title("Unified MCP + Flask API Client")

st.sidebar.page_link("pages/github_tools.py", label="GitHub Tools")
st.sidebar.page_link("pages/slack_tools.py", label="Slack Tools")
st.sidebar.page_link("pages/time_tools.py", label="Time Tools")

st.write(
    "Select a tool from the sidebar to interact with your backend!"
)
