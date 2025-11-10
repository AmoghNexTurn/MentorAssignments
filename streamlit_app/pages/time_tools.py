import streamlit as st
import requests

st.title("Time Tools API")

action = st.selectbox(
    "Choose Action",
    ["current_time", "sunrise_or_sunset"]
)

location = st.text_input("Location (city/country)")

if st.button("Submit"):
    payload = {
        "action": action,
        "location": location,
    }
    resp = requests.post("http://localhost:8000/time", json=payload)
    if resp.status_code == 200:
        st.success(resp.json()["response"])
    else:
        st.error(f"Error: {resp.json().get('error', 'Request failed')}")
