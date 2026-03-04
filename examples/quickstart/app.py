"""
Quick Start: FastAPI SSE Events Example (Simplified API).

This example demonstrates the RECOMMENDED way to use fastapi-sse-events.
It uses the simplified decorator-based API with SSEApp for minimal boilerplate.

Run with: uvicorn app:app --reload
Then open http://localhost:8000 for a simple interactive client.
"""

from fastapi import Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from fastapi_sse_events import SSEApp, publish_event, subscribe_to_events

# One-line setup with automatic SSE configuration!
# No manual broker setup, no lifecycle management needed.
app = SSEApp(
    title="Quick Start SSE Example",
    redis_url="redis://localhost:6379"
)


class TaskCreate(BaseModel):
    """Task creation request (no id needed - auto-generated)."""
    title: str
    description: str = ""


class Task(BaseModel):
    """Task response model (includes auto-generated id)."""
    id: int
    title: str
    description: str = ""


# In-memory storage for demo (use database in production)
tasks = {}
task_counter = 0


@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple HTML client to test real-time updates."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FastAPI SSE Quick Start</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .task { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
            form { margin: 20px 0; padding: 10px; border: 1px solid blue; }
            input { padding: 5px; }
            button { padding: 5px 10px; }
            #messages { border: 1px solid green; padding: 10px; height: 200px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <h1>FastAPI SSE Quick Start</h1>
        <p>Create tasks and see real-time updates via Server-Sent Events!</p>

        <form id="taskForm">
            <input type="text" id="title" placeholder="Task title" required />
            <input type="text" id="description" placeholder="Task description" />
            <button type="submit">Create Task</button>
        </form>

        <h2>Connected Tasks:</h2>
        <div id="tasks"></div>

        <h2>Live Events:</h2>
        <div id="messages"></div>

        <script>
            // ===== SETUP =====
            const messagesDiv = document.getElementById('messages');
            const tasksDiv = document.getElementById('tasks');

            // ===== HELPER FUNCTIONS =====
            function addMessage(msg) {
                console.log('💬 Adding message:', msg);
                const p = document.createElement('p');
                p.textContent = new Date().toLocaleTimeString() + ': ' + msg;
                messagesDiv.appendChild(p);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function addTaskToUI(task) {
                console.log('🎨 Adding task to UI:', task);
                const taskDiv = document.createElement('div');
                taskDiv.className = 'task';
                taskDiv.id = `task-${task.id}`;
                taskDiv.innerHTML = `
                    <strong>#${task.id}: ${task.title}</strong>
                    <p>${task.description || '(no description)'}</p>
                `;
                tasksDiv.appendChild(taskDiv);
            }

            function updateTaskInUI(task) {
                console.log('🎨 Updating task in UI:', task);
                const existingTask = document.getElementById(`task-${task.id}`);
                if (existingTask) {
                    existingTask.innerHTML = `
                        <strong>#${task.id}: ${task.title}</strong>
                        <p>${task.description || '(no description)'}</p>
                    `;
                } else {
                    addTaskToUI(task);
                }
            }

            // ===== SSE EVENT HANDLERS =====
            function handleTaskCreated(event) {
                console.log('🔥🔥🔥 HANDLING task:created 🔥🔥🔥');
                console.log('Event data:', event.data);

                let eventData;
                try {
                    eventData = JSON.parse(event.data);
                } catch (e) {
                    console.error('❌ Parse error:', e);
                    return;
                }

                const taskId = eventData.id;
                console.log('Task ID:', taskId);

                if (!taskId) {
                    console.error('❌ No task ID');
                    return;
                }

                console.log('🚀 FETCHING /tasks/' + taskId);
                fetch(`/tasks/${taskId}`)
                    .then(r => {
                        console.log('✅ Fetch response:', r.status);
                        if (!r.ok) throw new Error(`HTTP ${r.status}`);
                        return r.json();
                    })
                    .then(task => {
                        console.log('✅ Got task:', task);
                        addMessage(`✨ Task created: ${task.title}`);
                        addTaskToUI(task);
                    })
                    .catch(e => {
                        console.error('❌ Fetch error:', e);
                        addMessage(`❌ Error: ${e}`);
                    });
            }

            function handleTaskUpdated(event) {
                console.log('🔥🔥🔥 HANDLING task:updated 🔥🔥🔥');
                let eventData;
                try {
                    eventData = JSON.parse(event.data);
                } catch (e) {
                    console.error('❌ Parse error:', e);
                    return;
                }

                const taskId = eventData.id;
                fetch(`/tasks/${taskId}`)
                    .then(r => {
                        if (!r.ok) throw new Error(`HTTP ${r.status}`);
                        return r.json();
                    })
                    .then(task => {
                        console.log('✅ Got updated task:', task);
                        addMessage(`📝 Task updated: ${task.title}`);
                        updateTaskInUI(task);
                    })
                    .catch(e => {
                        console.error('❌ Fetch error:', e);
                        addMessage(`❌ Error: ${e}`);
                    });
            }

            function handleTaskDeleted(event) {
                console.log('🔥🔥🔥 HANDLING task:deleted 🔥🔥🔥');
                let eventData;
                try {
                    eventData = JSON.parse(event.data);
                } catch (e) {
                    console.error('❌ Parse error:', e);
                    return;
                }

                const taskId = eventData.id;
                fetch('/tasks')
                    .then(r => {
                        if (!r.ok) throw new Error(`HTTP ${r.status}`);
                        return r.json();
                    })
                    .then(data => {
                        console.log('✅ Got updated task list:', data);
                        addMessage(`🗑️ Task deleted: #${taskId}`);
                        tasksDiv.innerHTML = '';
                        if (data.tasks && Array.isArray(data.tasks)) {
                            data.tasks.forEach(task => addTaskToUI(task));
                        }
                    })
                    .catch(e => {
                        console.error('❌ Fetch error:', e);
                        addMessage(`❌ Error: ${e}`);
                    });
            }

            // ===== INITIALIZE SSE =====
            console.log('🔌 Creating EventSource...');
            const eventSource = new EventSource('/events?topic=tasks');

            eventSource.onopen = function() {
                console.log('🟢 SSE CONNECTED');
                addMessage('✅ Connected to real-time updates');
            };

            eventSource.onerror = function(e) {
                console.error('🔴 SSE ERROR:', e);
                addMessage('❌ Connection error');
            };

            // Catch all message events for debugging
            eventSource.addEventListener('message', (e) => {
                console.log('📢 Generic message received (this means SSE event parsing failed)');
                console.log('Raw data:', e.data.substring(0, 100));
            });

            // Attach event listeners
            console.log('Attaching event listeners...');
            eventSource.addEventListener('task:created', handleTaskCreated);
            eventSource.addEventListener('task:updated', handleTaskUpdated);
            eventSource.addEventListener('task:deleted', handleTaskDeleted);
            console.log('✅ Event listeners attached');

            // ===== FORM HANDLER =====
            document.getElementById('taskForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('title').value;
                const description = document.getElementById('description').value;

                console.log('📤 Submitting:', title);
                addMessage(`📤 Creating task...`);

                try {
                    const response = await fetch('/tasks', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, description })
                    });

                    if (response.ok) {
                        console.log('✅ Task submitted');
                        document.getElementById('title').value = '';
                        document.getElementById('description').value = '';
                    } else {
                        console.error('❌ Error:', response.status);
                        addMessage(`❌ Error: ${response.status}`);
                    }
                } catch (error) {
                    console.error('❌ Fetch error:', error);
                    addMessage(`❌ Request failed`);
                }
            });

            // ===== LOAD INITIAL TASKS =====
            console.log('📥 Loading initial tasks...');
            fetch('/tasks')
                .then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    console.log('✅ Initial tasks loaded:', data);
                    if (data.tasks && Array.isArray(data.tasks)) {
                        data.tasks.forEach(task => addTaskToUI(task));
                        addMessage(`📥 Loaded ${data.tasks.length} tasks`);
                    }
                })
                .catch(err => {
                    console.error('❌ Load error:', err);
                    addMessage(`❌ Failed to load tasks`);
                });
        </script>
    </body>
    </html>
    """


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Simple test page for SSE debugging."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SSE Test</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .test { border: 1px solid blue; padding: 10px; margin: 10px 0; }
            button { padding: 10px 20px; font-size: 16px; }
            #output { border: 1px solid green; padding: 10px; min-height: 200px; background: #f0f0f0; }
            .log { padding: 5px; margin: 5px 0; border-left: 3px solid #999; padding-left: 10px; }
            .error { border-left-color: red; color: red; }
            .success { border-left-color: green; color: green; }
            .info { border-left-color: blue; color: blue; }
        </style>
    </head>
    <body>
        <h1>SSE Test</h1>
        <div class="test">
            <h2>Test SSE Connection</h2>
            <button onclick="testSSE()">Test SSE (click here)</button>
            <div id="output"></div>
        </div>

        <script>
            const output = document.getElementById('output');

            function log(msg, type = 'info') {
                const div = document.createElement('div');
                div.className = 'log ' + type;
                div.textContent = new Date().toLocaleTimeString() + ' | ' + msg;
                output.appendChild(div);
                output.scrollTop = output.scrollHeight;
                console.log(`[${type}]`, msg);
            }

            function testSSE() {
                log('🔌 Creating EventSource to /test-sse...', 'info');
                const es = new EventSource('/test-sse');

                es.onopen = function() {
                    log('✅ Connection opened!', 'success');
                };

                es.addEventListener('test:event', (e) => {
                    log('🎯 Received test:event: ' + e.data, 'success');
                });

                es.addEventListener('message', (e) => {
                    log('📢 Received message event: ' + e.data.substring(0, 50) + '...', 'info');
                });

                es.onerror = function(e) {
                    log('❌ Error: ' + e, 'error');
                    log('ReadyState: ' + es.readyState, 'error');
                    es.close();
                };

                setTimeout(() => {
                    log('Closing connection...', 'info');
                    es.close();
                }, 5000);
            }
        </script>
    </body>
    </html>
    """


@app.get("/test-sse")
async def test_sse(_request: Request):
    """Test endpoint to verify SSE is working correctly."""
    import asyncio

    from fastapi.responses import StreamingResponse

    async def generate():
        # Test 1: Send raw SSE message
        message = """event: test:event
data: {"message": "Hello from test SSE"}
id: test-1

"""
        print(f"Backend sending test message:\n{repr(message)}")
        yield message
        await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/tasks", response_model=Task)
@publish_event(topic="tasks", event="task:created")
async def create_task(_request: Request, task: TaskCreate):
    """
    Create a task.

    THE SIMPLIFIED WAY: Just use the @publish_event decorator!
    - Your endpoint returns data
    - Decorator automatically publishes it as SSE event
    - No manual broker.publish() calls needed
    """
    global task_counter
    task_counter += 1

    new_task = Task(id=task_counter, title=task.title, description=task.description)
    tasks[task_counter] = new_task

    print(f"📤 [create_task] Publishing event - ID: {new_task.id}, Title: {new_task.title}")

    # Simply return - decorator handles SSE publishing automatically!
    return new_task


@app.get("/tasks")
async def list_tasks():
    """List all tasks."""
    return {
        "tasks": list(tasks.values())
    }


@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Get a specific task."""
    if task_id not in tasks:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.put("/tasks/{task_id}", response_model=Task)
@publish_event(topic="tasks", event="task:updated")
async def update_task(_request: Request, task_id: int, task_update: TaskCreate):
    """
    Update a task and notify subscribers with decorator.
    """
    if task_id not in tasks:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")

    task = Task(id=task_id, title=task_update.title, description=task_update.description)
    tasks[task_id] = task

    # Decorator automatically publishes this!
    return task


@app.delete("/tasks/{task_id}")
@publish_event(topic="tasks", event="task:deleted")
async def delete_task(_request: Request, task_id: int):
    """
    Delete a task and notify subscribers with decorator.
    """
    if task_id not in tasks:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")

    deleted = tasks.pop(task_id)

    # Decorator automatically publishes this!
    return deleted


@app.get("/events")
@subscribe_to_events()
async def events_endpoint(request: Request):
    """
    SSE streaming endpoint.

    THE SIMPLIFIED WAY: Just use the @subscribe_to_events decorator!
    - Gets topics from query parameter: ?topic=tasks
    - Decorator handles all streaming logic automatically
    - Returns EventSourceResponse with proper SSE headers
    """
    pass  # Decorator handles all streaming logic!


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
