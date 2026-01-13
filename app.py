import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/rdw', methods=['GET'])
def get_voertuig():
    kenteken = request.args.get('kenteken')
    if not kenteken:
        return jsonify({"error": "Geen kenteken opgegeven"}), 400

    kenteken = kenteken.replace('-', '').upper()
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={kenteken}"
    
    try:
        response = requests.get(url)
        data = response.json()
        if not data:
            return jsonify({"error": "Voertuig niet gevonden"}), 404
            
        voertuig = data[0]
        return jsonify({
            "merk": voertuig.get('merk'),
            "handelsbenaming": voertuig.get('handelsbenaming'),
            "eerste_toelating": voertuig.get('datum_eerste_toelating'),
            "laatste_tenaamstelling": voertuig.get('datum_laatste_tenaamstelling')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
