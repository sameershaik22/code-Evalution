const input = require('fs').readFileSync(0, 'utf-8').trim().split(/\s+/).map(Number);

let n = input[0], target = input[1];
let arr = input.slice(2);

let mp = new Map();

for (let i = 0; i < n; i++) {
    let need = target - arr[i];

    if (mp.has(need)) {
        console.log(mp.get(need) + 1, i + 1);
        break;
    }

    mp.set(arr[i], i);
}