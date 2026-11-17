export const SENSOR_THRESHOLDS = Object.freeze({
    'air-temp': { min: 18, max: 30, criticalMin: 10, criticalMax: 36 },
    'air-humidity': { min: 40, max: 70, criticalMin: 25, criticalMax: 85 },
    'water-temp': { min: 20, max: 28, criticalMin: 16, criticalMax: 32 },
    'water-level': { min: 40, max: 95, criticalMin: 20, criticalMax: 100 },
    turbidity: { min: 0, max: 25, criticalMin: 0, criticalMax: 50 },
    ph: { min: 6, max: 8, criticalMin: 5, criticalMax: 9 },
});

const SENSOR_DETAILS = Object.freeze({
    'air-temp': { name: 'Температура воздуха', unit: '°C', initial: 22.6, amplitude: 0.4, precision: 1 },
    'air-humidity': { name: 'Влажность воздуха', unit: '%', initial: 58, amplitude: 2, precision: 0 },
    'water-temp': { name: 'Температура воды', unit: '°C', initial: 23.4, amplitude: 0.3, precision: 1 },
    'water-level': { name: 'Уровень воды', unit: '%', initial: 76, amplitude: 1.5, precision: 0 },
    turbidity: { name: 'Мутность воды', unit: 'NTU', initial: 8.2, amplitude: 1, precision: 1 },
    ph: { name: 'Кислотность воды', unit: 'pH', initial: 7.1, amplitude: 0.15, precision: 1 },
});

function getStatus(id, value, connected) {
    if (!connected) return 'OFFLINE';

    const threshold = SENSOR_THRESHOLDS[id];
    if (value < threshold.criticalMin || value > threshold.criticalMax) return 'CRITICAL';
    if (value < threshold.min || value > threshold.max) return 'WARNING';
    return 'NORMAL';
}

/**
 * Provider contract: subscribe(listener), getSnapshot(), setValue(id, value), destroy().
 * A real provider can implement this contract without changing the presentation.
 */
export function createDemoProvider({ interval = 3000, now = Date.now } = {}) {
    const listeners = new Set();
    const startedAt = now();
    const readings = Object.fromEntries(
        Object.entries(SENSOR_DETAILS).map(([id, details]) => [id, details.initial]),
    );
    let connected = true;
    let timerId;

    function getSnapshot() {
        return {
            source: 'DEMO',
            connected,
            updatedAt: new Date(now()),
            readings: Object.fromEntries(
                Object.entries(readings).map(([id, value]) => [
                    id,
                    {
                        ...SENSOR_DETAILS[id],
                        value,
                        status: getStatus(id, value, connected),
                        threshold: SENSOR_THRESHOLDS[id],
                    },
                ]),
            ),
            camera: { status: connected ? 'DEMO' : 'OFFLINE', image: null, capturedAt: null },
        };
    }

    function notify() {
        const snapshot = getSnapshot();
        listeners.forEach(listener => listener(snapshot));
    }

    function advance() {
        const elapsed = (now() - startedAt) / 1000;
        Object.entries(SENSOR_DETAILS).forEach(([id, details], index) => {
            readings[id] = Number((
                details.initial
                + Math.sin(elapsed / (8 + index * 2) + index) * details.amplitude
            ).toFixed(details.precision));
        });
        notify();
    }

    timerId = window.setInterval(advance, interval);

    return {
        getSnapshot,
        subscribe(listener) {
            listeners.add(listener);
            return () => listeners.delete(listener);
        },
        setValue(id, value) {
            if (!(id in SENSOR_DETAILS)) throw new RangeError(`Unknown sensor: ${id}`);
            if (!Number.isFinite(value)) throw new TypeError('Sensor value must be a finite number');
            readings[id] = Number(value.toFixed(SENSOR_DETAILS[id].precision));
            notify();
        },
        setConnected(value) {
            connected = Boolean(value);
            notify();
        },
        destroy() {
            window.clearInterval(timerId);
            listeners.clear();
        },
    };
}
