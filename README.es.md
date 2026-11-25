# LE BLANC 2.5 — Consejo local y revisión defensiva

LE BLANC es un asistente local multi-persona para planificación de software, análisis estratégico, revisión de privacidad y aprendizaje de seguridad defensiva.

## Arquitectura

- Endpoint local de Ollama en `127.0.0.1:11435`; el servicio del sistema en el puerto 11434 permanece intacto.
- Un solo modelo cargado a la vez para ajustarse a equipos con recursos limitados.
- Seis personas especializadas: Professor, Rio, Denver, Alicia, Tokyo y Helsinki.
- Panel web local con la biblioteca estándar de Python.
- Interfaz de línea de comandos para personas individuales, una sesión de consejo y una revisión defensiva de solo lectura.

## Iniciar el panel

```bash
cd ~/LE-BLANC
python3 painel.py
```

Abre http://127.0.0.1:8765 en el mismo equipo. El panel escucha únicamente en loopback y no está expuesto a la red local.

## Ejemplos de CLI

```bash
python3 orquestrador.py --version
python3 orquestrador.py --list-models
python3 orquestrador.py --role denver "Compara costos, riesgos y alternativas."
python3 orquestrador.py --chat --role tokyo
python3 orquestrador.py --council
python3 orquestrador.py --guard --no-ai
```

## Seguridad y limitaciones

El modo guard realiza comprobaciones locales de solo lectura y una solicitud HTTPS GET al catálogo público fijo CISA Known Exploited Vulnerabilities. No escanea hosts externos, explota vulnerabilidades, modifica la configuración del sistema ni ejecuta comandos generados por modelos. Detectar un proceso VPN no demuestra que el tráfico pase por una VPN; una unidad de firewall de systemd inactiva no demuestra que no existan reglas en el kernel; y una entrada KEV no demuestra que este equipo sea vulnerable.

Las respuestas de los modelos son sugerencias, no aprobaciones ni acciones. El usuario conserva la responsabilidad de decidir. Los informes locales de auditoría y los datos específicos del equipo están excluidos de este repositorio.

---

[Português](./README.md) · [English](./README.en.md)
