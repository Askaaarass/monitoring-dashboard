(() => {
    const story = document.querySelector('[data-aqua-story]');
    if (!story) return;

    const steps = [...story.querySelectorAll('[data-aqua-step]')];
    const nodes = [...story.querySelectorAll('[data-aqua-node]')];
    const ring = story.querySelector('[data-aqua-progress]');
    const counter = story.querySelector('[data-aqua-count]');
    const target = story.querySelector('[data-aqua-target]');
    const animate = window.matchMedia('(prefers-reduced-motion: no-preference) and (min-height: 520px)');
    let frame = null;
    let activeIndex = -1;

    function selectStep(index) {
        if (activeIndex === index) return;
        activeIndex = index;
        steps.forEach((step, i) => {
            step.classList.toggle('is-current', i === index);
            nodes[i].classList.toggle('is-current', i === index);
        });
        counter.textContent = index < 0 ? '01–04' : `0${index + 1} / 0${steps.length}`;
        story.classList.toggle('is-target', index === steps.length - 1);
        target.setAttribute('aria-hidden', String(index >= 0 && index !== steps.length - 1));
    }

    function update() {
        frame = null;
        if (!animate.matches) return;

        const bounds = steps.map(step => step.getBoundingClientRect());
        const centers = bounds.map(rect => rect.top + rect.height / 2);
        const focusLine = window.innerHeight * .58;
        const start = centers[0];
        const last = centers.length - 1;
        const revealPoint = (centers[last - 1] + centers[last]) / 2;
        const progress = Math.max(0, Math.min(1, (focusLine - start) / Math.max(revealPoint - start, 1)));
        const index = centers.reduce((closest, center, i) =>
            Math.abs(center - focusLine) < Math.abs(centers[closest] - focusLine) ? i : closest, 0);
        ring.style.strokeDashoffset = String(100 * (1 - progress));
        selectStep(index);
    }

    function schedule() {
        if (animate.matches && frame === null) frame = requestAnimationFrame(update);
    }

    function syncMode() {
        story.classList.toggle('is-animated', animate.matches);
        if (animate.matches) {
            schedule();
        } else {
            ring.style.strokeDashoffset = '';
            selectStep(-1);
        }
    }

    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    animate.addEventListener('change', syncMode);
    syncMode();
})();
