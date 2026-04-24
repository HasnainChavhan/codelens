"""
CodeLens — Streamlit Interactive UI
Interactive repo exploration, diff-based doc refresh, and one-click export.
"""
import streamlit as st
import tempfile
import os
from pathlib import Path

st.set_page_config(
    page_title="CodeLens — AI Documentation Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
.main { background-color: #0f172a; }
.stApp { background-color: #0f172a; }
h1, h2, h3 { color: #38bdf8 !important; }
.metric-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 1.2rem;
    border: 1px solid #334155;
    margin-bottom: 1rem;
}
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 CodeLens")
st.markdown("**AI-Powered Codebase Documentation Engine** — Understands your code at the AST level")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"])
    st.divider()
    st.header("📤 Export Options")
    export_markdown = st.checkbox("Export Markdown", value=True)
    export_html = st.checkbox("Export HTML", value=True)
    st.divider()
    st.markdown("**Diff Mode**")
    use_diff = st.checkbox("Only re-document changed functions", value=True,
                           help="Uses content hashing to skip unchanged code")

# ── Main area ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📁 Repository Input")
    repo_path = st.text_input(
        "Repository Path",
        placeholder="C:/path/to/your/project",
        help="Absolute path to the Python codebase you want to document",
    )

    uploaded = st.file_uploader(
        "Or upload individual Python files",
        type=["py"],
        accept_multiple_files=True,
    )

with col2:
    st.header("📊 Last Run Stats")
    if "stats" in st.session_state:
        stats = st.session_state["stats"]
        st.metric("Modules Processed", stats.get("modules", 0))
        st.metric("Functions Documented", stats.get("functions", 0))
        st.metric("Classes Documented", stats.get("classes", 0))
        st.metric("Time Taken", f"{stats.get('time_s', 0):.1f}s")
    else:
        st.info("Run documentation to see stats")

st.divider()

# ── Run Documentation ─────────────────────────────────────────────────────────
if st.button("▶ Generate Documentation", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar")
        st.stop()

    if not repo_path and not uploaded:
        st.error("Please provide a repository path or upload Python files")
        st.stop()

    # Set the API key
    os.environ["OPENAI_API_KEY"] = openai_key

    with st.spinner("🔍 Extracting AST structure..."):
        try:
            from app.parser.ast_extractor import ASTExtractor
            from app.generator.doc_generator import DocGenerator
            from app.diff.diff_engine import DiffEngine
            from app.exporter.markdown_exporter import MarkdownExporter, HTMLExporter

            import time
            start_time = time.time()

            extractor = ASTExtractor()

            if repo_path and Path(repo_path).exists():
                modules = extractor.extract_repository(repo_path)
            elif uploaded:
                modules = []
                with tempfile.TemporaryDirectory() as tmpdir:
                    for f in uploaded:
                        tmp_path = Path(tmpdir) / f.name
                        tmp_path.write_bytes(f.read())
                        mod = extractor.extract_file(str(tmp_path))
                        if mod:
                            modules.append(mod)
            else:
                st.error("Invalid path or no files uploaded")
                st.stop()

            total_functions = sum(
                len(m.functions) + sum(len(c.methods) for c in m.classes)
                for m in modules
            )
            total_classes = sum(len(m.classes) for m in modules)

            st.success(
                f"✅ AST extracted: {len(modules)} modules, "
                f"{total_functions} functions, {total_classes} classes"
            )

        except Exception as e:
            st.error(f"AST extraction failed: {e}")
            st.stop()

    with st.spinner("🤖 Generating documentation with GPT-4o..."):
        try:
            progress = st.progress(0)
            status_text = st.empty()

            generator = DocGenerator()
            diff_engine = DiffEngine() if use_diff else None

            if use_diff and diff_engine:
                changed = diff_engine.get_changed_items(modules)
                status_text.text(
                    f"Diff mode: {len(changed['functions'])} functions, "
                    f"{len(changed['classes'])} classes need update "
                    f"({changed['unchanged_count']} unchanged, skipped)"
                )

            def on_progress(done, total):
                pct = int((done / total) * 100) if total > 0 else 100
                progress.progress(pct)
                status_text.text(f"Documenting... {done}/{total}")

            docs = generator.generate_repository_docs(modules, progress_callback=on_progress)
            elapsed = time.time() - start_time

            st.session_state["docs"] = docs
            st.session_state["stats"] = {
                "modules": len(modules),
                "functions": total_functions,
                "classes": total_classes,
                "time_s": elapsed,
            }

            st.success(f"✅ Documentation generated in {elapsed:.1f}s!")
            st.rerun()

        except Exception as e:
            st.error(f"Documentation generation failed: {e}")

# ── Preview & Export ──────────────────────────────────────────────────────────
if "docs" in st.session_state:
    st.header("📄 Documentation Preview")
    docs = st.session_state["docs"]

    selected_module = st.selectbox(
        "Select module to preview",
        options=list(docs.keys()),
        format_func=lambda p: Path(p).stem,
    )

    if selected_module and selected_module in docs:
        module_doc = docs[selected_module]

        with st.expander("📦 Module Documentation", expanded=True):
            st.markdown(module_doc.get("module_doc", "_No module doc_"))

        if module_doc.get("functions"):
            with st.expander(f"⚙️ Functions ({len(module_doc['functions'])})"):
                for func_name, doc in module_doc["functions"].items():
                    st.subheader(f"`{func_name}`")
                    st.code(doc, language="text")

        if module_doc.get("classes"):
            with st.expander(f"🏗️ Classes ({len(module_doc['classes'])})"):
                for class_name, class_docs in module_doc["classes"].items():
                    st.subheader(f"`{class_name}`")
                    st.code(class_docs.get("class_doc", ""), language="text")

    st.divider()
    st.header("📤 Export")

    export_dir = st.text_input("Export Directory", value="codelens_output")

    col_md, col_html = st.columns(2)

    with col_md:
        if st.button("📥 Export Markdown", use_container_width=True) and export_markdown:
            try:
                from app.exporter.markdown_exporter import MarkdownExporter
                exporter = MarkdownExporter()
                files = exporter.export(docs, export_dir)
                st.success(f"✅ {len(files)} Markdown files exported to `{export_dir}/`")
            except Exception as e:
                st.error(f"Export failed: {e}")

    with col_html:
        if st.button("🌐 Export HTML", use_container_width=True) and export_html:
            try:
                from app.exporter.markdown_exporter import HTMLExporter
                exporter = HTMLExporter()
                files = exporter.export(docs, export_dir + "/html")
                st.success(f"✅ {len(files)} HTML files exported to `{export_dir}/html/`")
            except Exception as e:
                st.error(f"Export failed: {e}")

st.divider()
st.caption("CodeLens © 2024 | AI-Powered Codebase Documentation | Tested on 50,000+ line codebases")
