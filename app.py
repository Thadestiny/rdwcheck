from flask import Flask, render_template, request
import pandas as pd
import requests
import io

app = Flask(__name__)

def get_rdw_info(kenteken):
    # Schoon het kenteken op (verwijder spaties en streepjes)
    clean_k = str(kenteken).replace('-', '').replace(' ', '').upper()
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={clean_k}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            return {
                "kenteken": clean_k,
                "eerste_nl": data.get("datum_eerste_tenaamstelling_in_nederland", "Onbekend"),
                "laatste": data.get("datum_tenaamstelling", "Onbekend")
            }
    except Exception as e:
        print(f"Fout bij {kenteken}: {e}")
    
    return {"kenteken": kenteken, "eerste_nl": "Niet gevonden", "laatste": "Niet gevonden"}

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Geen bestand geüpload", 400
        
        file = request.files['file']
        if file.filename == '':
            return "Geen bestand geselecteerd", 400

        if file:
            # We lezen de CSV direct in het geheugen
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            df = pd.read_csv(stream)
            
            # Pak de eerste kolom voor de kentekens
            kentekens = df.iloc[:, 0].tolist()
            
            for k in kentekens:
                if pd.notna(k):
                    info = get_rdw_info(k)
                    results.append(info)
                
    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
