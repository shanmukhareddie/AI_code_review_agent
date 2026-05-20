import streamlit as st
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from agent.pipeline import run_pipeline
from agent.ingestion import is_valid_github_url

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🔍",
    layout="wide"
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🔍 AI Code Review Agent")
st.markdown(
    "Paste a **public** Python GitHub repository URL below. "
    "The agent will clone it, parse every function and class, "
    "and return structured review comments with confidence scores."
)

# ── API key guard ─────────────────────────────────────────────────────────────
if not os.getenv("GROQ_API_KEY"):
    st.error(
        "🔒 **GROQ_API_KEY is not configured.**\n\n"
        "To fix this on Streamlit Cloud:\n"
        "1. Open your app dashboard\n"
        "2. Click **Settings → Secrets**\n"
        "3. Add: `GROQ_API_KEY = \"your-key-here\"`"
    )
    st.stop()

st.divider()

# ── Input section ─────────────────────────────────────────────────────────────
st.markdown(
    "💡 **Only public repositories are supported.** "
    "Private repos require authentication which is not available here.\n\n"
    "Example: `https://github.com/psf/requests` or `https://github.com/pallets/flask`"
)

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

# ── Validation + Run ──────────────────────────────────────────────────────────
if run_button:
    if not github_url.strip():
        st.error("❌ Please enter a GitHub repository URL.")
    else:
        valid, msg = is_valid_github_url(github_url.strip())
        if not valid:
            st.error(msg)
        else:
            with st.spinner("⏳ Cloning repo, parsing files, and reviewing code... this may take a minute."):
                try:
                    comments = run_pipeline(github_url.strip(), max_chunks=max_chunks)
                    st.session_state["comments"] = comments
                    st.session_state["url"] = github_url.strip()
                except ValueError as e:
                    st.error(str(e))
                    st.stop()
                except RuntimeError as e:
                    st.error("🔒 " + str(e))
                    st.stop()
                except Exception as e:
                    err = str(e).lower()
                    if "exit code(128)" in err or "could not read username" in err or "authentication" in err:
                        st.error(
                            "🔒 **Private repository detected.**\n\n"
                            "This tool only supports **public** GitHub repositories. "
                            "Please enter a public repo URL."
                        )
                    else:
                        st.error("❌ Something went wrong: " + str(e))
                    st.stop()

# ── Display results ───────────────────────────────────────────────────────────
if "comments" in st.session_state:
    comments = st.session_state["comments"]
    reviewed_url = st.session_state.get("url", "")

    if reviewed_url:
        st.caption("📎 Reviewing: " + reviewed_url)

    if not comments:
        st.warning(
            "⚠️ The agent ran but found no issues. "
            "Try increasing the max functions slider or use a different repo."
        )
    else:
        st.success("✅ Review complete! Found **" + str(len(comments)) + "** comment(s).")
        st.divider()

        # ── Filters ───────────────────────────────────────────────────────────
        st.subheader("🔎 Filter Results")
        fcol1, fcol2 = st.columns(2)

        with fcol1:
            severity_options = ["All"] + sorted(set(c.get("severity", "") for c in comments if c.get("severity")))
            selected_severity = st.selectbox("Filter by Severity", severity_options)

        with fcol2:
            category_options = ["All"] + sorted(set(c.get("category", "") for c in comments if c.get("category")))
            selected_category = st.selectbox("Filter by Category", category_options)

        # Apply filters
        filtered = comments
        if selected_severity != "All":
            filtered = [c for c in filtered if c.get("severity") == selected_severity]
        if selected_category != "All":
            filtered = [c for c in filtered if c.get("category") == selected_category]

        st.markdown("Showing **" + str(len(filtered)) + "** of **" + str(len(comments)) + "** comment(s)")
        st.divider()

        # ── Split by confidence ───────────────────────────────────────────────
        high_conf = [c for c in filtered if c.get("confidence", 0) >= 50]
        low_conf  = [c for c in filtered if c.get("confidence", 0) < 50]

        tab1, tab2 = st.tabs([
            "✅ Review Comments (" + str(len(high_conf)) + ")",
            "🔍 Verify This (" + str(len(low_conf)) + ")"
        ])

        def severity_emoji(s):
            return {"critical": "🔴", "warning": "🟡", "suggestion": "🟢"}.get(str(s).lower(), "⚪")

        def render_comments(comment_list, show_verify_label=False):
            if not comment_list:
                st.info("No comments in this category.")
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
                        label = " ⚠️ `VERIFY THIS`" if show_verify_label else ""
                        st.markdown(
                            severity_emoji(severity) +
                            " **" + issue + "**" +
                            "  `" + severity.upper() + "`" +
                            "  `" + category.upper() + "`" +
                            label
                        )

                    with badge_col:
                        if confidence >= 90:
                            st.success(str(confidence) + "%")
                        elif confidence >= 50:
                            st.warning(str(confidence) + "%")
                        else:
                            st.error(str(confidence) + "%")

                    st.markdown(desc)
                    loc_line = ("  |  Line: " + str(line)) if line else ""
                    st.caption("📄 " + fname + "  |  🔧 " + func + loc_line)

        with tab1:
            render_comments(high_conf, show_verify_label=False)
        with tab2:
            st.info(
                "⚠️ These comments have a confidence score below 50%. "
                "The AI is less certain about these — please review them manually."
            )
            render_comments(low_conf, show_verify_label=True)
