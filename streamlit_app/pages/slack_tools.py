import streamlit as st
import requests

st.title("Slack Tools API")

action = st.selectbox(
    "Choose Slack Action",
    ["send_message", "read_users"]
)

message = None
if action == "send_message":
    message = st.text_area("Message")

if st.button("Submit"):
    payload = {
        "action": action,
    }
    if message:
        payload["message"] = message
    resp = requests.post("http://localhost:8000/slack", json=payload)
    if resp.status_code == 200:
        st.success(resp.json()["response"])
    else:
        st.error(f"Error: {resp.json().get('error', 'Request failed')}")
