# This part is entirely done by me
##  Code Summarizer - Overview

###  Features
- Extracts **class names**, **function names**, and **imported modules**.
- Detects **function calls** to identify operations used.
- Generates a **clear, natural-language summary** of the code.

###  Methodology
- Utilizes Python’s `ast` module to parse code into an **Abstract Syntax Tree**.
- Traverses the AST using the **NodeVisitor** pattern to identify key components.

### Techniques
- **Static code analysis** (no execution of the input script).
- **Natural Language Generation** (basic summary construction).
- Organized using **clean OOP structure** for modularity and reusability.

## Why Our Solution is Better

Most existing tools provide **syntax-level analysis** or **basic summaries** based solely on libraries like `ast` or linters. However, they fall short in:
- **Mapping requirements to code.**
- **Understanding intent behind the implementation.**
- **Identifying unimplemented or extra features.**

Our phased solution improves this by:
- **Phase 1:** Lightweight AST-based summarization for quick structural understanding.
- **Phase 2 (Upcoming):** Using **LLMs** and **NLP** to extract semantic meaning, match it against natural-language requirements, and detect mismatches or gaps.

Limitations for phase-1:
- Cannot handle semantic mapping between requirements and code.
- Does not support dynamic behaviors or complex logic detection.

## Plan for Release-2 (Phase 2)
### Technologies to be Used:
- **LLMs** (e.g., GPT models via OpenAI API or open-source alternatives like LLaMA, Mistral, etc.)
- **NLP techniques** for semantic similarity, keyword extraction, and intent classification.
- Integration with requirement files (Markdown, plain text, or user input).


