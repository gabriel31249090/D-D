# Estado de implementação — ARCANUM

Atualizado em 18/11/2026. O [prompt mestre](docs/PROMPT_MESTRE.md) define a meta
completa. Este arquivo registra o que foi executado; a plataforma inteira ainda
está em construção.

## Concluído

- Inspeção do projeto: inicialmente havia somente AGENTS.md, configuração MCP e
  estado privado da ponte, sem código da aplicação.
- Prompt mestre preservado no projeto e divisão de responsabilidades documentada.
- Ponte MCP corrigida: SDK 2.3 incompatível substituído por SDK 1.30, dependência
  limitada à série 1.x, diagnóstico de importação/identidade/caminhos corrigido.
- 12 testes da ponte executados, incluindo handshake stdio, 8 ferramentas,
  mensagens, cursor e exclusividade ao assumir tarefa em banco temporário.
- Saúde, tarefas e caixa do Codex consultadas por MCP real neste projeto.
- Mensagem real enviada à caixa do Antigravity; tarefa #4 reservada ao frontend.
- Prompt de conexão e integração em `docs/ANTIGRAVITY_PROMPT.md`.
- Contrato inicial em `docs/API_CONTRACT.md`.
- Acesso ao Drive confirmado e inventário de fontes em andamento.

## Em implementação e verificação

- Base FastAPI/Pydantic/SQLAlchemy, migração inicial e SQLite local.
- Perfil mecânico de guerreiro nível 1/2014, atributos, CA, PV e ataque em Python.
- Grupos, encontros, iniciativa, turnos e eventos persistentes.
- Comandos com versão esperada para impedir alterações com estado antigo.
- Testes da aplicação e scripts de instalação/inicialização local.
- Auditoria estrutural dos ZIPs e PDFs, sem executar código externo.

## Integração pendente

- O próprio Antigravity precisa chamar `bridge_health` como `antigravity` e
  responder ao Codex. Nenhuma conexão dele foi simulada no banco do projeto.
- Frontend, retratos/animações 2.5D e teste de ponta a ponta com a interface.
- O fluxo vertical completo só estará pronto após essa integração ser executada.

## Funcionalidades futuras do prompt mestre

| Área | Estado |
| --- | --- |
| Enciclopédia/importação revisável e proveniência | Pendente; inventário não equivale a importação |
| Ficha completa, espécies, antecedentes, perícias | Pendente |
| Evolução de nível e multiclasse | Pendente |
| Magias, recursos de classe e condições completas | Pendente |
| Salvaguardas de morte e todas as ações de combate | Pendente |
| Ficha PDF preenchida/exportada e editor de fichas | Pendente |
| Campanhas, sessões e ferramentas do mestre | Pendente |
| Mapas, assets licenciados e geração procedural | Pendente |
| Homebrew declarativo e relíquias | Pendente |
| Simulações de balanceamento | Pendente |
| Autenticação, papéis e isolamento de campanhas | Pendente |
| Multiplayer/WebSockets/reconexão | Pendente |
| PostgreSQL em execução, Docker e produção | Pendente |

## Limites

O modo inicial é local e não possui autenticação. A API deve escutar em
`127.0.0.1`; os dados do mestre não estão preparados para compartilhamento
multiplayer. A revisão 2024 não é suportada. Conteúdo de treino é identificado
como exemplo e não é apresentado como extração dos livros privados.

As fontes privadas ficam fora do Git. Código e assets de projetos no Drive
só devem ser reutilizados depois da análise de suas licenças. Os resultados
da auditoria ficam em `docs/SOURCE_INVENTORY.md`.
