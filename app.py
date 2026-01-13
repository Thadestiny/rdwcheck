import requests
import io
import csv
import ast
import os
from flask import Flask, request, render_template_string, Response

app = Flask(__name__)

# We halen het token veilig op uit de systeeminstellingen
RDW_APP_TOKEN = os.environ.get('RDW_TOKEN', '')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>RDW Bulk Check PRO</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; max-width: 950px; margin: 40px auto; padding: 20px; background-color: #f4f7f6; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h2 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 0; }
        .form-group { background: #ebf2f7; padding: 20px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #d6eaf8; }
        button { padding: 12px 25px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #2980b9; }
        .btn-download { background: #27ae60; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; border: none; font-weight: bold; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #34495e; color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #fafafa; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚗 RDW Bulk Voertuig Check</h2>
        <div class="form-group">
            <form method="POST" enctype="multipart/form-data">
                <p><strong>Upload een kentekenlijst (.txt of .csv):</strong></p>
                <input type="file" name="file" accept=".txt,.csv" required>
                <button type="submit">Verwerken met App Token</button>
            </form>
        </div>

        {% if resultaten %}
        <div style="display: flex
