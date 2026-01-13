from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import io
import re

app = Flask(__name__)

# Tijdelijke opslag voor de laatste resultaten (nodig voor de download-functie)
last_results = []

def format_rdw_date(date_str):
    """Zet YYYYMMDD om naar DD-MM-YYYY, tenzij de tekst 'Onbekend' is."""
    if date_str and isinstance(date_str, str) and len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[6:8]}-{date_str[4:6]}-{date_str[0:4]}"
    return date_str

def clean_kenteken(k):
    """Maakt het kenteken schoon (geen streepjes/spaties) en zet om naar hoofdletters."""
    if pd.isna(k):
        return None
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(k)).upper()
    return clean if len(clean) >= 2 else None

def get_rdw_bulk(kentekens):
    """Haalt uitgebreide voertuiggegevens op bij de RDW."""
    clean_list = [clean_kenteken(k) for k in kentekens if clean_kenteken(k) is not None]
    if not clean_list:
        return []

    formatted_list = "','".join(clean_list)
    # We vragen kenteken, merk, handelsbenaming en tenaamstellingsdata op
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
                    "Kenteken":
