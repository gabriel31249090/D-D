# ARCANUM Agent Bridge — Versão 6.0

Ponte local em **Python** para Codex ↔ Google Antigravity, com servidor MCP, SQLite, dashboard e adaptadores de IA.

> **AVISO:** O ARCANUM Agent Bridge é o *orquestrador de agentes*, não o jogo D&D. A configuração MCP foi verificada por arquivos e testes locais; a conexão com sua conta Codex/Antigravity só pode ser confirmada no seu PC.

## Instalar no Windows (recomendado)

1. Extraia **todo o ZIP** em uma pasta nova, por exemplo `C:\Users\Aluno\Downloads\ARCANUM_Agent_Bridge_v6`.
2. Dê duplo clique em **`INSTALAR.bat`** (não precisa de administrador).
3. Digite o caminho de seu projeto, por exemplo `C:\Users\Aluno\Downloads\D&D`. O caractere `&` é aceito; **não renomeie a pasta**.
4. O instalador usa o Python já existente (`py -3.12`), instala `mcp`/`psutil`, faz cópias de segurança dos arquivos MCP e grava as duas configurações sem executar `codex.cmd mcp add`.
5. **Opcional:** abra **`ABRIR_PAINEL.bat`** para acompanhar tarefas e atividade. O browser abrirá o painel local em `http://127.0.0.1:8765` com um token exclusivo. Mantenha a janela aberta enquanto usar o painel; a comunicação MCP funciona sem ele.
6. Execute **`TESTAR_CONEXAO.bat`** para executar um handshake real com o servidor MCP e mostrar os caminhos de configuração.
7. Reinicie o Codex e o Antigravity. No agente, peça para executar a ferramenta `bridge_health`.

O instalador **não precisa de WinGet**, não altera a política de execução do PowerShell, não apaga projetos e **não depende de `codex.cmd mcp add`**.

### Se houver erros

- `duplicate key`: `REPARAR_CONFIG.bat` procura e remove todas as seções antigas do **arcanum-bridge**, mantendo as configurações de outros MCPs. Faz backup datado do `config.toml` antes de modificar.
- `D não é reconhecido`: não execute `codex.cmd mcp add ... D&D`; as configurações são gravadas em TOML/JSON como listas de argumentos por Python.
- `Python não encontrado`: use `py -3.12 --version` e reinstale Python 3.12 somente se esse comando também falhar.
- `codex.ps1 não pode ser carregado`: use `codex.cmd login` no PowerShell.
- `Antigravity não encontrado`: certifique-se de que o CLI `agy` foi instalado e autenticado. Seu IDE pode usar MCP sem que `agy` esteja disponível para execução headless.
- `MCP configurado` não é `agente conectado`. Para confirmar, faça `bridge_health` dentro de cada agente; o dashboard mostrará chamada recente.

## Funcionalidades

- MCP **stdio** para Codex e Antigravity; mensagens, tarefas e heartbeats separados.
- O transporte **stdio não exige o dashboard aberto**: cada cliente inicia seu próprio processo MCP e ambos compartilham o SQLite do mesmo projeto. O painel é opcional.
- Banco SQLite com fila, status, mensagens, execução, histórico e eventos.
- Dashboard autenticado **apenas no localhost (127.0.0.1)** com uso de CPU/RAM/disco, verificação SQLite, processos MCP, tarefas, modelos, logs e streaming SSE.
- Seleção por tarefa de Codex, Antigravity, Ollama local ou API OpenAI-compatível; troca dos modelos sem reiniciar o painel.
- Execução **sequencial** Codex→Antigravity ou inversa, com passagem de contexto e histórico; somente com aprovação o executor pode editar arquivos.
- Ollama e API compatível fazem **planejamento/revisão**, não edição de arquivos nesta versão.
- Barra de progresso mostra **proporção de tarefas cadastradas concluídas**, e não uma estimativa automática da implementação global.

## Arquivos de configuração

- Codex: `%USERPROFILE%\.codex\config.toml`
- Antigravity local: `<SEU_PROJETO>\.agents\mcp_config.json`
- Dados: `<SEU_PROJETO>\.agent-bridge\bridge.sqlite3`
- Arquivo da pasta de trabalho nesta instalação: `project_path.txt`
- Logs de execução: `<SEU_PROJETO>\.agent-bridge\logs`

Esses caminhos são gravados por Python, então espaços, acentos e `&` não precisam de escapes no shell.

## Comandos CLI (opcionais)

No PowerShell, dentro desta pasta, execute **uma linha por vez**:

```powershell
.\.venv\Scripts\python.exe bridge.py doctor --project-file project_path.txt
.\.venv\Scripts\python.exe bridge.py test-mcp --project-file project_path.txt
.\.venv\Scripts\python.exe bridge.py task --project-file project_path.txt "Implementar catalogo de magias" --description "Python + banco + frontend"
.\.venv\Scripts\python.exe bridge.py tasks --project-file project_path.txt
```

No dashboard: crie uma tarefa, selecione um provedor/modelo e pressione **Iniciar execução**. O modo inicial é **Planejamento, sem escrita**. Para liberar edições, o painel exige confirmação explícita e informa os riscos.

## Trocar modelos e provedores

- **Codex:** modelo em branco usa o padrão da conta; ou informe um identificador suportado pelo CLI.
- **Antigravity:** modelo em branco usa o padrão da conta; use `agy models` para consultar os nomes disponíveis.
- **Ollama:** instale e execute o Ollama localmente; `OLLAMA` usa por padrão `http://127.0.0.1:11434`.
- **API compatível:** defina `ARCANUM_COMPAT_URL` e, opcionalmente, `ARCANUM_COMPAT_API_KEY` **como variáveis de ambiente antes de abrir o dashboard**. O endpoint deverá aceitar `POST /chat/completions`.

**Segurança:** o painel fica restrito à máquina local com token gerado automaticamente. Não compartilhe o link com token, não exponha a porta à internet e não execute agentes em modo de escrita em repositórios desconhecidos. Ações destrutivas e deploys externos não têm autorização automática. O sistema não coloca chaves de API no banco SQLite.

## Limites atuais

- Esta versão usa `mcp.server.fastmcp.FastMCP`, incluído no **SDK MCP 1.x**. `requirements.txt` restringe a dependência a `mcp>=1.26,<2`; o SDK 2.x removeu esse módulo. Se uma instalação anterior trouxe MCP 2.x, execute `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` e recarregue os clientes MCP.
- `doctor` verifica o executável, o script, o projeto, a identidade de cada agente e a importação de FastMCP. A confirmação do protocolo continua sendo `test-mcp` ou uma chamada real a `bridge_health` no cliente.
- A execução automática depende dos CLIs instalados e logados, e de suas políticas de permissão. MCP registrado não garante que ambos estejam abertos.
- Em Windows, o executor busca o binário `.exe` ou invoca diretamente o entrypoint `.js` com `node.exe`, evitando `.cmd` para comandos que contêm dados do usuário. Se não localizar o `agy`, configure `ARCANUM_AGY_EXECUTABLE` com o caminho de um executável `.exe` ou entrypoint `.js` compatível.
- Os agentes se comunicam por mensagens e tarefas persistidas, **não conversam espontaneamente entre si sem que sejam executados**.
- O painel não transmite para internet, mas os CLIs e provedores externos podem usar rede de acordo com as suas configurações.
- O ARCANUM Bridge não instala Antigravity, Codex ou Ollama por conta própria.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Documentação de referência:
- https://developers.openai.com/codex/mcp/
- https://developers.openai.com/codex/non-interactive/
- https://antigravity.google/docs/cli/headless/
- https://antigravity.google/docs/cli/mcp/
