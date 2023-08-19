import streamlit as st
import time
from tempfile import TemporaryDirectory
from ganymede_core import unpack_and_validate

st.title("Ganymede")

if "consent" not in st.session_state:
    st.session_state.consent = False


def consent_callback():
    st.session_state.consent = not st.session_state.consent


st.write("This is a webapp for Ganymede, a tool for converting jupyter notebooks to pdfs.")
print(st.session_state["consent"])
with st.expander(expanded=not st.session_state["consent"], label="Privacy Policy") as e:
    st.write("Privacy Policy")  # TODO: Add privacy policy
    st.session_state["consent"] = st.checkbox(
        "I consent to the use of my data for the purposes outlined in the privacy policy.", on_change=consent_callback)

if st.session_state.consent:
    st.divider()
    with st.form(key="file_upload"):
        file = st.file_uploader("Upload your file:")
        with st.expander(label="Advanced options"):
            convert_mode = st.selectbox(
                "Select conversion mode:",
                ("latex", "html")
            )
            coercion = st.checkbox("Force conversion type")
        submitted = st.form_submit_button(label="Submit")

    if submitted:
        if not file:
            st.error("Please upload a file.")
            st.stop()
        with TemporaryDirectory() as temp_dir:
            file.seek(0)
            with open(f"{temp_dir}/{file.name}", "wb") as f:
                f.write(file.read())
            try:
                unpack_and_validate(temp_dir)
            except Exception as e:
                st.error(e)
                st.stop()

        # TODO: add real conversion logic
        pbar = st.progress(0, text="Uploading file...")
        for i in range(100):
            pbar.progress(i + 1)
            time.sleep(0.02)
        st.success("File converted successfully!")
        st.download_button("Download converted file", data="test", file_name="test.pdf")


