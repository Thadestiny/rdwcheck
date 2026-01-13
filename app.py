import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# De HTML-structuur met CSS voor een nette weergave
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RDW Kenteken Check</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; padding: 50px; background-color: #f0f2f5; }
        .card { background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); width: 100%; max-width: 450px; }
        h2 { color: #1a1a1a; text-align: center; margin-bottom: 1.5rem; }
        label { font-size: 0.9rem; color: #666; }
        input { width: 100%; padding: 12px; margin: 8px 0 18px 0; border: 2px solid #ddd; border-radius: 6px; box-sizing: border-box; text-transform: uppercase; font-weight: bold; font-size: 1.1rem; text-align: center; }
        input:focus { border-color: #007bff; outline: none; }
        button { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: background 0.2s; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 25px; padding: 20px; background: #f8f9fa; border-left: 5px solid #007bff; border-radius: 4px; line-height: 1.6; }
        .error { margin-top: 20px; padding: 15px; background: #fff5f5; border-left: 5px solid #ff4d4d; color: #cc0000; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚗 RDW Voertuig Check</h2>
        <form method="GET">
            <label for="kenteken">Voer het kenteken in:</label>
            <input type="text" id="kenteken" name="kenteken" placeholder="XX-YY-ZZ" required autofocus>
            <button type="submit">Gegevens ophalen</button>
        </form>

        {% if data %}
        <div class="result">
            <strong>Merk/Model:</strong> {{ data.merk }} {{ data.handelsbenaming }}<br>
            <strong>📅 Eerste toelating:</strong> {{ data.eerste_toelating }}<br>
            <strong>📝 Laatste tenaamstelling:</strong> {{ data.laatste_tenaamstelling }}
        </div>
        {% elif error %}
        <div class="error">
            <strong>Fout:</strong> {{ error }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def format_rdw_datum(datum_str):
    """Zet RDW datum (YYYYMMDD) om naar DD-MM-YYYY."""
    if datum_str and len(str(datum_str)) == 8:
        s = str(datum_str)
        return f"{s[6:8]}-{s[4:6]}-{s[0:4]}"
    return "Niet beschikbaar"

@app.route('/', methods=['GET'])
def index():
    kenteken = request.args.get('kenteken')
    data = None
    error = None

    if kenteken:
        # Kenteken opschonen voor de API
        schoon_kenteken = kenteken.replace('-', '').replace(' ', '').upper()
        
        # We raadplegen de hoofd-dataset van de RDW
        url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={schoon_kenteken}"
        
        try:
            response = requests.get(url, timeout=10)
            resultaat_lijst = response.json()
            
            if resultaat_lijst and len(resultaat_lijst) > 0:
                v = resultaat_lijst[0]
                
                # De RDW API gebruikt soms 'datum_laatste_tenaamstelling' 
                # en soms 'datum_tenaamstelling'. We proberen beide.
                raw_tenaamstelling = v.get('datum_laatste_tenaamstelling') or v.get('datum_tenaamstelling')
                raw_toelating = v.get('datum_eerste_toelating')

                data = {
                    "merk": v.get('merk', 'Onbekend'),
                    "handelsbenaming": v.get('handelsbenaming', 'Onbekend'),
                    "eerste_toelating": format_rdw_datum(raw_toelating),
                    "laatste_tenaamstelling": format_rdw_datum(raw_tenaamstelling)
                }
            else:
                error = f"Geen voertuig gevonden voor kenteken: {kenteken}"
                
        except Exception as e:
            error = "Er kon geen verbinding worden gemaakt met de RDW. Probeer het later opnieuw."

    return render_template_string(HTML_TEMPLATE, data=data, error=error)

if __name__ == '__main__':
    # Poort 5000 is standaard voor Flask, Render regelt de rest via Gunicorn
    app.run(host='0.0.0.0', port=5000)
