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