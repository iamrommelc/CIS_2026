import os
import zipfile
import shutil

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def build_project():
    print("Generating Freight UI Project...")
    base_dir = "Freight_Movement_Project"
    
    # --- 1. BACKEND FILES ---
    
    # Adapted shipping_cost.py
    shipping_cost_code = r"""import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

rf_model = None

def train_model():
    global rf_model
    try:
        df = pd.read_csv("Delivery_Logistics.csv")
        df["distance_km"] = df["distance_km"].astype(float)
        df["package_weight_kg"] = df["package_weight_kg"].astype(float)
        df["vehicle_type"] = pd.factorize(df["vehicle_type"].sort_values())[0]
        
        X = df[["distance_km", "package_weight_kg", "vehicle_type"]]
        y = df["delivery_cost"]
        
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
        rf_model = RandomForestRegressor()
        rf_model.fit(X_train, y_train)
        print("Shipping Cost model trained.")
    except Exception as e:
        print(f"Error training cost model: {e}")

def predict_cost(distance, weight, vehicle):
    if rf_model is None: train_model()
    input_data = pd.DataFrame({'distance_km': [float(distance)], 'package_weight_kg': [float(weight)], 'vehicle_type': [float(vehicle)]})
    return rf_model.predict(input_data)[0]
"""

    # Adapted dynamic_freight.py
    dynamic_freight_code = r"""import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler

delay_pipeline, cost_pipeline, partners, vehicles = None, None, [], []

def train_dynamic_models():
    global delay_pipeline, cost_pipeline, partners, vehicles
    try:
        df = pd.read_csv("Delivery_Logistics.csv")
        df['delayed'] = df['delayed'].apply(lambda x: 1 if str(x).strip().lower() == 'yes' else 0)
        
        leakage_cols = ['delivery_id', 'delivery_time_hours', 'expected_time_hours', 'delivery_status', 'delivery_rating', 'delayed', 'delivery_cost']
        X = df.drop(columns=[col for col in leakage_cols if col in df.columns])
        y_delay, y_cost = df['delayed'], df['delivery_cost']
        
        cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        preprocessor = ColumnTransformer(transformers=[('num', StandardScaler(), num_cols), ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols)])
        
        delay_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', RandomForestClassifier(n_estimators=50, random_state=42))])
        cost_pipeline = Pipeline([('preprocessor', preprocessor), ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))])
        
        delay_pipeline.fit(X, y_delay)
        cost_pipeline.fit(X, y_cost)
        
        partners = df['delivery_partner'].unique().tolist()
        vehicles = df['vehicle_type'].unique().tolist()
        print("Dynamic models trained.")
    except Exception as e:
        print(f"Error training dynamic models: {e}")

def evaluate_carriers(shipment_profile):
    if delay_pipeline is None: train_dynamic_models()
    options = []
    for partner in partners:
        for vehicle in ['van', 'truck', 'bike']:
            if vehicle not in vehicles: continue
            
            test_case = pd.DataFrame([{
                'delivery_partner': partner, 'package_type': shipment_profile['package_type'],
                'vehicle_type': vehicle, 'delivery_mode': shipment_profile['delivery_mode'],
                'region': shipment_profile['region'], 'weather_condition': shipment_profile['weather_condition'],
                'distance_km': float(shipment_profile['distance_km']), 'package_weight_kg': float(shipment_profile['package_weight_kg'])
            }])
            
            pred_cost = cost_pipeline.predict(test_case)[0]
            pred_delay_prob = delay_pipeline.predict_proba(test_case)[0][1]
            
            options.append({'Carrier': partner.capitalize(), 'Vehicle': vehicle.capitalize(), 'Est_Cost': round(pred_cost, 2), 'Delay_Probability': round(pred_delay_prob * 100, 1)})
            
    results_df = pd.DataFrame(options)
    reliable = results_df[results_df['Delay_Probability'] < 50.0]
    best_routes = reliable.sort_values(by='Est_Cost') if not reliable.empty else results_df.sort_values(by=['Delay_Probability', 'Est_Cost'])
    return best_routes.to_dict(orient='records')
"""

    # Flask App
    app_code = r"""from flask import Flask, request, jsonify
from flask_cors import CORS
import shipping_cost
import dynamic_freight

app = Flask(__name__)
CORS(app)

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
    app.run(debug=True, port=5000)
"""

    # --- 2. FRONTEND FILES (React + Vite + Tailwind) ---
    
    pkg_json = r"""{
  "name": "freight-ui",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.292.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "vite": "^5.0.0"
  }
}"""

    tailwind_cfg = r"""/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}"""

    index_html = r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fluidic Freight UI</title>
  </head>
  <body class="bg-gradient-to-br from-blue-900 via-indigo-800 to-purple-900 min-h-screen text-white">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>"""

    main_jsx = r"""import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""

    index_css = r"""@tailwind base;
@tailwind components;
@tailwind utilities;

.glass-panel {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 shadow-xl rounded-2xl p-6 transition-all duration-300;
}
.glass-panel:hover {
    @apply bg-white/20 shadow-2xl transform -translate-y-1;
}
.glass-input {
    @apply w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-indigo-400;
}
"""

    app_jsx = r"""import { useState } from 'react';
import { Package, Truck, Activity, ArrowLeft } from 'lucide-react';

export default function App() {
  const [view, setView] = useState('home');
  const [costData, setCostData] = useState({ distance: '', weight: '', vehicle: '' });
  const [dynData, setDynData] = useState({ distance_km: '', package_weight_kg: '', package_type: 'electronics', delivery_mode: 'express', region: 'north', weather_condition: 'rainy' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCostSubmit = async (e) => {
    e.preventDefault(); setLoading(true);
    const res = await fetch('http://localhost:5000/api/cost', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(costData) });
    setResult(await res.json()); setLoading(false);
  };

  const handleDynSubmit = async (e) => {
    e.preventDefault(); setLoading(true);
    const res = await fetch('http://localhost:5000/api/dynamic', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dynData) });
    setResult(await res.json()); setLoading(false);
  };

  return (
    <div className="container mx-auto px-4 py-12">
      {view !== 'home' && (
        <button onClick={() => { setView('home'); setResult(null); }} className="flex items-center text-indigo-300 hover:text-white mb-6 transition">
          <ArrowLeft className="mr-2" /> Back to Dashboard
        </button>
      )}

      {view === 'home' && (
        <>
          <h1 className="text-4xl font-bold mb-10 text-center tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-purple-300">Freight Movement Intelligence</h1>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 cursor-pointer">
            <div onClick={() => setView('cost')} className="glass-panel text-center">
              <Truck className="w-12 h-12 mx-auto mb-4 text-blue-400" />
              <h2 className="text-xl font-semibold mb-2">Cost Estimation</h2>
              <p className="text-gray-300 text-sm">Calculate shipping costs using random forest regression.</p>
            </div>
            <div onClick={() => setView('dynamic')} className="glass-panel text-center">
              <Activity className="w-12 h-12 mx-auto mb-4 text-purple-400" />
              <h2 className="text-xl font-semibold mb-2">Delay Prediction</h2>
              <p className="text-gray-300 text-sm">Analyze isolated delay risk using classification models.</p>
            </div>
            <div onClick={() => setView('dynamic')} className="glass-panel text-center">
              <Package className="w-12 h-12 mx-auto mb-4 text-indigo-400" />
              <h2 className="text-xl font-semibold mb-2">Dynamic Routing Model</h2>
              <p className="text-gray-300 text-sm">Evaluate overall carrier options prioritizing reliability and cost.</p>
            </div>
          </div>
        </>
      )}

      {view === 'cost' && (
        <div className="max-w-md mx-auto glass-panel">
          <h2 className="text-2xl font-bold mb-6 flex items-center"><Truck className="mr-3 text-blue-400"/> Cost Estimator</h2>
          <form onSubmit={handleCostSubmit} className="space-y-4">
            <input type="number" placeholder="Distance (km)" className="glass-input" onChange={e => setCostData({...costData, distance: e.target.value})} required/>
            <input type="number" placeholder="Weight (kg)" className="glass-input" onChange={e => setCostData({...costData, weight: e.target.value})} required/>
            <input type="number" placeholder="Vehicle Type (Int)" className="glass-input" onChange={e => setCostData({...costData, vehicle: e.target.value})} required/>
            <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition">{loading ? 'Calculating...' : 'Estimate Cost'}</button>
          </form>
          {result && <div className="mt-6 p-4 bg-green-500/20 border border-green-500/50 rounded-lg text-green-100 text-center text-xl font-semibold">Estimated Cost: ${result.cost}</div>}
        </div>
      )}

      {view === 'dynamic' && (
        <div className="max-w-4xl mx-auto glass-panel">
          <h2 className="text-2xl font-bold mb-6 flex items-center"><Activity className="mr-3 text-purple-400"/> Dynamic Routing Engine</h2>
          <form onSubmit={handleDynSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <input type="number" placeholder="Distance (km)" className="glass-input" onChange={e => setDynData({...dynData, distance_km: e.target.value})} required/>
            <input type="number" placeholder="Weight (kg)" className="glass-input" onChange={e => setDynData({...dynData, package_weight_kg: e.target.value})} required/>
            <select className="glass-input bg-indigo-900/50" onChange={e => setDynData({...dynData, package_type: e.target.value})}>
                <option value="electronics">Electronics</option><option value="furniture">Furniture</option><option value="groceries">Groceries</option>
            </select>
            <select className="glass-input bg-indigo-900/50" onChange={e => setDynData({...dynData, weather_condition: e.target.value})}>
                <option value="clear">Clear</option><option value="rainy">Rainy</option><option value="stormy">Stormy</option><option value="foggy">Foggy</option>
            </select>
            <button type="submit" className="md:col-span-2 bg-purple-500 hover:bg-purple-600 font-bold py-2 px-4 rounded-lg transition">{loading ? 'Running Models...' : 'Recommend Carrier'}</button>
          </form>
          
          {result && result.results && (
            <div className="overflow-x-auto bg-black/20 rounded-lg">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-white/10 text-white font-semibold">
                  <tr><th className="px-4 py-3">Carrier</th><th className="px-4 py-3">Vehicle</th><th className="px-4 py-3">Est. Cost</th><th className="px-4 py-3">Delay Risk</th></tr>
                </thead>
                <tbody>
                  {result.results.map((r, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                      <td className="px-4 py-3 font-medium text-white">{r.Carrier}</td><td className="px-4 py-3">{r.Vehicle}</td>
                      <td className="px-4 py-3">${r.Est_Cost.toFixed(2)}</td>
                      <td className={`px-4 py-3 ${r.Delay_Probability > 50 ? 'text-red-400' : 'text-green-400'}`}>{r.Delay_Probability}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}"""

    # --- DIRECTORY CREATION ---
    create_file(f"{base_dir}/backend/app.py", app_code)
    create_file(f"{base_dir}/backend/shipping_cost.py", shipping_cost_code)
    create_file(f"{base_dir}/backend/dynamic_freight.py", dynamic_freight_code)
    create_file(f"{base_dir}/backend/requirements.txt", "flask\nflask-cors\npandas\nscikit-learn")
    
    create_file(f"{base_dir}/frontend/package.json", pkg_json)
    create_file(f"{base_dir}/frontend/tailwind.config.js", tailwind_cfg)
    create_file(f"{base_dir}/frontend/postcss.config.js", "export default {\n  plugins: {\n    tailwindcss: {},\n    autoprefixer: {},\n  },\n}")
    create_file(f"{base_dir}/frontend/index.html", index_html)
    create_file(f"{base_dir}/frontend/src/main.jsx", main_jsx)
    create_file(f"{base_dir}/frontend/src/index.css", index_css)
    create_file(f"{base_dir}/frontend/src/App.jsx", app_jsx)
    
    # Try to copy the CSV file if it's in the current directory
    try:
        shutil.copy("Delivery_Logistics.csv", f"{base_dir}/backend/Delivery_Logistics.csv")
    except FileNotFoundError:
        print("Note: Delivery_Logistics.csv not found in current directory. Creating a dummy file so zip succeeds.")
        create_file(f"{base_dir}/backend/Delivery_Logistics.csv", "delivery_id,delivery_partner,package_type,vehicle_type,delivery_mode,region,weather_condition,distance_km,package_weight_kg,delayed,delivery_cost\n1,delhivery,electronics,van,express,north,rainy,120,15,no,450.0")

    # --- ZIP CREATION ---
    zip_filename = f"{base_dir}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, base_dir))
                
    print(f"\nSuccess! '{zip_filename}' has been generated.")
    print("Extract the zip to begin.")

if __name__ == "__main__":
    build_project()