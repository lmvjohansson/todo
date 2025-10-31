import React from "react";

export default class TodoItem extends React.Component {
    render() {
        const { task, onToggle, onRemove } = this.props;

        const taskStyle = {
            textDecoration: task.done ? "line-through" : "none"
        };

        return (
            <li>
                <input
                    type="checkbox"
                    checked={task.done}
                    onChange={() => onToggle(task.id)}
                />
                <span style={taskStyle}>{task.title}</span>
                <button onClick={() => onRemove(task.id)}>X</button>
            </li>
        );
    }
}
