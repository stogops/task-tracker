from flask import Flask, jsonify, request, render_template_string
import json
import os

app = Flask(__name__)

DATA_FILE = '/data/tasks.json'

# Default workstreams definition
WORKSTREAMS = [
    {"id": "tasktracker", "title": "Task Tracker"},
    {"id": "development", "title": "Development"},
    {"id": "operations", "title": "Operations"}
]

def load_tasks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                loaded_tasks = data.get('tasks', [])
                counter = data.get('counter', 1)
                
                # Migration: Ensure every existing task has a workstream_id
                for task in loaded_tasks:
                    if 'workstream_id' not in task:
                        task['workstream_id'] = "tasktracker"
                
                return loaded_tasks, counter
        except Exception:
            pass
    return [], 1

def save_tasks():
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump({'tasks': tasks, 'counter': task_id_counter}, f)
    except Exception as e:
        print(f"Error saving tasks: {e}")

tasks, task_id_counter = load_tasks()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-800 font-sans antialiased p-6">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-6 text-blue-600">Task Tracker</h1>
        
        <!-- Add Task Form -->
        <div class="bg-white shadow-md rounded-lg p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Add New Task</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <input type="text" id="taskName" placeholder="Task description..." class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                <input type="text" id="assigneeId" placeholder="Operative ID..." class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                <select id="workstreamSelect" class="border-gray-300 border rounded-md p-2 focus:ring focus:ring-blue-200 focus:outline-none">
                    <!-- Options populated by JS -->
                </select>
                <button onclick="addTask()" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition">Add Task</button>
            </div>
            <p id="errorMsg" class="text-red-500 mt-2 hidden text-sm"></p>
        </div>

        <!-- Task List Grouped by Workstream -->
        <div id="workstreamContainers" class="space-y-8"></div>
    </div>

    <script>
        const STATUSES = ['todo', 'in-progress', 'done'];
        let workstreams = [];
        
        async function fetchWorkstreams() {
            const res = await fetch('/api/workstreams');
            workstreams = await res.json();
            
            // Populate the "Add Task" dropdown
            const select = document.getElementById('workstreamSelect');
            select.innerHTML = workstreams.map(ws => 
                `<option value="${ws.id}">${ws.title}</option>`
            ).join('');
        }

        async function fetchTasks() {
            try {
                const res = await fetch('/api/tasks');
                const tasks = await res.json();
                const container = document.getElementById('workstreamContainers');
                container.innerHTML = '';
                
                if (tasks.length === 0) {
                    container.innerHTML = '<p class="text-gray-500 italic">No tasks found. Add one above!</p>';
                    return;
                }

                // Group tasks by workstream
                workstreams.forEach(ws => {
                    const wsTasks = tasks.filter(t => t.workstream_id === ws.id);
                    
                    if (wsTasks.length > 0) {
                        const wsSection = document.createElement('div');
                        wsSection.className = 'space-y-4';
                        wsSection.innerHTML = `
                            <h2 class="text-lg font-bold text-gray-700 border-b pb-2 uppercase tracking-wider">${ws.title}</h2>
                            <div id="ws-list-${ws.id}" class="space-y-3"></div>
                        `;
                        container.appendChild(wsSection);
                        
                        const list = wsSection.querySelector(`#ws-list-${ws.id}`);
                        
                        wsTasks.forEach(task => {
                            const div = document.createElement('div');
                            div.className = 'bg-white shadow-sm rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between border-l-4 ' + getStatusColor(task.status);
                            
                            let statusOptions = STATUSES.map(s => 
                                `<option value="${s}" ${task.status === s ? 'selected' : ''}>${s.replace('-', ' ').toUpperCase()}</option>`
                            ).join('');

                            let wsOptions = workstreams.map(w => 
                                `<option value="${w.id}" ${task.workstream_id === w.id ? 'selected' : ''}>${w.title}</option>`
                            ).join('');

                            div.innerHTML = `
                                <div class="flex-1 mb-4 sm:mb-0">
                                    <h3 class="text-md font-semibold">${task.name}</h3>
                                    <p class="text-xs text-gray-500 uppercase">Assignee: ${task.assignee}</p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <select onchange="updateTask(${task.id}, {workstream_id: this.value})" class="bg-gray-50 border-gray-200 border rounded-md p-1 text-xs focus:outline-none">
                                        ${wsOptions}
                                    </select>
                                    <select onchange="updateTask(${task.id}, {status: this.value})" class="border-gray-300 border rounded-md p-1 text-sm focus:outline-none focus:ring focus:ring-blue-200">
                                        ${statusOptions}
                                    </select>
                                    <button onclick="deleteTask(${task.id})" class="text-red-500 hover:text-red-700 px-2 py-1 bg-red-50 rounded-md transition text-sm">Delete</button>
                                </div>
                            `;
                            list.appendChild(div);
                        });
                    }
                });
            } catch (err) {
                console.error("Failed to fetch tasks", err);
            }
        }

        function getStatusColor(status) {
            if (status === 'todo') return 'border-yellow-400';
            if (status === 'in-progress') return 'border-blue-400';
            if (status === 'done') return 'border-green-400';
            return 'border-gray-400';
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
            fetchTasks();
        }

        async function updateTask(id, updates) {
            // Get current task data first to ensure we don't overwrite with nulls
            const res = await fetch('/api/tasks');
            const allTasks = await res.json();
            const task = allTasks.find(t => t.id === id);
            
            const payload = { ...task, ...updates };

            await fetch(`/api/tasks/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            fetchTasks();
        }

        async function deleteTask(id) {
            if(confirm("Are you sure you want to delete this task?")) {
                await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
                fetchTasks();
            }
        }

        // Initialize
        async function init() {
            await fetchWorkstreams();
            await fetchTasks();
        }
        init();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/workstreams', methods=['GET'])
def get_workstreams():
    return jsonify(WORKSTREAMS)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    global task_id_counter
    data = request.json
    if not data or not data.get("name") or not data.get("assignee"):
        return jsonify({"error": "Missing required fields: name, assignee"}), 400
        
    new_task = {
        "id": task_id_counter,
        "name": data.get("name"),
        "assignee": data.get("assignee"),
        "status": data.get("status", "todo"),
        "workstream_id": data.get("workstream_id", "tasktracker")
    }
    task_id_counter += 1
    tasks.append(new_task)
    save_tasks()
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
            save_tasks()
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    for task in tasks:
        if task["id"] == task_id:
            tasks = [t for t in tasks if t["id"] != task_id]
            save_tasks()
            return jsonify({"success": True}), 200
    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)