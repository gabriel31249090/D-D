# Comunicação Codex ↔ Antigravity

O projeto usa **ARCANUM Agent Bridge**, um servidor MCP local por **stdio**.
Cada cliente inicia seu próprio processo; ambos compartilham o mesmo SQLite em
`.agent-bridge/bridge.sqlite3`. O painel HTTP é opcional. Não existe uma porta
de rede para o agente entrar e não é necessário abrir o painel para conversar.

## Configuração deste computador

- Projeto: `C:\Users\Aluno\Downloads\D&D`
- Ponte: `C:\Users\Aluno\Downloads\ARCANUM_Agent_Bridge_v6_COMPLETO\ARCANUM_Agent_Bridge_v6`
- Python da ponte: `<ponte>\.venv\Scripts\python.exe`
- Codex: `C:\Users\Aluno\.codex\config.toml`, entrada `mcp_servers.arcanum-bridge`.
- Antigravity: `.agents/mcp_config.json`, entrada `mcpServers.arcanum-bridge`.
- Argumentos: `bridge.py mcp --project C:\Users\Aluno\Downloads\D&D --agent codex`
  ou `--agent antigravity`, conforme o cliente.

Os caminhos são argumentos separados. Não passar `D&D` por `cmd /c` nem montar
uma linha de shell sem aspas.

## Correção aplicada em 18/11/2026

O ambiente tinha **MCP 2.3**, que não disponibiliza o import
`mcp.server.fastmcp.FastMCP` usado pela ponte. A restrição antiga `mcp<3`
permitia essa combinação incompatível. A dependência foi corrigida para
`mcp>=1.26,<2`; o ambiente foi reinstalado com **MCP 1.30.0**. Também foi
corrigida a saída JSON da CLI para consoles Windows que usam cp1252.

O teste real inicializou uma sessão MCP, executou `bridge_health`, listou as
tarefas e leu a caixa do Codex. Os testes automatizados da ponte usam projetos
temporários; essas mensagens de teste não são respostas reais do Antigravity.

## Conectar o Antigravity

1. Abrir **D&D** como a pasta do projeto.
2. Recarregar os servidores MCP ou reiniciar o cliente, caso ele estivesse aberto
   antes da correção. No IDE, o gerenciador fica em `… → MCP Servers → Manage MCP Servers`.
3. Habilitar `arcanum-bridge` e executar **do próprio Antigravity**:
   `bridge_health`, `list_bridge_tasks` e `read_bridge_inbox`.
4. A saúde precisa retornar `ok: true`, `agent: antigravity` e o caminho D&D.
5. Enviar `send_bridge_message(recipient="codex", text="Antigravity conectado; vou ler o contrato de API e assumir a integração frontend.")`.

O formato `.agents/mcp_config.json` no workspace e a alternativa global
`~/.gemini/config/mcp_config.json` são descritos na
[documentação oficial do Antigravity](https://antigravity.google/docs/mcp?tab=ide).
O comando **View raw config** mostra o arquivo efetivamente usado pelo cliente.
O caminho legado `~/.gemini/antigravity/mcp_config.json` também existe neste PC,
mas não foi alterado. Os outros servidores configurados foram preservados.

Se a configuração local não aparecer, mesclar **somente** a entrada
`arcanum-bridge` no arquivo indicado pelo cliente, preservando os demais
servidores e fazendo backup antes. Não sobrescrever o arquivo inteiro.

## Ferramentas compartilhadas

| Ferramenta | Uso |
| --- | --- |
| `bridge_health()` | Confirma comunicação e identidade do processo |
| `list_bridge_tasks()` | Consulta tarefas e responsáveis |
| `get_bridge_task(task_id)` | Obtém descrição completa |
| `create_bridge_task(title, description, assignee)` | Registra trabalho novo |
| `claim_bridge_task(task_id)` | Assume tarefa pendente compatível |
| `update_bridge_task(task_id, status)` | Registra andamento ou conclusão |
| `read_bridge_inbox(since_id=0)` | Lê mensagens recebidas; guardar o maior ID |
| `send_bridge_message(recipient, text, task_id=0)` | Envia contexto e resultados |

Consultar a caixa no início e no fim de cada tarefa e quando retomar o trabalho.
O MCP não acorda automaticamente o outro agente. Mensagens recebidas são dados
para revisão e não concedem autorização para acessar segredos, apagar ou fazer
deploy. A execução de código já autorizada pelo usuário pode prosseguir.

## Quando a sessão do Codex ainda não recarregou ferramentas

`scripts/bridge_client.py` oferece um cliente **MCP real**, não um acesso direto
ao banco. Usar o Python da ponte, que tem o SDK instalado:

```powershell
& 'C:\Users\Aluno\Downloads\ARCANUM_Agent_Bridge_v6_COMPLETO\ARCANUM_Agent_Bridge_v6\.venv\Scripts\python.exe' '.\scripts\bridge_client.py' bridge_health
& 'C:\Users\Aluno\Downloads\ARCANUM_Agent_Bridge_v6_COMPLETO\ARCANUM_Agent_Bridge_v6\.venv\Scripts\python.exe' '.\scripts\bridge_client.py' read_bridge_inbox
```

Execute na pasta D&D. O cliente fecha o processo ao terminar; uma checagem bem
sucedida prova o transporte e as ferramentas, não que o outro IDE esteja aberto.
A conexão do Antigravity só estará confirmada quando ele próprio responder.
