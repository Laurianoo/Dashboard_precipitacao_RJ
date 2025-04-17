// snowfall.js
if (!window.snowing) {
    window.snowing = true;
    const canvas = document.createElement('canvas');
    canvas.id = 'snow-canvas';
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let snowflakes = [];

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

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
        snowflakes.forEach((flake, i) => {
            flake.y += flake.speed;
            if (flake.y > canvas.height) {
                snowflakes[i] = createSnowflake();
                snowflakes[i].y = 0;
            }
            ctx.beginPath();
            ctx.arc(flake.x, flake.y, flake.radius, 0, 2 * Math.PI);
            ctx.fillStyle = `rgba(255, 255, 255, ${flake.opacity})`;
            ctx.fill();
        });
        requestAnimationFrame(updateSnowflakes);
    }

    // Inicialização
    for (let i = 0; i < 100; i++) {
        snowflakes.push(createSnowflake());
    }

    updateSnowflakes();
    console.log("🌨️ Efeito de neve ativado!");
}