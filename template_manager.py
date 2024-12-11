
import os
from PyQt5.QtWidgets import QMessageBox
from utils import get_resource_path

def list_templates(directory):
    directory = get_resource_path(directory)
    if not os.path.exists(directory):
        return []
    files = os.listdir(directory)
    return [f for f in files if f.lower().endswith(".md")]

def load_template(file_path):
    file_path = get_resource_path(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        QMessageBox.warning(None, "Error", f"Error loading template: {str(e)}")
        return ""

def save_template(file_path, content):
    file_path = get_resource_path(file_path)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        QMessageBox.warning(None, "Error", f"Error saving template: {str(e)}")

def delete_template(file_path):
    file_path = get_resource_path(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        QMessageBox.warning(None, "Error", f"Template not found: {file_path}")
