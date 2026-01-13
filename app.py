import requests
import io
import csv
from flask import Flask, request, render_template_string, Response

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>RDW Bulk Check & Export</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background-color: #f4f7f6; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .form-group { background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        input[type="text"], input[type="file"] { padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #2980b9; }
        .btn-download { background: #27ae60; margin-top: 10px; text-decoration: none; display: inline-block; color: white; padding: 10px 20px; border-radius: 4px; font-weight: bold; }
        .btn-download:hover { background: #219150; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; background: white; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #34495e; color: white; }
        tr:hover { background-color: #f1f1f1; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚗 RDW Bulk Voertuig Check</h2>
        
        <div class="form-group">
            <form method="POST" enctype="multipart/form-data">
                <p><strong>Voer kenteken in of upload een lijst (.txt/.csv):</strong></p>
                <input type="text" name="kenteken" placeholder="01-ABC-2">
                <input type="file" name="file" accept=".txt,.csv">
                <button type="submit">Verwerken</button>
            </form>
        </div>

        {% if resultaten %}
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3>Resultaten</h3>
            <form action="/download" method="POST">
                <input type="hidden" name="data" value="{{ resultaten }}">
                <button type="submit" class="btn-download">📥 Download als Excel (CSV)</button>
            </form>
        </div>
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
    if d and len(str(d)) == 8:
        s = str(d)
        return f"{s[6:8]}-{s[4:6]}-{s[0:4]}"
    return "Onbekend"

def haal_voertuig_data(kenteken):
    if not kenteken: return None
    schoon = kenteken.replace('-', '').replace(' ', '').upper()
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={schoon}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data:
            v = data[0]
            tenaam_raw = v.get('datum_laatste_tenaamstelling') or v.get('datum_tenaamstelling')
            return {
                "kenteken": kenteken.upper(),
                "voertuig": f"{v.get('merk', '')} {v.get('handelsbenaming', '')}".strip(),
                "toelating": format_rdw_datum(v.get('datum_eerste_toelating')),
                "tenaamstelling": format_rdw_datum(tenaam_raw)
            }
    except: pass
    return {"kenteken": kenteken.upper(), "voertuig": "Niet gevonden", "toelating": "-", "tenaamstelling": "-"}

@app.route('/', methods=['GET', 'POST'])
def index():
    resultaten = []
    if request.method == 'POST':
        enkel = request.form.get('kenteken')
        if enkel:
            res = haal_voertuig_data(enkel)
            if res: resultaten.append(res)
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                for line in stream:
                    if line.strip():
                        res = haal_voertuig_data(line.strip())
                        if res: resultaten.append(res)

    return render_template_string(HTML_TEMPLATE, resultaten=resultaten)

@app.route('/download', methods=['POST'])
def download():
    # We halen de data op die als string in het verborgen veld staat
    import ast
    raw_data = request.form.get('data')
    data_list = ast.literal_eval(raw_data) # Zet string om terug naar lijst

    si = io.StringIO()
    cw = csv.writer(si, delimiter=';') # Puntkomma werkt het beste voor Nederlandse Excel
    cw.writerow(['Kenteken', 'Voertuig', 'Eerste Toelating', 'Laatste Tenaamstelling'])
    
    for row in data_list:
        cw.writerow([row['kenteken'], row['voertuig'], row['toelating'], row['tenaamstelling']])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=rdw_export.csv"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
