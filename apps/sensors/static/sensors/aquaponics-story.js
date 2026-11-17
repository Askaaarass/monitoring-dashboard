(() => {
    const scene = document.querySelector('[data-aqua-scene]');
    if (!scene) return;
    const pointerMotion = window.matchMedia('(prefers-reduced-motion: no-preference) and (hover: hover) and (pointer: fine)');
    let pointerFrame = null;
    let pointer = { x: 0, y: 0 };

    function renderScene() {
        pointerFrame = null;
        const bounds = scene.getBoundingClientRect();
        const x = (pointer.x - bounds.left) / bounds.width - .5;
        const y = (pointer.y - bounds.top) / bounds.height - .5;
        scene.style.setProperty('--scene-rotate-x', `${-y * 5}deg`);
        scene.style.setProperty('--scene-rotate-y', `${x * 7}deg`);
    }

    function moveScene(event) {
        if (!pointerMotion.matches || pointerFrame !== null) return;
        pointer = { x: event.clientX, y: event.clientY };
        pointerFrame = requestAnimationFrame(renderScene);
    }

    function resetScene() {
        scene.style.setProperty('--scene-rotate-x', '0deg');
        scene.style.setProperty('--scene-rotate-y', '0deg');
    }

    if (scene) {
        scene.addEventListener('pointermove', moveScene, { passive: true });
        scene.addEventListener('pointerleave', resetScene);
    }
})();
