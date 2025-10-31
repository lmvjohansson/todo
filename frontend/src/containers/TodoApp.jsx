import React, { useState, useEffect } from "react";
import TodoList from "../components/TodoList";
import AddTask from "../components/AddTask";
import { Task } from "../models/Task";

export default function TodoApp() {
    const [tasks, setTasks] = useState([]);

    useEffect(() => {
        fetch("http://localhost:5000/tasks")
            .then(res => res.json())
            .then(data => setTasks(data.map(t => new Task(t.id, t.title, t.done))))
            .catch(console.error);
    }, []);

    const toggleTask = (id) => {
        fetch(`http://localhost:5000/tasks/${id}`, { method: "PATCH" })
            .then(res => res.json())
            .then(data => {
                setTasks(tasks.map(task => task.id === data.id ? { ...task, done: data.done } : task));
            })
            .catch(console.error);
    };

    const addTask = (title) => {
        fetch("http://localhost:5000/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title }),
        })
            .then(res => res.json())
            .then(data => setTasks([...tasks, new Task(data.id, data.title, data.done)]))
            .catch(console.error);
    };

    const removeTask = (id) => {
        fetch(`http://localhost:5000/tasks/${id}`, { method: "DELETE" })
            .then(res => {
                if (res.ok) {
                    setTasks(tasks.filter(task => task.id !== id));
                } else {
                    console.error("Failed to delete task");
                }
            })
            .catch(console.error);
    };

    return (
        <div>
            <TodoList tasks={tasks} onToggle={toggleTask} onRemove={removeTask} />
            <AddTask onAdd={addTask} />
        </div>
    );
}
