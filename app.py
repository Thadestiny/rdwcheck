from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import io

app = Flask(__name__)

# We gebruiken een globale variabele om de laatste resultaten tijdelijk te onthouden voor de download
last_results = []

def get_rdw_bulk(kentekens):
    clean_list = [str(k).replace('-', '').replace(' ', '').upper() for k in kentekens if pd.notna(k)]
    if not clean_list: return []

    formatted_list = "','".join(clean_list)
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?$where=kenteken in('{formatted_list}')"
    
    results_dict = {}
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            for item in response.json():
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
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            df = pd.read_csv(stream)
            kentekens = df.iloc[:, 0].tolist()
            
            for i in range(0, len(kentekens), 100):
                results.extend(get_rdw_bulk(kentekens[i:i+100]))
            
            last_results = results # Sla op voor download
                
    return render_template('index.html', results=results)

@app.route('/download')
def download():
    global last_results
    if not last_results:
        return "Geen data om te downloaden", 400
    
    # Maak een CSV in het geheugen
    df_download = pd.DataFrame(last_results)
    proxy = io.StringIO()
    df_download.to_csv(proxy, index=False)
    
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode())
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='rdw_resultaten.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
