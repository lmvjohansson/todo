import React from "react";

export default class AddTask extends React.Component {
    constructor(props) {
        super(props);
        this.state = { title: "" };
    }

    handleChange = (e) => {
        this.setState({ title: e.target.value });
    };

    handleSubmit = (e) => {
        e.preventDefault();
        if (this.state.title.trim() !== "") {
            this.props.onAdd(this.state.title);
            this.setState({ title: "" });
        }
    };

    render() {
        return (
            <form onSubmit={this.handleSubmit}>
                <input
                    type="text"
                    placeholder="New task"
                    value={this.state.title}
                    onChange={this.handleChange}
                />
                <button type="submit">Add</button>
            </form>
        );
    }
}
