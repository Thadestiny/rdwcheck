from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import io
import re

app = Flask(__name__)

last_results = []

def clean_kenteken(k):
    """Maakt het kenteken echt schoon en filtert ruis weg."""
    if pd.isna(k):
        return None
    # Verwijder alles wat geen letter of cijfer is
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(k)).upper()
    # Een kenteken is in Nederland nooit korter dan 1 teken, 
    # maar we filteren hier op minimaal 2 om 'troep' in de CSV te negeren
    return clean if len(clean) >= 2 else None

def get_rdw_bulk(kentekens):
    # Filter de lijst met de nieuwe clean_kenteken functie
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
                d1 = item.get("datum_eerste_tenaamstelling_in_nederland", "Onbekend")
                d2 = item.get("datum_tenaamstelling", "Onbekend")
                
                results_dict[item['kenteken']] = {
                    "Kenteken": item['kenteken'],
                    "Eerste_Tenaamstelling_NL": f"{d1[6:8]}-{d1[4:6]}-{d1[0:4]}" if len(d1) == 8 else d1,
                    "Laatste_Tenaamstelling": f"{d2[6:8]}-{d2[4:6]}-{d2[0:4]}" if len(d2) == 8 else d2
                }
    except Exception as e:
        print(f"API Fout: {e}")
    
    return [results_dict.get(k, {"Kenteken": k, "Eerste_Tenaamstelling_NL": "Niet gevonden", "Laatste_Tenaamstelling": "Niet gevonden"}) for k in clean_list]

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
                # We lezen het bestand eerst in als ruwe tekst om fouten te voorkomen
                content = file.stream.read().decode("utf-8-sig")
                lines = content.splitlines()
                
                raw_kentekens = []
                for line in lines:
                    # We pakken alleen de tekst vóór de eerste komma of puntkomma
                    # Dit voorkomt de "Expected X fields" foutmeldingen volledig
                    first_part = re.split(r'[;,]', line)[0].strip()
                    if first_part:
                        raw_kentekens.append(first_part)

                if not raw_kentekens:
                    error_message = "Geen data gevonden in het bestand."
                else:
                    # Verwerk in batches
                    for i in range(0, len(raw_kentekens), 100):
                        batch = raw_kentekens[i:i+100]
                        results.extend(get_rdw_bulk(batch))
                    
                    last_results = results
            except Exception as e:
                error_message = f"Fout bij verwerken: {str(e)}"
                
    return render_template('index.html', results=results, error=error_message)

@app.route('/download')
def download():
    global last_results
    if not last_results: return "Geen data", 400
    df_download = pd.DataFrame(last_results)
    proxy = io.StringIO()
    df_download.to_csv(proxy, index=False, sep=';')
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='rdw_export.csv')

if __name__ == '__main__':
    app.run(debug=True)
