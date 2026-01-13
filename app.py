from flask import Flask, render_template, request
import pandas as pd
import requests
import io

app = Flask(__name__)

def get_rdw_bulk(kentekens):
    """Haalt gegevens op voor een lijst van kentekens in één API-aanroep."""
    # Kentekens opschonen: streepjes weg, spaties weg, hoofdletters
    clean_list = [str(k).replace('-', '').replace(' ', '').upper() for k in kentekens if pd.notna(k)]
    
    if not clean_list:
        return []

    # De RDW API Query: we vragen meerdere kentekens tegelijk op met een 'where in' filter
    formatted_list = "','".join(clean_list)
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?$where=kenteken in('{formatted_list}')"
    
    results_dict = {}
    try:
        # We geven de API 20 seconden de tijd (ruim zat voor bulk)
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                # API datums zijn vaak YYYYMMDD, we maken ze leesbaar: DD-MM-YYYY
                d1 = item.get("datum_eerste_tenaamstelling_in_nederland", "Onbekend")
                d2 = item.get("datum_tenaamstelling", "Onbekend")
                
                results_dict[item['kenteken']] = {
                    "kenteken": item['kenteken'],
                    "eerste_nl": f"{d1[6:8]}-{d1[4:6]}-{d1[0:4]}" if len(d1) == 8 else d1,
                    "laatste": f"{d2[6:8]}-{d2[4:6]}-{d2[0:4]}" if len(d2) == 8 else d2
                }
    except Exception as e:
        print(f"API Fout: {e}")
    
    # We zorgen dat we voor elk input-kenteken een resultaat teruggeven
    final_results = []
    for k in clean_list:
        final_results.append(results_dict.get(k, {"kenteken": k, "eerste_nl": "Niet gevonden", "laatste": "Niet gevonden"}))
    return final_results

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            try:
                # Lees het CSV bestand
                stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
                df = pd.read_csv(stream)
                
                # Pak de eerste kolom (ongeacht de naam)
                kentekens = df.iloc[:, 0].tolist()
                
                # Verwerk in blokken van 100 kentekens per keer
                for i in range(0, len(kentekens), 100):
                    batch = kentekens[i:i+100]
                    results.extend(get_rdw_bulk(batch))
            except Exception as e:
                print(f"Bestand verwerkingsfout: {e}")
                
    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
