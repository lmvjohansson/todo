# ─── Backend ALB ───────────────────────────────────────────────
resource "aws_lb" "todo_backend_alb" {
  name               = "todo-backend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.backend_alb.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false
}

resource "aws_lb_target_group" "todo_backend_tg" {
  name        = "todo-backend-tg"
  target_type = "ip"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  
  health_check {
    path      = "/api/health"
    protocol  = "HTTP"
    matcher   = "200"
  }
}

resource "aws_lb_listener" "todo_backend_listener" {
  load_balancer_arn = aws_lb.todo_backend_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.todo_backend_tg.arn
  }
}

