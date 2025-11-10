import streamlit as st
import requests

st.title("GitHub Tools API")

api_base = "http://localhost:8000/github"  # Adjust if deployed remotely

action = st.selectbox("Choose GitHub Action", ["create_repo", "issues"])
repo = st.text_input("Repository Name")

if st.button("Submit"):
    payload = {
        "action": action,
        "repo": repo,
    }
    resp = requests.post(api_base, json=payload)
    if resp.status_code == 200:
        st.success(resp.json()["response"])
    else:
        st.error(f"Error: {resp.json().get('error', 'Request failed')}")
