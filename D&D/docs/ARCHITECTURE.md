# Arquitetura inicial do ARCANUM

## Decisões

Python 3.12 é a base da aplicação. FastAPI publica os comandos e consultas,
Pydantic valida entradas/saídas, SQLAlchemy persiste o estado e Alembic versiona
o esquema. O banco local da aplicação é separado do banco de coordenação MCP.
O modo inicial é uma arena controlada pelo mestre no próprio computador.

As regras disponíveis são um subconjunto explícito do SRD 5.1/2014. Entradas
para conjuntos ainda não suportados são rejeitadas. Um perfil de combate de
guerreiro nível 1 não equivale a um criador completo de personagens. O catálogo
de treino usa conteúdo sintético marcado como exemplo.

## Responsabilidades

- `backend/schemas.py`: contratos de entrada e saída; rejeição de campos extras.
- `backend/rules.py`: modificadores, equipamento, dados e resolução de ataques.
- `backend/models.py` e `backend/database.py`: entidades e configuração SQLAlchemy.
- Demais módulos de serviço/API: transações, validação de comandos e endpoints.
- `migrations/`: evolução versionada do esquema da aplicação.
- `tests/`: regras e fluxos de API em bancos isolados.
- `frontend/`: implementação reservada ao Antigravity.
- `.agent-bridge/`: tarefas/mensagens da equipe, não dados do jogo.
- `.arcanum/sources/`: auditoria privada das fontes; ignorada pelo Git.

## Fluxo da primeira integração

O cliente pede a criação de um perfil, recebe a ficha calculada e salva um
grupo com os IDs desses personagens. Ao criar um encontro, o servidor grava
os participantes, a iniciativa e o primeiro turno. Cada ação inclui o
combatente, o alvo quando necessário e a versão esperada do encontro.

O backend valida a ação e grava o estado e seus eventos na mesma transação.
O frontend apresenta o snapshot retornado e anima os novos eventos em ordem.
Um comando com versão antiga recebe conflito; o cliente recarrega o estado.
Em caso de timeout não deve repetir uma ação mutável automaticamente, pois
a resposta pode ter sido perdida depois de a transação ser confirmada.

O histórico preserva as rolagens oficiais e os resultados necessários à
apresentação. Não depende de rerrolar dados no navegador. A persistência permite
reabrir encontros; um reprodutor gráfico completo do histórico fica para a
interface e deve respeitar o contrato em `docs/API_CONTRACT.md`.

## Próximas ampliações

Primeiro integrar e testar a experiência vertical no frontend. Depois ampliar
as regras por casos de referência e fontes verificadas. Importação de livros,
catálogo, evolução de nível, magias, campanhas e mapas são etapas próprias.
Autenticação, isolamento por campanha, permissões, WebSockets e reconexão
precisam existir antes de disponibilizar uma mesa multiplayer.

O esquema inicial guarda a ficha como documento JSON e normaliza grupos,
participantes, encontros e eventos. À medida que o catálogo validado for
incorporado, suas entidades devem ganhar tabelas e migrações específicas.
PostgreSQL está previsto por URL SQLAlchemy; sua validação operacional deve
ser registrada separadamente dos testes com SQLite.
