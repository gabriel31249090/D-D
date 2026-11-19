# Contrato de API ARCANUM 0.1

Modo local de desenvolvimento, porta 8000 em 127.0.0.1. OpenAPI em `/openapi.json`, interface `/docs`.
Não há autenticação/multiplayer nesta fase: somente o mestre local controla ambos os lados. Não expor na rede.
O frontend deve mostrar claramente que este é um recorte mecânico: guerreiro nível 1, regras 2014, arena sem movimento, sem magias, sem recursos de classe e sem salvaguardas contra morte.
Espécie, antecedentes, perícias e ficha completa serão acrescentados depois; a criação atual salva um perfil de combate.

## Rotas

| Método | Rota | Resultado |
|---|---|---|
| GET | `/health` | estado local e versão |
| GET/POST | `/api/characters` | lista/cria perfil |
| GET | `/api/characters/{id}` | ficha calculada |
| POST | `/api/characters/{id}/rest` | recupera PV para nova sessão de treino, fora de combate |
| GET/POST | `/api/parties` | lista/cria grupo |
| GET | `/api/parties/{id}` | grupo e IDs de personagens |
| GET | `/api/monsters` | catálogo de exemplos identificados |
| GET/POST | `/api/combat` | lista/inicia encontro |
| GET | `/api/combat/{id}` | snapshot autoritativo |
| POST | `/api/combat/{id}/actions` | comando e eventos novos |
| GET | `/api/combat/{id}/events?after_sequence=0` | eventos ordenados, paginação até 500 |
| POST | `/api/dice/roll` | rolagem validada e registrada |

Criar personagem:

```json
{"name":"Aria","rule_set":"dnd5e-2014","class_id":"fighter","level":1,"abilities":{"strength":16,"dexterity":14,"constitution":16,"intelligence":10,"wisdom":12,"charisma":8},"equipment":{"armor":"chain_mail","shield":true,"weapon":"longsword"},"fighting_style":"defense"}
```

Atributos são entrada manual final, 3..20, sem aplicar bônus de espécie automaticamente. Estilos aceitos: `defense` e `dueling`.
Armaduras: `chain_mail`, `leather`, `none`; espada longa em uma mão; escudo opcional. PV, CA, bônus e dados vêm do Python.
A resposta inclui `id`, `max_hp`, `current_hp`, `armor_class`, `ability_modifiers`, `saving_throws`, `initiative_bonus`, `proficiency_bonus`, `attacks` e `active_combat_id`.
O campo `scope` identifica os limites do perfil.

Criar grupo: `{"name":"Valebruma","character_ids":["<character-id>"]}`.
Iniciar encontro: `{"party_id":"<party-id>","monster_ids":["training-goblin"],"rule_set":"dnd5e-2014"}`.
O monstro é uma fixture sintética com `is_example:true`, não foi importado de livro ou Drive.

O encontro retorna `id`, `status` (`active`/`completed`), `version` (inicia em 1), `round`, `current_actor_id`, `winner` e `combatants` em ordem de iniciativa.
Empate de iniciativa é decidido pela ordem estável de criação dos participantes, decisão explícita do mestre nesta arena; a decisão é registrada no evento inicial.
O ID do combatente é diferente do ID do personagem e deve ser usado nos comandos.
Cada combatente possui retrato futuro, nome, equipe `party`/`enemy`, PV, CA, iniciativa, `action_available`, `conditions` e `attacks`.

Ataque:

```json
{"type":"attack","actor_id":"<current_actor_id>","target_id":"<enemy-combatant-id>","attack_id":"longsword","expected_version":1}
```

Encerrar turno: `{"type":"end_turn","actor_id":"<current_actor_id>","expected_version":2}`.
A versão deve ser a do último snapshot. Erro 409 exige recarregar snapshot antes de tentar novamente.
Não repetir automaticamente comandos mutáveis após timeout: consulte snapshot/eventos para saber se o comando foi aplicado.
Cada turno permite um ataque. A interface deve enviar `end_turn` explicitamente; o mestre local escolhe ações do inimigo também.
`attack_id` do inimigo de treino é `training-blade`. Não há IA de combate nesta fase.

Resposta de ação: `{"combat":{...},"events":[...]}`. Eventos têm `id`, `combat_id`, `sequence`, `type`, `payload`.
Evento `attack_resolved`: `actor_id`, `target_id`, `attack_id`, `hit`, `critical`, `damage`, `damage_type`, `hp_before`, `hp_after`, `attack_roll` (inclui `rolls`), `damage_roll`, `attack_bonus`, `attack_total`, `version`.
Animar somente esses eventos retornados. Nunca decidir acerto/dano no cliente.
`combat_started` preserva o estado inicial e as iniciativas; `turn_started` registra a transição, `combat_completed` inclui vencedor e PV finais.
Na arena de treino, PV zero significa incapacitado e é removido dos turnos. Não significa morte oficial; salvaguardas de morte ainda não implementadas.
O último inimigo/equipe incapacitado encerra o encontro; o servidor grava PV nas fichas e libera personagens para outro encontro.

Dados: `{"expression":"2d6+3","mode":"normal"}`. Modos `normal`, `advantage`, `disadvantage`; estes últimos só para `1d20`.
Limites: 50 dados, faces 4/6/8/10/12/20/100, modificador absoluto até 1000. Não aceita código, resultados ou seeds enviados pelo cliente.

Erros de domínio: `{"detail":{"code":"...","message":"..."}}`; 404 inexistente, 409 conflito de versão/turno/recurso, 422 entrada inválida.
Erros de schema seguem o formato padrão FastAPI `detail` com lista de erros. Banco indisponível ou sem migração retorna 503.
Campos adicionais são rejeitados. CORS permite `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:8000` e `http://127.0.0.1:8000`.
Listagens aceitam `limit` (1..100, padrão 50) e `offset`; eventos aceitam `limit` (1..500, padrão 200) e cursor `after_sequence`.

## Instalação e execução

No PowerShell, na raiz do projeto:

```powershell
.\scripts\setup_backend.ps1
.\scripts\run_api.ps1
```

Se a política do sistema bloquear scripts, execute os comandos diretamente, sem alterar a política global:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

SQLite local padrão: `data/arcanum.sqlite3`, separado de `.agent-bridge/bridge.sqlite3`.
`ARCANUM_DATABASE_URL` permite escolher outro banco; PostgreSQL exige instalar `.[postgres]` e fornecer uma URL `postgresql+psycopg://...` no ambiente local. PostgreSQL ainda não foi testado nesta etapa.
`alembic upgrade head` cria o schema inicial e preserva dados em execuções repetidas. O downgrade automático está desativado.
Não há deploy, acesso externo, recuperação de senha, conta de usuário ou segredos do mestre armazenados neste recorte.

## Fonte mecânica e licença

Subconjunto numérico consultado no [SRD 5.1 oficial](https://www.dndbeyond.com/attachments/39j2li89/SRD5.1-CCBY4.0License.pdf), seções Fighter, Armor and Shields, Weapons, Ability Scores, Combat.
Não há extração dos livros privados ou conversão automática de PDFs nesta fase. Não mistura revisão 2024.

This work includes material taken from the System Reference Document 5.1 (“SRD 5.1”) by Wizards of the Coast LLC and available at https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License available at https://creativecommons.org/licenses/by/4.0/legalcode.

