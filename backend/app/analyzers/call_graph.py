class CallGraphBuilder:
    def __init__(self, code: str, language: str = "python"):
        self.code = code
        self.language = language

    def build(self) -> dict:
        if self.language == "python":
            return self._build_python()
        return {"nodes": [], "edges": []}

    def _build_python(self) -> dict:
        import ast

        try:
            tree = ast.parse(self.code)
        except SyntaxError:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []
        function_calls = {}

        # Collect all function definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_calls[node.name] = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            function_calls[node.name].append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            function_calls[node.name].append(child.func.attr)

        # Collect all called functions at module level
        module_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and not self._is_inside_function(node, tree):
                if isinstance(node.func, ast.Name):
                    module_calls.append(node.func.id)

        # Build nodes
        all_functions = set(function_calls.keys())
        all_called = set()
        for calls in function_calls.values():
            all_called.update(calls)
        all_called.update(module_calls)

        node_id = 0
        node_map = {}

        # Add module entry node
        nodes.append({
            "id": "module",
            "label": "__main__",
            "type": "module",
            "is_dead": False,
            "color": "#4CAF50"
        })
        node_map["__main__"] = "module"

        for func_name in all_functions:
            is_dead = func_name not in all_called and func_name != "main"
            node_id += 1
            nid = f"node_{node_id}"
            node_map[func_name] = nid
            nodes.append({
                "id": nid,
                "label": func_name,
                "type": "function",
                "is_dead": is_dead,
                "color": "#E53935" if is_dead else "#1E88E5"
            })

        # Build edges
        for func_name, calls in function_calls.items():
            if func_name in node_map:
                for called in calls:
                    if called in node_map:
                        edges.append({
                            "source": node_map[func_name],
                            "target": node_map[called],
                            "label": "calls"
                        })

        # Connect module to called functions
        for called in module_calls:
            if called in node_map:
                edges.append({
                    "source": "module",
                    "target": node_map[called],
                    "label": "calls"
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_functions": len(all_functions),
                "dead_functions": sum(1 for n in nodes if n.get("is_dead")),
                "total_edges": len(edges)
            }
        }

    def _is_inside_function(self, target_node, tree) -> bool:
        import ast
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if child is target_node:
                        return True
        return False