import React, { useState } from 'react';
import { Package, Truck, Activity, ArrowLeft, Network, Map, LineChart, Construction } from 'lucide-react';

export default function App() {
  // 'landing' is the new root. 'dashboard' is the old home.
  const [view, setView] = useState('landing'); 
  const [costData, setCostData] = useState({ distance: '', weight: '', vehicle: '' });
  const [dynData, setDynData] = useState({ distance_km: '', package_weight_kg: '', package_type: 'electronics', delivery_mode: 'express', region: 'north', weather_condition: 'rainy' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [guideData, setGuideData] = useState(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [ecoData, setEcoData] = useState(null);
  const [ecoLoading, setEcoLoading] = useState(false);

  const handleEcoLoad = async () => {
    setEcoLoading(true);
    const res = await fetch('http://localhost:5001/api/econometrics');
    setEcoData(await res.json());
    setEcoLoading(false);
  };

  const handleCostSubmit = async (e) => {
    e.preventDefault(); setLoading(true);
    const res = await fetch('http://localhost:5001/api/cost', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(costData) });
    setResult(await res.json()); setLoading(false);
  };

  const handleDynSubmit = async (e) => {
    e.preventDefault(); setLoading(true);
    const res = await fetch('http://localhost:5001/api/dynamic', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dynData) });
    setResult(await res.json()); setLoading(false);
  };
  const handleGuideLoad = async () => {
  setGuideLoading(true);
  const res = await fetch('http://localhost:5001/api/master-guide');
  setGuideData(await res.json());
  setGuideLoading(false);
  };

  // Smart back navigation based on current view depth
  const handleBack = () => {
    setResult(null);
    if (['cost', 'delay', 'dynamic'].includes(view)) {
      setView('dashboard');
    } else {
      setView('landing');
    }
  };

  return (
    <div className="relative min-h-screen text-white overflow-x-hidden">
      
      {/* 1. THE DYNAMIC VIDEO BACKGROUND */}
      <video 
        autoPlay 
        loop 
        muted 
        playsInline 
        className="fixed top-0 left-0 w-full h-full object-cover z-[-2]"
      >
        {/* Placeholder: Aerial view of a highway in motion. Replace src with your own if needed. */}
        <source src="/public/video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* 2. THE DARK OVERLAY (Ensures glass panels and text are readable) */}
      {/* DARK OVERLAY FOR READABILITY */}
      <div className="fixed top-0 left-0 w-full h-full z-[-1] bg-black/40"></div>

      {/* 3. YOUR EXISTING APP CONTENT */}
      <div className="container mx-auto px-4 py-12 relative z-10">
      
      {/* Dynamic Back Button */}
      {view !== 'landing' && (
        <button onClick={handleBack} className="flex items-center text-indigo-300 hover:text-white mb-6 transition">
          <ArrowLeft className="mr-2" /> Back
        </button>
      )}

      {/* 1. MASTER LANDING PAGE */}
      {view === 'landing' && (
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-indigo-300 to-purple-300">
              Multi-Carrier Freight Cost and Lane Optimization
            </h1>
            <p className="text-xl text-indigo-200 font-light">
              Using Data Analytics to Minimize Strategic Shipping Expenditures
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 cursor-pointer">
            <div onClick={() => setView('dashboard')} className="glass-panel text-center border-indigo-400/40">
              <Network className="w-12 h-12 mx-auto mb-4 text-blue-400" />
              <h2 className="text-xl font-semibold mb-2">Freight Movement Intelligence</h2>
              <p className="text-gray-300 text-sm">Active machine learning models for cost, delay, and dynamic route prediction.</p>
            </div>
            
            <div onClick={() => setView('master_guide')} className="glass-panel text-center opacity-80 hover:opacity-100">
              <Map className="w-12 h-12 mx-auto mb-4 text-purple-400" />
              <h2 className="text-xl font-semibold mb-2">Master Routing Guide</h2>
              <p className="text-gray-300 text-sm">Static lane optimization and carrier compliance matrices. (In Development)</p>
            </div>
            
            <div onClick={() => setView('econometrics')} className="glass-panel text-center opacity-80 hover:opacity-100">
              <LineChart className="w-12 h-12 mx-auto mb-4 text-pink-400" />
              <h2 className="text-xl font-semibold mb-2">Econometrics of Shipping</h2>
              <p className="text-gray-300 text-sm">Macro-level expenditure forecasting and budget variance analytics. (In Development)</p>
            </div>
          </div>
        </div>
      )}

      {/* 2. FREIGHT MOVEMENT DASHBOARD (The original home) */}
      {view === 'dashboard' && (
        <>
          <h1 className="text-3xl font-bold mb-10 text-center tracking-tight text-indigo-100">Freight Movement Intelligence</h1>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 cursor-pointer">
            <div onClick={() => setView('cost')} className="glass-panel text-center">
              <Truck className="w-12 h-12 mx-auto mb-4 text-blue-400" />
              <h2 className="text-xl font-semibold mb-2">Cost Estimation</h2>
              <p className="text-gray-300 text-sm">Calculate shipping costs using random forest regression.</p>
            </div>
            <div onClick={() => setView('delay')} className="glass-panel text-center">
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

      {/* MASTER ROUTING GUIDE VIEW */}
      {view === 'master_guide' && (
      <div className="max-w-5xl mx-auto glass-panel">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold flex items-center"><Map className="mr-3 text-purple-400"/> Optimized Lane Allocations</h2>
          <button onClick={handleGuideLoad} className="bg-purple-500 hover:bg-purple-600 font-bold py-2 px-4 rounded-lg transition">
            {guideLoading ? 'Solving Simplex...' : 'Generate Matrix'}
          </button>
        </div>

        {guideData && guideData.results && (
          <div className="overflow-x-auto bg-black/20 rounded-lg max-h-96 overflow-y-auto">
            <table className="w-full text-left text-sm text-gray-300 relative">
              <thead className="bg-indigo-900/80 text-white font-semibold sticky top-0 backdrop-blur-md">
                <tr><th className="px-4 py-3">Region</th><th className="px-4 py-3">Weight Bracket</th><th className="px-4 py-3">Carrier</th><th className="px-4 py-3">Mode</th><th className="px-4 py-3">Vol. Allocation</th></tr>
              </thead>
              <tbody>
                {guideData.results.map((r, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                    <td className="px-4 py-3 font-medium text-white capitalize">{r.region}</td>
                    <td className="px-4 py-3">{r.weight_bracket}</td>
                    <td className="px-4 py-3 capitalize">{r.delivery_partner}</td>
                    <td className="px-4 py-3 capitalize">{r.delivery_mode}</td>
                    <td className="px-4 py-3 font-bold text-green-400">{r.Allocated_Volume} units</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      )}

      {/* ECONOMETRICS DASHBOARD */}
      {view === 'econometrics' && (
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-3xl font-bold flex items-center text-pink-400"><LineChart className="mr-3"/> Econometrics of Shipping</h2>
              <p className="text-gray-300 mt-1">Cost elasticity, structural inefficiencies, and carrier premiums.</p>
            </div>
            <button onClick={handleEcoLoad} className="bg-pink-500 hover:bg-pink-600 font-bold py-2 px-6 rounded-lg transition">
              {ecoLoading ? 'Running Regressions...' : 'Analyze Market Data'}
            </button>
          </div>

          {ecoData && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Elasticity Cards */}
              <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel border-pink-500/30">
                  <h3 className="text-lg text-pink-300 mb-2 font-semibold">Distance Elasticity</h3>
                  <div className="text-4xl font-bold mb-2">{ecoData.elasticity.distance.toFixed(3)}</div>
                  <p className="text-sm text-gray-400">
                    {ecoData.elasticity.distance < 1 ? "Economies of scale achieved. Costs rise slower than distance." : "Diseconomies of scale. Costs scale aggressively with distance."}
                  </p>
                </div>
                <div className="glass-panel border-pink-500/30">
                  <h3 className="text-lg text-pink-300 mb-2 font-semibold">Weight Elasticity</h3>
                  <div className="text-4xl font-bold mb-2">{ecoData.elasticity.weight.toFixed(3)}</div>
                  <p className="text-sm text-gray-400">
                    {ecoData.elasticity.weight < 1 ? "Economies of scale achieved. Costs rise slower than weight." : "Diseconomies of scale. Freight becomes exponentially expensive as weight increases."}
                  </p>
                </div>
              </div>

              {/* Carrier Premiums */}
              <div className="glass-panel lg:col-span-1 max-h-[500px] overflow-y-auto">
                <h3 className="text-lg font-bold mb-4 text-indigo-300">Carrier Price Premiums</h3>
                <p className="text-xs text-gray-400 mb-4">Relative to baseline carrier (controlled for distance & weight).</p>
                <div className="space-y-3">
                  {ecoData.premiums.map((p, i) => (
                    <div key={i} className="flex justify-between items-center border-b border-white/10 pb-2">
                      <span className="capitalize">{p.delivery_partner}</span>
                      <span className={`font-mono ${p.pct_premium > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {p.pct_premium > 0 ? '+' : ''}{p.pct_premium.toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Corridor Inefficiencies */}
              <div className="glass-panel lg:col-span-2 overflow-x-auto">
                <h3 className="text-lg font-bold mb-4 text-indigo-300">Corridor Structural Inefficiencies</h3>
                <p className="text-xs text-gray-400 mb-4">Analyzed via K-Means clustering and OLS residuals.</p>
                <table className="w-full text-left text-sm text-gray-300">
                  <thead className="bg-white/10 text-white">
                    <tr>
                      <th className="px-3 py-2">Dominant Region</th>
                      <th className="px-3 py-2">Avg Cost/km</th>
                      <th className="px-3 py-2">Delay Rate</th>
                      <th className="px-3 py-2">Overcharge Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ecoData.corridors.map((c, i) => (
                      <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                        <td className="px-3 py-2 capitalize font-medium">{c.dominant_region}</td>
                        <td className="px-3 py-2">${c.avg_cost_per_km.toFixed(2)}</td>
                        <td className="px-3 py-2">{c.delay_rate.toFixed(1)}%</td>
                        <td className={`px-3 py-2 font-semibold ${c.overcharge_pct > 15 ? 'text-red-400' : 'text-yellow-400'}`}>
                          {c.overcharge_pct.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* COST ESTIMATOR VIEW */}
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

      {/* DELAY PREDICTION VIEW */}
      {view === 'delay' && (
        <div className="max-w-4xl mx-auto glass-panel">
          <h2 className="text-2xl font-bold mb-6 flex items-center"><Activity className="mr-3 text-purple-400"/> Delay Risk Analyzer</h2>
          <form onSubmit={handleDynSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <input type="number" placeholder="Distance (km)" className="glass-input" onChange={e => setDynData({...dynData, distance_km: e.target.value})} required/>
            <input type="number" placeholder="Weight (kg)" className="glass-input" onChange={e => setDynData({...dynData, package_weight_kg: e.target.value})} required/>
            <select className="glass-input bg-indigo-900/50" onChange={e => setDynData({...dynData, package_type: e.target.value})}>
                <option value="electronics">Electronics</option><option value="furniture">Furniture</option><option value="groceries">Groceries</option>
            </select>
            <select className="glass-input bg-indigo-900/50" onChange={e => setDynData({...dynData, weather_condition: e.target.value})}>
                <option value="clear">Clear</option><option value="rainy">Rainy</option><option value="stormy">Stormy</option><option value="foggy">Foggy</option>
            </select>
            <button type="submit" className="md:col-span-2 bg-purple-500 hover:bg-purple-600 font-bold py-2 px-4 rounded-lg transition">{loading ? 'Running Classifier...' : 'Analyze Delay Risks'}</button>
          </form>
          
          {result && result.results && (
            <div className="overflow-x-auto bg-black/20 rounded-lg">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-white/10 text-white font-semibold">
                  <tr><th className="px-4 py-3">Carrier</th><th className="px-4 py-3">Vehicle</th><th className="px-4 py-3">Delay Probability</th><th className="px-4 py-3">Status</th></tr>
                </thead>
                <tbody>
                  {[...result.results].sort((a, b) => b.Delay_Probability - a.Delay_Probability).map((r, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                      <td className="px-4 py-3 font-medium text-white">{r.Carrier}</td><td className="px-4 py-3">{r.Vehicle}</td>
                      <td className={`px-4 py-3 font-bold ${r.Delay_Probability > 50 ? 'text-red-400' : 'text-green-400'}`}>{r.Delay_Probability}%</td>
                      <td className="px-4 py-3">
                        {r.Delay_Probability > 50 ? <span className="bg-red-500/20 text-red-300 px-2 py-1 rounded text-xs">High Risk</span> : <span className="bg-green-500/20 text-green-300 px-2 py-1 rounded text-xs">Reliable</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* DYNAMIC ROUTING VIEW */}
      {view === 'dynamic' && (
        <div className="max-w-4xl mx-auto glass-panel">
          <h2 className="text-2xl font-bold mb-6 flex items-center"><Package className="mr-3 text-indigo-400"/> Dynamic Routing Engine</h2>
          <form onSubmit={handleDynSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <input type="number" placeholder="Distance (km)" className="glass-input" onChange={e => setDynData({...dynData, distance_km: e.target.value})} required/>
            <input type="number" placeholder="Weight (kg)" className="glass-input" onChange={e => setDynData({...dynData, package_weight_kg: e.target.value})} required/>
            <select className="glass-input bg-indigo-900/50" onChange={e => setDynData({...dynData, package_type: e.target.value})}>
                <option value="electronics">Electronics</option><option value="furniture">Furniture</option><option value="groceries">Groceries</option>
            </select>
            <select className="glass-input bg-indigo-900/50" onChange={e => setDynData({...dynData, weather_condition: e.target.value})}>
                <option value="clear">Clear</option><option value="rainy">Rainy</option><option value="stormy">Stormy</option><option value="foggy">Foggy</option>
            </select>
            <button type="submit" className="md:col-span-2 bg-indigo-500 hover:bg-indigo-600 font-bold py-2 px-4 rounded-lg transition">{loading ? 'Running Models...' : 'Recommend Route'}</button>
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
    </div>
  );
}