import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.pipeline import run_pipeline

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🔍",
    layout="wide"
)

# ─── Header ────────────────────────────────────────────────────
st.title("🔍 AI Code Review Agent")
st.markdown("Paste a public Python GitHub repository URL and the agent will review the code for bugs, security issues, and style problems.")
st.divider()

# ─── Input ─────────────────────────────────────────────────────
github_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/username/repository"
)

col1, col2 = st.columns([1, 3])
with col1:
    max_chunks = st.slider("Max functions to review", min_value=5, max_value=100, value=20, step=5)
with col2:
    st.info("Higher values = more coverage but slower. Start with 20 for a quick review.")

run_button = st.button("🚀 Start Review", type="primary", use_container_width=True)

# ─── Run Pipeline ───────────────────────────────────────────────
if run_button:
    if not github_url.strip():
        st.error("Please enter a GitHub URL.")
    elif not github_url.startswith("https://github.com/"):
        st.error("Please enter a valid GitHub URL starting with https://github.com/")
    else:
        with st.spinner("Cloning repo, parsing files and reviewing code... this may take a minute."):
            try:
                comments = run_pipeline(github_url.strip(), max_chunks=max_chunks)
                st.session_state["comments"] = comments
                st.session_state["url"] = github_url.strip()
            except ValueError as e:
                st.error("Error: " + str(e))
                st.stop()
            except Exception as e:
                st.error("Something went wrong: " + str(e))
                st.stop()

# ─── Display Results ────────────────────────────────────────────
if "comments" in st.session_state and st.session_state["comments"]:
    comments = st.session_state["comments"]
    st.success("Review complete! Found " + str(len(comments)) + " comment(s) across the repository.")
    st.divider()

    # ─── Filters ────────────────────────────────────────────────
    st.subheader("🔎 Filters")
    fcol1, fcol2 = st.columns(2)

    with fcol1:
        severity_options = ["All"] + sorted(set(c["severity"] for c in comments))
        selected_severity = st.selectbox("Filter by Severity", severity_options)

    with fcol2:
        category_options = ["All"] + sorted(set(c["category"] for c in comments))
        selected_category = st.selectbox("Filter by Category", category_options)

    # Apply filters
    filtered = comments
    if selected_severity != "All":
        filtered = [c for c in filtered if c["severity"] == selected_severity]
    if selected_category != "All":
        filtered = [c for c in filtered if c["category"] == selected_category]

    st.markdown("Showing **" + str(len(filtered)) + "** comment(s)")
    st.divider()

    # ─── Split high vs low confidence ───────────────────────────
    high_conf = [c for c in filtered if c.get("confidence", 0) >= 50]
    low_conf  = [c for c in filtered if c.get("confidence", 0) < 50]

    # ─── Tabs ───────────────────────────────────────────────────
    tab1, tab2 = st.tabs([
        "✅ Review Comments (" + str(len(high_conf)) + ")",
        "🔍 Verify This (" + str(len(low_conf)) + ")"
    ])

    def severity_emoji(severity):
        return {"critical": "🔴", "warning": "🟡", "suggestion": "🟢"}.get(severity, "⚪")

    def confidence_color(confidence):
        if confidence >= 80:
            return "green"
        elif confidence >= 50:
            return "orange"
        else:
            return "red"

    def render_comments(comment_list):
        if not comment_list:
            st.info("No comments in this category.")
            return
        for c in comment_list:
            confidence = c.get("confidence", 0)
            severity   = c.get("severity", "suggestion")
            with st.container(border=True):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(
                        severity_emoji(severity) + " **" + c.get("issue", "Issue") + "**" +
                        "  `" + severity.upper() + "`" +
                        "  `" + c.get("category", "").upper() + "`"
                    )
                with col_b:
                    st.markdown(":" + confidence_color(confidence) + "[" + str(confidence) + "% confidence]")

                st.progress(confidence / 100)
                st.markdown(c.get("description", ""))

                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    st.caption("📄 File: " + os.path.basename(c.get("file", "unknown")))
                with meta_col2:
                    st.caption("⚙️ Function: " + c.get("function", "unknown"))
                with meta_col3:
                    line = c.get("line")
                    st.caption("📍 Line: " + (str(line) if line else "unknown"))

    with tab1:
        render_comments(high_conf)

    with tab2:
        st.warning("These comments have low confidence (< 50%). The agent is uncertain — please verify manually.")
        render_comments(low_conf)

    # ─── Download ───────────────────────────────────────────────
    st.divider()
    st.subheader("📥 Download Results")
    df = pd.DataFrame(filtered)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="code_review_results.csv",
        mime="text/csv",
        use_container_width=True
    )

elif "comments" in st.session_state and not st.session_state["comments"]:
    st.warning("The agent ran successfully but found no issues in the reviewed functions. Try increasing the max functions slider.")
