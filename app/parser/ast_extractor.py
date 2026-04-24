"""
CodeLens — AST-Based Code Extractor
Uses Python's AST parser to extract function signatures, docstrings,
parameters, return types, and call relationships — not just reading raw text.
"""
import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    name: str
    module: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    parameters: list[dict]
    return_type: Optional[str]
    existing_docstring: Optional[str]
    source_code: str
    decorators: list[str]
    is_async: bool
    is_method: bool
    class_name: Optional[str] = None
    calls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "module": self.module,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "existing_docstring": self.existing_docstring,
            "source_code": self.source_code,
            "decorators": self.decorators,
            "is_async": self.is_async,
            "is_method": self.is_method,
            "class_name": self.class_name,
            "calls": self.calls,
        }


@dataclass
class ClassInfo:
    name: str
    module: str
    file_path: str
    line_start: int
    line_end: int
    bases: list[str]
    existing_docstring: Optional[str]
    methods: list[FunctionInfo]
    decorators: list[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "module": self.module,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "bases": self.bases,
            "existing_docstring": self.existing_docstring,
            "methods": [m.to_dict() for m in self.methods],
            "decorators": self.decorators,
        }


@dataclass
class ModuleInfo:
    path: str
    module_name: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
    module_docstring: Optional[str]
    total_lines: int

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "module_name": self.module_name,
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "imports": self.imports,
            "module_docstring": self.module_docstring,
            "total_lines": self.total_lines,
        }


class ASTExtractor:
    """
    Extracts structured code metadata using Python's AST parser.

    Unlike raw text parsing, AST extraction gives us:
    - Exact parameter names, types, and defaults
    - Return type annotations
    - Full call relationships (what each function calls)
    - Class hierarchies and method ownership
    - Decorator chains
    """

    def extract_file(self, file_path: str) -> Optional[ModuleInfo]:
        """
        Extract all code metadata from a Python source file.

        Args:
            file_path: Absolute path to the .py file

        Returns:
            ModuleInfo with all functions, classes, and relationships
        """
        path = Path(file_path)
        if not path.exists() or path.suffix != ".py":
            return None

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path}, skipping")
            return None

        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return None

        module_name = path.stem
        source_lines = source.splitlines()

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._extract_function(node, source_lines, module_name, file_path)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class(node, source_lines, module_name, file_path)
                classes.append(class_info)

        module_docstring = ast.get_docstring(tree)

        return ModuleInfo(
            path=file_path,
            module_name=module_name,
            functions=functions,
            classes=classes,
            imports=imports,
            module_docstring=module_docstring,
            total_lines=len(source_lines),
        )

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source_lines: list[str],
        module_name: str,
        file_path: str,
        class_name: Optional[str] = None,
    ) -> FunctionInfo:
        """Extract complete metadata from a function/method AST node."""
        # Parameters
        parameters = []
        args = node.args

        # Positional-only args
        for arg in args.posonlyargs:
            parameters.append({
                "name": arg.arg,
                "type": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": None,
                "kind": "positional_only",
            })

        # Regular args
        defaults_offset = len(args.args) - len(args.defaults)
        for i, arg in enumerate(args.args):
            default_idx = i - defaults_offset
            default = ast.unparse(args.defaults[default_idx]) if default_idx >= 0 else None
            parameters.append({
                "name": arg.arg,
                "type": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": default,
                "kind": "positional_or_keyword",
            })

        # *args
        if args.vararg:
            parameters.append({
                "name": f"*{args.vararg.arg}",
                "type": ast.unparse(args.vararg.annotation) if args.vararg.annotation else None,
                "default": None,
                "kind": "var_positional",
            })

        # **kwargs
        if args.kwarg:
            parameters.append({
                "name": f"**{args.kwarg.arg}",
                "type": ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None,
                "default": None,
                "kind": "var_keyword",
            })

        # Return type
        return_type = ast.unparse(node.returns) if node.returns else None

        # Build signature
        params_str = ", ".join(
            p["name"] + (f": {p['type']}" if p["type"] else "") +
            (f" = {p['default']}" if p["default"] else "")
            for p in parameters
        )
        is_async = isinstance(node, ast.AsyncFunctionDef)
        prefix = "async def" if is_async else "def"
        ret = f" -> {return_type}" if return_type else ""
        signature = f"{prefix} {node.name}({params_str}){ret}:"

        # Extract call relationships
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(f"{ast.unparse(child.func.value)}.{child.func.attr}")

        # Source code
        end_line = getattr(node, "end_lineno", node.lineno)
        source_code = "\n".join(source_lines[node.lineno - 1:end_line])

        # Decorators
        decorators = [ast.unparse(d) for d in node.decorator_list]

        return FunctionInfo(
            name=node.name,
            module=module_name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=end_line,
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            existing_docstring=ast.get_docstring(node),
            source_code=source_code,
            decorators=decorators,
            is_async=is_async,
            is_method=class_name is not None,
            class_name=class_name,
            calls=list(set(calls)),
        )

    def _extract_class(
        self,
        node: ast.ClassDef,
        source_lines: list[str],
        module_name: str,
        file_path: str,
    ) -> ClassInfo:
        """Extract complete metadata from a class AST node."""
        methods = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_function(
                    child, source_lines, module_name, file_path, class_name=node.name
                )
                methods.append(method)

        bases = [ast.unparse(b) for b in node.bases]
        decorators = [ast.unparse(d) for d in node.decorator_list]
        end_line = getattr(node, "end_lineno", node.lineno)

        return ClassInfo(
            name=node.name,
            module=module_name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=end_line,
            bases=bases,
            existing_docstring=ast.get_docstring(node),
            methods=methods,
            decorators=decorators,
        )

    def extract_repository(self, repo_path: str) -> list[ModuleInfo]:
        """
        Extract metadata from an entire repository.

        Tested on codebases with 50,000+ lines of code.
        """
        repo = Path(repo_path)
        modules = []
        py_files = list(repo.rglob("*.py"))

        logger.info(f"Extracting AST from {len(py_files)} Python files in {repo_path}")

        for py_file in py_files:
            # Skip common non-source directories
            parts = py_file.parts
            if any(d in parts for d in ["__pycache__", ".venv", "venv", "node_modules", ".git"]):
                continue

            module = self.extract_file(str(py_file))
            if module:
                modules.append(module)

        total_functions = sum(
            len(m.functions) + sum(len(c.methods) for c in m.classes)
            for m in modules
        )
        total_classes = sum(len(m.classes) for m in modules)
        total_lines = sum(m.total_lines for m in modules)

        logger.info(
            f"Extraction complete: {len(modules)} modules, "
            f"{total_functions} functions, {total_classes} classes, "
            f"{total_lines:,} total lines"
        )

        return modules
