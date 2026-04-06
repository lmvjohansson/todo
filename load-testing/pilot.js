import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 800,
    duration: '20m',
};

export default function () {
    const res = http.get('http://todo-backend-alb-1874524542.eu-north-1.elb.amazonaws.com/api/tasks');
    check(res, {
        'status is 200': (r) => r.status === 200,
    });
    sleep(1);
}