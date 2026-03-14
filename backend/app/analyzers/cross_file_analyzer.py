import ast
import os
from typing import Dict, List, Set

class CrossFileAnalyzer:
    def __init__(self):
        self.files: Dict[str, str] = {}
        self.global_defined_functions: Dict[str, Dict] = {}
        self.global_defined_variables: Dict[str, Dict] = {}
        self.global_called_functions: Set[str] = set()
        self.global_used_variables: Set[str] = set()
        self.imports_map: Dict[str, List[str]] = {}
        self.dead_code: List[Dict] = []

    def add_file(self, filename: str, code: str):
        self.files[filename] = code

    def analyze_all(self) -> dict:
        # First pass — collect ALL definitions across all files
        for filename, code in self.files.items():
            self._collect_definitions(filename, code)

        # Second pass — collect ALL usages across all files
        for filename, code in self.files.items():
            self._collect_usages(filename, code)

        # Third pass — find dead code
        self._find_dead_code()

        # Build cross-file call graph
        graph = self._build_cross_file_graph()

        return {
            "success": True,
            "files_analyzed": list(self.files.keys()),
            "total_files": len(self.files),
            "dead_code_items": self.dead_code,
            "dead_count": len(self.dead_code),
            "global_functions": list(self.global_defined_functions.keys()),
            "call_graph": graph,
            "summary": {
                "dead_functions": sum(1 for i in self.dead_code if i["type"] == "dead_function"),
                "dead_variables": sum(1 for i in self.dead_code if i["type"] == "dead_variable"),
                "unreachable_blocks": sum(1 for i in self.dead_code if i["type"] == "unreachable_code"),
                "files_analyzed": len(self.files)
            }
        }

    def _collect_definitions(self, filename: str, code: str):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                key = f"{filename}::{node.name}"
                self.global_defined_functions[key] = {
                    "name": node.name,
                    "file": filename,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "args": [arg.arg for arg in node.args.args]
                }
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        key = f"{filename}::{target.id}"
                        self.global_defined_variables[key] = {
                            "name": target.id,
                            "file": filename,
                            "line": node.lineno
                        }

        # Collect imports
        self.imports_map[filename] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    self.imports_map[filename].append(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports_map[filename].append(alias.asname or alias.name)

    def _collect_usages(self, filename: str, code: str):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.global_called_functions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    self.global_called_functions.add(node.func.attr)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self.global_used_variables.add(node.id)

    def _find_dead_code(self):
        self.dead_code = []

        # Check each defined function against ALL usages across ALL files
        for key, info in self.global_defined_functions.items():
            func_name = info["name"]
            if (func_name not in self.global_called_functions
                    and func_name != "main"
                    and not func_name.startswith("__")):

                # Also check if it's imported anywhere
                is_imported = any(
                    func_name in imports
                    for f, imports in self.imports_map.items()
                    if f != info["file"]
                )

                if not is_imported:
                    self.dead_code.append({
                        "type": "dead_function",
                        "name": func_name,
                        "file": info["file"],
                        "line_start": info["line_start"],
                        "line_end": info["line_end"],
                        "severity": "high",
                        "message": f"Function '{func_name}' in '{info['file']}' is never called across any file"
                    })

        # Check dead variables
        for key, info in self.global_defined_variables.items():
            var_name = info["name"]
            if var_name not in self.global_used_variables:
                self.dead_code.append({
                    "type": "dead_variable",
                    "name": var_name,
                    "file": info["file"],
                    "line_start": info["line"],
                    "line_end": info["line"],
                    "severity": "medium",
                    "message": f"Variable '{var_name}' in '{info['file']}' is never used across any file"
                })

    def _build_cross_file_graph(self) -> dict:
        nodes = []
        edges = []
        node_map = {}

        # Add file nodes
        for filename in self.files.keys():
            short_name = os.path.basename(filename)
            nid = f"file_{short_name}"
            node_map[filename] = nid
            nodes.append({
                "id": nid,
                "label": short_name,
                "type": "file",
                "is_dead": False,
                "color": "#7c3aed"
            })

        # Add function nodes
        for key, info in self.global_defined_functions.items():
            func_name = info["name"]
            is_dead = any(
                d["name"] == func_name and d["file"] == info["file"]
                for d in self.dead_code
                if d["type"] == "dead_function"
            )
            nid = f"func_{key}"
            node_map[key] = nid
            nodes.append({
                "id": nid,
                "label": f"{func_name}()",
                "type": "function",
                "file": info["file"],
                "is_dead": is_dead,
                "color": "#E53935" if is_dead else "#1E88E5"
            })

            # Edge from file to function
            file_nid = node_map.get(info["file"])
            if file_nid:
                edges.append({
                    "source": file_nid,
                    "target": nid,
                    "label": "defines"
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_functions": len(self.global_defined_functions),
                "dead_functions": sum(1 for n in nodes if n.get("is_dead")),
                "total_files": len(self.files)
            }
        }