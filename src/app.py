
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

tasks = []
task_id_counter = 1

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
    <div class="max-w-3xl mx-auto">
        <h1 class="text-3xl font-bold mb-6 text-indigo-600">Task Tracker</h1>
        
        <div class="bg-white shadow-md rounded-lg p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Add New Task</h2>
            <div class="flex flex-col md:flex-row gap-4">
                <input type="text" id="taskName" placeholder="Task description..." class="flex-1 border-gray-300 border rounded-md p-2 focus:ring focus:ring-indigo-200 focus:outline-none">
                <input type="text" id="assigneeId" placeholder="Operative ID..." class="flex-1 border-gray-300 border rounded-md p-2 focus:ring focus:ring-indigo-200 focus:outline-none">
                <button onclick="addTask()" class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition">Add Task</button>
            </div>
            <p id="errorMsg" class="text-red-500 mt-2 hidden text-sm"></p>
        </div>

        <div id="taskList" class="space-y-4"></div>
    </div>

    <script>
        const STATUSES = ['todo', 'in-progress', 'done'];
        
        async function fetchTasks() {
            try {
                const res = await fetch('/api/tasks');
                const tasks = await res.json();
                const list = document.getElementById('taskList');
                list.innerHTML = '';
                
                if (tasks.length === 0) {
                    list.innerHTML = '<p class="text-gray-500 italic">No tasks found. Add one above!</p>';
                    return;
                }

                tasks.forEach(task => {
                    const div = document.createElement('div');
                    div.className = 'bg-white shadow-md rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between border-l-4 ' + getStatusColor(task.status);
                    
                    let statusOptions = STATUSES.map(s => 
                        `<option value="${s}" ${task.status === s ? 'selected' : ''}>${s.replace('-', ' ').toUpperCase()}</option>`
                    ).join('');

                    div.innerHTML = `
                        <div class="flex-1 mb-4 sm:mb-0">
                            <h3 class="text-lg font-semibold">${task.name}</h3>
                            <p class="text-sm text-gray-600">Assigned to: <span class="font-medium text-gray-800">${task.assignee}</span></p>
                        </div>
                        <div class="flex items-center gap-2">
                            <select onchange="updateTask(${task.id}, this.value, '${task.assignee}', '${task.name}')" class="border-gray-300 border rounded-md p-1 text-sm focus:outline-none focus:ring focus:ring-indigo-200">
                                ${statusOptions}
                            </select>
                            <button onclick="deleteTask(${task.id})" class="text-red-500 hover:text-red-700 px-2 py-1 bg-red-50 rounded-md transition text-sm">Delete</button>
                        </div>
                    `;
                    list.appendChild(div);
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
                body: JSON.stringify({name: name, assignee: assignee, status: 'todo'})
            });
            
            document.getElementById('taskName').value = '';
            document.getElementById('assigneeId').value = '';
            fetchTasks();
        }

        async function updateTask(id, newStatus, assignee, name) {
            await fetch(`/api/tasks/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: newStatus, assignee: assignee, name: name})
            });
            fetchTasks();
        }

        async function deleteTask(id) {
            if(confirm("Are you sure you want to delete this task?")) {
                await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
                fetchTasks();
            }
        }

        fetchTasks();
    </script>
</body>
</html>
'''

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
        return jsonify({"error": "Missing required fields: name, assignee"}), 400
        
    new_task = {
        "id": task_id_counter,
        "name": data.get("name"),
        "assignee": data.get("assignee"),
        "status": data.get("status", "todo")
    }
    task_id_counter += 1
    tasks.append(new_task)
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    for task in tasks:
        if task["id"] == task_id:
            task["name"] = data.get("name", task["name"])
            task["assignee"] = data.get("assignee", task["assignee"])
            task["status"] = data.get("status", task["status"])
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    for task in tasks:
        if task["id"] == task_id:
            tasks = [t for t in tasks if t["id"] != task_id]
            return jsonify({"success": True}), 200
    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
