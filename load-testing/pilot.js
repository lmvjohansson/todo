import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '2m', target: 200 },
        { duration: '2m', target: 400 },
        { duration: '2m', target: 600 },
        { duration: '2m', target: 800 },
        { duration: '2m', target: 1000 },
        { duration: '2m', target: 0 },
    ],
};

export default function () {
    const res = http.get('http://todo-backend-alb-532988684.eu-north-1.elb.amazonaws.com/api/tasks');
    check(res, {
        'status is 200': (r) => r.status === 200,
    });
    sleep(1);
}