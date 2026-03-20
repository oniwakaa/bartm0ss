from pathlib import Path
from typing import Optional
from . import ToolResult


def run(filepath: str) -> ToolResult:
    file_path = Path(filepath)
    
    if not file_path.exists():
        return ToolResult(output="", success=False, error=f"File not found: {filepath}")
    
    try:
        import tree_sitter_python as tspython
        from tree_sitter import Language, Parser
        
        PY_LANGUAGE = Language(tspython.language())
        parser = Parser(PY_LANGUAGE)
        
        source = file_path.read_bytes()
        tree = parser.parse(source)
        
        symbols = []
        
        def extract_symbols(node, depth=0):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(f"{'  ' * depth}def {name_node.text.decode()}")
            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    symbols.append(f"{'  ' * depth}class {name_node.text.decode()}")
            for child in node.children:
                extract_symbols(child, depth + (1 if node.type in ("class_definition", "module") else 0))
        
        extract_symbols(tree.root_node)
        return ToolResult(output="\n".join(symbols) if symbols else "No symbols found", success=True)
    except ImportError:
        return ToolResult(output="", success=False, error="tree-sitter not installed. Run: pip install tree-sitter-python")
    except Exception as e:
        return ToolResult(output="", success=False, error=str(e))