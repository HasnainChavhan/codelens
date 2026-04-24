"""
CodeLens — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


app = FastAPI(
    title="CodeLens",
    description="AI-Powered Codebase Documentation Engine",
    version=settings.app_version,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
async def root():
    return {"service": "CodeLens", "version": settings.app_version,
            "ui": "streamlit run ui/streamlit_app.py"}


@app.post("/extract")
async def extract(repo_path: str):
    """Extract AST metadata from a repository."""
    from app.parser.ast_extractor import ASTExtractor
    extractor = ASTExtractor()
    modules = extractor.extract_repository(repo_path)
    return {
        "modules": len(modules),
        "total_functions": sum(len(m.functions) for m in modules),
        "total_classes": sum(len(m.classes) for m in modules),
        "total_lines": sum(m.total_lines for m in modules),
        "module_list": [m.to_dict() for m in modules],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "CodeLens"}
