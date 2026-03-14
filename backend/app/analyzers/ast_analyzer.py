import ast
import json
from typing import Any

class ASTAnalyzer:
    def __init__(self, code: str, language: str = "python"):
        self.code = code
        self.language = language
        self.defined_functions = {}
        self.called_functions = set()
        self.defined_variables = {}
        self.used_variables = set()
        self.dead_code = []

    def analyze(self) -> dict:
        if self.language == "python":
            return self._analyze_python()
        return {"error": "Language not supported yet"}

    def _analyze_python(self) -> dict:
        try:
            tree = ast.parse(self.code)
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}"}

        # First pass — collect all definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.defined_functions[node.name] = {
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "name": node.name
                }
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.defined_variables[target.id] = {
                            "line": node.lineno,
                            "name": target.id
                        }

        # Second pass — collect all usages
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.called_functions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    self.called_functions.add(node.func.attr)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self.used_variables.add(node.id)

        # Find dead functions
        dead_functions = []
        for name, info in self.defined_functions.items():
            if name not in self.called_functions and name != "main":
                dead_functions.append({
                    "type": "dead_function",
                    "name": name,
                    "line_start": info["line_start"],
                    "line_end": info["line_end"],
                    "severity": "high",
                    "message": f"Function '{name}' is defined but never called"
                })

        # Find dead variables
        dead_variables = []
        for name, info in self.defined_variables.items():
            if name not in self.used_variables:
                dead_variables.append({
                    "type": "dead_variable",
                    "name": name,
                    "line_start": info["line"],
                    "line_end": info["line"],
                    "severity": "medium",
                    "message": f"Variable '{name}' is assigned but never used"
                })

        # Find unreachable code (after return statements)
        unreachable = self._find_unreachable(tree)

        self.dead_code = dead_functions + dead_variables + unreachable

        return {
            "language": self.language,
            "total_lines": len(self.code.splitlines()),
            "dead_code_items": self.dead_code,
            "dead_count": len(self.dead_code),
            "defined_functions": list(self.defined_functions.keys()),
            "called_functions": list(self.called_functions),
            "summary": {
                "dead_functions": len(dead_functions),
                "dead_variables": len(dead_variables),
                "unreachable_blocks": len(unreachable)
            }
        }

    def _find_unreachable(self, tree) -> list:
        unreachable = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stmts = node.body
                for i, stmt in enumerate(stmts):
                    if isinstance(stmt, ast.Return) and i < len(stmts) - 1:
                        next_stmt = stmts[i + 1]
                        unreachable.append({
                            "type": "unreachable_code",
                            "name": f"code_after_return_in_{node.name}",
                            "line_start": next_stmt.lineno,
                            "line_end": stmts[-1].end_lineno,
                            "severity": "high",
                            "message": f"Unreachable code after return in '{node.name}'"
                        })
        return unreachable