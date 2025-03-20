import ast

class CodeSummarizer(ast.NodeVisitor):
    """Analyzes a Python script and summarizes its functionalities."""

    def __init__(self):
        self.classes = []
        self.functions = []
        self.operations = set()

    def visit_ClassDef(self, node):
        """Extract class names."""
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Extract function names."""
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Detect function calls to infer functionalities."""
        if isinstance(node.func, ast.Name):
            self.operations.add(node.func.id)
        self.generic_visit(node)

    def summarize(self):
        """Generate a summary of the code's functionalities."""
        summary = "Code Summary:\n"
        if self.classes:
            summary += f"- Classes: {', '.join(self.classes)}\n"
        if self.functions:
            summary += f"- Functions: {', '.join(self.functions)}\n"
        if self.operations:
            summary += f"- Uses operations: {', '.join(self.operations)}\n"
        return summary

def analyze_code(file_path):
    """Reads a Python file and generates a summary."""
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    summarizer = CodeSummarizer()
    summarizer.visit(tree)
    
    return summarizer.summarize()

# Example usage
if __name__ == "__main__":
    file_path = "test1.py"  
    print(analyze_code(file_path))
