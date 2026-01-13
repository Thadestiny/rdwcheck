from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import io
import re

app = Flask(__name__)

# Tijdelijke opslag voor de resultaten
last_results = []

def format_rdw_date(date_str):
    if date_str and isinstance(date_str, str) and len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[6:8]}-{date_str[4:6]}-{date_str[0:4]}"
    return date_str

def clean_kenteken(k):
    if pd.isna(k):
        return None
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(k)).upper()
    return clean if len(clean) >= 2 else None

def get_rdw_bulk(kentekens):
    clean_list = [clean_kenteken(k) for k in kentekens if clean_kenteken(k) is not None]
    if not clean_list:
        return []

    formatted_list = "','".join(clean_list)
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?$where=kenteken in('{formatted_list}')"
    
    results_dict = {}
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                results_dict[item['kenteken']] = {
                    "Kenteken": item['kenteken'],
                    "Merk": item.get("merk", "Onbekend"),
                    "Model": item.get("handelsbenaming", "Onbekend"),
                    "Eerste_Tenaamstelling_NL": format_rdw_date(item.get("datum_eerste_tenaamstelling_in_nederland", "Onbekend")),
                    "Laatste_Tenaamstelling": format_rdw_date(item.get("datum_tenaamstelling", "Onbekend"))
                }
    except Exception as e:
        print(f"API Fout: {e}")
    
    return [results_dict.get(k, {"Kenteken": k, "Merk": "Niet gevonden", "Model": "Niet gevonden", "Eerste_Tenaamstelling_NL": "Niet gevonden", "Laatste_Tenaamstelling": "Niet gevonden"}) for k in clean_list]

@app.route('/', methods=['GET', 'POST'])
def index():
    global last_results
    results = []
    error_message = None

    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            error_message = "Geen bestand geselecteerd."
        else:
            try:
                content = file.stream.read().decode("utf-8-sig")
                lines = content.splitlines()
                raw_kentekens = [re.split(r'[;,]', l)[0].strip().replace('"', '') for l in lines if l.strip()]
