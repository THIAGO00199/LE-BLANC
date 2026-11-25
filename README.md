# LE BLANC — versão 2.5

## Arquitetura
- Ollama local em 127.0.0.1:11435; o serviço de sistema em 11434 permanece intocado.
- Um modelo carregado por vez; contexto de 2.048 tokens e geração limitada para caber no notebook de 8 GB.
- Personas: Professor (raciocínio), Rio (engenharia de software), Denver (valor, perdas, custos e plano), Alicia (negociação ética), Tokyo (privacidade) e Helsinki (infraestrutura).
- Modelos: Professor deepseek-r1:1.5b; Rio qwen2.5-coder:1.5b; demais qwen2.5:3b. Fallback qwen2.5:3b quando aplicável.

## Painel visual
Execute: cd ~/LE-BLANC && python3 painel.py
Abra no próprio notebook: http://127.0.0.1:8765
O painel usa apenas a biblioteca padrão do Python, sem instalar dependências. Escuta exclusivamente em loopback (não fica exposto à rede local).

### Abas
- Conselho: seis personas respondem em sequência, compartilhando o contexto da rodada.
- Denver: análise individual de ganhos, perdas, custos, dependências, prioridades, alternativas e plano B.
- Auditoria: inventário local somente leitura, feed público CISA KEV por HTTPS e análises de Tokyo/Helsinki.

## Denver — Strategic Value Analyst
Denver não é moderador nem autoridade de aprovação. Ele apresenta valor e benefício esperado; perdas e impactos; custos de tempo, dinheiro, recursos e complexidade; pré-requisitos; etapas priorizadas; alternativas e plano B; recomendação fundamentada. Separa fatos, estimativas e desconhecidos e não inventa valores ou probabilidades ausentes. A decisão continua com o usuário.

## Comandos CLI
- python3 orquestrador.py --version
- python3 orquestrador.py --list-models
- python3 orquestrador.py --guard
- python3 orquestrador.py --guard --no-ai
- python3 orquestrador.py --role denver "Avalie ganhos, perdas, custos e plano."
- python3 orquestrador.py --chat --role tokyo
- python3 orquestrador.py --council

## Limites e segurança
- O painel é uma interface local; não concede às personas execução de comandos.
- O conselho chama um modelo por vez e pode levar alguns minutos.
- A auditoria faz consultas locais de leitura e um GET HTTPS para o catálogo fixo CISA KEV.
- Detectar processo/interface VPN ou Tor não prova que todo o tráfego passe pelo túnel.
- Estado de unidades systemd não equivale a inspecionar regras do kernel.
- A presença de CVE no catálogo KEV não prova que o computador esteja vulnerável.
- Não faz scans de terceiros, exploração, força bruta, roubo de credenciais, malware, evasão, apagamento de rastros ou alterações de firewall/DNS/VPN/rotas/serviços/bootloader/Windows/Garuda.
- Recomendações devem ser revisadas por uma pessoa antes de qualquer mudança.

Backup anterior: orquestrador.py.bak-2.1-20261119.
