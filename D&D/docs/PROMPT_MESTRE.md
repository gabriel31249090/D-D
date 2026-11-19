# ARCANUM — Plataforma Definitiva de Dungeons & Dragons

## PROMPT MESTRE PARA CODEX

### 1. MISSÃO

Você é um arquiteto de software sênior, desenvolvedor Python, engenheiro de jogos, especialista em D&D 5e, designer de interfaces e desenvolvedor de sistemas de RPG.

Sua missão é desenvolver **ARCANUM**, uma plataforma profissional e completa para criar personagens, administrar campanhas de Dungeons & Dragons, consultar livros de regras, construir masmorras, organizar aventuras e simular batalhas visualmente.

O aplicativo deverá reunir recursos semelhantes aos de D&D Beyond, Foundry VTT, Roll20, Dungeon Alchemist e ferramentas de gerenciamento de campanhas, mantendo identidade própria.

**REQUISITO FUNDAMENTAL: PYTHON DEVE SER A BASE DO PROJETO.**

Não quero uma aplicação cuja lógica principal esteja em JavaScript. Python deve controlar as regras, simulações, persistência e processamento central.

O sistema deve ser funcional, modular, extensível e utilizável por jogadores e mestres.

---

# 2. ARQUITETURA E TECNOLOGIAS

## Backend — Python

Utilizar preferencialmente:

- Python 3.12 ou superior, conforme compatibilidade das dependências.
- FastAPI para APIs.
- Pydantic para validação.
- SQLAlchemy para persistência.
- Alembic para migrações.
- PostgreSQL para produção.
- SQLite para desenvolvimento e modo local.
- WebSockets para sincronização das sessões.
- PyMuPDF e bibliotecas complementares para processar PDFs.
- Pillow para processamento de imagens.
- pytest e Hypothesis para testes automatizados.
- Redis para cache e tarefas quando necessário.

## Frontend

É permitido utilizar React, TypeScript e tecnologias gráficas para construir a interface.

Bibliotecas sugeridas:

- React com TypeScript.
- Tailwind CSS.
- PixiJS para mapas e batalhas 2D/2.5D.
- Three.js apenas para funcionalidades que realmente necessitem de 3D.
- Zustand para estado de interface.

A escolha definitiva deve considerar manutenção, desempenho e integração com Python.

**Nenhuma regra essencial de D&D deve depender exclusivamente do frontend.** O cliente renderiza e envia comandos; o motor Python valida e processa.

## Estrutura modular

Organizar o projeto em módulos independentes:

```text
arcanum/
├── backend/
│   ├── app/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── rules_engine/
│   ├── character_engine/
│   ├── combat_engine/
│   ├── dungeon_engine/
│   ├── campaign_engine/
│   ├── content_importer/
│   ├── inventory_engine/
│   ├── dice_engine/
│   └── services/
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── character-sheet/
│   ├── dungeon-editor/
│   ├── combat-view/
│   └── gm-dashboard/
├── assets/
├── migrations/
├── tests/
├── scripts/
├── docs/
└── docker-compose.yml
```

---

# 3. INTEGRAÇÃO COM GOOGLE DRIVE E LIVROS

Pasta principal:

https://drive.google.com/drive/u/0/folders/1Pl8z4uFcutTBoc0XB2Pe-qjHoWJjVZFm

Arquivos já identificados nessa pasta:

- Livro do Jogador D&D 5e.
- Manual dos Monstros D&D 5e.
- Atalho para o Guia do Mestre.
- Ficha editável de D&D 5e.
- Ficha de guerreiro draconato preenchida.
- Pasta contendo cinco fichas de Valebruma e dados de rolagens.
- chronicler-master.zip.
- Dungeoneer-master.zip.
- AsLib-master.zip.
- COMPASS-master.zip.

### Processamento dos arquivos

1. Acessar os arquivos com autorização do usuário, pela integração do Google Drive ou cópias locais.
2. Inventariar o conteúdo dos arquivos ZIP.
3. Identificar recursos reutilizáveis e suas licenças.
4. Identificar e processar livros em PDF.
5. Extrair textos, tabelas e estruturas.
6. Identificar capítulos, seções, páginas e referências.
7. Normalizar informações para o banco de dados.
8. Detectar duplicações, conflitos e erros de extração.
9. Criar uma interface de revisão para corrigir dados importados.
10. Permitir sincronização manual de alterações nos arquivos.

Não presumir que todos os ZIPs são pacotes de imagens.

### Enciclopédia de D&D

Criar um catálogo pesquisável que comporte:

- Classes e subclasses.
- Espécies/raças e subespécies.
- Antecedentes.
- Talentos e características.
- Perícias e proficiências.
- Magias e truques.
- Armas, armaduras e escudos.
- Equipamentos e ferramentas.
- Itens mágicos, poções e artefatos.
- Monstros, criaturas e NPCs.
- Condições e efeitos.
- Regras de exploração, combate e descanso.
- Tesouros, recompensas e encontros.
- Tabelas e regras especiais.

Cada registro deve preservar todos os campos aplicáveis, incluindo dados numéricos, fórmulas e exceções.

Exemplos:

**Magia:** nível, escola, componentes, alcance, duração, concentração, tempo de conjuração, classes, descrição, dano, salvaguarda, efeitos superiores e referência da fonte.

**Monstro:** ND, XP, tamanho, tipo, atributos, CA, pontos de vida, deslocamentos, resistências, imunidades, sentidos, ataques, CDs, ações, reações, habilidades e regras especiais.

**Arma:** categoria, propriedades, peso, alcance, dano, tipo de dano, proficiência e efeitos adicionais.

Não atribuir CA ou CD a objetos para os quais esses atributos não se aplicam.

### Versionamento

Tratar D&D 5e 2014 e a revisão de 2024 como conjuntos de regras separados. Permitir selecionar o conjunto utilizado por campanha e sinalizar incompatibilidades.

### Direitos de uso

Conteúdos protegidos importados de livros fornecidos pelo usuário devem permanecer privados e acessíveis apenas aos usuários autorizados. Não republicar comercialmente ou distribuir automaticamente textos e imagens protegidos.

Usar conteúdos SRD e outros materiais abertos apenas dentro de suas licenças.

---

# 4. CRIADOR INTELIGENTE DE PERSONAGENS

Implementar um criador guiado com:

- Escolha de conjunto de regras.
- Nome e informações básicas.
- Retrato e aparência.
- Espécie/raça.
- Classe e subclasse.
- Multiclasse.
- Antecedente.
- Alinhamento quando aplicável.
- Atributos.
- Perícias.
- Talentos.
- Proficiências.
- Equipamentos.
- Magias.
- História e personalidade.
- Evolução de personagem.

Métodos de atributos:

- Matriz padrão.
- Compra por pontos.
- Rolagem de dados.
- Entrada manual.
- Métodos personalizados do mestre.

## Cálculos automáticos

O motor Python deve calcular corretamente:

- Modificadores de atributos.
- Bônus de proficiência.
- Pontos de vida máximos e atuais.
- Dados de vida.
- Classe de Armadura.
- Iniciativa.
- Deslocamento.
- Salvaguardas.
- Bônus de ataque.
- Dano de armas.
- Ataques adicionais.
- CDs de magia.
- Modificadores de ataque mágico.
- Espaços de magia.
- Recursos de classe.
- Capacidade de carga.
- Inventário e peso.
- Resistências e imunidades.
- Percepção passiva.
- Condições temporárias.
- Evolução por nível.
- Modificadores de equipamentos e itens mágicos.

Os cálculos devem respeitar exceções e condições específicas das regras selecionadas.

Exemplo:

Um guerreiro com Constituição +3 deve ter a vida determinada pelo dado de vida, nível, modificador de Constituição e demais regras aplicáveis. O sistema não deve confundir resultados de rolagens com os limites válidos dos dados.

## Fichas

Implementar três modalidades:

1. Ficha digital moderna.
2. Ficha clássica no estilo tradicional de D&D.
3. Editor personalizado de fichas com campos, fórmulas e organização visual.

Permitir importar o PDF editável original fornecido pelo usuário, preencher seus campos e exportar cópias preservando o layout, quando tecnicamente permitido.

Exportações:

- PDF.
- JSON.
- Impressão.
- Backup completo.
- Formato compartilhável entre instâncias do ARCANUM.

Oferecer salvamento automático, histórico de mudanças, desfazer e recuperação.

---

# 5. PAINEL PROFISSIONAL DO MESTRE

Criar um painel exclusivo para mestres com ferramentas para:

- Criar campanhas.
- Criar e organizar sessões.
- Convidar jogadores.
- Administrar personagens.
- Criar missões principais e secundárias.
- Registrar eventos.
- Organizar NPCs.
- Controlar facções.
- Construir cidades e reinos.
- Registrar locais.
- Organizar cronologias.
- Registrar segredos.
- Controlar objetivos.
- Organizar encontros.
- Distribuir recompensas.
- Registrar decisões dos jogadores.
- Criar tabelas aleatórias.
- Acompanhar progressão da história.

## Planejador de aventuras

Cada aventura deve conter:

- Sinopse.
- Contexto histórico.
- Ganchos.
- Objetivos.
- Atos e capítulos.
- Cenas.
- NPCs participantes.
- Diálogos preparados.
- Desafios.
- Combates.
- Armadilhas.
- Tesouros.
- Caminhos alternativos.
- Consequências.
- Possíveis desfechos.

Adicionar editor de narrativa ramificada com nós conectados.

As escolhas dos jogadores poderão alterar estados da campanha, relações entre NPCs, objetivos e eventos futuros.

## Ferramentas adicionais

- Calendário fictício da campanha.
- Linha do tempo interativa.
- Gerador de nomes.
- Gerador de encontros.
- Gerador de tesouros.
- Gerador de NPCs.
- Gerador de rumores.
- Gerador de estabelecimentos.
- Tabelas de encontros aleatórios.
- Rastreador de missões.
- Diário de sessão.
- Diário dos jogadores.
- Diário secreto do mestre.
- Registro automático do histórico do combate.
- Biblioteca de documentos compartilhados.
- Controle de inspiração e recompensas.

O mestre deve conseguir preparar uma sessão inteira dentro do aplicativo.

---

# 6. CRIADOR PROFISSIONAL DE MASMORRAS

Desenvolver um editor gráfico completo integrado ao Python.

## Funcionalidades

- Criação de mapas do zero.
- Importação de mapas prontos.
- Editor de salas e corredores.
- Grade quadrada ou hexagonal.
- Ferramenta de desenho livre.
- Paredes, pisos e portas.
- Escadas e passagens.
- Obstáculos e móveis.
- Baús e objetos interativos.
- Armadilhas.
- Portais.
- Ambientes internos e externos.
- Iluminação.
- Sombras.
- Camadas.
- Tokens.
- Marcadores.
- Anotações.
- Áreas secretas.
- Portas bloqueadas.
- Pontos de entrada e saída.

## Mecânicas

Implementar:

- Snap to grid.
- Zoom e movimentação do mapa.
- Rotação e escala de elementos.
- Seleção múltipla.
- Copiar/colar.
- Desfazer/refazer.
- Histórico de alterações.
- Ferramentas de seleção e preenchimento.
- Biblioteca de assets.
- Colisões e bloqueios.
- Medição de distância.
- Linha de visão.
- Áreas de efeito.
- Névoa de guerra.
- Visão exclusiva dos jogadores.
- Revelação de salas pelo mestre.

## Gerador procedural em Python

Criar algoritmos para gerar:

- Masmorras.
- Cavernas.
- Ruínas.
- Castelos.
- Florestas.
- Catacumbas.
- Templos.
- Labirintos.
- Fortalezas.

Permitir determinar tamanho, número de salas, densidade de obstáculos, conexões, temática, dificuldade e elementos especiais.

Validar conectividade e acessibilidade dos ambientes.

## Importação de assets

Criar um pipeline para identificar imagens, sprites, tilesets e recursos compatíveis nos ZIPs do Google Drive.

Caso algum arquivo ZIP não contenha recursos apropriados, registrar essa limitação.

Permitir adicionar bibliotecas externas posteriormente.

Exportar mapas como PNG e JSON, preservando camadas, objetos, colisões e metadados.

---

# 7. SIMULADOR DE COMBATE 2.5D

Este é um dos módulos prioritários.

Criar um sistema de combate com apresentação visual inspirada em RPGs como Pokémon, utilizando as regras de D&D.

## Direção visual

Não é necessário criar personagens tridimensionais ou animações complexas.

Cada personagem deverá ser representado por uma imagem PNG, JPG ou WebP enviada pelo jogador ou mestre.

O cenário será uma composição 2.5D com profundidade simulada.

Os participantes aparecerão distribuídos visualmente em posições semelhantes às de um RPG de turnos.

### Animação das imagens

Quando um personagem atacar:

1. A imagem se desloca levemente em direção ao alvo.
2. Executa uma pequena inclinação ou movimento.
3. Ocorre um efeito visual correspondente ao ataque.
4. O alvo reage ao impacto.
5. O sistema mostra dano, resistência ou falha.
6. A imagem retorna à posição inicial.

Implementar animações por transformações simples:

- Translation.
- Scale.
- Rotation.
- Squash and stretch.
- Shake.
- Opacity.
- Particle effects.

### Tipos de animação

Criar conjuntos reutilizáveis:

- Ataque corpo a corpo.
- Ataque à distância.
- Magia de fogo.
- Magia de gelo.
- Raio.
- Cura.
- Explosão.
- Defesa.
- Bloqueio.
- Esquiva.
- Ataque crítico.
- Erro.
- Condição aplicada.
- Morte ou inconsciência.
- Invocação.
- Efeito em área.

Todas devem utilizar as imagens existentes, dispensando spritesheets individuais para cada personagem.

Personalizar efeitos sem alterar as regras mecânicas.

## Motor de combate Python

Criar um motor central responsável por:

- Ordem de iniciativa.
- Rodadas e turnos.
- Ações.
- Ações bônus.
- Reações.
- Movimento.
- Ataques.
- Testes de resistência.
- Magias.
- Concentração.
- Condições.
- Recursos consumíveis.
- Resistências.
- Vulnerabilidades.
- Imunidades.
- Cobertura.
- Dano crítico.
- Cura.
- Morte e inconsciência.
- Dados de vida.
- Recuperação de recursos.
- Ações especiais de criaturas.
- Ações lendárias, conforme as regras aplicáveis.
- Efeitos com duração em turnos.
- Recargas de habilidades.

O frontend jamais poderá declarar unilateralmente um ataque como bem-sucedido.

## HUD de batalha

Mostrar para cada personagem:

- Retrato.
- Nome.
- Nível ou ND.
- Pontos de vida.
- CA.
- Condições.
- Recursos disponíveis.
- Espaços de magia.
- Concentração ativa.
- Ataques possíveis.
- Bônus relevantes.
- Turno atual.

O jogador poderá clicar em um ataque e visualizar:

- Nome.
- Tipo.
- Alcance.
- Alvo.
- Rolagem necessária.
- Bônus aplicado.
- Dano.
- Tipo de dano.
- Custo.
- Descrição.
- Condições de uso.

Exemplo de fluxo:

O guerreiro seleciona Espada Longa, escolhe um goblin, confirma o ataque e o sistema realiza a rolagem de d20 com os modificadores corretos.

O motor compara o resultado com a CA aplicável, calcula o dano e registra o evento.

Se atingir, a imagem do guerreiro avança, ocorre um efeito de corte e os pontos de vida do goblin são atualizados.

Todo o processo deve ser reproduzível a partir de eventos registrados.

## Party

Criar grupos de aventureiros com:

- Até dezenas de participantes, respeitando limites de desempenho.
- Participantes jogadores e NPCs.
- Criaturas aliadas.
- Inimigos.
- Invocações.
- Equipes customizadas.

## Mestre durante o combate

Permitir:

- Controlar monstros.
- Ajustar pontos de vida.
- Adicionar reforços.
- Modificar iniciativa.
- Aplicar condições.
- Alterar terreno.
- Encerrar encontros.
- Corrigir resultados.
- Desfazer ações com registro.
- Executar rolagens secretas.
- Controlar criaturas especiais.

O mestre tem autoridade para realizar exceções, mas todas devem ser registradas no histórico.

---

# 8. SIMULAÇÃO E BALANCEAMENTO

Criar ferramentas de simulação automática de encontros.

O mestre deverá conseguir:

- Selecionar uma party existente.
- Escolher monstros.
- Configurar níveis e equipamentos.
- Determinar terreno.
- Definir condições iniciais.
- Executar simulações repetidas.
- Comparar estratégias.
- Estimar consumo de recursos.
- Avaliar dificuldade.

Resultados:

- Taxa de vitória estimada.
- Rodadas médias.
- Dano médio.
- Dano recebido.
- Personagens incapacitados.
- Magias utilizadas.
- Recursos consumidos.
- Identificação de combinações perigosas.

Essas estimativas devem indicar as hipóteses utilizadas e não devem ser tratadas como previsão garantida.

Criar um modo de combate automático com estratégias configuráveis, separado do modo normal em que os jogadores escolhem suas ações.

---

# 9. CRIADOR DE CONTEÚDO HOMEBREW

Permitir ao mestre criar:

- Armas.
- Armaduras.
- Escudos.
- Itens mágicos.
- Relíquias.
- Artefatos lendários.
- Poções.
- Magias.
- Truques.
- Monstros.
- Raças/espécies.
- Classes.
- Subclasses.
- Talentos.
- Antecedentes.
- Condições personalizadas.
- Regras alternativas.

## Editor de relíquias

Campos sugeridos:

- Nome.
- História.
- Aparência.
- Raridade.
- Tipo.
- Peso.
- Valor.
- Requisitos de sintonização.
- Habilidades.
- Cargas.
- Efeitos passivos.
- Efeitos ativos.
- CDs.
- Dados de dano.
- Recursos consumidos.
- Condições.
- Maldições.
- Evoluções.
- Restrições.

As relíquias podem possuir efeitos condicionais e evolução por eventos da campanha.

## Sistema de regras extensíveis

Não implementar regras personalizadas através de execução arbitrária de código Python fornecido pelos usuários.

Criar uma linguagem declarativa segura para efeitos, com operações tipadas como:

- Somar modificador.
- Substituir valor.
- Adicionar dado de dano.
- Aplicar condição.
- Recuperar recurso.
- Conceder resistência.
- Alterar deslocamento.
- Aplicar efeito temporário.
- Executar rolagem validada.

Validar dependências e conflitos entre efeitos.

---

# 10. SISTEMA DE DADOS E ROLAGENS

Implementar um motor Python de dados.

Suportar expressões como:

- 1d20
- 2d6+3
- 4d8
- 1d10+5
- 8d6

Também suportar:

- Vantagem.
- Desvantagem.
- Rolagens críticas.
- Dados adicionais.
- Repetição de dados quando uma regra permitir.
- Modificadores temporários.
- Testes opostos.
- Rolagens secretas.
- Histórico auditável.

Utilizar geração aleatória apropriada, registrar entradas e resultados e fornecer ferramentas de teste estatístico.

Permitir que cada dado seja rolado visualmente, mas garantir que o valor oficial venha do motor Python.

---

# 11. MESA VIRTUAL MULTIPLAYER

Implementar sessões online em tempo real.

Papéis:

- Administrador.
- Mestre.
- Jogador.
- Espectador autorizado.

Funcionalidades:

- Convites.
- Salas privadas.
- Chat.
- Rolagens públicas e secretas.
- Compartilhamento de fichas.
- Mapas sincronizados.
- Movimentação de tokens.
- Combate compartilhado.
- Inventários.
- Diários.
- Anotações.
- Permissões granulares.
- Reconexão sem perda de estado.

O jogador não poderá acessar informações secretas do mestre através de endpoints, respostas de API ou dados ocultos no frontend.

O servidor deve enviar apenas os dados autorizados a cada usuário.

---

# 12. DESIGN VISUAL E EXPERIÊNCIA

Criar uma interface premium inspirada em livros de fantasia e RPGs modernos.

## Identidade visual

- Fantasia medieval sombria.
- Detalhes dourados.
- Texturas sutis de pergaminho.
- Tipografia refinada.
- Painéis inspirados em grimórios.
- Ícones próprios.
- Bordas ornamentadas discretas.
- Modo escuro e claro.
- Animações suaves.
- Transições elegantes.
- Interface responsiva.

Evitar interfaces excessivamente carregadas e efeitos visuais que atrapalhem a leitura.

## Telas principais

1. Dashboard.
2. Biblioteca de personagens.
3. Criador de personagens.
4. Ficha detalhada.
5. Enciclopédia.
6. Biblioteca de monstros.
7. Grimório de magias.
8. Inventário.
9. Painel do mestre.
10. Gerenciador de campanhas.
11. Planejador de aventuras.
12. Editor de masmorras.
13. Mesa virtual.
14. Simulador de combate.
15. Criador de conteúdo homebrew.
16. Biblioteca de assets.
17. Configurações.
18. Administração e permissões.

Garantir navegação consistente e acessibilidade por teclado.

---

# 13. RECURSOS EXTRAS

Acrescentar, conforme a evolução do projeto:

### Gerenciamento de inventário

- Equipar e desequipar itens.
- Peso carregado.
- Moedas.
- Itens consumíveis.
- Munições.
- Contêineres.
- Transferência de objetos.
- Baús compartilhados.
- Itens identificados ou desconhecidos.

### Ferramentas de exploração

- Descanso curto e longo.
- Viagens.
- Tempo de deslocamento.
- Suprimentos.
- Exaustão, conforme a versão.
- Visibilidade.
- Condições ambientais.
- Sobrevivência.
- Eventos aleatórios.

### Biblioteca de personagens

- Clonagem de personagens.
- Templates.
- Fichas rápidas de NPCs.
- Histórico por nível.
- Comparação de construções.
- Verificador de regras.
- Progressão planejada.
- Exportação e importação.

### Ferramentas do mestre

- Tela de mestre personalizável.
- Atalhos configuráveis.
- Iniciativa em tempo real.
- Cartões rápidos de monstros.
- Encontros predefinidos.
- Gerador de recompensas.
- Estatísticas de campanha.
- Anotações privadas vinculadas aos mapas.

### Recursos opcionais de IA

Criar uma arquitetura preparada para integrar modelos de IA no futuro.

Possíveis aplicações:

- Auxílio para escrever aventuras.
- Sugestões de NPCs.
- Diálogos de referência.
- Criação de histórias de personagens.
- Resumos das sessões.
- Pesquisa semântica nos documentos autorizados.

A IA não deve inventar regras oficiais ou substituir o motor determinístico de D&D.

Toda sugestão que envolva regras deve indicar as fontes utilizadas e permitir revisão humana.

O aplicativo precisa funcionar sem serviços pagos de IA.

---

# 14. PERSISTÊNCIA E SEGURANÇA

Utilizar um modelo de dados relacional com entidades para:

- Usuários.
- Campanhas.
- Participantes.
- Personagens.
- Classes.
- Espécies.
- Magias.
- Monstros.
- Itens.
- Relíquias.
- Inventários.
- Mapas.
- Assets.
- Encontros.
- Turnos.
- Ações de combate.
- Eventos.
- Sessões.
- Fontes documentais.
- Versões das regras.
- Conteúdo homebrew.

Implementar:

- Autenticação segura.
- Hash de senhas.
- Autorização no backend.
- Isolamento entre campanhas.
- Validação de uploads.
- Limites de tamanho dos arquivos.
- Proteção contra traversal em ZIPs.
- Proteção contra arquivos maliciosos.
- Migrações de banco.
- Backups.
- Logs de erros.
- Auditoria.
- Tratamento de concorrência.
- Recuperação de dados.

Permitir instalação local e implantação online.

Não colocar senhas, tokens e credenciais no código-fonte.

---

# 15. API PYTHON

Projetar endpoints organizados.

Exemplos:

```text
/api/characters
/api/characters/{id}
/api/characters/{id}/level-up
/api/characters/{id}/rest
/api/spells
/api/monsters
/api/items
/api/homebrew
/api/campaigns
/api/adventures
/api/encounters
/api/maps
/api/assets
/api/dice/roll
/api/combat/{id}
/api/combat/{id}/actions
/api/combat/{id}/events
/api/library/import
/api/library/sources
```

Toda operação deve possuir schemas de entrada e saída, autenticação quando apropriada, validações e respostas de erro claras.

Criar documentação OpenAPI.

---

# 16. TESTES E CORREÇÃO DAS REGRAS

Este é um requisito obrigatório.

Criar testes automatizados para:

- Criação de personagens.
- Atributos e modificadores.
- Vida por classe e nível.
- Bônus de proficiência.
- Classe de Armadura.
- Salvaguardas.
- Multiclasse.
- Progressão de magias.
- Recuperação de recursos.
- Ataques com vantagem e desvantagem.
- Críticos.
- Resistências.
- Concentração.
- Condições.
- Ações e reações.
- Rodadas.
- Equipamentos.
- Itens mágicos.
- Exportação de fichas.
- Permissões do mestre.
- Importação de PDFs.
- Importação segura de ZIPs.
- Sincronização multiplayer.

Criar testes de referência com casos conhecidos dos livros, quando acessíveis e autorizados.

Não inventar resultados quando uma regra estiver ausente ou ambígua. Registrar a lacuna, indicar a fonte necessária e permitir decisão do mestre.

---

# 17. PLANO DE IMPLEMENTAÇÃO

Não tentar construir tudo em uma única alteração gigantesca.

Desenvolver em etapas verificáveis.

## Fase 1 — Auditoria e arquitetura

- Verificar o repositório existente, caso seja fornecido.
- Inspecionar a pasta do Google Drive.
- Analisar ZIPs e livros.
- Definir modelo de dados.
- Criar estrutura Python.
- Configurar banco de dados.
- Configurar testes.
- Configurar ambiente de desenvolvimento.

Entregável: projeto executável com API, banco e estrutura modular.

## Fase 2 — Enciclopédia

- Importação de documentos.
- Catálogo de entidades.
- Busca e filtros.
- Revisão de dados.
- Proveniência por livro e página.
- Versionamento de regras.

Entregável: biblioteca utilizável com registros realmente importados ou identificados como dados de exemplo.

## Fase 3 — Fichas e personagens

- Criador guiado.
- Motor de atributos.
- Classes e espécies.
- Magias.
- Equipamentos.
- Progressão.
- Fichas digitais.
- Exportação PDF.

Entregável: criação e evolução completa de personagens de um subconjunto validado das regras, expandido progressivamente.

## Fase 4 — Combate Python

- Motor de rolagens.
- Iniciativa.
- Ações.
- Dano.
- Magias.
- Recursos.
- Condições.
- Histórico.
- Testes.

Entregável: combate funcional sem depender da interface gráfica.

## Fase 5 — Visual 2.5D

- Retratos animados.
- Interface de turnos.
- Barras de vida.
- Efeitos de ataque.
- Feedback visual.
- Seleção de alvos.
- Integração com o motor Python.

Entregável: uma batalha jogável na interface.

## Fase 6 — Campanhas e mestre

- Gerenciador de campanhas.
- Sessões.
- Aventuras.
- NPCs.
- Missões.
- Organização narrativa.
- Permissões.

Entregável: campanha persistente e administrável.

## Fase 7 — Editor de masmorras

- Canvas.
- Ferramentas gráficas.
- Assets.
- Camadas.
- Grade.
- Tokens.
- Colisões.
- Exportação.
- Geração procedural.

Entregável: editor utilizável com mapas salvos e reabertos corretamente.

## Fase 8 — Multiplayer

- Autenticação.
- Salas.
- WebSockets.
- Controle de jogadores.
- Sincronização de eventos.
- Segurança.
- Reconexão.

Entregável: mestre e jogadores participando de uma sessão real.

## Fase 9 — Homebrew e ferramentas avançadas

- Criador de itens.
- Relíquias.
- Monstros.
- Magias.
- Regras declarativas.
- Simulação de encontros.
- Estatísticas.

## Fase 10 — Finalização

- Testes de integração.
- Correção de bugs.
- Testes de desempenho.
- Segurança.
- Documentação.
- Instalação local.
- Docker.
- Preparação para produção.

---

# 18. CRITÉRIOS DE ACEITAÇÃO

O sistema só poderá ser considerado uma versão funcional completa quando:

1. Um usuário conseguir criar um personagem e salvar sua ficha.
2. Os cálculos automáticos forem testados e consistentes com o conjunto de regras selecionado.
3. O usuário puder subir de nível e atualizar corretamente seus recursos.
4. O catálogo conseguir consultar dados realmente importados.
5. O mestre puder criar e salvar uma campanha.
6. O mestre puder criar e salvar um mapa.
7. Uma party puder iniciar uma batalha.
8. Os participantes puderem atacar, conjurar magias e consumir recursos corretamente.
9. O combate produzir animações a partir das imagens dos personagens.
10. Os pontos de vida e condições forem atualizados.
11. O mestre puder criar um item mágico ou relíquia e utilizá-lo no jogo.
12. Os dados persistirem após reiniciar o aplicativo.
13. Os testes automatizados forem executados.
14. As interfaces críticas estiverem integradas ao backend.
15. O sistema tiver instruções claras de instalação.

Funcionalidades ainda não implementadas devem ser identificadas de forma transparente.

---

# 19. REGRAS DE TRABALHO PARA O CODEX

- Não substituir Python por Node.js no backend.
- Não deixar cálculos oficiais exclusivamente no frontend.
- Não usar valores fictícios como se fossem dados reais importados.
- Não inventar conteúdo dos PDFs ou ZIPs.
- Não presumir acesso ao Drive sem credenciais autorizadas.
- Não criar apenas telas sem funcionalidade.
- Não declarar testes bem-sucedidos sem executá-los.
- Não apagar arquivos existentes sem necessidade.
- Não realizar mudanças destrutivas no banco sem migrações.
- Evitar dependências pagas e serviços obrigatórios externos.
- Preferir código legível, organizado e documentado.
- Implementar testes para cada recurso crítico.
- Fazer commits pequenos e coerentes.
- Manter um arquivo `IMPLEMENTATION_STATUS.md` com recursos concluídos, incompletos e bloqueados.

Quando necessário, faça escolhas técnicas justificadas e registre-as.

---

# 20. INSTRUÇÃO FINAL

Comece inspecionando o ambiente de desenvolvimento, o repositório existente e os arquivos disponibilizados.

Se houver um projeto anterior de criação de fichas, avalie a possibilidade de reaproveitar dados, regras e funcionalidades sem comprometer a arquitetura Python.

Não comece pela aparência visual. Comece pela estrutura do projeto, banco de dados, motor de regras e testes.

Depois implemente uma primeira experiência vertical completa:

**Criar personagem → salvar ficha → selecionar party → enfrentar monstro → executar ataques → calcular dano em Python → apresentar animações 2.5D → finalizar encontro → salvar resultados.**

Esta experiência precisa funcionar antes de ampliar o aplicativo para dezenas de recursos adicionais.

Continue implementando as fases seguintes de acordo com as prioridades, mantendo cada fase executável.

O resultado esperado é um verdadeiro sistema de gerenciamento e execução de RPG, construído sobre Python, com recursos profundos para jogadores e mestres, arquitetura profissional e potencial de expansão.

**NOME DO PROJETO: ARCANUM**

**LINGUAGEM PRINCIPAL: PYTHON**

**OBJETIVO: UMA PLATAFORMA UNIFICADA DE DUNGEONS & DRAGONS COM FICHAS, REGRAS, AVENTURAS, MAPAS E COMBATE 2.5D.**