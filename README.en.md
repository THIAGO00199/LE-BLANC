# LE BLANC 2.5 — Local Council and Defensive Review

LE BLANC is a local multi-persona assistant for software planning, strategic analysis, privacy review, and defensive security learning.

## Architecture

- Local Ollama endpoint at `127.0.0.1:11435`; the system Ollama service on port 11434 is left untouched.
- One model loaded at a time to fit constrained hardware.
- Six focused personas: Professor, Rio, Denver, Alicia, Tokyo, and Helsinki.
- A lightweight local web panel built with Python's standard library.
- A command-line interface for individual personas, a council session, and a defensive read-only review.

## Start the panel

```bash
cd ~/LE-BLANC
python3 painel.py
```

Open http://127.0.0.1:8765 on the same computer. The panel listens only on loopback and is not exposed to the local network.

## CLI examples

```bash
python3 orquestrador.py --version
python3 orquestrador.py --list-models
python3 orquestrador.py --role denver "Compare costs, risks, and alternatives."
python3 orquestrador.py --chat --role tokyo
python3 orquestrador.py --council
python3 orquestrador.py --guard --no-ai
```

## Safety and limitations

The guard mode performs local read-only checks and one HTTPS GET request to the fixed public CISA Known Exploited Vulnerabilities catalogue. It does not scan external hosts, exploit vulnerabilities, modify system settings, or execute model-generated commands. A detected VPN process does not prove that traffic is routed through a VPN; an inactive systemd firewall unit does not prove that kernel firewall rules are absent; and a KEV entry does not prove that this computer is vulnerable.

Model outputs are suggestions, not approvals or actions. The user remains responsible for decisions. Local audit reports and machine-specific data are excluded from this repository.

---

[Português](./README.md) · [Español](./README.es.md)
