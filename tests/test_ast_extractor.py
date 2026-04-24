"""
CodeLens — AST Extractor Tests
"""
import ast
import textwrap
import tempfile
from pathlib import Path
import pytest
from app.parser.ast_extractor import ASTExtractor, FunctionInfo, ClassInfo


class TestASTExtractor:

    def _write_temp_file(self, source: str) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp.write(textwrap.dedent(source))
        tmp.flush()
        return tmp.name

    def test_extract_simple_function(self):
        source = '''
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y
        '''
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)

        assert module is not None
        assert len(module.functions) == 1
        func = module.functions[0]
        assert func.name == "add"
        assert func.return_type == "int"
        assert len(func.parameters) == 2
        assert func.existing_docstring == "Add two numbers."
        assert func.is_async is False

    def test_extract_async_function(self):
        source = '''
        async def fetch_data(url: str) -> dict:
            pass
        '''
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)

        assert module.functions[0].is_async is True

    def test_extract_class_with_methods(self):
        source = '''
        class Calculator:
            """A simple calculator."""
            def add(self, x: float, y: float) -> float:
                return x + y
            def subtract(self, x: float, y: float) -> float:
                return x - y
        '''
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)

        assert len(module.classes) == 1
        cls = module.classes[0]
        assert cls.name == "Calculator"
        assert cls.existing_docstring == "A simple calculator."
        assert len(cls.methods) == 2

    def test_extract_call_relationships(self):
        source = '''
        def process(data):
            validated = validate(data)
            result = transform(validated)
            return save(result)
        '''
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)

        calls = module.functions[0].calls
        assert "validate" in calls
        assert "transform" in calls
        assert "save" in calls

    def test_extract_function_with_defaults(self):
        source = '''
        def connect(host: str = "localhost", port: int = 5432, timeout: float = 30.0):
            pass
        '''
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)

        params = module.functions[0].parameters
        assert params[0]["default"] == "'localhost'"
        assert params[1]["default"] == "5432"
        assert params[2]["default"] == "30.0"

    def test_handles_syntax_error_gracefully(self):
        source = "def broken( invalid syntax :"
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)
        assert module is None

    def test_extract_module_docstring(self):
        source = '''
        """This is a module docstring."""
        def foo():
            pass
        '''
        path = self._write_temp_file(source)
        extractor = ASTExtractor()
        module = extractor.extract_file(path)
        assert module.module_docstring == "This is a module docstring."

    def test_skips_non_python_files(self):
        extractor = ASTExtractor()
        result = extractor.extract_file("readme.md")
        assert result is None


class TestDiffEngine:

    def test_new_item_is_detected_as_changed(self):
        from app.diff.diff_engine import DiffEngine
        import tempfile, os
        cache_file = tempfile.mktemp(suffix=".json")
        engine = DiffEngine(cache_path=cache_file)

        assert engine.has_changed("/foo.py", "my_func", "def my_func(): pass") is True
        os.unlink(cache_file) if os.path.exists(cache_file) else None

    def test_unchanged_item_not_detected_as_changed(self):
        from app.diff.diff_engine import DiffEngine
        import tempfile, os
        cache_file = tempfile.mktemp(suffix=".json")
        engine = DiffEngine(cache_path=cache_file)

        source = "def my_func(): pass"
        engine.mark_documented("/foo.py", "my_func", source)
        assert engine.has_changed("/foo.py", "my_func", source) is False
        os.unlink(cache_file) if os.path.exists(cache_file) else None

    def test_modified_item_detected_as_changed(self):
        from app.diff.diff_engine import DiffEngine
        import tempfile, os
        cache_file = tempfile.mktemp(suffix=".json")
        engine = DiffEngine(cache_path=cache_file)

        engine.mark_documented("/foo.py", "my_func", "def my_func(): pass")
        assert engine.has_changed("/foo.py", "my_func", "def my_func(): return 42") is True
        os.unlink(cache_file) if os.path.exists(cache_file) else None
