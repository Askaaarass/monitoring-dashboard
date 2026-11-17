# System architecture

Planned data path: ESP32 sensors → Wi-Fi → backend API or MQTT bridge → website data provider → dashboard and 3D presentation.

The website is built with Django and Django REST Framework. Its project page includes a Three.js scene with independent procedural objects and a GSAP ScrollTrigger assembly animation.

The website currently demonstrates the dashboard with a DEMO provider. A deployed ESP32 telemetry connection is planned, not implemented.
