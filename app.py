import streamlit as st
import pandas as pd
import sys
import os
from dotenv import load_dotenv


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.pipeline import run_pipeline

# Page config
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🔍",
    layout="wide"
)

# Header
st.title("🔍 AI Code Review Agent")
st.markdown(
    "Paste a **public Python GitHub repository** URL below. "
    "The agent will clone it, parse every function and class, "
    "and return structured review comments with confidence scores."
)
st.divider()

# Input section
github_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/username/repository"
)

col1, col2 = st.columns([1, 3])
with col1:
    max_chunks = st.slider(
        "Max functions to review",
        min_value=5,
        max_value=100,
        value=20,
        step=5
    )
with col2:
    st.info("💡 Higher = more coverage but slower. Start with 20 for a quick test.")

run_button = st.button("🚀 Start Review", type="primary", use_container_width=True)

# Run pipeline
if run_button:
    if not github_url.strip():
        st.error("❌ Please enter a GitHub URL.")
    elif not github_url.strip().startswith("https://github.com/"):
        st.error("❌ Please enter a valid public GitHub URL starting with https://github.com/")
    else:
        with st.spinner("⏳ Cloning repo, parsing files, and reviewing code... this may take a minute."):
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

# Display results
if "comments" in st.session_state:
    comments = st.session_state["comments"]

    if not comments:
        st.warning("⚠️ The agent ran but found no issues. Try increasing the max functions slider or use a different repo.")
    else:
        st.success("✅ Review complete! Found **" + str(len(comments)) + "** comment(s).")
        st.divider()

        # Filters
        st.subheader("🔎 Filter Results")
        fcol1, fcol2 = st.columns(2)

        with fcol1:
            severity_options = ["All"] + sorted(set(c.get("severity", "") for c in comments))
            selected_severity = st.selectbox("Filter by Severity", severity_options)

        with fcol2:
            category_options = ["All"] + sorted(set(c.get("category", "") for c in comments))
            selected_category = st.selectbox("Filter by Category", category_options)

        # Apply filters
        filtered = comments
        if selected_severity != "All":
            filtered = [c for c in filtered if c.get("severity") == selected_severity]
        if selected_category != "All":
            filtered = [c for c in filtered if c.get("category") == selected_category]

        st.markdown("Showing **" + str(len(filtered)) + "** of **" + str(len(comments)) + "** comment(s)")
        st.divider()

        # Split by confidence
        high_conf = [c for c in filtered if c.get("confidence", 0) >= 50]
        low_conf  = [c for c in filtered if c.get("confidence", 0) < 50]

        # Tabs
        tab1, tab2 = st.tabs([
            "✅ Review Comments (" + str(len(high_conf)) + ")",
            "🔍 Verify This (" + str(len(low_conf)) + ")"
        ])

        def severity_emoji(s):
            return {"‘critical’": "🔴", "critical": "🔴", "warning": "🟡", "suggestion": "🟢"}.get(s, "⚪")

        def render_comments(comment_list, show_verify_label=False):
            if not comment_list:
                st.info("No comments here.")
                return
            for c in comment_list:
                confidence = c.get("confidence", 0)
                severity   = c.get("severity", "suggestion")
                category   = c.get("category", "")
                issue      = c.get("issue", "Issue")
                desc       = c.get("description", "")
                fname      = os.path.basename(c.get("file", "unknown"))
                func       = c.get("function", "unknown")
                line       = c.get("line", None)

                with st.container(border=True):
                    top_col, badge_col = st.columns([5, 1])

                    with top_col:
                        label = ""
                        if show_verify_label:
                            label = " ⚠️ `VERIFY THIS`"
                        st.markdown(
                            severity_emoji(severity) +
                            " **" + issue + "**" +
                            "  `" + severity.upper() + "`" +
                            "  `" + category.upper() + "`" +
                            label
                        )

                    with badge_col:
                        if confidence >= 80:
                            st.success(str(confidence) + "%")
                        elif confidence >= 50:
                            st.warning(str(confidence) + "%")
                        else:
                            st.error(str(confidence) + "%")

                    st.progress(confidence / 100)
                    st.markdown(desc)

                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.caption("📄 " + fname)
                    with m2:
                        st.caption("⚙️ " + func)
                    with m3:
                        st.caption("📍 Line " + (str(line) if line else "unknown"))

        with tab1:
            render_comments(high_conf, show_verify_label=False)

        with tab2:
            st.warning("⚠️ These comments have low confidence (below 50%). The agent is uncertain — please verify manually before acting on them.")
            render_comments(low_conf, show_verify_label=True)

        # Download
        st.divider()
        st.subheader("📥 Download Results")
        if filtered:
            df = pd.DataFrame(filtered)
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download filtered results as CSV",
                data=csv,
                file_name="code_review_results.csv",
                mime="text/csv",
                use_container_width=True
            )
