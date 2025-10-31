export class Task {
    constructor(id, title, done = false) {
        this.id = id;
        this.title = title;
        this.done = done;
    }

    toggleDone() {
        this.done = !this.done;
    }
}
