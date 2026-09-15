from flask import Flask, request, jsonify
from flask_cors import CORS
import shipping_cost
import dynamic_freight
import rerouting
import econometrics

app = Flask(__name__)
CORS(app)





@app.route('/api/econometrics', methods=['GET'])
def get_econometrics():
    try:
        data = econometrics.get_econometrics_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/master-guide', methods=['GET'])
def get_master_guide():
    try:
        guide = rerouting.get_master_routing_guide()
        return jsonify({'results': guide})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cost', methods=['POST'])
def get_cost():
    data = request.json
    cost = shipping_cost.predict_cost(data['distance'], data['weight'], data['vehicle'])
    return jsonify({'cost': round(cost, 2)})

@app.route('/api/dynamic', methods=['POST'])
def get_dynamic():
    data = request.json
    results = dynamic_freight.evaluate_carriers(data)
    return jsonify({'results': results})

if __name__ == '__main__':
    shipping_cost.train_model()
    dynamic_freight.train_dynamic_models()
    app.run(debug=True, port=5001)
