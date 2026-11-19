# Inventário das fontes — ARCANUM

Auditoria realizada em **18/11/2026** sobre a [pasta indicada no prompt](https://drive.google.com/drive/u/0/folders/1Pl8z4uFcutTBoc0XB2Pe-qjHoWJjVZFm), pela integração autenticada Google Drive. Foram confirmados os dez itens principais e onze itens diretos na subpasta Valebruma. Este documento registra metadados e achados estruturais; não contém transcrições dos livros.

## Método e evidências privadas

- Metadados MIME, nomes, IDs, URLs e tamanhos foram consultados antes dos downloads.
- Os quatro ZIPs principais, quatro PDFs principais, dois ZIPs de Valebruma, seu JSON de rolagens e README foram baixados completos. Os tamanhos locais coincidem com os metadados; SHA-256 foi calculado para cada arquivo.
- Os arquivos estão em `.arcanum/sources/raw/`; evidências detalhadas estão em `.arcanum/sources/drive_metadata.json`, `.arcanum/sources/audit.json` e `.arcanum/sources/valebruma_audit.json`. Todo esse diretório permanece ignorado pelo Git e fora das rotas públicas da aplicação.
- ZIPs foram abertos com `zipfile`, sem extração de caminhos e sem execução de código, instaladores ou HTML contidos neles. Foram lidos apenas metadados dos membros, arquivos de licença/README/manifests limitados a 128 KB e os PDFs conhecidos de Valebruma em memória.
- PDFs foram inspecionados com PyMuPDF 1.28.2, instalado exclusivamente em `.arcanum/sources/python_deps/`. Não foram alterados os ambientes Python do backend nem da ponte MCP.

## ZIPs principais

As contagens de imagens consideram extensões PNG, JPG/JPEG, WEBP, SVG, GIF, BMP e ICO. Incluem ícones, capturas de tela e material de documentação: não representam uma coleção de tokens pronta para uso.

| Fonte | Tamanho em bytes | Entradas / arquivos | Imagens | Conteúdo verificado | Licença encontrada |
| --- | ---: | ---: | ---: | --- | --- |
| [chronicler-master.zip](https://drive.google.com/file/d/1WbPp0qfrMqKrm7a2MXG_jP1E93d5MSnw/view?usp=drivesdk) | 14.924.397 | 403 / 359 | 66 | Aplicação de organização de mundos e notas; Svelte/TypeScript, Rust e Tauri; fontes e material de demonstração. | `chronicler-master/LICENSE`: PolyForm Shield 1.0.0. README identifica o projeto como *source-available* e restringe reutilização para software concorrente. |
| [Dungeoneer-master.zip](https://drive.google.com/file/d/192HAkjlmq96f7Z8NDgfx6H6yplSjJWpb/view?usp=drivesdk) | 121.054.505 | 591 / 534 | 204 | Aplicação Electron/JavaScript para mesa virtual, encontros e consulta; HTML/CSS, sons, fontes e cinco arquivos `.dungeoneer_map`. | `Dungeoneer-master/LICENSE.md`: GNU AGPL versão 3; `package.json`: `AGPL-3.0-or-later`. Foram encontrados avisos adicionais de dependências e fontes. |
| [AsLib-master.zip](https://drive.google.com/file/d/12qVGlg9XQ1IRg8uutvLMTVkCRGtPqSpi/view?usp=drivesdk) | 64.976.155 | 218 / 209 | 126 | Projeto de editor de mapas predominantemente C++/headers, arquivos de projeto, CSVs, exemplos e imagens. | `AsLib-master/LICENSE`: CC0 1.0 Universal. README aplica CC0 ao código e ressalva os direitos do conteúdo de terceiros. |
| [COMPASS-master.zip](https://drive.google.com/file/d/11ujbSeFKlv2b-40-dMJgCUYVxQMdN-Pa/view?usp=drivesdk) | 31.400.737 | 732 / 602 | 34 | Aplicação de catálogo de recursos de RPG em C#/Avalonia; AXAML, projetos, fontes, documentação e vídeos. | `COMPASS-master/LICENSE`: GNU AGPL versão 3. |

**Decisão de implementação:** os quatro pacotes são projetos de software, com documentação e recursos adicionais; não são meros pacotes de imagens. Nenhum código, imagem, fonte ou outro recurso foi incorporado ao ARCANUM. Antes de qualquer incorporação, será necessário verificar a licença e os avisos do arquivo específico e a compatibilidade com a forma de distribuição pretendida. O conteúdo do Chronicler não deve ser tratado como código aberto irrestrito; a ressalva de terceiros da AsLib também impede presumir CC0 para todas as imagens.

Nos seis ZIPs auditados, não foram identificados nomes de membros com caminho absoluto/traversal, links simbólicos Unix, criptografia ou entradas acima do critério de compressão suspeita usado nesta inspeção (mais de 1 MB e razão superior a 200:1). Isso descreve as verificações realizadas; não equivale a análise completa de malware. Não foi executado `testzip()` para verificar o CRC de cada membro.

## PDFs principais

“Páginas com texto” significa páginas nas quais PyMuPDF retornou algum texto; não atesta a correção da ordem de leitura, das tabelas ou do reconhecimento de regras.

| Fonte | Bytes | Páginas | Páginas com texto | Campos de formulário |
| --- | ---: | ---: | ---: | ---: |
| [D&D 5ed — Ficha Editável](https://drive.google.com/file/d/1_nwu7T3Hd9wQOuJhLpaDE-UT0Fn44D7V/view?usp=drivesdk) | 974.767 | 3 | 0 | 335 |
| [Ficha de guerreiro draconato preenchida](https://drive.google.com/file/d/1zFShcvGuUhfNwETk0Df-sOXcVw55gYRY/view?usp=drivesdk) | 993.824 | 2 | 2 | 120 |
| [Manual dos Monstros](https://drive.google.com/file/d/1UmU78E_TJWyW9vsR6jnri6-njuz5QYk-/view?usp=drivesdk) | 19.949.915 | 352 | 349 | 0 |
| [Livro do Jogador](https://drive.google.com/file/d/1bNYHw3R23kPZGysYFo9FxiwnaR5v7eva/view?usp=drivesdk) | 21.943.540 | 315 | 314 | 0 |

O PDF editável contém widgets acessíveis mesmo sem uma camada de texto retornada pelo extrator. Há ao menos duas estruturas diferentes de formulário, com 335 e 120 campos, portanto a importação/exportação precisará de mapeamentos específicos e testes que preservem o layout. Não foi realizado preenchimento de teste, exportação ou comparação visual nesta auditoria.

Os livros estão disponíveis localmente para processamento privado futuro. **Ainda não foram convertidos em entidades da enciclopédia, fontes de regras validadas ou registros de banco.** A edição/conjunto de regras e a proveniência por página precisam ser confirmados durante a normalização; o nome “5e” não foi usado para decidir automaticamente entre 2014 e 2024.

O [Guia do Mestre](https://drive.google.com/file/d/1vVk6rVXxMl2OGn27S6ho2ifvsHTaa1QG/view?usp=drivesdk) foi identificado pelo MIME **`application/vnd.google-apps.shortcut`**. Os metadados retornados não forneceram o destino do atalho. O livro não foi baixado nem lido, e seu conteúdo não integra este inventário estrutural.

## Valebruma

A [subpasta Valebruma](https://drive.google.com/drive/folders/18BrvJjVLdT8rnXIyAnYwyNpqhJGSa8cw) retornou onze itens: cinco fichas PDF, dois ZIPs, um JSON de dados/rolagens, um HTML interativo, um README e um Google Doc. O conteúdo do Google Doc e do HTML avulso não foi lido nem executado nesta etapa.

- `Valebruma_5_fichas_e_rolagens.zip`: 2.613.044 bytes, sete membros — cinco PDFs, `Dados_e_Rolagens.json` e `LEIA-ME.txt`.
- `Valebruma_Pacote_Completo_Painel_Interativo.zip`: 2.618.220 bytes, oito membros — os mesmos arquivos e um HTML interativo.
- Os cinco PDFs dos dois ZIPs são idênticos entre si por SHA-256. Foram analisados em memória, sem extrair seus caminhos.

| Ficha identificada pelo nome do arquivo | Páginas | Campos / nomes distintos |
| --- | ---: | ---: |
| Mago / elfo alto | 4 | 335 / 335 |
| Clérigo / anão da colina | 4 | 335 / 335 |
| Ladino / halfling pés-leves | 3 | 120 / 120 |
| Bárbaro / meio-orc | 3 | 120 / 120 |
| Bardo / tiefling | 4 | 335 / 335 |

O `Dados_e_Rolagens.json` avulso tem 11.308 bytes e uma lista de cinco registros, com seis rolagens por registro. Foram conferidas as trinta rolagens de quatro d6, o descarte do menor dado, as somas resultantes, a atribuição dos resultados aos atributos-base e os modificadores calculados a partir dos atributos finais. Não foram encontradas inconsistências nessas verificações aritméticas.

O JSON contém cinco referências absolutas legadas a `/mnt/data/...`, que não correspondem a caminhos locais deste projeto, e não explicita um identificador de conjunto de regras. A importação deverá substituir essas referências por IDs de assets e definir o conjunto de regras. Esses resultados não validam automaticamente classe, equipamento, proficiências, pontos de vida, CA, características raciais ou a ficha inteira.

## Pendências objetivas

1. Resolver o destino do atalho do Guia do Mestre com acesso autorizado.
2. Construir importação privada de documentos com proveniência, revisão e isolamento de usuários/campanhas.
3. Mapear e testar os dois modelos de formulário PDF sem alterar os originais.
4. Normalizar o conjunto de regras e os campos legados antes de importar as fichas de Valebruma.
5. Avaliar individualmente os recursos candidatos a reutilização, preservando atribuições e condições aplicáveis.
6. Não publicar os PDFs, textos extraídos ou evidências privadas em Git, endpoints públicos ou catálogos compartilhados.
