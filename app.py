from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import threading
import json
from tracker_manager import TrackerManager
from link_verifier import LinkVerifier
from site_inspector import SiteInspector
from automation.engine import create_batch_job, ACTIVE_JOBS
from automation.audit_engine import get_audit_state, run_mass_audit
from automation.learn_sites import create_learning_job, ACTIVE_LEARNING_JOBS

app = Flask(__name__, template_folder='templates', static_folder='static')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

tracker_mgr = TrackerManager()
link_verifier = LinkVerifier(tracker_mgr)
site_inspector = SiteInspector(tracker_mgr)

# Global status for tasks
VERIFY_TASKS = {}
INSPECTOR_TASKS = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tracker', methods=['GET'])
def get_tracker():
    try:
        data = tracker_mgr.get_data()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tracker/campaign', methods=['POST'])
def add_campaign():
    req = request.json or {}
    name = req.get('name')
    if not name:
        return jsonify({"status": "error", "message": "Campaign name is required"}), 400
    
    ok, msg = tracker_mgr.add_campaign(name)
    if ok:
        return jsonify({"status": "success", "message": msg})
    return jsonify({"status": "error", "message": msg}), 400

@app.route('/api/tracker/update', methods=['POST'])
def update_cell():
    req = request.json or {}
    row_id = req.get('row_id')
    campaign = req.get('campaign')
    link = req.get('link', '')
    
    if not row_id or not campaign:
        return jsonify({"status": "error", "message": "Row ID and campaign required"}), 400
        
    ok, msg = tracker_mgr.update_cell(row_id, campaign, link)
    if ok:
        return jsonify({"status": "success", "message": msg})
    return jsonify({"status": "error", "message": msg}), 400

@app.route('/api/upload-media', methods=['POST'])
def upload_media():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    
    return jsonify({
        "status": "success",
        "filepath": filepath,
        "filename": file.filename
    })

@app.route('/api/upload/start', methods=['POST'])
def start_upload():
    req = request.json or {}
    campaign_name = req.get('campaign_name', 'Kampanye Auto')
    target_sites = req.get('target_sites', [])
    payload = {
        "title": req.get('title', 'Auto Post Content'),
        "content_text": req.get('content_text', ''),
        "file_path": req.get('file_path'),
        "visible_browser": req.get('visible_browser', True),
        "tokens": req.get('tokens', {})
    }
    
    if not target_sites:
        return jsonify({"status": "error", "message": "No target sites specified"}), 400
        
    job_id = create_batch_job(campaign_name, target_sites, payload)
    return jsonify({
        "status": "success",
        "job_id": job_id,
        "message": f"Batch upload job '{job_id}' started."
    })

@app.route('/api/upload/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = ACTIVE_JOBS.get(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404
        
    percent = round((job.completed / job.total * 100), 1) if job.total > 0 else 0
    return jsonify({
        "job_id": job.job_id,
        "campaign_name": job.campaign_name,
        "status": job.status,
        "completed": job.completed,
        "total": job.total,
        "percent": percent,
        "success_count": job.success_count,
        "fail_count": job.fail_count,
        "current_site": job.current_site,
        "current_tier": job.current_tier,
        "logs": job.logs,
        "results": job.results
    })

@app.route('/api/learn/hints/start', methods=['POST'])
def start_hint_generation():
    req = request.json or {}
    target_sites = req.get('target_sites', [])
    if not target_sites:
        return jsonify({"status": "error", "message": "No target sites specified"}), 400
        
    from automation.learn_sites import create_hint_job
    job_id = create_hint_job(target_sites)
    return jsonify({
        "status": "success",
        "job_id": job_id,
        "message": f"Phase A (Hint Generation) started for {len(target_sites)} sites."
    })

@app.route('/api/learn/execute/start', methods=['POST'])
def start_learning_execution():
    req = request.json or {}
    target_sites = req.get('target_sites', [])
    if not target_sites:
        return jsonify({"status": "error", "message": "No target sites specified"}), 400
        
    job_id = create_learning_job(target_sites)
    return jsonify({
        "status": "success",
        "job_id": job_id,
        "message": f"Phase B (Playwright Traversal) started for {len(target_sites)} sites."
    })

@app.route('/api/learn/hints', methods=['GET', 'POST'])
def manage_hints():
    hints_file = os.path.join(os.path.dirname(__file__), 'search_hints.json')
    if request.method == 'GET':
        if not os.path.exists(hints_file):
            return jsonify({})
        with open(hints_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    elif request.method == 'POST':
        data = request.json or {}
        with open(hints_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success", "message": "Hints saved successfully"})

@app.route('/api/learn/knowledge', methods=['GET'])
def get_site_knowledge():
    knowledge_file = os.path.join(os.path.dirname(__file__), 'automation', 'site_knowledge.json')
    if not os.path.exists(knowledge_file):
        return jsonify({})
    try:
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/learn/job/<job_id>', methods=['GET'])
def get_learning_status(job_id):
    job = ACTIVE_LEARNING_JOBS.get(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404
        
    percent = round((job.completed / job.total * 100), 1) if job.total > 0 else 0
    return jsonify({
        "job_id": job.job_id,
        "status": job.status,
        "completed": job.completed,
        "total": job.total,
        "percent": percent,
        "current_site": job.current_site,
        "logs": job.logs,
        "results": job.results
    })

@app.route('/api/verify-links', methods=['POST'])
def run_link_verifier():
    req = request.json or {}
    campaign_name = req.get('campaign_name')
    
    task_id = str(uuid.uuid4())[:8]
    VERIFY_TASKS[task_id] = {"status": "RUNNING", "progress": "Checking URLs..."}
    
    def worker():
        res = link_verifier.verify_campaign(campaign_name=campaign_name)
        VERIFY_TASKS[task_id] = {"status": "COMPLETED", "result": res}

    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()
    
    return jsonify({"status": "success", "task_id": task_id})

@app.route('/api/wakeup-bot', methods=['POST'])
def wakeup_bot():
    try:
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        bat_file = os.path.join(base_dir, "Reset_Lalu_Jalankan_Chrome_Robot.bat")
        
        # Menggunakan os.startfile agar sama persis seperti di-double-click oleh user di Windows
        os.startfile(bat_file)
        return jsonify({"status": "success", "message": "Chrome Robot berhasil dibangunkan! Silakan cek taskbar Anda."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/verify-status/<task_id>', methods=['GET'])
def get_verify_status(task_id):
    task = VERIFY_TASKS.get(task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    return jsonify(task)

@app.route('/api/inspector/data', methods=['GET'])
def get_inspector_data():
    data = site_inspector.load_cached_capabilities()
    return jsonify({"status": "success", "data": data})

@app.route('/api/inspector/run', methods=['POST'])
def run_inspector_audit():
    task_id = str(uuid.uuid4())[:8]
    INSPECTOR_TASKS[task_id] = {"status": "RUNNING"}

    def worker():
        data = site_inspector.run_full_audit()
        INSPECTOR_TASKS[task_id] = {"status": "COMPLETED", "result": data}

    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

    return jsonify({"status": "success", "task_id": task_id})

@app.route('/api/inspector/status/<task_id>', methods=['GET'])
def get_inspector_status(task_id):
    task = INSPECTOR_TASKS.get(task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    return jsonify(task)

import sys
sys.stdout.reconfigure(encoding='utf-8')

@app.route('/api/audit/data', methods=['GET'])
def get_audit_data():
    return jsonify({"status": "success", "data": get_audit_state()})

@app.route('/api/audit/run', methods=['POST'])
def start_audit():
    data = tracker_mgr.get_data()
    rows = data.get("rows", [])
    
    # URL Auto-Router (Sync with engine.py)
    auto_router = {
        "medium.com": "https://medium.com/new-story",
        "tumblr.com": "https://www.tumblr.com/new",
        "wordpress.com": "https://wordpress.com/post",
        "blogger.com": "https://www.blogger.com/post-create.g",
        "hubspot.com": "https://app.hubspot.com/blog/new",
        "livejournal.com": "https://www.livejournal.com/update.bml",
        "weebly.com": "https://www.weebly.com/weebly/main.php",
        "wix.com": "https://manage.wix.com/dashboard"
    }
    
    started = run_mass_audit(rows, auto_router)
    if started:
        return jsonify({"status": "success", "message": "Mass audit started in background."})
    else:
        return jsonify({"status": "error", "message": "An audit is already running."}), 400

if __name__ == '__main__':
    print("Starting AutoPost Matrix Server on http://0.0.0.0:5000 (accessible via http://localhost:5000 or http://127.0.0.1:5000)")
    app.run(host='0.0.0.0', port=5000, debug=False)
