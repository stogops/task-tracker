
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

tasks = []
task_id_counter = 1

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Task Tracker</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; max-width: 600px; }
        .task { border: 1px solid #ccc; padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }
        .task.completed { background-color: #f0f0f0; text-decoration: line-through; }
        button, input { padding: 0.5rem; }
    </style>
</head>
<body>
    <h1>Task Tracker</h1>
    <div>
        <input type="text" id="taskName" placeholder="New task name...">
        <button onclick="addTask()">Add Task</button>
    </div>
    <div id="taskList" style="margin-top: 2rem;"></div>

    <script>
        async function fetchTasks() {
            const res = await fetch('/api/tasks');
            const tasks = await res.json();
            const list = document.getElementById('taskList');
            list.innerHTML = '';
            tasks.forEach(task => {
                const div = document.createElement('div');
                div.className = 'task ' + (task.completed ? 'completed' : '');
                div.innerHTML = `
                    <strong>${task.name}</strong> 
                    <button onclick="toggleTask(${task.id})" style="float: right;">Toggle</button>
                `;
                list.appendChild(div);
            });
        }

        async function addTask() {
            const name = document.getElementById('taskName').value;
            if(!name) return;
            await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            });
            document.getElementById('taskName').value = '';
            fetchTasks();
        }

        async function toggleTask(id) {
            await fetch(`/api/tasks/${id}/toggle`, { method: 'POST' });
            fetchTasks();
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
    new_task = {
        "id": task_id_counter,
        "name": data.get("name", "Unnamed task"),
        "completed": False
    }
    task_id_counter += 1
    tasks.append(new_task)
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
