from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import io
import re

app = Flask(__name__)

last_results = []

def format_rdw_date(date_str):
    """Zet YYYYMMDD om naar DD-MM-YYYY, anders behoud de originele tekst."""
    if date_str and isinstance(date_str, str) and len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[6:8]}-{date_str[4:6]}-{date_str[0:4]}"
    return date_str

def clean_kenteken(k):
    """Maakt het kenteken schoon en filtert ruis weg."""
    if pd.isna(k):
        return None
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(k)).upper()
    return clean if len(clean) >= 2 else None

def get_rdw_bulk(kentekens):
    clean_list = [clean_kenteken(k) for k in kentekens if clean_kenteken(k) is not None]
    if not clean_list:
        return []

    formatted_list = "','".join(clean_list)
    # De API-query vraagt nu om merk en handelsbenaming
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?$where=kenteken in('{formatted_list}')"
    
    results_dict = {}
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                d1 = item.get("datum_eerste_tenaamstelling_in_nederland", "Onbekend")
                d2 = item.get("datum_tenaamstelling", "Onbekend")
                merk = item.get("merk", "Onbekend")
                model = item.get("handelsbenaming", "Onbekend")
                
                results_dict[item['kenteken']] = {
                    "Kenteken": item['kenteken'],
                    "Merk": merk,
                    "Model": model,
                    "Eerste_Tenaamstelling_NL": format_rdw_date(d1),
                    "Laatste_Tenaamstelling": format_rdw_date(d2)
                }
    except Exception as e:
        print(f"API Fout: {e}")
    
    # Zorg dat we voor elk gevraagd kenteken een rij teruggeven
    final_results = []
    for k in clean_list:
        final_results.append(results_dict.get(k, {
            "Kenteken": k, 
            "Merk": "Niet gevonden",
            "Model": "Niet gevonden",
            "Eerste_Tenaamstelling_NL": "Niet gevonden", 
            "Laatste_Tenaamstelling": "Niet gevonden"
        }))
    return final_results

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
                
                raw_kentekens = []
                for line in lines:
                    if not line.strip(): continue
                    parts = re.split(r'[;,]', line)
                    first_part = parts[0].strip().replace('"', '')
                    if first_part:
