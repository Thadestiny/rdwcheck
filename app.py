import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Dit is de HTML-structuur voor je website
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RDW Kenteken Check</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; padding: 50px; background-color: #f4f4f9; }
        .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; text-transform: uppercase; }
        button { width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚗 RDW Check</h2>
        <form method="GET">
            <input type="text" name="kenteken" placeholder="Bijv. 01-ABC-2" required>
            <button type="submit">Zoek gegevens</button>
        </form>

        {% if data %}
        <div class="result">
            <strong>Voertuig:</strong> {{ data.merk }} {{ data.handelsbenaming }}<br>
            <strong>Eerste toelating:</strong> {{ data.eerste_toelating }}<br>
            <strong>Laatste tenaamstelling:</strong> {{ data.laatste_tenaamstelling }}
        </div>
        {% elif error %}
        <div class="result" style="color: red;">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    kenteken = request.args.get('kenteken')
    data = None
    error = None

    if kenteken:
        # Opschonen van kenteken
        schoon_kenteken = kenteken.replace('-', '').upper()
        url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={schoon_kenteken}"
        
        try:
            response = requests.get(url)
            result = response.json()
            
            if result:
                v = result[0]
                data = {
                    "merk": v.get('merk', 'Onbekend'),
                    "handelsbenaming": v.get('handelsbenaming', 'Onbekend'),
                    "eerste_toelating": v.get('datum_eerste_toelating', 'Onbekend'),
                    "laatste_tenaamstelling": v.get('datum_laatste_tenaamstelling', 'Onbekend')
                }
            else:
                error = "Kenteken niet gevonden in de RDW database."
        except Exception as e:
            error = f"Fout bij ophalen gegevens: {e}"

    return render_template_string(HTML_TEMPLATE, data=data, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
