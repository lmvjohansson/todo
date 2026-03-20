resource "aws_ecr_repository" "todo_backend" {
  name = "todo-backend"
  
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ecr_repository" "todo_frontend" {
  name = "todo-frontend"

  lifecycle {
    prevent_destroy = true
  }
}