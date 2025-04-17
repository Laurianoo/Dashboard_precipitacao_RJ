const canvas = document.createElement('canvas');
canvas.id = 'snowfall';
canvas.style.position = 'fixed';
canvas.style.top = '0';
canvas.style.left = '0';
canvas.style.width = '100%';
canvas.style.height = '100%';
canvas.style.pointerEvents = 'none';
document.body.appendChild(canvas);

const ctx = canvas.getContext('2d');
const snowflakes = [];

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

function createSnowflake() {
    return {
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 4 + 1,
        speed: Math.random() * 1 + 0.5,
        opacity: Math.random() * 0.5 + 0.3,
    };
}

function updateSnowflakes() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    snowflakes.forEach((flake, index) => {
        flake.y += flake.speed;
        if (flake.y > canvas.height) {
            snowflakes[index] = createSnowflake();
            snowflakes[index].y = 0;
        }
        ctx.beginPath();
        ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${flake.opacity})`;
        ctx.fill();
    });
    requestAnimationFrame(updateSnowflakes);
}

for (let i = 0; i < 100; i++) {
    snowflakes.push(createSnowflake());
}
updateSnowflakes();