import streamlit as st
try:
    st.page_link("pages/1_surplus_radar.py", label="Radar", icon="🌶️")
    st.write("Link rendered successfully!")
except Exception as e:
    st.write(f"Error: {e}")
