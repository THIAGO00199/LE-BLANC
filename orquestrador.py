#!/usr/bin/env python3
"""LE BLANC 2.5 — conselho local, análise estratégica e auditoria defensiva.

O modo --guard consulta somente o catálogo público KEV da CISA por HTTPS
e faz verificações locais de leitura. Não executa exploração, varredura de
rede, força bruta, alteração de configurações ou comandos sugeridos por IA.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_BASE = "http://127.0.0.1:11435"
FALLBACK_MODEL = "qwen2.5:3b"
VERSION = "2.5"
KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)
PROJECT_DIR = Path(__file__).resolve().parent
REPORT_DIR = PROJECT_DIR / "reports"

MODELS = {
    "professor": "deepseek-r1:1.5b",
    "rio": "qwen2.5-coder:1.5b",
    "denver": "qwen2.5:3b",
    "alicia": "qwen2.5:3b",
    "tokyo": "qwen2.5:3b",
    "helsinki": "qwen2.5:3b",
}

SYSTEM_BASE = (
    "Você é LE BLANC 2.5, assistente local em português brasileiro. "
    "Atue somente em programação, aprendizagem e segurança defensiva. "
    "Analise dados fornecidos, explique riscos, recomende atualizações e "
    "melhorias para dispositivos próprios. Não instrua invasões, exploração "
    "de falhas, roubo de credenciais, malware, persistência furtiva, "
    "exfiltração, apagamento de rastros, evasão de monitoramento, varreduras "
    "de terceiros ou contorno de controles. Não afirme que executou ações. "
    "Nunca execute código ou comandos produzidos por modelos."
)

ROLE_GUIDANCE = {
    "professor": (
        "PERFIL PROFESSOR — raciocínio e planejamento. Separe fatos, hipóteses "
        "e lacunas; priorize riscos e apresente etapas verificáveis."
    ),
    "rio": (
        "PERFIL RIO — engenharia de software. Priorize código legível, testes, "
        "tratamento de erros e revisão estática. Não execute código."
    ),
    "denver": (
        "PERFIL DENVER — Strategic Value Analyst. Avalie o que pode ser ganho, "
        "perdido ou comprometido e o que precisa ser feito. Estruture: (1) valor "
        "e benefício esperado; (2) perdas e impactos possíveis; (3) custos de "
        "tempo, dinheiro, recursos e complexidade; (4) pré-requisitos e "
        "dependências; (5) etapas priorizadas; (6) alternativas e plano B; "
        "(7) recomendação fundamentada. Diferencie fatos, estimativas e "
        "desconhecidos. Nunca invente valores monetários, probabilidades ou "
        "números: declare lacunas quando faltarem dados. Denver não é líder, "
        "não autoriza operações e não executa ações; entrega análise para o "
        "usuário decidir."
    ),
    "alicia": (
        "PERFIL ALICIA — análise de influência e negociação ética. Identifique "
        "pressões, inconsistências e interesses sem coerção, fraude ou "
        "exploração de vulnerabilidades pessoais."
    ),
    "tokyo": (
        "PERFIL TOKYO — Privacy & Security Sentinel. Revise exposição de dados, "
        "permissões, sinais locais de ferramentas de privacidade e limitações "
        "de VPN/Tor. Um processo ou interface detectado NÃO comprova túnel ativo, "
        "rota padrão, DNS protegido ou cobertura de todo o tráfego. O nível de "
        "privilégio 'regular user' não permite concluir que um serviço VPN não "
        "funciona. Serviços de firewall inativos NÃO provam ausência de regras no "
        "kernel. O catálogo KEV NÃO prova que este sistema seja afetado. Não ensine "
        "a ocultar atividades, apagar rastros ou evitar auditoria."
    ),
    "helsinki": (
        "PERFIL HELSINKI — Network Guardian. Avalie somente informações locais "
        "de interfaces, indicadores de firewall e conectividade. O estado systemd "
        "de unidades firewalld/ufw/nftables não representa uma inspeção das regras "
        "do kernel; não conclua que não há firewall apenas porque essas unidades "
        "estão inativas. Um nome de interface VPN não prova que o tráfego a utiliza. "
        "Recomende hardening e manutenção. Não faça sondagens, scans ou testes "
        "em hosts externos; não altere a rede."
    ),
}

class OllamaError(RuntimeError):
    pass


def request_json(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_BASE + path,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OllamaError(
            f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:500]}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise OllamaError(f"Ollama local indisponível em {API_BASE}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise OllamaError("Resposta JSON inválida do Ollama.") from exc
    if not isinstance(result, dict):
        raise OllamaError("Formato inesperado da API local.")
    return result


def installed_models() -> set[str]:
    return {
        model.get("name", "")
        for model in request_json("/api/tags").get("models", [])
    }


def choose_model(role: str, available: set[str]) -> str:
    preferred = MODELS[role]
    if preferred in available:
        return preferred
    if FALLBACK_MODEL in available:
        print(
            f"[aviso] {preferred} não está instalado; usando {FALLBACK_MODEL}.",
            file=sys.stderr,
        )
        return FALLBACK_MODEL
    raise OllamaError("Nenhum modelo leve disponível. Confira --list-models.")


def chat(
    role: str,
    prompt: str,
    max_tokens: int = 360,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    model = choose_model(role, installed_models())
    messages = [
        {
            "role": "system",
            "content": SYSTEM_BASE + "\n\n" + ROLE_GUIDANCE[role],
        }
    ]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": prompt})
    result = request_json("/api/chat", {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "20s",
        "options": {
            "temperature": 0.2,
            "num_ctx": 2048,
            "num_predict": max_tokens,
        },
    })
    answer = result.get("message", {}).get("content", "")
    if not isinstance(answer, str) or not answer.strip():
        raise OllamaError("Modelo respondeu sem conteúdo.")
    return model, answer.strip()


def list_models() -> None:
    models = request_json("/api/tags").get("models", [])
    if not models:
        print("Nenhum modelo disponível.")
        return
    for item in models:
        size = item.get("size", 0) / (1024 ** 3)
        print(f"- {item.get('name')} ({size:.2f} GiB)")


def read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, _, rest = line.partition(":")
            parts = rest.strip().split()
            if parts and parts[0].isdigit():
                values[key] = int(parts[0]) * 1024
    except OSError:
        pass
    return values


def read_process_indicators() -> list[str]:
    """Retorna apenas nomes de processos conhecidos; nunca lê argumentos."""
    names = {
        "tor": "Tor",
        "openvpn": "OpenVPN",
        "wg-quick": "WireGuard helper",
        "warp-svc": "Cloudflare WARP service",
        "windscribe": "Windscribe service",
        "mullvad-daemon": "Mullvad service",
        "tailscaled": "Tailscale service",
        "protonvpn": "Proton VPN process",
    }
    found: set[str] = set()
    proc = Path("/proc")
    try:
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                comm = (entry / "comm").read_text(encoding="utf-8").strip().lower()
            except (OSError, UnicodeError):
                continue
            for key, label in names.items():
                if comm == key or comm.startswith(key + "-"):
                    found.add(label)
    except OSError:
        return []
    return sorted(found)


def firewall_status() -> dict[str, str]:
    status: dict[str, str] = {}
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return {"systemd": "systemctl indisponível"}
    for unit in ("firewalld", "ufw", "nftables"):
        try:
            result = subprocess.run(
                [systemctl, "is-active", unit],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            state = result.stdout.strip() or result.stderr.strip()
            status[unit] = state if result.returncode == 0 else (state or "inativo/não identificado")
        except (OSError, subprocess.TimeoutExpired):
            status[unit] = "não foi possível consultar"
    return status


def collect_local_posture() -> dict[str, Any]:
    interfaces: list[str] = []
    try:
        interfaces = sorted(
            name for name in os.listdir("/sys/class/net") if name != "lo"
        )
    except OSError:
        pass

    mem = read_meminfo()
    disk = shutil.disk_usage("/")
    return {
        "observed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "system": platform.system(),
        "distribution": platform.freedesktop_os_release().get("PRETTY_NAME", "Linux")
            if hasattr(platform, "freedesktop_os_release") else platform.platform(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "memory_total_gib": round(mem.get("MemTotal", 0) / (1024 ** 3), 2),
        "memory_available_gib": round(mem.get("MemAvailable", 0) / (1024 ** 3), 2),
        "root_free_gib": round(disk.free / (1024 ** 3), 2),
        "network_interfaces": interfaces,
        "vpn_or_privacy_process_indicators": read_process_indicators(),
        "firewall_services": firewall_status(),
        "firewall_scope_note": (
            "Somente estado de unidades systemd conhecidas; nenhuma regra do "
            "kernel foi inspecionada. Unidades inativas não provam ausência de regras."
        ),
        "privilege_level": "elevated" if hasattr(os, "geteuid") and os.geteuid() == 0 else "regular user",
        "scope": "somente leitura local; sem sondagem de rede",
    }


def fetch_cisa_kev() -> dict[str, Any]:
    """Busca um único feed público fixo; sem URLs fornecidas pelo utilizador."""
    request = urllib.request.Request(
        KEV_URL,
        headers={"User-Agent": "LE-BLANC/2.4 defensive-audit"},
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("Feed excedeu o limite de tamanho.")
        data = json.loads(raw.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Não foi possível obter o feed CISA por HTTPS: {exc}") from exc

    entries = data.get("vulnerabilities", [])
    if not isinstance(entries, list):
        raise RuntimeError("Formato inesperado no catálogo CISA.")
    recent = sorted(
        entries,
        key=lambda item: str(item.get("dateAdded", "")),
        reverse=True,
    )[:5]
    return {
        "source": "CISA Known Exploited Vulnerabilities (KEV)",
        "catalog_version": data.get("catalogVersion"),
        "date_released": data.get("dateReleased"),
        "total_entries": len(entries),
        "recent_entries": [
            {
                "cve": item.get("cveID"),
                "vendor": item.get("vendorProject"),
                "product": item.get("product"),
                "date_added": item.get("dateAdded"),
                "name": item.get("vulnerabilityName"),
            }
            for item in recent
        ],
        "note": (
            "O catálogo indica vulnerabilidades exploradas no mundo real; "
            "não significa que este computador esteja vulnerável a elas."
        ),
    }


def save_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    destination = REPORT_DIR / f"guard_{stamp}.json"
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def print_guard_summary(report: dict[str, Any]) -> None:
    local = report["local"]
    kev = report.get("cisa_kev")
    print("\n=== LE BLANC 2.4 | GUARD ===")
    print(f"Sistema: {local['distribution']} | kernel {local['kernel']}")
    print(
        f"Memória disponível: {local['memory_available_gib']} GiB | "
        f"espaço livre em /: {local['root_free_gib']} GiB"
    )
    print("Interfaces:", ", ".join(local["network_interfaces"]) or "não identificadas")
    indicators = local["vpn_or_privacy_process_indicators"]
    print("Indicadores de privacidade:", ", ".join(indicators) if indicators else "nenhum processo conhecido detectado")
    print("Firewall (estado de unidades systemd):", json.dumps(local["firewall_services"], ensure_ascii=False))
    print("Nota:", local["firewall_scope_note"])
    if kev:
        print(
            f"CISA KEV: catálogo {kev.get('catalog_version')} | "
            f"{kev.get('total_entries')} registros | "
            f"última atualização {kev.get('date_released')}"
        )
        for item in kev.get("recent_entries", [])[:3]:
            print(f"  - {item.get('cve')}: {item.get('vendor')} / {item.get('product')} ({item.get('date_added')})")
    else:
        print("CISA KEV: indisponível nesta execução.")
    print("\nAtenção: detectar um processo VPN/Tor não comprova que o tráfego passe por ele.")
    print("Nenhum scan, exploração, alteração de rede ou ação em terceiros foi realizado.")


def run_guard(use_ai: bool = True) -> int:
    print("[1/4] Tokyo: verificando postura local e sinais de privacidade...")
    local = collect_local_posture()

    print("[2/4] Helsinki: consultando indicadores de rede e firewall (somente leitura)...")
    print("[3/4] Conectando por HTTPS ao catálogo público CISA KEV...")
    kev: dict[str, Any] | None = None
    kev_error: str | None = None
    try:
        kev = fetch_cisa_kev()
    except (RuntimeError, ValueError) as exc:
        kev_error = str(exc)

    report: dict[str, Any] = {
        "version": VERSION,
        "mode": "defensive_read_only",
        "local": local,
        "cisa_kev": kev,
        "cisa_error": kev_error,
        "network_actions": "somente GET HTTPS para o feed público CISA KEV",
        "system_actions": "consultas locais de leitura; nenhuma configuração alterada",
    }
    path = save_report(report)
    print_guard_summary(report)
    print(f"\nRelatório local salvo em: {path}")

    if not use_ai:
        return 0

    context = json.dumps(report, ensure_ascii=False)
    prompts = (
        (
            "tokyo",
            "Analise estes dados locais como Privacy Sentinel. Separe fatos, "
            "indícios e desconhecidos. Não infira que uma VPN está a funcionar "
            "apenas por haver processo/interface detetado; não use 'regular user' "
            "para concluir que um túnel não funciona. Não diga que KEVs afetam "
            "esta máquina sem evidência de produto/versão. Unidades de firewall "
            "inativas não provam ausência de regras. Dê até três recomendações "
            "defensivas e não prometa anonimato.\n\n" + context,
        ),
        (
            "helsinki",
            "Analise estes dados locais como Network Guardian. Avalie firewall, "
            "interfaces e limitações do inventário. O estado systemd de três "
            "unidades não inspeciona as regras do kernel; não conclua que não "
            "existe firewall. Um indicador VPN não comprova túnel ou rota ativa. "
            "Não afirme que CVEs KEV afetam esta máquina sem confirmar produto "
            "e versão. Sugira hardening defensivo e não proponha scans ou testes "
            "em hosts externos.\n\n" + context,
        ),
    )
    for role, prompt in prompts:
        print(f"\n[4/4] {role.upper()} está analisando...")
        try:
            model, answer = chat(role, prompt, 300)
            print(f"\n[{role.upper()} | {model}]\n{answer}")
        except (OllamaError, OSError, ValueError) as exc:
            print(f"[aviso] Análise de {role} indisponível: {exc}", file=sys.stderr)
    print("\n[GUARD concluído] Nenhuma ação ofensiva ou alteração do sistema foi executada.")
    return 0


def interactive_chat(role: str) -> None:
    history: list[dict[str, str]] = []
    print(f"\nLE BLANC {VERSION} | {role.upper()}")
    print("Conversa contínua ativada. Digite /sair para encerrar ou /limpar para limpar o contexto.")
    print("O histórico fica somente nesta sessão e mantém as últimas cinco trocas.\n")
    while True:
        try:
            prompt = input("Você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSessão encerrada.")
            return
        if not prompt:
            continue
        command = prompt.lower()
        if command in {"/sair", "sair", "exit", "quit"}:
            print("Sessão encerrada.")
            return
        if command in {"/limpar", "limpar"}:
            history.clear()
            print("[Contexto da conversa limpo.]")
            continue
        try:
            model, answer = chat(role, prompt, 420, history)
            print(f"\n[{role.upper()} | {model}]\n{answer}\n")
            history.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ])
            history = history[-10:]
        except (OllamaError, OSError, ValueError) as exc:
            print(f"[erro] {exc}", file=sys.stderr)


COUNCIL_ORDER = ("professor", "rio", "denver", "alicia", "tokyo", "helsinki")


def council_chat() -> None:
    transcript: list[str] = []
    print(f"\nLE BLANC {VERSION} | MESA REDONDA")
    print("As seis personas participam em sequência e podem responder umas às outras.")
    print("Digite /sair para encerrar ou /limpar para iniciar um novo assunto.\n")
    while True:
        try:
            topic = input("Você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMesa encerrada.")
            return
        if not topic:
            continue
        if topic.lower() in {"/sair", "sair", "exit", "quit"}:
            print("Mesa encerrada.")
            return
        if topic.lower() in {"/limpar", "limpar"}:
            transcript.clear()
            print("[Discussão anterior removida do contexto.]")
            continue

        transcript.append("USUÁRIO: " + topic)
        print("\n========== NOVA RODADA ==========")
        for role in COUNCIL_ORDER:
            discussion = "\n\n".join(transcript[-12:])[-5200:]
            prompt = (
                "Você participa de uma mesa-redonda com outras cinco personas do LE BLANC. "
                "Leia a conversa e contribua com sua especialidade. Responda diretamente "
                "ao usuário e, quando útil, concorde, discorde ou complemente uma fala "
                "anterior citando a persona. Não repita tudo o que já foi dito. Seja "
                "objetivo (até 100 palavras), indique incertezas e proponha apenas ações "
                "legais, autorizadas e defensivas. Não execute ferramentas, comandos ou "
                "ações externas.\n\nTRANSCRIÇÃO ATÉ AGORA:\n" + discussion
            )
            try:
                model, answer = chat(role, prompt, 150)
                line = f"{role.upper()}: {answer}"
                transcript.append(line)
                print(f"\n[{role.upper()} | {model}]\n{answer}\n")
            except (OllamaError, OSError, ValueError) as exc:
                line = f"{role.upper()}: indisponível nesta rodada ({exc})"
                transcript.append(line)
                print(f"[aviso] {line}", file=sys.stderr)
        print("========== FIM DA RODADA ==========")
        print("Você pode responder para iniciar outra rodada; /limpar reinicia o assunto.\n")


def repair_demo() -> None:
    buggy = 'STATUS = "LE BLANC OFF"\nprint(STATUS)'
    expected = "LE BLANC ON"
    feedback = ""
    print("[2.4] Depuração demonstrativa — código gerado nunca é executado.")
    for attempt in range(1, 4):
        prompt = (
            "Analise este trecho didático e proponha apenas a correção textual.\n"
            f"Trecho:\n{buggy}\n"
            f"O valor correto de STATUS deve ser exatamente {expected!r}.\n"
            "Responda: DIAGNOSTICO: ... e CORRECAO: STATUS = ... . "
            "Não inclua comandos de terminal."
            + (f"\nFeedback anterior: {feedback}" if feedback else "")
        )
        model, answer = chat("rio", prompt, 180)
        print(f"\n[Tentativa {attempt}/3 | {model}]\n{answer}")
        if expected in answer and "STATUS" in answer:
            print("\n[VALIDADOR] Critério textual satisfeito: LE BLANC ON.")
            return
        feedback = "Inclua o literal LE BLANC ON na correção."
    print("\n[VALIDADOR] Limite atingido. Nenhum código foi executado.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LE BLANC 2.5 — conselho local, análise estratégica e auditoria defensiva."
    )
    parser.add_argument("--version", action="version", version=f"LE BLANC {VERSION}")
    parser.add_argument("--role", choices=tuple(MODELS), default="denver")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="abre uma conversa contínua com a persona escolhida em --role",
    )
    parser.add_argument(
        "--council",
        action="store_true",
        help="abre uma mesa-redonda contínua com as seis personas",
    )
    parser.add_argument(
        "--guard",
        action="store_true",
        help="executa auditoria local de leitura + consulta HTTPS ao feed CISA KEV",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="com --guard, gera relatório sem chamar modelos locais",
    )
    parser.add_argument(
        "--repair-demo",
        action="store_true",
        help="demonstra depuração textual controlada",
    )
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()

    if args.no_ai and not args.guard:
        parser.error("--no-ai só pode ser usado com --guard")
    if sum((args.list_models, args.guard, args.repair_demo, args.chat, args.council)) > 1:
        parser.error("Escolha apenas uma ação entre --list-models, --guard, --repair-demo, --chat e --council")
    if (args.chat or args.council) and args.prompt:
        parser.error("Não informe texto junto com --chat/--council; digite as mensagens dentro da sessão.")

    try:
        if args.list_models:
            list_models()
        elif args.guard:
            return run_guard(use_ai=not args.no_ai)
        elif args.repair_demo:
            repair_demo()
        elif args.chat:
            interactive_chat(args.role)
        elif args.council:
            council_chat()
        else:
            prompt = " ".join(args.prompt).strip() or input("LE BLANC > ").strip()
            if not prompt:
                print("Nenhuma tarefa informada.", file=sys.stderr)
                return 2
            model, answer = chat(args.role, prompt)
            print(f"\n[LE BLANC {VERSION} | {args.role.upper()} | {model}]\n\n{answer}")
            print("\n[Análise textual; nenhuma ação externa foi executada.]")
        return 0
    except (OllamaError, OSError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
