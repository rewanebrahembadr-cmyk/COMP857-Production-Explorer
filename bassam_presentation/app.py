from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Staff-hour sensitivity | Bassam", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1rem; padding-bottom: 0;}
</style>""", unsafe_allow_html=True)
st.caption("Bassam · COMP857 | Use Previous / Next to navigate. Replay animation restarts the current chart.")
# The reviewed presentation is a bundled local asset, never visitor-supplied HTML.
st.iframe(Path(__file__).with_name("index.html"), height=760, tab_index=0)
