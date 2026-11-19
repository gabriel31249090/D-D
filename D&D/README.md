# ARCANUM

## Edição para Windows

Use `ARCANUM-Setup-0.2.0-win-x64.exe` para instalar o aplicativo pelo seu usuário.
O instalador inclui o runtime Python e cria um atalho no menu Iniciar. O app
abre em uma janela própria e salva os dados em `%LOCALAPPDATA%\Arcanum`.

- Personagens, grupos, dados e arena com controle dos dois lados do combate.
- Campanhas com diário de sessão e anotações por categoria.
- Mapas desenháveis com geração de masmorras e exportação em JSON.
- Biblioteca de fontes privadas com busca e favoritos. Escolha a pasta `raw`
  se ela não aparecer automaticamente. PDFs e imagens abrem no leitor do Windows.
- Coordenação com abas para agentes, tarefas e mensagens do MCP local.

Para compilar o instalador, prepare o Python 3.12 x64 com a seção de backend
abaixo e rode ` .\.venv\Scripts\python.exe packaging\build_windows.py `.
O executável será criado na pasta `dist`.

Plataforma de Dungeons & Dragons com regras, persistência e combate controlados
por **Python**. O trabalho segue o [prompt mestre](docs/PROMPT_MESTRE.md) e as
[instruções de cooperação](AGENTS.md).

O estado real de cada etapa e as limitações estão em
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Começar pelo backend

Requisitos: Python 3.12 ou superior e PowerShell.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_api.ps1
```

Esses comandos aplicam a opção de execução apenas ao processo atual; não
alteram a política do Windows. O servidor de desenvolvimento usa loopback.
A documentação interativa da API fica em `http://127.0.0.1:8000/docs` e o
schema em `http://127.0.0.1:8000/openapi.json`.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

As instruções e formatos para a interface estão no
[contrato da API](docs/API_CONTRACT.md). Esta base local não deve ser tratada
como uma mesa multiplayer pronta para publicação.

## Trabalhar com o Antigravity

O MCP local compartilha tarefas e mensagens; cada cliente inicia a ponte por
stdio. Leia [como conectar](docs/MCP_CONNECTION.md).

Envie ao Antigravity o [prompt de integração](docs/ANTIGRAVITY_PROMPT.md).
Codex mantém backend, banco, regras e testes. Antigravity mantém frontend,
UX/UI, visual 2.5D e mapas. Coordenar pelo MCP antes de editar os mesmos arquivos.

## Fontes

O inventário de livros, fichas e arquivos do Drive fica em
[SOURCE_INVENTORY.md](docs/SOURCE_INVENTORY.md). Fontes privadas e dados locais
não são adicionados ao Git. Conteúdo de exemplo precisa ser identificado como
tal; a existência de um arquivo no Drive não significa que ele já foi importado.
