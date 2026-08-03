const canvas = document.getElementById('snowCanvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    let mouseX = width / 2;

    window.addEventListener('resize', () => { 
        width = canvas.width = window.innerWidth; 
        height = canvas.height = window.innerHeight; 
        mouseX = width / 2; 
    });
    
    window.addEventListener('mousemove', (e) => { 
        mouseX = e.clientX; 
    });

    const particles = [];
    const colors = ['rgba(255,255,255,0.2)', 'rgba(102,252,241,0.25)', 'rgba(255,74,74,0.2)'];

    for (let i = 0; i < 90; i++) {
        particles.push({
            x: Math.random() * width, 
            y: Math.random() * height,
            r: Math.random() * 1.5 + 0.5, 
            d: Math.random() * 0.2 + 0.05,
            color: colors[Math.floor(Math.random() * colors.length)], 
            tilt: Math.random() * 10
        });
    }

    let angle = 0;
    function drawParticles() {
        ctx.clearRect(0, 0, width, height);
        angle += 0.005;
        const wind = (mouseX - width / 2) * 0.001;
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            ctx.beginPath(); 
            ctx.fillStyle = p.color; 
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2, true); 
            ctx.fill();
            p.y += p.d; 
            p.x += Math.sin(angle + p.tilt) * 0.2 + wind;
            if (p.x > width + 5 || p.x < -5 || p.y > height) {
                particles[i] = { x: Math.random() * width, y: -10, r: p.r, d: p.d, color: p.color, tilt: p.tilt };
            }
        }
        requestAnimationFrame(drawParticles);
    }
    drawParticles();
}