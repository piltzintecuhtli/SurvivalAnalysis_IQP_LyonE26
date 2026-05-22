import streamlit as st
import pandas as pd

st.write("Here's our first attempt at using data to create a table:")
st.write(pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
}))

file = st.file_uploader("Upload dataset here:", type="csv", accept_multiple_files=False, width="stretch""")

if file is not None:
    st.write("Uploaded file successfully!")
    st.write("Data:")
    df = pd.read_csv(file)
    df