from flask import Flask, request, render_template, send_file
import os
import re
import git
import shutil
import requests
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
model = SentenceTransformer("all-MiniLM-L6-v2")

HF_API_KEY = os.environ.get("HF_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


def clone_or_update_repo(repo_url, local_path):
    if os.path.exists(local_path):
        try:
            repo = git.Repo(local_path)
            current_url = repo.remotes.origin.url
            if current_url != repo_url:
                shutil.rmtree(local_path)
                git.Repo.clone_from(repo_url, local_path)
            else:
                try:
                    repo.git.reset('--hard')
                    repo.remotes.origin.pull()
                except git.exc.GitCommandError:
                    shutil.rmtree(local_path)
                    git.Repo.clone_from(repo_url, local_path)
        except git.exc.InvalidGitRepositoryError:
            shutil.rmtree(local_path)
            git.Repo.clone_from(repo_url, local_path)
    else:
        git.Repo.clone_from(repo_url, local_path)


def find_module_files(local_path):
    module_files = []
    for root, _, files in os.walk(local_path):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.cpp', '.ts')):
                module_files.append(os.path.join(root, file))
    return module_files


def extract_functions_and_comments(file_path, module_name):
    functions, comments = [], []
    module_name_lower = module_name.lower()

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    inside_multiline_comment = False
    multiline_comment = ""

    for line in lines:
        line = line.strip()
        match = re.search(r'\b(def|function|void|int|str|public|private|class)\s+(\w+)\s*\(', line)
        if match:
            function_name = match.group(2)
            if module_name_lower in function_name.lower():
                functions.append(line)

        if line.startswith(("#", "//", "/*", "*")) and module_name_lower in line.lower():
            comments.append(line)

        if '"""' in line or "'''" in line:
            if inside_multiline_comment:
                multiline_comment += " " + line
                if module_name_lower in multiline_comment.lower():
                    comments.append(multiline_comment)
                inside_multiline_comment = False
            else:
                inside_multiline_comment = True
                multiline_comment = line
        elif inside_multiline_comment:
            multiline_comment += " " + line
            if module_name_lower in multiline_comment.lower():
                comments.append(multiline_comment)

    return functions, comments if functions or comments else (None, None)


def generate_report(result_data, module_name):
    report_path = "report.txt"
    report_content = f"Module Analysis Report for '{module_name}'\n"
    report_content += "=" * 50 + "\n\n"

    if not result_data:
        report_content += "No relevant functions or comments found.\n"
    else:
        for item in result_data:
            report_content += f"\U0001F4C2 File: {item['file']}\n\n"

            if item["functions"]:
                report_content += "\U0001F539 Functions Found:\n"
                for func in item["functions"]:
                    report_content += f"   - {func}\n"
                report_content += "\n"

            if item["comments"]:
                report_content += "\U0001F4AC Comments Found:\n"
                for comment in item["comments"]:
                    report_content += f"   - {comment}\n"
                report_content += "\n"

            report_content += "=" * 50 + "\n\n"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_path, report_content

def extract_subheadings_from_pdf(pdf_text):
    lines = pdf_text.split('\n')
    subheadings = set()
    for line in lines:
        line = line.strip()
        if line.endswith(':') and len(line.split()) < 15:
            subheadings.add(line.rstrip(':').strip())
    return list(subheadings)


def check_subheadings_implementation(subheadings, report_content):
    implemented = []
    not_implemented = []

    content_lower = report_content.lower()
    for sub in subheadings:
        if sub.lower() in content_lower:
            implemented.append(sub)
        else:
            not_implemented.append(sub)

    return implemented, not_implemented


def generate_hf_summary(prompt_text):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt_text[:1024]}
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

    response = requests.post(url, headers=headers, json=payload)
    try:
        data = response.json()
        if isinstance(data, list):
            return data[0].get("summary_text", "")
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        return str(data)
    except Exception as e:
        return f"Error generating summary: {e}"


def generate_openrouter_suggestions(summary_text):
    prompt = f"""Suggest improvements:\n\n{summary_text}"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are an expert software reviewer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    try:
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error from OpenRouter: {e}\nResponse: {response.text}"


def generate_openrouter_suggestions1(summary_text):
    prompt = f"""Answer the question or respond if it's a greeting:\n\n{summary_text}"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are an expert software reviewer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    try:
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error from OpenRouter: {e}\nResponse: {response.text}"


def adjusted_similarity_score(module_name, pdf_text, title_text, report_summary):
    def clean_text(text):
        return re.sub(r'\s+', ' ', text.strip())

    pdf_text = clean_text(pdf_text)
    title_text = clean_text(title_text)
    report_summary = clean_text(report_summary)

    if module_name.lower() not in pdf_text.lower() and module_name.lower() not in title_text.lower():
        return 0.09

    prompt = f"""
    Compare the following two texts for semantic similarity.
    Return only a float score between 0 and 1 (no explanation).

    Report Summary:
    {generate_hf_summary(report_summary)}

    PDF Content:
    {pdf_text}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a semantic comparison expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        score = float(re.findall(r"[\d.]+", content)[0])
        return max(0, min(1, score)) if score != 0 else 0.00
    except Exception as e:
        return 0.00


@app.route("/", methods=["GET", "POST"])
def index():
    report_content = None
    ai_summary = None
    ai_suggestions = None
    similarity_score = None
    implemented = []
    not_implemented = []

    if request.method == "POST":
        repo_url = request.form["repo_url"]
        module_name = request.form["module_name"]
        pdf_file = request.files.get("pdf_file")

        local_repo_path = "temp_repo"
        clone_or_update_repo(repo_url, local_repo_path)
        module_files = find_module_files(local_repo_path)

        result_data = []
        for file in module_files:
            functions, comments = extract_functions_and_comments(file, module_name)
            if functions or comments:
                result_data.append({
                    "file": file,
                    "functions": functions,
                    "comments": comments
                })

        report_path, report_content = generate_report(result_data, module_name)
        ai_summary = generate_hf_summary(report_content)
        ai_suggestions = generate_openrouter_suggestions(ai_summary)

        if pdf_file:
            reader = PdfReader(pdf_file)
            pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            title_text = reader.pages[0].extract_text() if reader.pages else ""
            similarity_score = adjusted_similarity_score(module_name, pdf_text, title_text, report_content)

            subheadings = extract_subheadings_from_pdf(pdf_text)
            implemented, not_implemented = check_subheadings_implementation(subheadings, report_content)

    return render_template("index.html",
                           report_content=report_content,
                           ai_summary=ai_summary,
                           ai_suggestions=ai_suggestions,
                           similarity_score=similarity_score,
                           implemented=implemented,
                           not_implemented=not_implemented)


@app.route("/download_report", methods=["GET"])
def download_report():
    return send_file("report.txt", as_attachment=True)


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("user_message", "")
    ai_response = generate_openrouter_suggestions1(user_message)
    return {"response": ai_response}


@app.route("/generate_issues", methods=["POST"])
def generate_issues():
    data = request.json
    repo_url = data.get("repo_url", "")
    if not repo_url:
        return {"issues": "No repository URL provided."}

    local_repo_path = "temp_repo"
    clone_or_update_repo(repo_url, local_repo_path)

    module_files = find_module_files(local_repo_path)
    all_code = ""

    for file_path in module_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                all_code += f"\n\n# File: " + file_path + "\n" + f.read()
        except Exception as e:
            all_code += f"\n\n# File: {file_path}\n# Error reading file: {e}\n"

    prompt = f"""
Analyze the following codebase and point out potential issues, bugs, security vulnerabilities, or bad practices.
Respond in a clear, concise bullet-point format.

{all_code[:12000]}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a software auditor and code reviewer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        issues = result['choices'][0]['message']['content'].strip()
        return {"issues": issues}
    except Exception as e:
        return {"issues": f"Error generating issues: {e}"}


if __name__ == "__main__":
    app.run(debug=True)
