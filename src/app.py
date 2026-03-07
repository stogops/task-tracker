from flask import Flask, jsonify, request, render_template_string
import json
import os

app = Flask(__name__)

# Persistence settings
DATA_FILE = '/data/tasks.json'

tasks = []
workstreams = []
task_id_counter = 1

def load_data():
    global tasks, task_id_counter, workstreams
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                tasks = data.get('tasks', [])
                task_id_counter = data.get('counter', 1)
                workstreams = data.get('workstreams', [
                    {"id": "tasktracker", "title": "Task Tracker"},
                    {"id": "development", "title": "Development"},
                    {"id": "operations", "title": "Operations"}
                ])
                
                # Migration: Ensure every existing task has a workstream_id
                for task in tasks:
                    if 'workstream_id' not in task:
                        task['workstream_id'] = "tasktracker"
                return
        except Exception as e:
            print(f"Error loading data: {e}")
    
    # Default data if file doesn't exist
    tasks = []
    task_id_counter = 1
    workstreams = [
        {"id": "tasktracker", "title": "Task Tracker"},
        {"id": "development", "title": "Development"},
        {"id": "operations", "title": "Operations"}
    ]

def save_data():
    try:
        dir_name = os.path.dirname(DATA_FILE)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'tasks': tasks, 
                'counter': task_id_counter,
                'workstreams': workstreams
            }, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

# Initial load
load_data()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-800 font-sans antialiased p-6">
    <div class="max-w-5xl mx-auto">
        <header class="mb-8">
            <h1 class="text-4xl font-extrabold text-blue-600">Task Tracker</h1>
            <p class="text-gray-500">Consolidated Project Management View</p>
        </header>
        
        <!-- Action Forms -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- Add Task Form -->
            <div class="bg-white shadow-md rounded-lg p-6 border-t-4 border-blue-500">
                <h2 class="text-xl font-bold mb-4">Create New Task</h2>
                <div class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input type="text" id="taskName" placeholder="Task description..." class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                        <input type="text" id="assigneeId" placeholder="Operative ID..." class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                    </div>
                    <div class="flex gap-4">
                        <select id="workstreamSelect" class="flex-1 border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none bg-white"></select>
                        <button onclick="addTask()" class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition font-bold">Add Task</button>
                    </div>
                    <p id="errorMsg" class="text-red-500 hidden text-sm"></p>
                </div>
            </div>

            <!-- Add Workstream Form -->
            <div class="bg-white shadow-md rounded-lg p-6 border-t-4 border-purple-500">
                <h2 class="text-xl font-bold mb-4">Create New Workstream</h2>
                <div class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input type="text" id="wsId" placeholder="ID (e.g. backend-api)" class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                        <input type="text" id="wsTitle" placeholder="Workstream Title" class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                    </div>
                    <button onclick="addWorkstream()" class="w-full bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition font-bold">Add Workstream</button>
                    <p id="wsErrorMsg" class="text-red-500 hidden text-sm"></p>
                </div>
            </div>
        </div>

        <!-- Workstreams Display Area -->
        <div id="workstreamContainers" class="space-y-10">
            <!-- Dynamic Content -->
        </div>
    </div>

    <script>
        const STATUSES = ['todo', 'in-progress', 'done'];
        let workstreams = [];
        let allTasks = [];

        async function fetchWorkstreams() {
            const res = await fetch('/api/workstreams');
            workstreams = await res.json();
            
            // Update the Add Task dropdown
            const select = document.getElementById('workstreamSelect');
            select.innerHTML = workstreams.map(ws => 
                `<option value="${ws.id}">${ws.title}</option>`
            ).join('');
        }

        async function addWorkstream() {
            const id = document.getElementById('wsId').value.trim();
            const title = document.getElementById('wsTitle').value.trim();
            const errorMsg = document.getElementById('wsErrorMsg');

            if(!id || !title) {
                errorMsg.textContent = 'Both ID and Title are required.';
                errorMsg.classList.remove('hidden');
                return;
            }
            errorMsg.classList.add('hidden');

            const res = await fetch('/api/workstreams', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id, title })
            });

            if (res.ok) {
                document.getElementById('wsId').value = '';
                document.getElementById('wsTitle').value = '';
                await updateUI();
            } else {
                const data = await res.json();
                errorMsg.textContent = data.error || 'Failed to add workstream';
                errorMsg.classList.remove('hidden');
            }
        }

        async function deleteWorkstream(id) {
            if(confirm(`Are you sure? Deleting "${id}" will permanently remove all its tasks.`)) {
                await fetch(`/api/workstreams/${id}`, { method: 'DELETE' });
                await updateUI();
            }
        }

        async function fetchTasks() {
            const res = await fetch('/api/tasks');
            allTasks = await res.json();
        }

        async function updateUI() {
            await fetchWorkstreams();
            await fetchTasks();
            render();
        }

        function render() {
            const container = document.getElementById('workstreamContainers');
            container.innerHTML = '';

            if (workstreams.length === 0) {
                container.innerHTML = '<div class="text-center p-10 bg-gray-200 rounded-lg italic text-gray-500">No workstreams found. Create one above to get started.</div>';
                return;
            }

            workstreams.forEach(ws => {
                const wsTasks = allTasks.filter(t => t.workstream_id === ws.id);
                
                const wsSection = document.createElement('section');
                wsSection.className = 'bg-gray-50 rounded-xl p-6 shadow-inner border border-gray-200';
                
                let tasksHtml = '';
                if (wsTasks.length === 0) {
                    tasksHtml = `<p class="text-gray-400 italic text-sm py-4">No tasks in this workstream.</p>`;
                } else {
                    tasksHtml = wsTasks.map(task => `
                        <div class="bg-white shadow-sm rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between border-l-4 ${getStatusColor(task.status)} mb-3">
                            <div class="flex-1">
                                <h3 class="font-bold text-gray-800">${task.name}</h3>
                                <p class="text-xs text-gray-500 font-mono uppercase">Assignee: ${task.assignee}</p>
                            </div>
                            <div class="flex items-center gap-2 mt-3 sm:mt-0">
                                <select onchange="updateTask(${task.id}, {workstream_id: this.value})" class="bg-gray-50 border-gray-200 border rounded p-1 text-xs">
                                    ${workstreams.map(w => `<option value="${w.id}" ${task.workstream_id === w.id ? 'selected' : ''}>${w.title}</option>`).join('')}
                                </select>
                                <select onchange="updateTask(${task.id}, {status: this.value})" class="border-gray-300 border rounded p-1 text-xs font-bold ${getStatusTextClass(task.status)}">
                                    ${STATUSES.map(s => `<option value="${s}" ${task.status === s ? 'selected' : ''}>${s.toUpperCase()}</option>`).join('')}
                                </select>
                                <button onclick="deleteTask(${task.id})" class="text-red-400 hover:text-red-600 p-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    `).join('');
                }

                wsSection.innerHTML = `
                    <div class="flex justify-between items-center mb-6 border-b-2 border-gray-200 pb-2">
                        <div class="flex items-baseline gap-3">
                            <h2 class="text-2xl font-black text-gray-700 uppercase tracking-tight">${ws.title}</h2>
                            <span class="text-xs font-mono text-gray-400 bg-gray-200 px-2 py-0.5 rounded">${ws.id}</span>
                        </div>
                        <button onclick="deleteWorkstream('${ws.id}')" class="text-xs bg-red-100 text-red-600 px-3 py-1 rounded hover:bg-red-200 transition font-bold uppercase">
                            Delete Workstream
                        </button>
                    </div>
                    <div class="space-y-2">
                        ${tasksHtml}
                    </div>
                `;
                container.appendChild(wsSection);
            });
        }

        function getStatusColor(status) {
            if (status === 'todo') return 'border-yellow-400';
            if (status === 'in-progress') return 'border-blue-400';
            if (status === 'done') return 'border-green-400';
            return 'border-gray-400';
        }

        function getStatusTextClass(status) {
            if (status === 'todo') return 'text-yellow-600';
            if (status === 'in-progress') return 'text-blue-600';
            if (status === 'done') return 'text-green-600';
            return 'text-gray-600';
        }

        async function addTask() {
            const name = document.getElementById('taskName').value.trim();
            const assignee = document.getElementById('assigneeId').value.trim();
            const workstream_id = document.getElementById('workstreamSelect').value;
            const errorMsg = document.getElementById('errorMsg');
            
            if(!name || !assignee) {
                errorMsg.textContent = 'Both task description and operative ID are required.';
                errorMsg.classList.remove('hidden');
                return;
            }
            errorMsg.classList.add('hidden');

            await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name, 
                    assignee: assignee, 
                    status: 'todo', 
                    workstream_id: workstream_id
                })
            });
            
            document.getElementById('taskName').value = '';
            document.getElementById('assigneeId').value = '';
            updateUI();
        }

        async function updateTask(id, updates) {
            const task = allTasks.find(t => t.id === id);
            const payload = { ...task, ...updates };

            await fetch(`/api/tasks/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            updateUI();
        }

        async function deleteTask(id) {
            if(confirm("Delete this task?")) {
                await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
                updateUI();
            }
        }

        // Initialize
        updateUI();
    </script>
</body>
</html>'''

# --- Routes ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    global task_id_counter
    data = request.json
    if not data or not data.get("name") or not data.get("assignee"):
        return jsonify({"error": "Missing required fields"}), 400
        
    new_task = {
        "id": task_id_counter,
        "name": data.get("name"),
        "assignee": data.get("assignee"),
        "status": data.get("status", "todo"),
        "workstream_id": data.get("workstream_id", "tasktracker")
    }
    task_id_counter += 1
    tasks.append(new_task)
    save_data()
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    for task in tasks:
        if task["id"] == task_id:
            task["name"] = data.get("name", task["name"])
            task["assignee"] = data.get("assignee", task["assignee"])
            task["status"] = data.get("status", task["status"])
            task["workstream_id"] = data.get("workstream_id", task["workstream_id"])
            save_data()
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    initial_len = len(tasks)
    tasks[:] = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < initial_len:
        save_data()
        return jsonify({"success": True}), 200
    return jsonify({"error": "Task not found"}), 404

@app.route('/api/workstreams', methods=['GET'])
def get_workstreams():
    return jsonify(workstreams)

@app.route('/api/workstreams', methods=['POST'])
def add_workstream():
    data = request.json
    if not data or 'id' not in data or 'title' not in data:
        return jsonify({"error": "Missing id or title"}), 400
    
    if any(ws['id'] == data['id'] for ws in workstreams):
        return jsonify({"error": "Workstream ID already exists"}), 400
        
    new_ws = {"id": data['id'], "title": data['title']}
    workstreams.append(new_ws)
    save_data()
    return jsonify(new_ws), 201

@app.route('/api/workstreams/<ws_id>', methods=['DELETE'])
def delete_workstream(ws_id):
    global workstreams, tasks
    workstreams[:] = [ws for ws in workstreams if ws['id'] != ws_id]
    tasks[:] = [t for t in tasks if t.get('workstream_id') != ws_id]
    save_data()
    return jsonify({"success": True}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)