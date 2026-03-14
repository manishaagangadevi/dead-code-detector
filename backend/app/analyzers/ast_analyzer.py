import ast
import json

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
        if not self.code or len(self.code.strip()) == 0:
            return {"error": "Empty code provided"}
        if len(self.code) > 100000:
            return {"error": "Code too large. Max 100,000 characters allowed"}
        if self.language == "python":
            return self._analyze_python()
        elif self.language in ["javascript", "typescript"]:
            return self._analyze_javascript()
        return {"error": f"Language '{self.language}' not supported yet"}

    def _analyze_python(self) -> dict:
        try:
            tree = ast.parse(self.code)
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}"}

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

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.called_functions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    self.called_functions.add(node.func.attr)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self.used_variables.add(node.id)

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

    def _analyze_javascript(self) -> dict:
        try:
            import esprima
        except ImportError:
            return {"error": "esprima not installed. Run: pip install esprima"}

        try:
            tree = esprima.parseScript(
                self.code,
                tolerant=True,
                loc=True
            )
        except Exception as e:
            try:
                tree = esprima.parseModule(
                    self.code,
                    tolerant=True,
                    loc=True
                )
            except Exception as e2:
                return {"error": f"JS parse error: {str(e2)}"}

        defined_functions = {}
        called_functions = set()
        defined_variables = {}
        used_variables = set()

        def walk(node):
            if node is None:
                return
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return
            if not hasattr(node, 'type'):
                return

            # Collect function declarations
            if node.type == 'FunctionDeclaration':
                if node.id and node.id.name:
                    name = node.id.name
                    line_start = node.loc.start.line if node.loc else 0
                    line_end = node.loc.end.line if node.loc else 0
                    defined_functions[name] = {
                        "line_start": line_start,
                        "line_end": line_end,
                        "name": name
                    }

            # Collect arrow functions and function expressions
            elif node.type in ['VariableDeclarator']:
                if (node.id and node.id.name and node.init and
                        node.init.type in ['ArrowFunctionExpression', 'FunctionExpression']):
                    name = node.id.name
                    line_start = node.loc.start.line if node.loc else 0
                    line_end = node.loc.end.line if node.loc else 0
                    defined_functions[name] = {
                        "line_start": line_start,
                        "line_end": line_end,
                        "name": name
                    }
                elif node.id and node.id.name:
                    name = node.id.name
                    line = node.loc.start.line if node.loc else 0
                    defined_variables[name] = {
                        "line": line,
                        "name": name
                    }

            # Collect function calls
            elif node.type == 'CallExpression':
                if node.callee:
                    if node.callee.type == 'Identifier':
                        called_functions.add(node.callee.name)
                    elif node.callee.type == 'MemberExpression':
                        if node.callee.property:
                            called_functions.add(node.callee.property.name)

            # Collect identifier usages
            elif node.type == 'Identifier':
                used_variables.add(node.name)

            # Walk children
            for key in node.__dict__:
                child = getattr(node, key)
                if hasattr(child, 'type') or isinstance(child, list):
                    walk(child)

        walk(tree)

        # Find dead functions
        dead_functions = []
        for name, info in defined_functions.items():
            if name not in called_functions:
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
        for name, info in defined_variables.items():
            if name not in used_variables and name not in called_functions:
                dead_variables.append({
                    "type": "dead_variable",
                    "name": name,
                    "line_start": info["line"],
                    "line_end": info["line"],
                    "severity": "medium",
                    "message": f"Variable '{name}' is declared but never used"
                })

        # Find unreachable code (after return statements)
        unreachable = self._find_js_unreachable(tree)

        all_dead = dead_functions + dead_variables + unreachable

        return {
            "language": self.language,
            "total_lines": len(self.code.splitlines()),
            "dead_code_items": all_dead,
            "dead_count": len(all_dead),
            "defined_functions": list(defined_functions.keys()),
            "called_functions": list(called_functions),
            "summary": {
                "dead_functions": len(dead_functions),
                "dead_variables": len(dead_variables),
                "unreachable_blocks": len(unreachable)
            }
        }

    def _find_js_unreachable(self, tree) -> list:
        unreachable = []

        def check_body(body, func_name="anonymous"):
            if not isinstance(body, list):
                return
            for i, stmt in enumerate(body):
                if hasattr(stmt, 'type') and stmt.type == 'ReturnStatement':
                    if i < len(body) - 1:
                        next_stmt = body[i + 1]
                        line_start = next_stmt.loc.start.line if next_stmt.loc else 0
                        line_end = body[-1].loc.end.line if body[-1].loc else 0
                        unreachable.append({
                            "type": "unreachable_code",
                            "name": f"code_after_return_in_{func_name}",
                            "line_start": line_start,
                            "line_end": line_end,
                            "severity": "high",
                            "message": f"Unreachable code after return in '{func_name}'"
                        })
                        break

        def walk(node, func_name="anonymous"):
            if node is None or not hasattr(node, 'type'):
                return
            if node.type == 'FunctionDeclaration':
                name = node.id.name if node.id else "anonymous"
                if hasattr(node, 'body') and hasattr(node.body, 'body'):
                    check_body(node.body.body, name)
            elif node.type in ['ArrowFunctionExpression', 'FunctionExpression']:
                if hasattr(node, 'body') and hasattr(node.body, 'body'):
                    check_body(node.body.body, func_name)
            for key in node.__dict__:
                child = getattr(node, key)
                if hasattr(child, 'type'):
                    walk(child, func_name)
                elif isinstance(child, list):
                    for item in child:
                        if hasattr(item, 'type'):
                            walk(item, func_name)

        walk(tree)
        return unreachable

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