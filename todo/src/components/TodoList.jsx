import React from "react";
import TodoItem from "./TodoItem";

export default class TodoList extends React.Component {
    render() {
        const { tasks, onToggle, onRemove } = this.props;
        return (
            <>
                {tasks.map(task => (
                    <TodoItem
                        key={task.id}
                        task={task}
                        onToggle={onToggle}
                        onRemove={onRemove}
                    />
                ))}
            </>
        );
    }
}
