import streamlit as st
import os
import sys
import json
import csv
import io
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from agent.pipeline import run_pipeline
from agent.ingestion import is_valid_github_url

# ── Page config
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🔍",
    layout="wide"
)

# ── Header 
st.title("🔍 AI Code Review Agent")
st.markdown(
    "Paste a **public** GitHub repository URL below. "
    "The agent will clone it, parse every function and class, "
    "and return structured review comments with confidence scores.\n\n"
    "🐍 **Python** and ☕ **Java** files are supported."
)


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

# ── Input section 
st.markdown(
    "💡 **Only public repositories are supported.** "
    "Private repos require authentication which is not available here."
)

github_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/username/repository"
)

st.divider()

# ── Settings 
st.subheader("⚙️ Review Settings")

col1, col2 = st.columns(2)

with col1:
    max_chunks = st.slider(
        "🔢 Max functions/classes to review",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        help=(
            "Controls how many functions and classes are sent to the AI for review. "
            "The repo may contain more, but only this many will be reviewed per run. "
            "Higher = more thorough but slower and uses more API quota. "
            "Recommended: 20 for a quick test, 50–100 for full coverage."
        )
    )
    st.caption(
        "💡 The agent picks the **first " + str(max_chunks) + "** functions/classes found in the repo. "
        "Increase this for larger codebases."
    )

with col2:
    max_lines = st.slider(
        "📐 Max lines per function/class",
        min_value=20,
        max_value=300,
        value=100,
        step=10,
        help=(
            "Functions or classes longer than this limit are **skipped** — they would be too large "
            "to send to the LLM in a single prompt without hitting token limits. "
            "Lower = faster and cheaper but skips more code. "
            "Higher = reviews larger functions but may slow down or exceed token limits. "
            "Recommended: 100 lines for most repos."
        )
    )
    st.caption(
        "⚠️ Functions/classes longer than **" + str(max_lines) + " lines** will be skipped. "
        "Increase this if you want larger blocks reviewed."
    )

run_button = st.button("🚀 Start Review", type="primary", use_container_width=True)

# ── Validation + Run 
if run_button:
    if not github_url.strip():
        st.error("❌ Please enter a GitHub repository URL.")
    else:
        valid, msg = is_valid_github_url(github_url.strip())
        if not valid:
            st.error(msg)
        else:
            progress_placeholder = st.empty()
            with st.spinner("⏳ Cloning repo, parsing files, and reviewing code..."):
                try:
                    progress_placeholder.info("📥 Step 1/3 — Cloning repository...")
                    comments, total_found = run_pipeline(
                        github_url.strip(),
                        max_chunks=max_chunks,
                        max_lines_per_chunk=max_lines
                    )
                    progress_placeholder.empty()
                    st.session_state["comments"]    = comments
                    st.session_state["url"]         = github_url.strip()
                    st.session_state["total_found"] = total_found
                    st.session_state["max_chunks"]  = max_chunks
                except ValueError as e:
                    progress_placeholder.empty()
                    st.error(str(e))
                    st.stop()
                except RuntimeError as e:
                    progress_placeholder.empty()
                    st.error("🔒 " + str(e))
                    st.stop()
                except Exception as e:
                    progress_placeholder.empty()
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

# ── Display results 
if "comments" in st.session_state:
    comments    = st.session_state["comments"]
    reviewed_url = st.session_state.get("url", "")
    total_found  = st.session_state.get("total_found", 0)
    max_chunks   = st.session_state.get("max_chunks", 20)

    if reviewed_url:
        st.caption("📎 Reviewing: " + reviewed_url)

    # Show skipped warning if not all chunks were reviewed
    if total_found > max_chunks:
        st.warning(
            "⚠️ Found **" + str(total_found) + "** functions/classes in the repo, "
            "but only the first **" + str(max_chunks) + "** were reviewed. "
            "Increase the **Max functions/classes to review** slider for more coverage."
        )

    if not comments:
        st.warning(
            "⚠️ The agent ran but found no issues. "
            "Try increasing the sliders or use a different repo."
        )
    else:
        st.success("✅ Review complete! Found **" + str(len(comments)) + "** comment(s).")
        st.divider()

        # ── Export buttons 
        st.subheader("📤 Export Results")
        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            json_str = json.dumps(comments, indent=2)
            st.download_button(
                label="⬇️ Download as JSON",
                data=json_str,
                file_name="review_results.json",
                mime="application/json",
                use_container_width=True
            )

        with exp_col2:
            csv_buffer = io.StringIO()
            fieldnames = ["issue", "severity", "category", "confidence", "description", "file", "function", "line", "language"]
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(comments)
            st.download_button(
                label="⬇️ Download as CSV",
                data=csv_buffer.getvalue(),
                file_name="review_results.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.divider()

        # ── Filters 
        st.subheader("🔎 Filter Results")
        fcol1, fcol2, fcol3 = st.columns(3)

        with fcol1:
            severity_options = ["All"] + sorted(set(c.get("severity", "") for c in comments if c.get("severity")))
            selected_severity = st.selectbox("Filter by Severity", severity_options)

        with fcol2:
            category_options = ["All"] + sorted(set(c.get("category", "") for c in comments if c.get("category")))
            selected_category = st.selectbox("Filter by Category", category_options)

        with fcol3:
            language_options = ["All"] + sorted(set(c.get("language", "") for c in comments if c.get("language")))
            selected_language = st.selectbox("Filter by Language", language_options)

        # Apply filters
        filtered = comments
        if selected_severity != "All":
            filtered = [c for c in filtered if c.get("severity") == selected_severity]
        if selected_category != "All":
            filtered = [c for c in filtered if c.get("category") == selected_category]
        if selected_language != "All":
            filtered = [c for c in filtered if c.get("language") == selected_language]

        st.markdown("Showing **" + str(len(filtered)) + "** of **" + str(len(comments)) + "** comment(s)")
        st.divider()

        # ── Split by confidence 
        high_conf = [c for c in filtered if c.get("confidence", 0) >= 50]
        low_conf  = [c for c in filtered if c.get("confidence", 0) < 50]

        tab1, tab2 = st.tabs([
            "✅ Review Comments (" + str(len(high_conf)) + ")",
            "🔍 Verify This (" + str(len(low_conf)) + ")"
        ])

        def severity_emoji(s):
            return {"critical": "🔴", "warning": "🟡", "suggestion": "🟢"}.get(str(s).lower(), "⚪")

        def lang_badge(lang):
            return {"🐍": "python", "☕": "java"}.get(lang, lang)

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
                lang       = c.get("language", "")
                lang_icon  = "🐍" if lang == "python" else ("☕" if lang == "java" else "")

                with st.container(border=True):
                    top_col, badge_col = st.columns([5, 1])

                    with top_col:
                        label = " ⚠️ `VERIFY THIS`" if show_verify_label else ""
                        st.markdown(
                            severity_emoji(severity) +
                            " **" + issue + "**" +
                            "  `" + severity.upper() + "`" +
                            "  `" + category.upper() + "`" +
                            ("  " + lang_icon + " `" + lang.upper() + "`" if lang else "") +
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
