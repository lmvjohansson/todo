import React from "react";
import TodoList from "../components/TodoList";
import AddTask from "../components/AddTask";
import { Task } from "../models/Task";

export default class TodoApp extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            tasks: [
                new Task(1, "Learn React"),
                new Task(2, "Connect to Flask backend")
            ]
        };
    }

    toggleTask = (id) => {
        const tasks = this.state.tasks.map(task => {
            if (task.id === id) task.toggleDone();
            return task;
        });
        this.setState({ tasks });
    };

    addTask = (title) => {
        const newTask = new Task(Date.now(), title); // use timestamp as id
        this.setState({ tasks: [...this.state.tasks, newTask] });
    };

    removeTask = (id) => {
        const tasks = this.state.tasks.filter(task => task.id !== id);
        this.setState({ tasks });
    };

    render() {
        return (
            <div>
                <TodoList
                    tasks={this.state.tasks}
                    onToggle={this.toggleTask}
                    onRemove={this.removeTask}
                />
                <AddTask onAdd={this.addTask} />
            </div>
        );
    }
}