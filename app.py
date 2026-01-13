import requests
import io
import csv
from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RDW Bulk Check</title>
    <style>
        body { font-family: sans-serif; padding: 30px; background-color: #f0f2f5; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .section { margin-bottom: 30px; padding: 15px; border: 1px solid #eee; border-radius: 8px; }
        input[type="text"], input[type="file"] { padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .error { color: red; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚗 RDW Bulk Kenteken Check</h2>
        
        <div class="section">
            <p><strong>Optie 1: Enkel kenteken</strong></p>
            <form method="POST">
                <input type="text" name="kenteken" placeholder="XX-YY-ZZ">
                <button type="submit">Zoek</button>
            </form>
        </div>

        <div class="section">
            <p><strong>Optie 2: Bulk upload (CSV of TXT)</strong></p>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="file" accept=".csv, .txt">
                <button type="submit">Upload en verwerk</button>
            </form>
            <small>Upload een bestand met één kenteken per regel.</small>
        </div>

        {% if resultaten %}
        <h3>Resultaten</h3>
        <table>
            <thead>
                <tr>
                    <th>Kenteken</th>
                    <th>Merk/Model</th>
                    <th>Eerste Toelating</th>
                    <th>Laatste Tenaamstelling</th>
                </tr>
            </thead>
            <tbody>
                {% for r in resultaten %}
                <tr>
                    <td><strong>{{ r.kenteken }}</strong></td>
                    <td>{{ r.voertuig }}</td>
                    <td>{{ r.toelating }}</td>
                    <td>{{ r.tenaamstelling }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

def format_rdw_datum(d):
    if d and len(str(d)) == 8:
        s = str(d); return f"{s[6:8]}-{s[4:6]}-{s[0:4]}"
    return "Niet beschikbaar"

def haal_rdw_data(kenteken):
    schoon = kenteken.replace('-', '').replace(' ', '').upper()
    try:
        url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={schoon}"
        res = requests.get(url, timeout=5).json()
        if res:
            v = res[0]
            return {
                "kenteken": kenteken.upper(),
                "voertuig": f"{v.get('merk', '')} {v.get('handelsbenaming', '')}",
                "toelating": format_rdw_datum(v.get('datum_eerste_toelating')),
                "tenaamstelling": format_rdw_datum(v.get('datum_laatste_tenaamstelling') or v.get('datum_tenaamstelling'))
            }
    except:
        pass
    return {"kenteken": kenteken.upper(), "voertuig": "Niet gevonden", "toelating": "-", "tenaamstelling": "-"}

@app.route('/', methods=['GET', 'POST'])
def index():
    resultaten = []
    error = None

    if request.method == 'POST':
        # Check of het een enkel kenteken is
        enkel_kenteken = request.form.get('kenteken')
        if enkel_kenteken:
            resultaten.append(haal_rdw_data(enkel_kenteken))
        
        # Check of het een bestand is
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
                # Lees regels, strip witruimte en filter lege regels
                kentekens = [line.strip() for line in stream if line.strip()]
                for k in kentekens:
                    resultaten.append(haal_rdw_data(k))

    return render_template_string(HTML_TEMPLATE, resultaten=resultaten, error=
