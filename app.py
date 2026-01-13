import requests
import io
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Verbeterde HTML met een tabel voor bulk-resultaten
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>RDW Bulk Check</title>
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background-color: #f8f9fa; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { color: #007bff; }
        .form-group { margin-bottom: 20px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }
        input[type="text"] { padding: 10px; width: 250px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #f1f1f1; }
        .status-ok { color: green; font-weight: bold; }
        .status-error { color: red; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚗 RDW Bulk Voertuig Check</h2>
        
        <div class="form-group">
            <form method="POST" enctype="multipart/form-data">
                <p><strong>Enkel kenteken of bestand uploaden:</strong></p>
                <input type="text" name="kenteken" placeholder="01-ABC-2">
                <span style="margin: 0 15px;">OF</span>
                <input type="file" name="file" accept=".txt,.csv">
                <br><br>
                <button type="submit">Start Zoekopdracht</button>
            </form>
        </div>

        {% if resultaten %}
        <h3>Resultaten:</h3>
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
    </div>
</body>
</html>
"""

def format_rdw_datum(d):
    """Formatteert YYYYMMDD naar DD-MM-YYYY"""
    if d and len(str(d)) == 8:
        s = str(d)
        return f"{s[6:8]}-{s[4:6]}-{s[0:4]}"
    return "Onbekend"

def haal_voertuig_data(kenteken):
    """Haalt data op bij de RDW API"""
    if not kenteken:
        return None
    
    schoon_kenteken = kenteken.replace('-', '').replace(' ', '').upper()
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={schoon_kenteken}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            v = data[0]
            # Check beide mogelijke veldnamen voor de tenaamstelling
            tenaam_raw = v.get('datum_laatste_tenaamstelling') or v.get('datum_tenaamstelling')
            toelating_raw = v.get('datum_eerste_toelating')
            
            return {
                "kenteken": kenteken.upper(),
                "voertuig": f"{v.get('merk', 'Onbekend')} {v.get('handelsbenaming', '')}",
                "toelating": format_rdw_datum(toelating_raw),
                "tenaamstelling": format_rdw_datum(tenaam_raw)
            }
        return {"kenteken": kenteken.upper(), "voertuig": "Niet gevonden", "toelating": "-", "tenaamstelling": "-"}
    except Exception:
        return {"kenteken": kenteken.upper(), "voertuig": "Fout bij ophalen", "toelating": "-", "tenaamstelling": "-"}

@app.route('/', methods=['GET', 'POST'])
def index():
    resultaten = []
    
    if request.method == 'POST':
        # 1. Check op enkel kenteken
        enkel_kenteken = request.form.get('kenteken')
        if enkel_kenteken:
            res = haal_voertuig_data(enkel_kenteken)
            if res: resultaten.append(res)
        
        # 2. Check op bestandsupload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                try:
                    # Lees het bestand regel voor regel
                    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                    for line in stream:
                        k = line.strip()
                        if k:
                            res = haal_voertuig_data(k)
                            if res: resultaten.append(res)
                except Exception as e:
                    print(f"Fout bij verwerken bestand: {e}")

    return render_template_string(HTML_TEMPLATE, resultaten=resultaten)

if __name__ == '__main__':
    # Belangrijk voor Render: luisteren op 0.0.0.0
    app.run(host='0.0.0.0', port=5000)
