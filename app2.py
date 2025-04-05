from flask import Flask, request, render_template, send_file
import os
import re
import git
import requests
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")

def clone_or_update_repo(repo_url, local_path):
    if os.path.exists(local_path):
        repo = git.Repo(local_path)
        repo.remotes.origin.pull()
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

    if functions or comments:
        return functions, comments
    return None, None

def generate_report(result_data, module_name):
    report_path = "report.txt"
    report_content = f"Module Analysis Report for '{module_name}'\n"
    report_content += "="*50 + "\n\n"

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

            report_content += "="*50 + "\n\n"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_path, report_content

def generate_ai_response(prompt_text, api_key, model="facebook/bart-large-cnn"):
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": prompt_text[:1024]}

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            if isinstance(result, list):
                return result[0].get("summary_text", "No summary returned.")
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                return str(result)
        except Exception as e:
            return f"Error parsing response: {e}"
    else:
        return f"AI response failed: {response.status_code} - {response.text}"

def compute_semantic_similarity(text1, text2, api_key=None):
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    return float(util.pytorch_cos_sim(emb1, emb2)[0][0])

def generate_diff_suggestions(code_summary, pdf_text, api_key):
    prompt = f"""
Compare the following module report from code with the intended description from a PDF. Identify any missing features, extra functionality, or inconsistencies. Then provide suggestions to improve the code to better match the description.

--- CODE SUMMARY ---
{code_summary}

--- PDF DESCRIPTION ---
{pdf_text}
"""
    return generate_ai_response(prompt, api_key, model="google-t5/t5-small")

@app.route("/", methods=["GET", "POST"])
def index():
    report_content = None
    ai_summary = None
    ai_suggestions = None
    similarity_score = None
    diff_suggestions = None

    if request.method == "POST":
        repo_url = request.form["repo_url"]
        module_name = request.form["module_name"]
        api_key = request.form["api_key"]
        pdf_file = request.files.get("pdf_file")

        local_repo_path = "temp_repo"
        clone_or_update_repo(repo_url, local_repo_path)
        module_files = find_module_files(local_repo_path)

        result_data = []
        seen_files = set()

        for file in module_files:
            if file in seen_files:
                continue
            seen_files.add(file)

            functions, comments = extract_functions_and_comments(file, module_name)
            if functions or comments:
                result_data.append({
                    "file": file,
                    "functions": functions,
                    "comments": comments
                })

        report_path, report_content = generate_report(result_data, module_name)

        ai_summary = generate_ai_response(report_content, api_key, "facebook/bart-large-cnn")

        improvement_prompt = f"Suggest improvements for the following code and comments:\n\n{report_content}"
        ai_suggestions = generate_ai_response(improvement_prompt, api_key, "google-t5/t5-small")

        if pdf_file:
            reader = PdfReader(pdf_file)
            pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            similarity_score = compute_semantic_similarity(report_content, pdf_text)
            if similarity_score < 0.5:
                diff_suggestions = generate_diff_suggestions(report_content, pdf_text, api_key)

    return render_template("index.html", 
        report_content=report_content,
        ai_summary=ai_summary,
        ai_suggestions=ai_suggestions,
        similarity_score=similarity_score,
        diff_suggestions=diff_suggestions)

@app.route("/download_report", methods=["GET"])
def download_report():
    return send_file("report.txt", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
