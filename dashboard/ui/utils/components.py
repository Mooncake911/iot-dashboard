import streamlit as st


def section_header(title: str, subtitle: str = None, icon: str = None, level: int = 3):
    """Render a consistent section header."""
    header_text = ("#" * level) + " " + f"{icon} {title}" if icon else title
    st.markdown(header_text)
    if subtitle:
        st.markdown(f"*{subtitle}*")
