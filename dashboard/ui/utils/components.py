import streamlit as st

def section_header(title: str, subtitle: str = None, icon: str = None):
    """Render a consistent section header."""
    header_text = f"{icon} {title}" if icon else title
    st.markdown(f"### {header_text}")
    if subtitle:
        st.markdown(f"*{subtitle}*")

def config_container(title: str = "⚙️ Configuration"):
    """Context manager for a configuration section."""
    st.subheader(title)
    return st.container()

def metric_row(metrics_dict: dict, columns=None):
    """Render a row of metrics from a dictionary."""
    num_metrics = len(metrics_dict)
    cols = st.columns(columns or num_metrics)
    for idx, (label, val_data) in enumerate(metrics_dict.items()):
        col = cols[idx % len(cols)]
        if isinstance(val_data, tuple):
            val, delta = val_data
            col.metric(label, val, delta)
        else:
            col.metric(label, val_data)

def render_apply_button(key: str):
    """Render a consistent 'Apply' button."""
    return st.button("💾 Apply Configuration", key=key, use_container_width=True)
