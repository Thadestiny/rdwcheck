from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import io

app = Flask(__name__)

# Opslag voor de laatste resultaten (voor download-functie)
last_results = []

def get_rdw_bulk(kentekens):
    """Haalt gegevens op voor een lijst van kentekens in één API-aanroep."""
    clean_list = [str(k).replace('-', '').replace(' ', '').upper() for k in kentekens if pd.notna(k)]
    if not clean_list:
        return []

    # RDW API Query met 'where in' filter voor snelheid
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
                
                # Formatteer datums van YYYYMMDD naar DD-MM-YYYY
                results_dict[item['kenteken']] = {
                    "Kenteken": item['kenteken'],
                    "Eerste_Tenaamstelling_NL": f"{d1[6:8]}-{d1[4:6]}-{d1[0:4]}" if len(d1) == 8 else d1,
                    "Laatste_Tenaamstelling": f"{d2[6:8]}-{d2[4:6]}-{d2[0:4]}" if len(d2) == 8 else d2
                }
    except Exception as e:
        print(f"API Fout: {e}")
    
    final_results = []
    for k in clean_list:
        final_results.append(results_dict.get(k, {
            "Kenteken": k, 
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
        if not file or file.filename == '':
            error_message = "Geen bestand geselecteerd."
        else:
            try:
                # Lees bestand met utf-8-sig om Excel-problemen te voorkomen
                content = file.stream.read().decode("utf-8-sig")
                stream = io.StringIO(content)
                
                # Automatische detectie van scheidingsteken (komma of puntkomma)
                df = pd.read_csv(stream, sep=None, engine='python')

                if df.empty:
                    error_message = "Het CSV-bestand lijkt leeg te zijn."
                else:
                    kentekens = df.iloc[:, 0].dropna().tolist()
                    if not kentekens:
                        error_message = "Geen kentekens gevonden in de eerste kolom."
                    else:
                        # Verwerk in batches van 100
                        for i in range(0, len(kentekens), 100):
                            batch = kentekens[i:i+100]
                            results.extend(get_rdw_bulk(batch))
                        
                        last_results = results
                        if not results:
                            error_message = "De RDW kon geen van deze kentekens vinden."
            except Exception as e:
                error_message = f"Fout bij inlezen: {str(e)}"
                
    return render_template('index.html', results=results, error=error_message)

@app.route('/download')
def download():
    global last_results
    if not last_results:
        return "Geen data beschikbaar", 400
    
    df_download = pd.DataFrame(last_results)
    proxy = io.StringIO()
    df_download.to_csv(proxy, index=False, sep=';') # Puntkomma is beter voor NL Excel
    
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='rdw_export.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
