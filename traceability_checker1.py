import ast

class CodeSummarizer(ast.NodeVisitor):
    """Analyzes a Python script and generates a natural-language summary."""

    def __init__(self):
        self.classes = []
        self.functions = []
        self.operations = set()
        self.imports = []

    def visit_Import(self, node):
        """Extract imported modules."""
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node):
        """Extract imported modules from 'from ... import ...'."""
        if node.module:
            self.imports.append(node.module)

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

    def generate_summary(self):
        """Generates a human-readable paragraph summarizing the code."""
        summary = "This Python script "

        if self.imports:
            summary += f"imports the following modules: {', '.join(self.imports)}. "

        if self.classes:
            summary += f"It defines {len(self.classes)} class{'es' if len(self.classes) > 1 else ''}: {', '.join(self.classes)}. "

        if self.functions:
            summary += f"It also includes {len(self.functions)} function{'s' if len(self.functions) > 1 else ''}: {', '.join(self.functions)}. "

        if self.operations:
            summary += f"The script performs operations such as {', '.join(self.operations)}. "

        if not (self.classes or self.functions or self.operations):
            summary += "does not contain any functions, classes, or notable operations."

        return summary.strip()

def analyze_code(file_path):
    """Reads a Python file and generates a natural-language summary."""
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    summarizer = CodeSummarizer()
    summarizer.visit(tree)

    return summarizer.generate_summary()

# Example usage
if __name__ == "__main__":
    file_path = "test1.py"  
    print(analyze_code(file_path))
