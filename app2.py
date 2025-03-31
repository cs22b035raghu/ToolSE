import os
import shutil
import re
import subprocess
import mimetypes
from flask import Flask, request, render_template_string

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Git Repo Word Frequency</title>
</head>
<body>
    <h2>Enter Git Repository URL</h2>
    <form method="post">
        <input type="text" name="git_url" placeholder="GitHub Repo URL" required>
        <input type="text" name="search_word" placeholder="Word to search" required>
        <button type="submit">Analyze</button>
    </form>
    {% if error %}
        <p style="color: red;"><strong>Error:</strong> {{ error }}</p>
    {% endif %}
    {% if word_count is not none %}
        <h3>Word Count:</h3>
        <p>The word "{{ search_word }}" appears <strong>{{ word_count }}</strong> times (including as part of other words).</p>
    {% endif %}
</body>
</html>
"""

def clone_repo(git_url, repo_dir):
    """Clone the given Git repository into the specified directory."""
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)  # Clean up existing repo
    result = subprocess.run(["git", "clone", git_url, repo_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        return False, result.stderr.decode("utf-8")
    return True, None


def get_word_count(repo_dir, search_word):
    """Count occurrences of search_word in all text files in repo, ignoring README files."""
    word_counter = 0
    search_word = search_word.lower()
    regex_pattern = re.compile(re.escape(search_word), re.IGNORECASE)  # Case-insensitive search

    for root, _, files in os.walk(repo_dir):
        for file in files:
            if file.lower().startswith("readme"):
                continue  # Ignore README files
            
            file_path = os.path.join(root, file)
            
            # Ensure the file is a text file
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith("text"):
                continue  # Skip binary files
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    word_counter += len(regex_pattern.findall(text))  # Count occurrences using regex
            except Exception:
                continue  # Ignore unreadable files
    
    return word_counter


@app.route("/", methods=["GET", "POST"])
def index():
    word_count = None
    search_word = None
    error = None
    repo_dir = "temp_repo"

    if request.method == "POST":
        git_url = request.form["git_url"].strip()
        search_word = request.form["search_word"].strip()

        if not git_url or not search_word:
            error = "Git URL and search word are required."
        else:
            success, error_message = clone_repo(git_url, repo_dir)
            if not success:
                error = f"Failed to clone repository. Error: {error_message}"
            else:
                word_count = get_word_count(repo_dir, search_word)
                shutil.rmtree(repo_dir, ignore_errors=True)  # Cleanup after processing
    
    return render_template_string(TEMPLATE, word_count=word_count, search_word=search_word, error=error)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

