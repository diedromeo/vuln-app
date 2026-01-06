import sqlite3
import os
import random
import datetime
import time
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from flask import Flask, render_template_string, request, jsonify, make_response, redirect, send_from_directory, session

# =============================================================================
# TEGH INDUSTRIES - LANDING & MARKETING PLATFORM
# =============================================================================
# Purpose: Vulnerable CTF Target
# Theme: White/Yellow Corporate Industrial
# =============================================================================

app = Flask(__name__)
app.secret_key = 'TEGH_IND_SECRET_KEY_2025'

# --- DATABASE ---
DB_FILE = 'tegh_industries.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db()
        c = conn.cursor()
        
        # 1. Users
        c.execute('DROP TABLE IF EXISTS users')
        c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)')
        c.execute("INSERT INTO users VALUES (1, 'admin', 'industrial_titan_99', 'admin')")
        
        # 2. Campaigns (CMS Content)
        c.execute('DROP TABLE IF EXISTS campaigns')
        c.execute('''CREATE TABLE campaigns 
                     (id INTEGER PRIMARY KEY, title TEXT, client TEXT, budget TEXT, status TEXT, 
                      image TEXT, description TEXT, roi TEXT, is_public INTEGER)''')
        
        campaigns_data = [
            (1, 'Project Titan Launch', 'DefenseCorp', '$50M', 'Active', 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&q=80&w=800', 'Strategic rollout of next-gen defense logistics.', '150%', 1),
            (2, 'Eco-Synthesis', 'GreenFuture', '$12M', 'Completed', 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&q=80&w=800', 'Global sustainability initiative awareness.', '320%', 1),
            (3, 'Global Summit 2026', 'WorldBank', '$5M', 'Planning', 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=800', 'Coordinate exclusive invite-only summit marketing.', 'N/A', 1),
            (4, 'Black Operations IV', 'Unknown', 'Classified', 'Redacted', 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=800', 'Classified Operation: Deployment of autonomous kinetic tracking assets in Sector 7. Access requires Level 5 clearance.', 'N/A', 0),
            (5, 'Quantum Grid', 'TechGiant', '$750M', 'Active', 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=800', 'National energy grid modernization campaign.', '210%', 1),
            (6, 'Deep Sea Mining', 'ResourceCo', '$80M', 'Active', 'https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?auto=format&fit=crop&q=80&w=800', 'Extraction technology public relations.', '500%', 1)
        ]
        c.executemany('INSERT INTO campaigns VALUES (?,?,?,?,?,?,?,?,?)', campaigns_data)

        # 3. Inventory (New)
        c.execute('DROP TABLE IF EXISTS inventory')
        c.execute('CREATE TABLE inventory (id INTEGER PRIMARY KEY, item_name TEXT, category TEXT, quantity INTEGER, location TEXT)')
        inventory_data = [
            (1, 'Titanium Casing', 'Raw Material', 500, 'Warehouse A'),
            (2, 'Guidance Chips v9', 'Electronics', 1200, 'Vault B'),
            (3, 'Hydraulic Fluid', 'Fluids', 5000, 'Tank 4'),
            (4, 'Drone Motors (Brushless)', 'Electronics', 450, 'Warehouse A')
        ]
        c.executemany('INSERT INTO inventory VALUES (?,?,?,?,?)', inventory_data)

        # 4. Personnel (New)
        c.execute('DROP TABLE IF EXISTS personnel')
        c.execute('CREATE TABLE personnel (id INTEGER PRIMARY KEY, name TEXT, clearance TEXT, assignment TEXT)')
        personnel_data = [
            (1, 'J. Smith', 'L3', 'Logistics'),
            (2, 'A. Doe', 'L4', 'R&D'),
            (3, 'M. Chen', 'L5', 'Black Ops'),
            (4, 'SYSTEM_ADMIN', 'L10', 'Root')
        ]
        c.executemany('INSERT INTO personnel VALUES (?,?,?,?)', personnel_data)

        conn.commit()

if not os.path.exists(DB_FILE):
    init_db()

# --- SECURITY & HEADERS ---

@app.after_request
def add_headers(response):
    response.headers['Server'] = 'TeghServer/4.0 (RedHat)'
    response.headers['X-Powered-By'] = 'TeghFrame v1.2'
    if 'Origin' in request.headers:
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# --- SECURITY FILTER (WAF - Cloudflare Simulation) ---
def security_filter(raw_data):
    # WAF Logic: Checks RAW bytes.
    decoded = raw_data.decode('utf-8', errors='ignore').lower()
    blacklist = [
        '<script>', 'javascript:', 'vbscript:', 'onload', 'onmouseover', 'eval(', 'alert(', 
        'union select', 'union all select' 
    ]
    for bad in blacklist:
        if bad in decoded:
            return False
    return True

# --- ROUTE HANDLERS ---

@app.route('/')
def index():
    user = session.get('user_id')
    return render_template_string(HTML_TEMPLATE, user=user)

@app.route('/dashboard')
def dashboard():
    user = session.get('user_id')
    if not user:
        return redirect('/login')
    return render_template_string(DASHBOARD_TEMPLATE, user=user)

# --- MARKETING / CAMPAIGNS ---

@app.route('/campaign/<int:id>')
def view_campaign(id):
    # IDOR Vulnerability
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM campaigns WHERE id=?", (id,))
    row = c.fetchone()
    if row:
        return render_template_string(DETAIL_TEMPLATE, c=dict(row))
    return "Asset not found", 404

@app.route('/api/search')
def api_search():
    # WAF Check
    if not security_filter(request.query_string):
        return render_template_string(CLOUDFLARE_BLOCK_TEMPLATE), 403

    # SQL Injection & Reflected XSS
    q = request.args.get('q', '')
    conn = get_db()
    c = conn.cursor()
    try:
        if q:
            # SQL Injection Vulnerability
            sql = f"SELECT * FROM campaigns WHERE title LIKE '%{q}%' AND is_public=1"
            c.execute(sql)
            rows = c.fetchall()
            if not rows:
                return jsonify({'results': [], 'message': f"No data found for: {q}"})
            return jsonify({'results': [dict(r) for r in rows]})
        else:
            c.execute("SELECT * FROM campaigns WHERE is_public=1")
            rows = c.fetchall()
            return jsonify({'results': [dict(r) for r in rows]})
    except Exception as e:
        # Error Disclosure AND Reflected XSS
        return jsonify({'error': str(e), 'message': f"System Error processing: {q}"}), 500

# --- FUNCTIONAL FEATURES (NEW) ---

@app.route('/inventory')
def inventory():
    # Vulnerability: SQL Injection potential via 'cat' parameter
    cat = request.args.get('cat', '')
    conn = get_db()
    c = conn.cursor()
    if cat:
        # Simulating secure query for now, but user can ask to make it vulnerable later
        c.execute("SELECT * FROM inventory WHERE category LIKE ?", (f'%{cat}%',))
    else:
        c.execute("SELECT * FROM inventory")
    items = c.fetchall()
    return render_template_string(INVENTORY_TEMPLATE, items=[dict(i) for i in items])

@app.route('/personnel')
def personnel():
    # Vulnerability: IDOR in 'view' details?
    user = session.get('user_id')
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM personnel")
    staff = c.fetchall()
    return render_template_string(PERSONNEL_TEMPLATE, staff=[dict(s) for s in staff], user=user)

@app.route('/api/grid/status')
def grid_status():
    # Function 1: Grid Status
    statuses = ['NOMINAL', 'PEAK_LOAD', 'MAINTENANCE', 'REROUTING']
    return jsonify({
        'status': random.choice(statuses),
        'load': f"{random.randint(40, 98)}%",
        'frequency': f"{random.uniform(49.8, 50.2):.2f}Hz",
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/fleet/coords')
def fleet_coords():
    # Function 2: Fleet Tracking
    assets = []
    for i in range(5):
        assets.append({
            'callsign': f"UAV-{random.randint(100,999)}",
            'lat': random.uniform(-90, 90),
            'lng': random.uniform(-180, 180),
            'fuel': f"{random.randint(10,100)}%"
        })
    return jsonify({'active_assets': assets})

@app.route('/api/weather')
def weather():
    # Function 3: Weather Data
    conditions = ['Clear', 'Turbulence', 'Storm', 'Low Visibility']
    return jsonify({'sector': '7G', 'condition': random.choice(conditions), 'wind': f"{random.randint(0,100)} km/h"})

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    # Function 4: Secure Transfer (Dummy)
    if request.method == 'POST':
        return "<h1>File Encrypted & Uploaded to Secure Vault.</h1><a href='/dashboard'>Return</a>"
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head><title>Secure Transfer</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-50 flex items-center justify-center h-screen">
        <form method="POST" enctype="multipart/form-data" class="bg-white p-8 border border-gray-200 shadow-lg text-center">
            <h2 class="text-xl font-bold mb-4">Secure Uplink</h2>
            <input type="file" class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-yellow-50 file:text-yellow-700 hover:file:bg-yellow-100 mb-4"/>
            <button class="bg-yellow-500 text-white px-4 py-2 font-bold uppercase transition hover:bg-yellow-600">Transmit</button>
        </form>
    </body></html>
    """)

# --- UTILITY ENDPOINTS ---

@app.route('/redirect')
def campaign_redirect():
    target = request.args.get('url')
    if target: return redirect(target)
    return "Destination required"

@app.route('/api/track')
def tracking_pixel():
    source = request.args.get('source', 'direct')
    resp = make_response(jsonify({'status': 'logged'}))
    try: resp.headers['X-Campaign-Source'] = source
    except: pass
    return resp

@app.route('/assets/analytics.js')
def analytics_js():
    host = request.headers.get('X-Forwarded-Host', request.host)
    js_content = f"""var _ti_base = "http://{host}/api/"; console.log("Telemetry: " + _ti_base);"""
    resp = make_response(js_content)
    resp.headers['Content-Type'] = 'application/javascript'
    resp.headers['Cache-Control'] = 'public, max-age=3600'
    return resp

@app.route('/contact', methods=['POST'])
def contact_form():
    if not security_filter(request.get_data()): return render_template_string(CLOUDFLARE_BLOCK_TEMPLATE), 403
    time.sleep(0.5) # DoS
    data = request.form
    msg = data.get('message', '')
    sanitized_msg = msg.replace('<script>', '') 
    if 'preview' in msg.lower(): return f"<h1>NOTE PREVIEW</h1><hr>{sanitized_msg}"
    return redirect('/')

@app.route('/newsletter', methods=['POST'])
def newsletter():
    if not security_filter(request.get_data()): return render_template_string(CLOUDFLARE_BLOCK_TEMPLATE), 403
    return f"<h1>Subscribed</h1><a href='/'>Return</a>"

@app.route('/api/process_report', methods=['POST'])
def process_report():
    xml_data = request.data
    try:
        root = ET.fromstring(xml_data)
        report_id = root.find('id').text if root.find('id') is not None else 'UNKNOWN'
        content = root.find('content').text if root.find('content') is not None else ''
        return jsonify({'status': 'processed', 'id': report_id})
    except Exception as e:
        return jsonify({'error': 'Invalid XML', 'details': str(e)}), 400

@app.route('/backups/')
@app.route('/backups/<path:filename>')
def list_backups(filename=None):
    if filename: return f"Encrypted content..."
    return "<h1>Index of /backups/</h1><hr><pre>db_backup.sql</pre>"

@app.route('/.git/')
def git_expose():
    return "ref: refs/heads/main\n"

# --- AUTH ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        if user:
            session['user_id'] = user['username']
            return redirect('/')
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Authentication Failed.")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/about')
def about(): return render_template_string(ABOUT_TEMPLATE)

@app.route('/careers', methods=['GET', 'POST'])
def careers():
    if request.method == 'POST': return render_template_string(CAREERS_TEMPLATE, success="Application Received.")
    return render_template_string(CAREERS_TEMPLATE)

# =============================================================================
# TEMPLATES (WHITE & YELLOW THEME)
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Tegh Industries | Global Defense Grid</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Chakra Petch', sans-serif; background-color: #ffffff; color: #111111; }
        .nav-link { color: #4b5563; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; transition: 0.3s; }
        .nav-link:hover { color: #ca8a04; }
        .btn-primary { background-color: #eab308; color: white; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.75rem 2rem; transition: 0.3s; }
        .btn-primary:hover { background-color: #ca8a04; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .glass-header { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid #e5e7eb; }
        .feature-card { border: 1px solid #e5e7eb; background: white; transition: 0.3s; }
        .feature-card:hover { border-color: #eab308; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); transform: translateY(-2px); }
    </style>
</head>
<body class="antialiased bg-gray-50">

    <!-- Navbar -->
    <nav class="fixed w-full z-50 glass-header">
        <div class="max-w-7xl mx-auto px-6 h-20 flex justify-between items-center">
            <div class="flex items-center gap-3 cursor-pointer" onclick="window.location.href='/'">
                <i class="fas fa-cube text-3xl text-yellow-500"></i>
                <div class="leading-none">
                    <h1 class="text-xl font-bold text-gray-900 tracking-wider">TEGH</h1>
                    <span class="text-[0.6rem] font-bold text-gray-500 tracking-[0.3em] uppercase block">INDUSTRIES</span>
                </div>
            </div>
            <div class="hidden md:flex gap-8 items-center">
                <a href="/inventory" class="nav-link text-xs">Inventory</a>
                <a href="/personnel" class="nav-link text-xs">Personnel</a>
                <a href="/about" class="nav-link text-xs">About</a>
                <a href="/careers" class="nav-link text-xs">Careers</a>
                {% if user %}
                    <span class="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-1">{{ user }}</span>
                    <a href="/dashboard" class="nav-link text-xs !text-yellow-600">Dashboard</a>
                    <a href="/logout" class="nav-link text-xs">Sign Out</a>
                {% else %}
                    <a href="/login" class="btn-primary text-xs !py-3">Portal Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <!-- Hero -->
    <header class="pt-32 pb-20 px-6 bg-white relative">
        <div class="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
            <div>
                <div class="inline-block bg-yellow-100 text-yellow-800 text-xs font-bold px-3 py-1 mb-6 uppercase tracking-widest">Global Defense Infrastructure</div>
                <h1 class="text-6xl font-bold text-gray-900 leading-tight mb-6">
                    ENGINEERING <br> <span class="text-yellow-500">SUPERIORITY</span>
                </h1>
                <p class="text-xl text-gray-500 mb-10 max-w-lg leading-relaxed">
                    Advanced logistics, kinetic tracking, and resource extraction solutions for a modernized world.
                </p>
                <div class="flex gap-4">
                    <button class="btn-primary" onclick="window.location.href='/about'">Mission Brief</button>
                    <button class="border border-gray-300 text-gray-600 px-8 py-3 font-bold uppercase text-xs hover:border-yellow-500 transition">View Contracts</button>
                </div>
            </div>
            <div class="relative bg-gray-100 h-96 w-full overflow-hidden rounded-sm">
                <img src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80" class="object-cover w-full h-full grayscale opacity-80 hover:grayscale-0 transition duration-700">
            </div>
        </div>
    </header>

    <!-- Search / Stats Bar -->
    <div class="bg-gray-900 py-12 text-white">
        <div class="max-w-7xl mx-auto px-6">
            <div class="flex flex-col md:flex-row gap-8 items-center justify-between">
                <div class="w-full md:w-1/2 relative">
                    <input type="text" id="search-input" placeholder="SEARCH CONTRACT DATABASE..." 
                        class="w-full bg-gray-800 border-none p-5 text-white focus:ring-2 focus:ring-yellow-500 placeholder-gray-500 font-mono text-sm">
                    <button onclick="searchProjects()" class="absolute right-3 top-3 text-yellow-500 font-bold text-xs uppercase px-4 py-2 hover:bg-gray-700">Scan</button>
                </div>
                <div class="flex gap-12 text-center">
                    <div>
                        <div class="text-3xl font-bold text-yellow-500">98.4%</div>
                        <div class="text-xs text-gray-500 uppercase tracking-widest">Grid Uptime</div>
                    </div>
                    <div>
                        <div class="text-3xl font-bold text-yellow-500">142</div>
                        <div class="text-xs text-gray-500 uppercase tracking-widest">Active nodes</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Results Area -->
    <section class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-6">
            <h3 class="text-2xl font-bold text-gray-900 uppercase mb-12 border-l-4 border-yellow-500 pl-4">Active Operations</h3>
            <div id="results-area" class="grid md:grid-cols-3 gap-8">
                <!-- JS LOADS CONTENT HERE -->
            </div>
        </div>
    </section>

    <footer class="bg-white border-t border-gray-200 py-12">
        <div class="max-w-7xl mx-auto px-6 flex justify-between items-center text-xs text-gray-400 uppercase tracking-widest">
            <div>&copy; 2026 Tegh Industries. All Rights Reserved.</div>
            <div class="space-x-6">
                <a href="/redirect?url=/privacy" class="hover:text-yellow-600">Privacy</a>
                <a href="/redirect?url=/legal" class="hover:text-yellow-600">Legal</a>
            </div>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', searchProjects);
        async function searchProjects() {
            const q = document.getElementById('search-input').value;
            const container = document.getElementById('results-area');
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                
                if (res.status === 500) {
                     if (data.message) {
                         container.innerHTML = `<div class="col-span-full bg-red-50 border-l-4 border-red-500 p-6 text-red-700 font-mono text-sm">
                            <strong>SYSTEM ERROR:</strong> ${data.message}
                            <div class="mt-2 text-xs text-red-400">${data.error}</div>
                         </div>`;
                     }
                     return;
                }
                
                if (data.results && data.results.length > 0) {
                    container.innerHTML = data.results.map(p => `
                        <div class="feature-card group cursor-pointer" onclick="window.location.href='/campaign/${p.id}'">
                            <div class="h-48 overflow-hidden relative bg-gray-200">
                                <img src="${p.image}" class="w-full h-full object-cover transition duration-700 group-hover:scale-110 grayscale group-hover:grayscale-0">
                                <div class="absolute top-4 right-4 bg-yellow-500 text-white text-[0.6rem] font-bold px-2 py-1 uppercase">${p.status}</div>
                            </div>
                            <div class="p-6">
                                <div class="text-xs text-gray-400 font-mono mb-2">${p.client}</div>
                                <h3 class="text-lg font-bold text-gray-900 mb-2 uppercase group-hover:text-yellow-600 transition">${p.title}</h3>
                                <div class="w-12 h-1 bg-gray-200 mt-4 group-hover:bg-yellow-500 transition"></div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="col-span-full text-center text-gray-400 py-12">No operations found matching criteria.</div>';
                }
            } catch(e) {}
        }
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Command Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Chakra Petch', sans-serif; }</style>
</head>
<body class="bg-gray-100 text-gray-800">
    <div class="flex h-screen">
        <!-- Sidebar -->
        <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div class="p-6 border-b border-gray-100">
                <h1 class="font-bold text-gray-900 tracking-wider">TEGH <span class="text-yellow-500">CMD</span></h1>
            </div>
            <nav class="flex-1 p-4 space-y-2">
                <a href="#" class="block p-3 bg-yellow-50 text-yellow-700 font-bold text-sm rounded-sm">Overview</a>
                <a href="/inventory" class="block p-3 text-gray-600 hover:bg-gray-50 text-sm font-bold rounded-sm">Inventory</a>
                <a href="/personnel" class="block p-3 text-gray-600 hover:bg-gray-50 text-sm font-bold rounded-sm">Personnel</a>
                <a href="/upload" class="block p-3 text-gray-600 hover:bg-gray-50 text-sm font-bold rounded-sm">Secure Transfer</a>
                <a href="/" class="block p-3 text-gray-600 hover:bg-gray-50 text-sm font-bold rounded-sm">Public Site</a>
            </nav>
            <div class="p-6 border-t border-gray-100">
                <div class="text-xs text-gray-400 uppercase">Logged in as</div>
                <div class="font-bold text-sm">{{ user }}</div>
                <a href="/logout" class="text-xs text-red-500 hover:underline mt-2 block">Terminate Session</a>
            </div>
        </div>
        
        <!-- Main -->
        <div class="flex-1 overflow-y-auto p-12">
            <h2 class="text-3xl font-bold text-gray-900 mb-8">System Overview</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                <!-- Widget 1: Grid -->
                <div class="bg-white p-6 border border-gray-200 shadow-sm rounded-sm">
                    <div class="text-xs text-gray-400 uppercase mb-2">Power Grid</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1" id="grid-status">--</div>
                    <div class="text-xs text-green-500 font-mono" id="grid-load">Load: --%</div>
                </div>
                <!-- Widget 2: Weather -->
                <div class="bg-white p-6 border border-gray-200 shadow-sm rounded-sm">
                    <div class="text-xs text-gray-400 uppercase mb-2">Local Atmospheric</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1" id="weather-cond">--</div>
                    <div class="text-xs text-gray-500 font-mono" id="weather-wind">Wind: --</div>
                </div>
                <!-- Widget 3: Assets -->
                <div class="bg-white p-6 border border-gray-200 shadow-sm rounded-sm">
                    <div class="text-xs text-gray-400 uppercase mb-2">Active Assets</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1" id="asset-count">5</div>
                    <div class="text-xs text-gray-500 font-mono">UAV Squad A</div>
                </div>
            </div>

            <!-- Fleet Table -->
            <div class="bg-white border border-gray-200 shadow-sm rounded-sm mb-12">
                <div class="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900">Live Telemetry</h3>
                    <button class="bg-gray-900 text-white text-xs px-3 py-1 uppercase rounded-sm" onclick="updateStats()">Refresh</button>
                </div>
                <div class="p-6">
                    <table class="w-full text-sm text-left">
                        <thead>
                            <tr class="text-gray-400 uppercase text-xs border-b border-gray-100">
                                <th class="pb-3">Callsign</th>
                                <th class="pb-3">Coordinates</th>
                                <th class="pb-3">Fuel</th>
                                <th class="pb-3">Status</th>
                            </tr>
                        </thead>
                        <tbody id="fleet-rows" class="font-mono text-gray-600">
                            <!-- JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function updateStats() {
            try {
                // Grid
                const r1 = await fetch('/api/grid/status');
                const d1 = await r1.json();
                document.getElementById('grid-status').innerText = d1.status;
                document.getElementById('grid-load').innerText = `Load: ${d1.load} / ${d1.frequency}`;
                
                // Weather
                const r2 = await fetch('/api/weather');
                const d2 = await r2.json();
                document.getElementById('weather-cond').innerText = d2.condition;
                document.getElementById('weather-wind').innerText = `Wind: ${d2.wind}`;

                // Fleet
                const r3 = await fetch('/api/fleet/coords');
                const d3 = await r3.json();
                const rows = d3.active_assets.map(a => `
                    <tr class="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                        <td class="py-3 font-bold text-gray-900">${a.callsign}</td>
                        <td class="py-3">${a.lat.toFixed(4)}, ${a.lng.toFixed(4)}</td>
                        <td class="py-3 text-yellow-600">${a.fuel}</td>
                        <td class="py-3 text-green-600">ONLINE</td>
                    </tr>
                `).join('');
                document.getElementById('fleet-rows').innerHTML = rows;
            } catch(e) {}
        }
        updateStats();
        setInterval(updateStats, 5000);
    </script>
</body>
</html>
"""

INVENTORY_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><title>Inventory</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 p-12 font-sans">
    <div class="max-w-4xl mx-auto">
        <div class="flex justify-between mb-8">
            <h1 class="text-3xl font-bold text-gray-900">Inventory Management</h1>
            <a href="/dashboard" class="text-yellow-600 font-bold hover:underline">Back to Dashboard</a>
        </div>
        <div class="bg-white p-6 shadow-sm border border-gray-200 mb-8">
            <form class="flex gap-4">
                <input type="text" name="cat" placeholder="Filter by Category..." class="flex-1 p-3 border border-gray-300">
                <button class="bg-gray-900 text-white px-6 font-bold uppercase">Filter</button>
            </form>
        </div>
        <div class="bg-white shadow-sm border border-gray-200">
            <table class="w-full text-left">
                <thead class="bg-gray-100 text-gray-600 uppercase text-xs">
                    <tr><th class="p-4">Item</th><th class="p-4">Category</th><th class="p-4">Qty</th><th class="p-4">Location</th></tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                    {% for i in items %}
                    <tr>
                        <td class="p-4 font-bold text-gray-900">{{ i.item_name }}</td>
                        <td class="p-4 text-gray-600">{{ i.category }}</td>
                        <td class="p-4 text-gray-600">{{ i.quantity }}</td>
                        <td class="p-4 text-gray-500 text-xs font-mono">{{ i.location }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body></html>
"""

PERSONNEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><title>Personnel</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 p-12 font-sans">
    <div class="max-w-4xl mx-auto">
        <div class="flex justify-between mb-8">
            <h1 class="text-3xl font-bold text-gray-900">Personnel Directory</h1>
            <a href="/dashboard" class="text-yellow-600 font-bold hover:underline">Back to Dashboard</a>
        </div>
        <div class="grid grid-cols-2 gap-4">
            {% for s in staff %}
            <div class="bg-white p-6 border border-gray-200 flex justify-between items-center shadow-sm">
                <div>
                    <div class="font-bold text-lg text-gray-900">{{ s.name }}</div>
                    <div class="text-sm text-gray-500">{{ s.assignment }}</div>
                </div>
                <div class="bg-gray-100 text-gray-600 text-xs font-bold px-3 py-1 rounded">CLEARANCE: {{ s.clearance }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
</body></html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ c.title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Chakra Petch', sans-serif; }</style>
</head>
<body class="bg-gray-50">
    <nav class="bg-white border-b border-gray-200 p-6">
        <div class="max-w-7xl mx-auto flex justify-between">
            <div class="font-bold text-xl uppercase">TEGH <span class="text-yellow-500">IND</span></div>
            <a href="/" class="text-sm font-bold text-gray-600 hover:text-yellow-600 uppercase">Back</a>
        </div>
    </nav>
    <div class="max-w-5xl mx-auto py-12 px-6">
        <div class="bg-white border border-gray-200 shadow-lg overflow-hidden">
            <div class="h-80 bg-gray-200 relative">
                <img src="{{ c.image }}" class="w-full h-full object-cover">
                <div class="absolute inset-0 bg-black/30"></div>
                <div class="absolute bottom-8 left-8 text-white">
                    <div class="bg-yellow-500 text-black text-xs font-bold inline-block px-2 py-1 mb-2 uppercase">Status: {{ c.status }}</div>
                    <h1 class="text-5xl font-bold uppercase shadow-sm">{{ c.title }}</h1>
                </div>
            </div>
            <div class="p-8 grid md:grid-cols-3 gap-12">
                <div class="md:col-span-2">
                    <h3 class="text-yellow-600 font-bold uppercase text-xs mb-4">Operational Briefing</h3>
                    <p class="text-gray-700 text-lg leading-relaxed mb-8">{{ c.description }}</p>
                    
                    <div class="bg-gray-50 p-6 border border-gray-200">
                        <h4 class="font-bold text-gray-900 text-sm uppercase mb-3">Internal Comm Log</h4>
                        <form action="/contact" method="POST">
                            <textarea name="message" class="w-full bg-white border border-gray-300 p-3 text-sm focus:border-yellow-500 outline-none" rows="3" placeholder="Enter secure notes..."></textarea>
                            <div class="flex justify-end gap-3 mt-3">
                                <button name="preview" value="true" class="text-xs text-gray-500 hover:underline uppercase">Preview</button>
                                <button class="bg-gray-900 text-white text-xs font-bold px-4 py-2 uppercase">Log Entry</button>
                            </div>
                        </form>
                    </div>
                </div>
                <div class="space-y-6">
                    <div class="p-4 bg-gray-50 border border-gray-100">
                        <div class="text-xs text-gray-400 uppercase">Client</div>
                        <div class="font-bold text-gray-900">{{ c.client }}</div>
                    </div>
                    <div class="p-4 bg-gray-50 border border-gray-100">
                         <div class="text-xs text-gray-400 uppercase">Budget</div>
                         <div class="font-bold text-gray-900 font-mono">{{ c.budget }}</div>
                    </div>
                    <div class="p-4 bg-gray-50 border border-gray-100">
                         <div class="text-xs text-gray-400 uppercase">ROI</div>
                         <div class="font-bold text-yellow-600 font-mono">{{ c.roi }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><title>Login</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-100 flex items-center justify-center h-screen">
    <div class="w-full max-w-sm bg-white p-8 border border-gray-200 shadow-xl">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-bold text-gray-900">SECURE ACCESS</h1>
            <p class="text-xs text-yellow-600 font-bold uppercase tracking-widest">Authorized Personnel Only</p>
        </div>
        {% if error %}<div class="bg-red-50 text-red-600 text-xs p-3 mb-4 text-center border border-red-200">{{ error }}</div>{% endif %}
        <form method="POST" class="space-y-4">
            <input type="text" name="username" placeholder="OPERATIVE ID" class="w-full border-gray-300 border p-3 text-sm outline-none focus:border-yellow-500">
            <input type="password" name="password" placeholder="ACCESS KEY" class="w-full border-gray-300 border p-3 text-sm outline-none focus:border-yellow-500">
            <button class="w-full bg-yellow-500 text-white font-bold py-3 uppercase hover:bg-yellow-600 transition">Authenticate</button>
        </form>
        <div class="mt-6 text-center">
            <a href="/" class="text-xs text-gray-400 hover:text-gray-600 uppercase">Return to Public Grid</a>
        </div>
    </div>
</body>
</html>
"""

CAREERS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><title>Careers</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-white font-sans text-gray-900">
    <div class="max-w-4xl mx-auto px-6 py-20">
        <a href="/" class="text-yellow-600 font-bold text-xs uppercase mb-8 block">&larr; Back to Home</a>
        <h1 class="text-5xl font-bold mb-4">Join the <span class="text-yellow-500">Vanguard</span></h1>
        <p class="text-gray-500 mb-12 text-lg">We are looking for elite engineers to build the future of defense.</p>
        {% if success %}<div class="bg-green-50 text-green-700 p-4 mb-8 border border-green-200">{{ success }}</div>{% endif %}
        <div class="space-y-6">
            <div class="border border-gray-200 p-8 hover:border-yellow-500 transition">
                <h3 class="text-xl font-bold mb-2">Systems Architect</h3>
                <p class="text-gray-500 mb-4">Design scalable kinetic tracking grids.</p>
                <form method="POST"><button class="text-yellow-600 font-bold uppercase text-xs">Apply Now</button></form>
            </div>
            <div class="border border-gray-200 p-8 hover:border-yellow-500 transition">
                 <h3 class="text-xl font-bold mb-2">Field Operative</h3>
                 <p class="text-gray-500 mb-4">On-site logistics in Sector 7.</p>
                 <form method="POST"><button class="text-yellow-600 font-bold uppercase text-xs">Apply Now</button></form>
            </div>
        </div>
    </div>
</body></html>
"""

ABOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head><title>About</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 font-sans text-gray-900">
    <div class="max-w-3xl mx-auto px-6 py-20">
        <a href="/" class="text-yellow-600 font-bold text-xs uppercase mb-8 block">&larr; Back to Home</a>
        <h1 class="text-4xl font-bold mb-8 uppercase border-b-4 border-yellow-500 inline-block">Mission Parameters</h1>
        <div class="prose lg:prose-xl text-gray-600">
            <p>Tegh Industries is the world's leading provider of autonomous defense infrastructure. We do not just build; we secure the future. Our operations span 14 countries, providing critical logistical support to sovereign nations.</p>
            <p>From deep-sea mining to orbital defense, our engineering creates the backbone of modern civilization.</p>
        </div>
        <div class="grid grid-cols-2 gap-8 mt-12">
            <div class="bg-white p-6 shadow-sm">
                <div class="text-3xl font-bold text-gray-900">24/7</div>
                <div class="text-xs text-gray-400 uppercase">Readiness</div>
            </div>
            <div class="bg-white p-6 shadow-sm">
                <div class="text-3xl font-bold text-gray-900">14</div>
                <div class="text-xs text-gray-400 uppercase">Global Hubs</div>
            </div>
        </div>
    </div>
</body></html>
"""

CLOUDFLARE_BLOCK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en-US">
<head>
    <title>Access Denied</title>
    <style>body{font-family:sans-serif;background:#fff;color:#333;text-align:center;padding:50px}h1{color:#e00}</style>
</head>
<body>
    <h1>Security Check Failed</h1>
    <p>Your request was flagged by the Tegh Industries WAF.</p>
    <hr>
    <p>Ray ID: 1234567890</p>
</body>
</html>
"""

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
