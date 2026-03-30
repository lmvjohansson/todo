# ─── Frontend ALB ───────────────────────────────────────────────
resource "aws_lb" "todo_frontend_alb" {
  name               = "todo-frontend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.frontend_alb.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false
}

resource "aws_lb_target_group" "todo_frontend_tg" {
  name        = "todo-frontend-tg"
  target_type = "ip"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  
  health_check {
    path      = "/"
    protocol  = "HTTP"
    matcher   = "200"
  }
}

resource "aws_lb_listener" "todo_frontend_listener" {
  load_balancer_arn = aws_lb.todo_frontend_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.todo_frontend_tg.arn
  }
}

