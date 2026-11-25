#!/usr/bin/env python3
"""LE BLANC 2.5 — painel local, limitado ao loopback."""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import orquestrador as lb

HOST, PORT = "127.0.0.1", 8765
ROLES = ("professor", "rio", "denver", "alicia", "tokyo", "helsinki")

HTML = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LE BLANC // Control Room</title>
<style>
:root{color-scheme:dark;--bg:#090b10;--panel:#111620;--line:#263244;--muted:#8d9aab;--txt:#e9eef6;--cyan:#79e0d2;--gold:#e8bd73;--red:#e58d8d}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 15% 0%,#182331 0,transparent 40%),var(--bg);color:var(--txt);font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}
header{height:76px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 28px;background:#0b0f16dd;position:sticky;top:0;backdrop-filter:blur(14px);z-index:2}
.brand{letter-spacing:.22em;font-size:14px;font-weight:800}.brand span{color:var(--cyan)}.status{color:var(--muted);font-size:12px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--cyan);margin-right:8px;box-shadow:0 0 12px var(--cyan)}
main{max-width:1440px;margin:auto;padding:28px;display:grid;grid-template-columns:245px minmax(0,1fr);gap:22px}
aside,.panel{background:linear-gradient(145deg,#141b26,#0e131c);border:1px solid var(--line);border-radius:16px}
aside{padding:18px;height:max-content} .eyebrow{font-size:10px;letter-spacing:.18em;color:var(--muted);text-transform:uppercase;margin:4px 0 14px}
nav button{width:100%;text-align:left;background:transparent;color:var(--muted);border:1px solid transparent;padding:12px;border-radius:10px;margin:3px 0;cursor:pointer}
nav button.active,nav button:hover{background:#1a2632;border-color:#304151;color:var(--cyan)}
.persona{padding:11px 0;border-top:1px solid #202b38;display:flex;justify-content:space-between;gap:8px;font-size:13px}.persona small{color:var(--muted)}
.content{min-width:0}.hero{display:flex;justify-content:space-between;align-items:end;margin:2px 0 20px;gap:20px}.hero h1{font-size:clamp(24px,3vw,36px);letter-spacing:-.04em;margin:0}.hero p{color:var(--muted);margin:5px 0 0}.tag{border:1px solid #31524f;color:var(--cyan);padding:6px 10px;border-radius:99px;font-size:11px;white-space:nowrap}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}.metric{background:#101721;border:1px solid var(--line);border-radius:13px;padding:15px}.metric small{color:var(--muted)}.metric strong{display:block;font-size:19px;margin-top:4px}
.panel{padding:18px;margin-bottom:15px}.panel h2{font-size:14px;letter-spacing:.04em;margin:0 0 12px}.chatlog{height:410px;overflow:auto;display:flex;flex-direction:column;gap:10px;padding:4px 2px 14px}
.msg{max-width:88%;padding:12px 14px;border-radius:12px;background:#182230;border:1px solid #29394b;white-space:pre-wrap;overflow-wrap:anywhere}.msg.user{align-self:flex-end;background:#17302f;border-color:#2b5551}.msg .who{font-size:10px;letter-spacing:.12em;color:var(--cyan);margin-bottom:5px;font-weight:700}.msg.user .who{color:var(--gold)}
.composer{display:flex;gap:10px;margin-top:12px}textarea,select{background:#0b1119;border:1px solid #2b3949;color:var(--txt);border-radius:10px;padding:12px;font:inherit}textarea{width:100%;min-height:76px;resize:vertical}select{min-width:155px}
button.action{background:var(--cyan);color:#071210;border:0;border-radius:10px;padding:11px 16px;font-weight:800;cursor:pointer}button.secondary{background:#1b2734;color:var(--txt);border:1px solid #334356;border-radius:10px;padding:10px 13px;cursor:pointer}
.toolbar{display:flex;flex-wrap:wrap;gap:9px;margin:12px 0}.note{font-size:12px;color:var(--muted)}.hidden{display:none}.report{white-space:pre-wrap;color:#cbd6e4;font-size:13px;overflow-wrap:anywhere}
@media(max-width:850px){main{grid-template-columns:1fr;padding:14px}aside{order:2}header{padding:0 16px}.grid{grid-template-columns:1fr}.hero{align-items:start;flex-direction:column}.composer{flex-direction:column}.msg{max-width:96%}}
</style></head><body>
<header><div class="brand">LE <span>BLANC</span> / CONTROL ROOM</div><div class="status"><i class="dot"></i><span id="connection">VERIFICANDO MOTOR LOCAL</span></div></header>
<main><aside><div class="eyebrow">Navegação</div><nav>
<button class="active" data-tab="council">◈ Conselho</button><button data-tab="denver">◈ Denver / Estratégia</button><button data-tab="guard">◈ Auditoria defensiva</button>
</nav><div class="eyebrow" style="margin-top:25px">Unidades ativas</div>
<div class="persona"><span>Professor</span><small>Raciocínio</small></div><div class="persona"><span>Rio</span><small>Engenharia</small></div><div class="persona"><span>Denver</span><small>Valor & perdas</small></div><div class="persona"><span>Alicia</span><small>Comunicação</small></div><div class="persona"><span>Tokyo</span><small>Privacidade</small></div><div class="persona"><span>Helsinki</span><small>Infraestrutura</small></div>
<p class="note" style="margin-top:18px">Execução sequencial · um modelo por vez · processamento local.</p></aside>
<section class="content"><div class="hero"><div><h1 id="heading">Mesa-redonda</h1><p id="subheading">Seis perspectivas, uma conversa compartilhada.</p></div><span class="tag">LOCAL FIRST / v2.5</span></div>
<div class="grid"><div class="metric"><small>Motor de inferência</small><strong>Ollama local</strong></div><div class="metric"><small>Endereço</small><strong>127.0.0.1:11435</strong></div><div class="metric"><small>Política</small><strong>Human-in-the-loop</strong></div></div>
<div id="council" class="tab panel"><h2>CONSELHO / CONVERSA COMPARTILHADA</h2><div id="log" class="chatlog"><div class="msg"><div class="who">LE BLANC</div>Conselho pronto. Envie um tema para iniciar uma rodada. As personas respondem em sequência.</div></div><div class="composer"><textarea id="prompt" placeholder="Defina o objetivo, contexto e limites..."></textarea></div><div class="toolbar"><button class="action" id="sendCouncil">Iniciar rodada completa</button><button class="secondary" id="clear">Limpar conversa</button></div><div class="note">Uma rodada completa chama seis modelos sequencialmente; pode levar alguns minutos no notebook.</div></div>
<div id="denver" class="tab panel hidden"><h2>DENVER / ANÁLISE DE VALOR E CONSEQUÊNCIAS</h2><div id="denverLog" class="chatlog"><div class="msg"><div class="who">DENVER</div>Informe uma decisão ou projeto. Vou analisar ganhos, perdas, custos, pré-requisitos, prioridades e plano B — sem inventar números que não foram fornecidos.</div></div><div class="composer"><textarea id="denverPrompt" placeholder="O que estamos considerando fazer? Quais dados já temos?"></textarea></div><div class="toolbar"><button class="action" id="askDenver">Avaliar cenário</button></div></div>
<div id="guard" class="tab panel hidden"><h2>AUDITORIA DEFENSIVA / SOMENTE LEITURA</h2><p class="note">Inventário local, indicadores de privacidade/firewall e consulta HTTPS fixa ao catálogo público CISA KEV. Não executa scans, exploração ou alterações no sistema.</p><div class="toolbar"><button class="action" id="runGuard">Executar auditoria</button></div><div id="guardResult" class="report">Nenhuma auditoria executada nesta sessão.</div></div>
</section></main>
<script>
const $=id=>document.getElementById(id), log=$('log');
function add(target,who,text,cls=''){const d=document.createElement('div');d.className='msg '+cls;const w=document.createElement('div');w.className='who';w.textContent=who;const b=document.createElement('div');b.textContent=text;d.append(w,b);target.append(d);target.scrollTop=target.scrollHeight}
async function post(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)throw Error(j.error||'Falha na solicitação');return j}
function busy(button,on,label){button.disabled=on;button.textContent=on?'Processando…':label}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.tab').forEach(x=>x.classList.add('hidden'));$(b.dataset.tab).classList.remove('hidden');$('heading').textContent={council:'Mesa-redonda',denver:'Denver / Estratégia',guard:'Auditoria defensiva'}[b.dataset.tab];$('subheading').textContent={council:'Seis perspectivas, uma conversa compartilhada.',denver:'Avaliação de valor, custos, perdas e próximos passos.',guard:'Inventário local e inteligência pública.'}[b.dataset.tab]});
$('sendCouncil').onclick=async()=>{const p=$('prompt').value.trim();if(!p)return;add(log,'VOCÊ',p,'user');$('prompt').value='';const b=$('sendCouncil');busy(b,true,'Iniciar rodada completa');try{const r=await post('/api/council',{prompt:p});for(const x of r.replies)add(log,x.role.toUpperCase()+' / '+x.model,x.answer); }catch(e){add(log,'ERRO',e.message)}finally{busy(b,false,'Iniciar rodada completa')}};
$('clear').onclick=()=>{log.replaceChildren();add(log,'LE BLANC','Contexto visual limpo. A próxima rodada começa um novo assunto.')};
$('askDenver').onclick=async()=>{const p=$('denverPrompt').value.trim();if(!p)return;const l=$('denverLog');add(l,'VOCÊ',p,'user');$('denverPrompt').value='';const b=$('askDenver');busy(b,true,'Avaliar cenário');try{const r=await post('/api/chat',{role:'denver',prompt:p});add(l,'DENVER / '+r.model,r.answer)}catch(e){add(l,'ERRO',e.message)}finally{busy(b,false,'Avaliar cenário')}};
$('runGuard').onclick=async()=>{const b=$('runGuard');busy(b,true,'Executando auditoria');$('guardResult').textContent='Coletando dados locais e consultando feed público…';try{const r=await post('/api/guard',{});$('guardResult').textContent=JSON.stringify(r,null,2)}catch(e){$('guardResult').textContent='Erro: '+e.message}finally{busy(b,false,'Executar auditoria')}};
fetch('/api/status').then(r=>r.json()).then(x=>$('connection').textContent=x.ok?'OLLAMA CONECTADO / '+x.models.length+' MODELOS':'OLLAMA INDISPONÍVEL').catch(()=>$('connection').textContent='API LOCAL INDISPONÍVEL');
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[painel]", fmt % args)

    def send_json(self, obj, status=200):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/":
            raw = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif self.path == "/api/status":
            try:
                models = sorted(lb.installed_models())
                self.send_json({"ok": True, "models": models, "version": lb.VERSION})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc), "models": []}, 503)
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 16000:
                return self.send_json({"error": "Corpo ausente ou acima de 16 KB."}, 413)
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(data, dict):
                return self.send_json({"error": "JSON inválido."}, 400)
            if self.path == "/api/chat":
                role, prompt = data.get("role"), str(data.get("prompt", "")).strip()
                if role not in ROLES or not prompt:
                    return self.send_json({"error": "Persona ou mensagem inválida."}, 400)
                model, answer = lb.chat(role, prompt, 280)
                return self.send_json({"role": role, "model": model, "answer": answer})
            if self.path == "/api/council":
                prompt = str(data.get("prompt", "")).strip()
                if not prompt:
                    return self.send_json({"error": "Informe um tema."}, 400)
                transcript = ["USUÁRIO: " + prompt]
                replies = []
                for role in lb.COUNCIL_ORDER:
                    context = "\n\n".join(transcript[-12:])[-5200:]
                    task = ("Contribua com sua especialidade nesta mesa-redonda. "
                            "Responda ao usuário e dialogue com as falas anteriores sem repetir. "
                            "Até 100 palavras. Diferencie fatos e incertezas. Não execute ferramentas "
                            "ou ações externas. Ações de segurança devem permanecer autorizadas, "
                            "defensivas e dentro do escopo informado.\n\n" + context)
                    try:
                        model, answer = lb.chat(role, task, 120)
                    except Exception as exc:
                        model, answer = "indisponível", "Não consegui responder: " + str(exc)
                    replies.append({"role": role, "model": model, "answer": answer})
                    transcript.append(role.upper() + ": " + answer)
                return self.send_json({"replies": replies})
            if self.path == "/api/guard":
                local = lb.collect_local_posture()
                try:
                    kev, kev_error = lb.fetch_cisa_kev(), None
                except Exception as exc:
                    kev, kev_error = None, str(exc)
                report = {"version": lb.VERSION, "mode": "defensive_read_only",
                          "local": local, "cisa_kev": kev, "cisa_error": kev_error,
                          "network_actions": "somente GET HTTPS para feed público CISA KEV",
                          "system_actions": "consultas locais somente leitura"}
                saved = lb.save_report(report)
                analyses = []
                context = json.dumps(report, ensure_ascii=False)
                for role in ("tokyo", "helsinki"):
                    try:
                        model, answer = lb.chat(role, "Analise estes dados. Separe fatos, "
                            "indícios e desconhecidos; não afirme vulnerabilidade sem evidência. "
                            "Recomende até três melhorias defensivas.\n\n" + context, 260)
                        analyses.append({"role": role, "model": model, "answer": answer})
                    except Exception as exc:
                        analyses.append({"role": role, "error": str(exc)})
                return self.send_json({"report": report, "saved_to": str(saved), "analyses": analyses})
            return self.send_json({"error": "Endpoint inexistente."}, 404)
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            return self.send_json({"error": "Entrada inválida: " + str(exc)}, 400)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, 500)

def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"LE BLANC {lb.VERSION} — painel em http://{HOST}:{PORT}")
    print("Acesso restrito ao próprio computador (loopback). Ctrl+C encerra.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
