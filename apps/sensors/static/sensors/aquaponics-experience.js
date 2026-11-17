import { createDemoProvider } from './aquaponics-data.js';
import { initializeAquaponicsScene } from './aquaponics-three.js';

const lab = document.querySelector('[data-aqua-lab]');
const assembly = document.querySelector('[data-aqua-assembly]');
if (assembly) {
    const updateAssemblyViewport = () => {
        const width = document.documentElement.clientWidth;
        assembly.style.setProperty('--aqua-viewport-width', `${width}px`);
        assembly.style.setProperty('--aqua-viewport-half', `${width / 2}px`);
    };
    updateAssemblyViewport();
    window.addEventListener('resize', updateAssemblyViewport, { passive: true });
}
if (lab) {
    const provider = createDemoProvider();
    const dateTime = new Intl.DateTimeFormat('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
    const sensorNodes = [...lab.querySelectorAll('[data-sensor-id]')];
    const readingCards = [...lab.querySelectorAll('[data-reading-id]')];
    const selectedName = lab.querySelector('[data-selected-name]');
    const selectedValue = lab.querySelector('[data-selected-value]');
    const selectedUnit = lab.querySelector('[data-selected-unit]');
    const cameraChecked = lab.querySelector('[data-camera-checked]');
    let selectedId = 'water-temp';

    function selectSensor(id) {
        const reading = provider.getSnapshot().readings[id];
        if (!reading) return;
        selectedId = id;
        sensorNodes.forEach(node => {
            const selected = node.dataset.sensorId === id;
            node.classList.toggle('is-selected', selected);
            node.setAttribute('aria-pressed', String(selected));
        });
        readingCards.forEach(card => {
            const selected = card.dataset.readingId === id;
            card.classList.toggle('is-selected', selected);
            card.setAttribute('aria-pressed', String(selected));
        });
        selectedName.textContent = reading.name;
        selectedValue.textContent = reading.value;
        selectedUnit.textContent = reading.unit;
        lab.querySelector('[data-test-sensor]').value = id;
        window.dispatchEvent(new CustomEvent('aqua:sensor-select', { detail: { id } }));
    }

    function render(snapshot) {
        Object.entries(snapshot.readings).forEach(([id, reading]) => {
            const value = lab.querySelector(`[data-reading-value="${id}"]`);
            const status = lab.querySelector(`[data-reading-status="${id}"]`);
            const time = lab.querySelector(`[data-reading-time="${id}"]`);
            value.textContent = reading.value;
            status.textContent = reading.status;
            status.dataset.status = reading.status.toLowerCase();
            time.textContent = dateTime.format(snapshot.updatedAt);
        });
        const selected = snapshot.readings[selectedId];
        if (selected) {
            selectedValue.textContent = selected.value;
            selectedUnit.textContent = selected.unit;
        }
        lab.querySelector('[data-camera-status]').textContent = snapshot.camera.status;
        lab.querySelector('[data-camera-status]').dataset.status = snapshot.camera.status.toLowerCase();
        lab.dataset.connection = snapshot.connected ? 'online' : 'offline';
    }

    sensorNodes.forEach(node => {
        node.addEventListener('click', () => selectSensor(node.dataset.sensorId));
        node.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                selectSensor(node.dataset.sensorId);
            }
        });
    });
    readingCards.forEach(card => card.addEventListener('click', () => selectSensor(card.dataset.readingId)));
    lab.querySelector('[data-test-sensor]').addEventListener('change', event => selectSensor(event.target.value));
    lab.querySelectorAll('[data-test-value]').forEach(button => {
        button.addEventListener('click', () => {
            const id = lab.querySelector('[data-test-sensor]').value;
            const { min, max, criticalMin, criticalMax } = provider.getSnapshot().readings[id].threshold;
            const value = button.dataset.testValue === 'normal'
                ? (min + max) / 2
                : button.dataset.testValue === 'warning'
                    ? (max + criticalMax) / 2
                    : criticalMax + (criticalMax - max);
            provider.setValue(id, value);
        });
    });
    lab.querySelector('[data-camera-refresh]').addEventListener('click', () => {
        cameraChecked.textContent = `Проверено ${dateTime.format(new Date())}`;
        lab.querySelector('[data-camera-preview] p').textContent = 'Снимок пока не загружен';
    });

    provider.subscribe(render);
    render(provider.getSnapshot());
    selectSensor(selectedId);
    if (assembly) {
        initializeAquaponicsScene(assembly, {
            onSensorSelect: selectSensor,
        });
    }
    lab.addEventListener('keydown', event => {
        if (event.key === 'Escape') selectSensor('water-temp');
    });
    window.addEventListener('pagehide', () => {
        provider.destroy();
    }, { once: true });
}
