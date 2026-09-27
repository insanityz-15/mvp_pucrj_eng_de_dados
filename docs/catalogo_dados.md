# Catálogo de dados

> Gerado automaticamente a partir da tabela `governanca.catalogo_dados` (notebook `06_catalogo_dados`). Os mesmos textos estão aplicados como comentários de tabela/coluna no Unity Catalog.

> **Domínio observado** = mín/máx (numéricos) ou categorias (texto) medidos nos dados; **% nulos** medido na própria tabela.


## `gold.dim_time`

Dimensão de clubes. Grão: 1 linha por clube. Fonte: silver.jogador_partida + silver.time_de_para.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `team_id` | bigint | Identificador StatsBomb do clube | inteiro; 20 valores | [1183 ; 5695] | 0.0% | silver.jogador_partida.team_id |
| `nome_time` | string | Nome padronizado do clube | 20 clubes da Série A 2025 | 20 valores distintos | 0.0% | silver.time_de_para.nome_time |
| `nome_curto` | string | Nome curto para exibição | texto | 20 valores distintos | 0.0% | silver.time_de_para.nome_curto |
| `sigla` | string | Sigla de 3 letras | texto de 3 caracteres | 20 valores distintos | 0.0% | silver.time_de_para.sigla (manual) |
| `uf` | string | Unidade federativa da sede | UF brasileira | 7 valores distintos | 0.0% | silver.time_de_para.uf (manual) |
| `nome_fonte` | string | Nome do clube como veio da StatsBomb | texto | 20 valores distintos | 0.0% | bronze.team_name |

## `gold.dim_jogador`

Dimensão de jogadores. Grão: 1 linha por player_id.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `player_id` | bigint | Identificador StatsBomb do jogador | inteiro; 737 valores | [2949 ; 5.311e+05] | 0.0% | silver.jogador_partida.player_id |
| `nome_jogador` | string | Nome do jogador como na fonte | texto | 689 valores distintos | 0.0% | silver.jogador_partida.player_name |
| `nome_exibicao` | string | Nome sem ambiguidade: homônimos recebem o clube principal entre parênteses | texto único | 737 valores distintos | 0.0% | derivado de nome_jogador + time_principal |
| `tipo_jogador` | string | Goleiro ou Linha | {Goleiro, Linha} | {Goleiro, Linha} | 0.0% | derivado de is_goleiro |
| `is_goleiro` | boolean | Jogador atuou como goleiro ao menos uma vez (tem métrica obv_gk) | true/false | {False, True} | 0.0% | silver.jogador_partida.is_goleiro |
| `time_principal_id` | bigint | Clube em que o jogador somou mais minutos na temporada | FK dim_time | [1183 ; 5695] | 0.0% | silver: argmax(soma minutos) por team_id |
| `time_principal` | string | Nome curto do clube principal | texto | 20 valores distintos | 0.0% | dim_time.nome_curto |
| `qtd_times` | bigint | Quantidade de clubes pelos quais atuou na temporada | 1 ou 2 | [1 ; 2] | 0.0% | silver: count distinct team_id |
| `nome_homonimo` | boolean | Existe outro player_id com o mesmo nome | true/false | {False, True} | 0.0% | derivado |

## `gold.dim_partida`

Dimensão de partidas. Grão: 1 linha por partida. Placar derivado da soma dos gols dos jogadores (fonte sem placar, data ou mando).

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `match_id` | bigint | Identificador StatsBomb da partida | inteiro; 380 valores | [3.989e+06 ; 3.989e+06] | 0.0% | silver.jogador_partida.match_id |
| `time_a_id` | bigint | Clube de menor team_id no confronto (não indica mando) | FK dim_time | [1183 ; 5693] | 0.0% | silver.team_id |
| `time_a` | string | Nome curto do time A | texto | 19 valores distintos | 0.0% | dim_time |
| `time_b_id` | bigint | Clube de maior team_id no confronto | FK dim_time | [1184 ; 5695] | 0.0% | silver.team_id |
| `time_b` | string | Nome curto do time B | texto | 19 valores distintos | 0.0% | dim_time |
| `gols_time_a` | int | Gols do time A | inteiro >= 0 | [0 ; 8] | 0.0% | SUM(silver.player_match_goals) do time A |
| `gols_time_b` | int | Gols do time B | inteiro >= 0 | [0 ; 6] | 0.0% | SUM(silver.player_match_goals) do time B |
| `total_gols` | int | Total de gols na partida | inteiro >= 0 | [0 ; 8] | 0.0% | gols_time_a + gols_time_b |
| `confronto` | string | Texto 'Time A gols x gols Time B' | texto | 373 valores distintos | 0.0% | derivado |
| `vencedor` | string | Nome do vencedor ou 'Empate' | texto | 21 valores distintos | 0.0% | derivado |
| `temporada` | int | Temporada | 2025 | [2025 ; 2025] | 0.0% | parâmetro do pipeline |

## `gold.fato_jogador_partida`

Fato de desempenho do jogador por partida. Grão: match_id + player_id. Métricas StatsBomb renomeadas em português.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `match_id` | bigint | Identificador StatsBomb da partida | inteiro; 380 valores | [3.989e+06 ; 3.989e+06] | 0.0% | silver.jogador_partida.match_id |
| `player_id` | bigint | Identificador StatsBomb do jogador | inteiro; 737 valores | [2949 ; 5.311e+05] | 0.0% | silver.jogador_partida.player_id |
| `team_id` | bigint | Identificador StatsBomb do clube | inteiro; 20 valores | [1183 ; 5695] | 0.0% | silver.jogador_partida.team_id |
| `adversario_id` | bigint | team_id do adversário na partida (derivado do self-join por match_id) | inteiro; FK dim_time | [1183 ; 5695] | 0.0% | gold.dim_partida (time_a_id/time_b_id) |
| `minutos` | double | Minutos jogados pelo atleta na partida (inclui acréscimos) | 0 < x <= 130 | [0.2833 ; 114] | 0.0% | silver.jogador_partida.player_match_minutes |
| `gols` | int | Gols marcados (inclui pênaltis; gols contra não são creditados) | inteiro >= 0 | [0 ; 3] | 0.0% | silver.jogador_partida.player_match_goals |
| `gols_sem_penalti` | int | Gols marcados excluindo pênaltis | inteiro >= 0, <= gols | [0 ; 3] | 0.0% | silver.jogador_partida.player_match_np_goals |
| `assistencias` | int | Assistências para gol | inteiro >= 0 | [0 ; 3] | 0.0% | silver.jogador_partida.player_match_assists |
| `finalizacoes_sem_penalti` | int | Finalizações excluindo pênaltis | inteiro >= 0 | [0 ; 11] | 0.0% | silver.jogador_partida.player_match_np_shots |
| `finalizacoes_no_alvo` | int | Finalizações sem pênalti no alvo | inteiro >= 0, <= finalizacoes_sem_penalti | [0 ; 5] | 0.0% | silver.jogador_partida.player_match_np_shots_on_target |
| `xg_sem_penalti` | double | Gols esperados (xG StatsBomb) das finalizações sem pênalti; NULL = não finalizou | 0 <= x; NULL permitido | [0 ; 1.919] | 0.0% | silver.jogador_partida.player_match_np_xg |
| `xg_por_finalizacao` | double | xG médio por finalização sem pênalti; NULL = não finalizou | 0 <= x <= 1; NULL permitido | [0.003011 ; 0.95] | 52.9% | silver.jogador_partida.player_match_np_xg_per_shot |
| `xa` | double | Assistências esperadas: soma do xG das finalizações originadas de passes do jogador | 0 <= x; NULL permitido | [0 ; 1.508] | 0.0% | silver.jogador_partida.player_match_xa |
| `passes_decisivos` | int | Passes que resultaram em finalização (key passes) | inteiro >= 0 | [0 ; 9] | 0.0% | silver.jogador_partida.player_match_key_passes |
| `passes_em_profundidade` | int | Passes em profundidade (through balls) | inteiro >= 0 | [0 ; 3] | 0.0% | silver.jogador_partida.player_match_through_balls |
| `passes` | int | Passes tentados | inteiro >= 0 | [0 ; 144] | 0.0% | silver.jogador_partida.player_match_passes |
| `passes_certos` | int | Passes completados | inteiro >= 0, <= passes | [0 ; 135] | 0.0% | silver.jogador_partida.player_match_successful_passes |
| `passes_para_frente` | int | Passes para frente | inteiro >= 0 | [0 ; 36] | 0.0% | silver.jogador_partida.player_match_forward_passes |
| `passes_terco_final` | int | Passes em jogo aberto no terço final | inteiro >= 0 | [0 ; 65] | 0.0% | silver.jogador_partida.player_match_op_f3_passes |
| `passes_para_area` | int | Passes completados para dentro da área | inteiro >= 0 | [0 ; 10] | 0.0% | silver.jogador_partida.player_match_passes_into_box |
| `progressoes_profundas` | int | Passes/conduções que chegam ao terço final (deep progressions) | inteiro >= 0 | [0 ; 26] | 0.0% | silver.jogador_partida.player_match_deep_progressions |
| `cruzamentos` | int | Cruzamentos tentados | inteiro >= 0 | [0 ; 12] | 0.0% | silver.jogador_partida.player_match_crosses |
| `cruzamentos_certos` | int | Cruzamentos completados | inteiro >= 0, <= cruzamentos | [0 ; 6] | 0.0% | silver.jogador_partida.player_match_successful_crosses |
| `bolas_longas` | int | Bolas longas tentadas | inteiro >= 0 | [0 ; 40] | 0.0% | silver.jogador_partida.player_match_long_balls |
| `bolas_longas_certas` | int | Bolas longas completadas | inteiro >= 0, <= bolas_longas | [0 ; 20] | 0.0% | silver.jogador_partida.player_match_successful_long_balls |
| `dribles_certos` | int | Dribles bem-sucedidos | inteiro >= 0 | [0 ; 9] | 0.0% | silver.jogador_partida.player_match_dribbles |
| `toques` | int | Toques na bola | inteiro >= 0 | [0 ; 282] | 0.0% | silver.jogador_partida.player_match_touches |
| `toques_na_area` | int | Toques na bola dentro da área adversária | inteiro >= 0 | [0 ; 25] | 0.0% | silver.jogador_partida.player_match_touches_inside_box |
| `desarmes` | int | Desarmes | inteiro >= 0 | [0 ; 10] | 0.0% | silver.jogador_partida.player_match_tackles |
| `interceptacoes` | int | Interceptações | inteiro >= 0 | [0 ; 8] | 0.0% | silver.jogador_partida.player_match_interceptions |
| `recuperacoes` | int | Recuperações de bola | inteiro >= 0 | [0 ; 30] | 0.0% | silver.jogador_partida.player_match_ball_recoveries |
| `pressoes` | int | Pressões sobre o portador da bola | inteiro >= 0 | [0 ; 51] | 0.0% | silver.jogador_partida.player_match_pressures |
| `contrapressoes` | int | Pressões nos 5 s após perda da posse (counterpressures) | inteiro >= 0 | [0 ; 15] | 0.0% | silver.jogador_partida.player_match_counterpressures |
| `recuperacoes_pos_pressao` | int | Recuperações de bola até 5 s após uma pressão | inteiro >= 0 | [0 ; 16] | 0.0% | silver.jogador_partida.player_match_pressure_regains |
| `acoes_defensivas` | int | Total de ações defensivas | inteiro >= 0 | [0 ; 61] | 0.0% | silver.jogador_partida.player_match_defensive_actions |
| `cortes` | int | Cortes/afastamentos (clearances) | inteiro >= 0 | [0 ; 14] | 0.0% | silver.jogador_partida.player_match_clearances |
| `duelos_aereos` | int | Duelos aéreos disputados | inteiro >= 0 | [0 ; 22] | 0.0% | silver.jogador_partida.player_match_aerials |
| `duelos_aereos_vencidos` | int | Duelos aéreos vencidos | inteiro >= 0, <= duelos_aereos | [0 ; 14] | 0.0% | silver.jogador_partida.player_match_successful_aerials |
| `vezes_driblado` | int | Vezes em que o jogador foi driblado | inteiro >= 0 | [0 ; 8] | 0.0% | silver.jogador_partida.player_match_dribbled_past |
| `faltas_cometidas` | int | Faltas cometidas | inteiro >= 0 | [0 ; 9] | 0.0% | silver.jogador_partida.player_match_fouls |
| `faltas_sofridas` | int | Faltas sofridas | inteiro >= 0 | [0 ; 11] | 0.0% | silver.jogador_partida.player_match_fouls_won |
| `perdas_de_posse` | int | Desarmado com a bola (dispossessed) | inteiro >= 0 | [0 ; 10] | 0.0% | silver.jogador_partida.player_match_dispossessions |
| `erros_com_bola` | int | Perdas de posse por erro (turnovers) | inteiro >= 0 | [0 ; 13] | 0.0% | silver.jogador_partida.player_match_turnovers |
| `xg_chain` | double | xG das posses em que o jogador participou | >= 0; NULL permitido | [0 ; 3.278] | 0.3% | silver.jogador_partida.player_match_xgchain |
| `xg_buildup` | double | xG Chain excluindo o chute e o passe para o chute | >= 0; NULL permitido | [0 ; 2.445] | 0.3% | silver.jogador_partida.player_match_xgbuildup |
| `obv_total` | double | On-Ball Value total: variação da probabilidade de gol causada pelas ações com bola | real (pode ser negativo) | [-2.858 ; 2.578] | 0.0% | silver.jogador_partida.player_match_obv |
| `obv_passe` | double | OBV de passes | real (pode ser negativo) | [-0.4985 ; 1.168] | 0.0% | silver.jogador_partida.player_match_obv_pass |
| `obv_conducao` | double | OBV de dribles e conduções | real (pode ser negativo) | [-0.6812 ; 1.118] | 0.0% | silver.jogador_partida.player_match_obv_dribble_carry |
| `obv_defesa` | double | OBV de ações defensivas | real (pode ser negativo) | [-1.415 ; 1.161] | 0.0% | silver.jogador_partida.player_match_obv_defensive_action |
| `obv_finalizacao` | double | OBV de finalizações; NULL = não finalizou | real; NULL permitido | [-0.9753 ; 1.435] | 52.8% | silver.jogador_partida.player_match_obv_shot |
| `posse_time` | double | Posse de bola do time do jogador na partida | 0 <= x <= 1 | [0.2165 ; 0.7835] | 0.0% | silver.jogador_partida.player_match_possession |
| `gols_sofridos_gk` | double | Gols sofridos enquanto goleiro; NULL = não atuou no gol | inteiro >= 0; NULL p/ jogador de linha | [0 ; 8] | 0.0% | silver.jogador_partida.player_match_goals_conceded |
| `gsaa_gk` | double | Gols evitados acima do esperado (goleiro); NULL = não atuou no gol | real; NULL p/ jogador de linha | [-3.025 ; 3.039] | 0.0% | silver.jogador_partida.player_match_gsaa |
| `is_goleiro` | boolean | Jogador atuou como goleiro ao menos uma vez (tem métrica obv_gk) | true/false | {False, True} | 0.0% | silver.jogador_partida.is_goleiro |
| `tem_cobertura_360` | boolean | Partida do jogador com cobertura StatsBomb 360 (360_minutes > 0) | true/false | {False, True} | 0.0% | silver.jogador_partida.tem_cobertura_360 |
| `_id_carga` | string | Identificador da execução de ingestão Bronze que originou o registro | texto yyyymmddThhmmss-hash | {20260926T024030-679f2d7d} | 0.0% | bronze._id_carga |

## `gold.fato_time_partida`

Fato de desempenho do time por partida. Grão: match_id + team_id.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `match_id` | bigint | Identificador StatsBomb da partida | inteiro; 380 valores | [3.989e+06 ; 3.989e+06] | 0.0% | gold.fato_jogador_partida.match_id |
| `team_id` | bigint | Identificador StatsBomb do clube | inteiro; 20 valores | [1183 ; 5695] | 0.0% | gold.fato_jogador_partida.team_id |
| `adversario_id` | bigint | team_id do adversário na partida (derivado do self-join por match_id) | inteiro; FK dim_time | [1183 ; 5695] | 0.0% | gold.fato_jogador_partida.adversario_id |
| `gols_pro` | int | Gols do time | >= 0 | [0 ; 8] | 0.0% | SUM(fato_jogador_partida.gols) do time |
| `gols_contra` | int | Gols do adversário (sofridos) | >= 0 | [0 ; 8] | 0.0% | SUM(fato_jogador_partida.gols) do adversário |
| `gols_sem_penalti_pro` | int | Gols sem pênalti do time | >= 0 | [0 ; 7] | 0.0% | SUM(fato_jogador_partida.gols_sem_penalti) do time |
| `gols_sem_penalti_contra` | int | Gols sem pênalti do adversário (sofridos) | >= 0 | [0 ; 7] | 0.0% | SUM(fato_jogador_partida.gols_sem_penalti) do adversário |
| `xg_sem_penalti_pro` | double | xG sem pênalti do time | >= 0 | [0.0204 ; 3.678] | 0.0% | SUM(fato_jogador_partida.xg_sem_penalti) do time |
| `xg_sem_penalti_contra` | double | xG sem pênalti do adversário (sofridos) | >= 0 | [0.0204 ; 3.678] | 0.0% | SUM(fato_jogador_partida.xg_sem_penalti) do adversário |
| `finalizacoes_pro` | int | Finalizações sem pênalti do time | >= 0 | [1 ; 35] | 0.0% | SUM(fato_jogador_partida.finalizacoes_sem_penalti) do time |
| `finalizacoes_contra` | int | Finalizações sem pênalti do adversário (sofridos) | >= 0 | [1 ; 35] | 0.0% | SUM(fato_jogador_partida.finalizacoes_sem_penalti) do adversário |
| `finalizacoes_no_alvo_pro` | int | Finalizações no alvo do time | >= 0 | [0 ; 13] | 0.0% | SUM(fato_jogador_partida.finalizacoes_no_alvo) do time |
| `finalizacoes_no_alvo_contra` | int | Finalizações no alvo do adversário (sofridos) | >= 0 | [0 ; 13] | 0.0% | SUM(fato_jogador_partida.finalizacoes_no_alvo) do adversário |
| `passes` | int | Passes tentados — soma do time | inteiro >= 0 | [212 ; 909] | 0.0% | SUM(fato_jogador_partida.passes) |
| `passes_certos` | int | Passes completados — soma do time | inteiro >= 0, <= passes | [130 ; 835] | 0.0% | SUM(fato_jogador_partida.passes_certos) |
| `pct_passes_certos` | double | Percentual de passes certos do time | 0 a 1 | [0.5399 ; 0.9225] | 0.0% | passes_certos / passes |
| `passes_decisivos` | int | Passes que resultaram em finalização (key passes) — soma do time | inteiro >= 0 | [0 ; 29] | 0.0% | SUM(fato_jogador_partida.passes_decisivos) |
| `toques_na_area` | int | Toques na bola dentro da área adversária — soma do time | inteiro >= 0 | [1 ; 70] | 0.0% | SUM(fato_jogador_partida.toques_na_area) |
| `pressoes` | int | Pressões sobre o portador da bola — soma do time | inteiro >= 0 | [43 ; 282] | 0.0% | SUM(fato_jogador_partida.pressoes) |
| `contrapressoes` | int | Pressões nos 5 s após perda da posse (counterpressures) — soma do time | inteiro >= 0 | [13 ; 65] | 0.0% | SUM(fato_jogador_partida.contrapressoes) |
| `recuperacoes` | int | Recuperações de bola — soma do time | inteiro >= 0 | [43 ; 147] | 0.0% | SUM(fato_jogador_partida.recuperacoes) |
| `desarmes` | int | Desarmes — soma do time | inteiro >= 0 | [5 ; 40] | 0.0% | SUM(fato_jogador_partida.desarmes) |
| `interceptacoes` | int | Interceptações — soma do time | inteiro >= 0 | [1 ; 25] | 0.0% | SUM(fato_jogador_partida.interceptacoes) |
| `obv_total` | double | On-Ball Value total: variação da probabilidade de gol causada pelas ações com bola — soma do time | real (pode ser negativo) | [-2.743 ; 5.673] | 0.0% | SUM(fato_jogador_partida.obv_total) |
| `posse` | double | Posse de bola do time | 0 a 1 | [0.2165 ; 0.7835] | 0.0% | AVG(fato_jogador_partida.posse_time) |
| `jogadores_utilizados` | int | Jogadores que entraram em campo | 11 a 16 | [13 ; 17] | 0.0% | COUNT(fato_jogador_partida) |
| `resultado` | string | Resultado para o time | {V, E, D} | {D, E, V} | 0.0% | gols_pro vs gols_contra |
| `pontos` | int | Pontos conquistados | {0, 1, 3} | [0 ; 3] | 0.0% | V=3, E=1, D=0 |

## `gold.mart_classificacao`

Mart: classificação derivada do Brasileirão 2025 e indicadores de xG por clube. Grão: 1 linha por clube.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `posicao` | int | Posição na classificação derivada (pontos, vitórias, saldo, gols pró) | 1 a 20 | [1 ; 20] | 0.0% | ROW_NUMBER sobre fato_time_partida |
| `team_id` | bigint | Identificador StatsBomb do clube | inteiro; 20 valores | [1183 ; 5695] | 0.0% | fato_time_partida.team_id |
| `time` | string | Nome curto do clube | texto | 20 valores distintos | 0.0% | dim_time.nome_curto |
| `jogos` | bigint | Jogos disputados | 38 | [38 ; 38] | 0.0% | COUNT(fato_time_partida) |
| `pontos` | bigint | Pontos | 0 a 114 | [16 ; 79] | 0.0% | SUM(pontos) |
| `vitorias` | bigint | Vitórias | 0 a 38 | [2 ; 23] | 0.0% | SUM(resultado='V') |
| `empates` | bigint | Empates | 0 a 38 | [6 ; 13] | 0.0% | SUM(resultado='E') |
| `derrotas` | bigint | Derrotas | 0 a 38 | [5 ; 26] | 0.0% | SUM(resultado='D') |
| `gols_pro` | bigint | Gols marcados | >= 0 | [26 ; 78] | 0.0% | SUM(gols_pro) |
| `gols_contra` | bigint | Gols sofridos | >= 0 | [27 ; 72] | 0.0% | SUM(gols_contra) |
| `saldo_gols` | bigint | Saldo de gols | inteiro | [-46 ; 51] | 0.0% | gols_pro - gols_contra |
| `aproveitamento` | double | Aproveitamento de pontos | 0 a 1 | [0.1404 ; 0.693] | 0.0% | pontos / (jogos*3) |
| `xg_sem_penalti_pro` | double | xG sem pênalti gerado | >= 0 | [31.25 ; 52.9] | 0.0% | SUM(xg_sem_penalti_pro) |
| `xg_sem_penalti_contra` | double | xG sem pênalti cedido | >= 0 | [28.02 ; 56.8] | 0.0% | SUM(xg_sem_penalti_contra) |
| `saldo_xg` | double | Saldo de xG sem pênalti | real | [-21.14 ; 24.88] | 0.0% | pro - contra |
| `gols_menos_xg_pro` | double | Gols sem pênalti menos xG gerado (>0 = finalização acima do esperado) | real | [-11.66 ; 18.1] | 0.0% | gols_sem_penalti_pro - xg_sem_penalti_pro |
| `gols_menos_xg_contra` | double | Gols sem pênalti sofridos menos xG cedido (<0 = defesa/goleiro acima do esperado) | real | [-6.38 ; 10.26] | 0.0% | gols_sem_penalti_contra - xg_sem_penalti_contra |
| `finalizacoes_pro_por_jogo` | double | Finalizações por jogo | >= 0 | [10.89 ; 15.26] | 0.0% | AVG(finalizacoes_pro) |
| `finalizacoes_contra_por_jogo` | double | Finalizações cedidas por jogo | >= 0 | [9.37 ; 16] | 0.0% | AVG(finalizacoes_contra) |
| `pressoes_por_jogo` | double | Pressões por jogo | >= 0 | [150.6 ; 185.7] | 0.0% | AVG(pressoes) |
| `recuperacoes_por_jogo` | double | Recuperações por jogo | >= 0 | [74.8 ; 89.2] | 0.0% | AVG(recuperacoes) |
| `posse_media` | double | Posse média | 0 a 1 | [0.4174 ; 0.6142] | 0.0% | AVG(posse) |
| `pct_passes_certos` | double | Percentual de passes certos | 0 a 1 | [0.7661 ; 0.8701] | 0.0% | SUM(passes_certos)/SUM(passes) |
| `obv_total` | double | OBV total da temporada | real | [32.68 ; 78.17] | 0.0% | SUM(obv_total) |
| `posicao_oficial` | int | Posição na classificação oficial CBF | 1 a 20 | [1 ; 20] | 0.0% | silver.classificacao_oficial_referencia.posicao |
| `pontos_oficiais` | int | Pontos na classificação oficial CBF | 0 a 114 | [17 ; 79] | 0.0% | silver.classificacao_oficial_referencia.pontos |
| `gols_pro_oficial` | int | Gols pró oficiais (inclui gols contra do adversário) | >= gols_pro | [28 ; 78] | 0.0% | silver.classificacao_oficial_referencia.gols_pro |
| `gols_contra_oficial` | int | Gols sofridos oficiais | >= gols_contra | [27 ; 75] | 0.0% | silver.classificacao_oficial_referencia.gols_contra |
| `gols_contra_a_favor_nao_creditados` | bigint | Gols contra marcados pelo adversário a favor do clube (não creditados na StatsBomb) | inteiro >= 0 | [0 ; 3] | 0.0% | gols_pro_oficial - gols_pro |

## `gold.mart_jogador_temporada`

Mart: jogador x temporada com totais e métricas per-90. Grão: 1 linha por jogador.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `player_id` | bigint | Identificador StatsBomb do jogador | inteiro; 737 valores | [2949 ; 5.311e+05] | 0.0% | fato_jogador_partida.player_id |
| `nome_jogador` | string | Nome do jogador | texto | 689 valores distintos | 0.0% | dim_jogador |
| `nome_exibicao` | string | Nome sem ambiguidade | texto | 737 valores distintos | 0.0% | dim_jogador |
| `tipo_jogador` | string | Goleiro ou Linha | {Goleiro, Linha} | {Goleiro, Linha} | 0.0% | dim_jogador |
| `time_principal_id` | bigint | Clube principal | FK dim_time | [1183 ; 5695] | 0.0% | dim_jogador |
| `time_principal` | string | Nome curto do clube principal | texto | 20 valores distintos | 0.0% | dim_jogador |
| `qtd_times` | bigint | Clubes na temporada | 1 ou 2 | [1 ; 2] | 0.0% | dim_jogador |
| `partidas` | bigint | Partidas disputadas | 1 a 38 | [1 ; 38] | 0.0% | COUNT DISTINCT match_id |
| `minutos` | double | Minutos na temporada | >= 0 | [5.7 ; 3817] | 0.0% | SUM(minutos) |
| `minutos_por_partida` | double | Média de minutos por partida | 0 a 130 | [5.7 ; 104.9] | 0.0% | minutos / partidas |
| `elegivel_analise` | boolean | Jogador de linha com >= 900 minutos (amostra estável para per-90) | true/false | {False, True} | 0.0% | regra de negócio |
| `gols` | int | Gols na temporada | >= 0 | [0 ; 21] | 0.0% | SUM(gols) |
| `gols_sem_penalti` | int | Gols sem pênalti | >= 0 | [0 ; 20] | 0.0% | SUM |
| `assistencias` | int | Assistências | >= 0 | [0 ; 14] | 0.0% | SUM |
| `xg_sem_penalti` | double | xG sem pênalti | >= 0 | [0 ; 14.84] | 0.0% | SUM |
| `xa` | double | xA | >= 0 | [0 ; 8.844] | 0.0% | SUM |
| `gols_menos_xg` | double | Gols sem pênalti - xG sem pênalti (>0 = finalizou acima do esperado) | real | [-3.711 ; 8.803] | 0.0% | derivado |
| `finalizacoes_sem_penalti` | int | Finalizações sem pênalti | >= 0 | [0 ; 98] | 0.0% | SUM |
| `pct_finalizacoes_no_alvo` | double | % de finalizações no alvo | 0 a 1; NULL se 0 finalizações | [0 ; 1] | 16.3% | no_alvo / finalizações |
| `pct_passes_certos` | double | % de passes certos | 0 a 1 | [0.3333 ; 1] | 0.1% | passes_certos / passes |
| `pct_duelos_aereos_vencidos` | double | % de duelos aéreos vencidos | 0 a 1; NULL se 0 duelos | [0 ; 1] | 11.7% | vencidos / disputados |
| `gols_sem_penalti_p90` | double | Gols marcados excluindo pênaltis por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 2.79] | 0.0% | SUM(fato_jogador_partida.gols_sem_penalti) / SUM(minutos) * 90 |
| `xg_sem_penalti_p90` | double | Gols esperados (xG StatsBomb) das finalizações sem pênalti; NULL = não finalizou por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 1.094] | 0.0% | SUM(fato_jogador_partida.xg_sem_penalti) / SUM(minutos) * 90 |
| `xa_p90` | double | Assistências esperadas: soma do xG das finalizações originadas de passes do jogador por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 1.422] | 0.0% | SUM(fato_jogador_partida.xa) / SUM(minutos) * 90 |
| `assistencias_p90` | double | Assistências para gol por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 3.511] | 0.0% | SUM(fato_jogador_partida.assistencias) / SUM(minutos) * 90 |
| `finalizacoes_sem_penalti_p90` | double | Finalizações excluindo pênaltis por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 17.01] | 0.0% | SUM(fato_jogador_partida.finalizacoes_sem_penalti) / SUM(minutos) * 90 |
| `passes_decisivos_p90` | double | Passes que resultaram em finalização (key passes) por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 7.059] | 0.0% | SUM(fato_jogador_partida.passes_decisivos) / SUM(minutos) * 90 |
| `passes_terco_final_p90` | double | Passes em jogo aberto no terço final por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 26.55] | 0.0% | SUM(fato_jogador_partida.passes_terco_final) / SUM(minutos) * 90 |
| `passes_para_area_p90` | double | Passes completados para dentro da área por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 10.53] | 0.0% | SUM(fato_jogador_partida.passes_para_area) / SUM(minutos) * 90 |
| `progressoes_profundas_p90` | double | Passes/conduções que chegam ao terço final (deep progressions) por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 12.64] | 0.0% | SUM(fato_jogador_partida.progressoes_profundas) / SUM(minutos) * 90 |
| `dribles_certos_p90` | double | Dribles bem-sucedidos por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 14.12] | 0.0% | SUM(fato_jogador_partida.dribles_certos) / SUM(minutos) * 90 |
| `toques_na_area_p90` | double | Toques na bola dentro da área adversária por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 25.51] | 0.0% | SUM(fato_jogador_partida.toques_na_area) / SUM(minutos) * 90 |
| `desarmes_p90` | double | Desarmes por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 21.77] | 0.0% | SUM(fato_jogador_partida.desarmes) / SUM(minutos) * 90 |
| `interceptacoes_p90` | double | Interceptações por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 8.948] | 0.0% | SUM(fato_jogador_partida.interceptacoes) / SUM(minutos) * 90 |
| `recuperacoes_p90` | double | Recuperações de bola por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 22.37] | 0.0% | SUM(fato_jogador_partida.recuperacoes) / SUM(minutos) * 90 |
| `pressoes_p90` | double | Pressões sobre o portador da bola por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 77.51] | 0.0% | SUM(fato_jogador_partida.pressoes) / SUM(minutos) * 90 |
| `contrapressoes_p90` | double | Pressões nos 5 s após perda da posse (counterpressures) por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 17.01] | 0.0% | SUM(fato_jogador_partida.contrapressoes) / SUM(minutos) * 90 |
| `duelos_aereos_vencidos_p90` | double | Duelos aéreos vencidos por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 11.65] | 0.0% | SUM(fato_jogador_partida.duelos_aereos_vencidos) / SUM(minutos) * 90 |
| `cortes_p90` | double | Cortes/afastamentos (clearances) por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 10.95] | 0.0% | SUM(fato_jogador_partida.cortes) / SUM(minutos) * 90 |
| `xg_chain_p90` | double | xG das posses em que o jogador participou por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 1.919] | 0.0% | SUM(fato_jogador_partida.xg_chain) / SUM(minutos) * 90 |
| `xg_buildup_p90` | double | xG Chain excluindo o chute e o passe para o chute por 90 minutos | >= 0 (OBV pode ser negativo) | [0 ; 1.514] | 0.0% | SUM(fato_jogador_partida.xg_buildup) / SUM(minutos) * 90 |
| `obv_total_p90` | double | On-Ball Value total: variação da probabilidade de gol causada pelas ações com bola por 90 minutos | >= 0 (OBV pode ser negativo) | [-1.983 ; 1.433] | 0.0% | SUM(fato_jogador_partida.obv_total) / SUM(minutos) * 90 |
| `obv_passe_p90` | double | OBV de passes por 90 minutos | >= 0 (OBV pode ser negativo) | [-0.256 ; 0.7566] | 0.0% | SUM(fato_jogador_partida.obv_passe) / SUM(minutos) * 90 |
| `obv_conducao_p90` | double | OBV de dribles e conduções por 90 minutos | >= 0 (OBV pode ser negativo) | [-0.3532 ; 1.408] | 0.0% | SUM(fato_jogador_partida.obv_conducao) / SUM(minutos) * 90 |
| `obv_defesa_p90` | double | OBV de ações defensivas por 90 minutos | >= 0 (OBV pode ser negativo) | [-2.149 ; 0.3214] | 0.0% | SUM(fato_jogador_partida.obv_defesa) / SUM(minutos) * 90 |

## `gold.feature_similaridade_jogador`

Feature store: 28 métricas per-90 padronizadas por jogador elegível (linha, >= 900 min). Insumo do modelo de similaridade.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `player_id` | bigint | Identificador StatsBomb do jogador | inteiro; 737 valores | [2949 ; 4.738e+05] | 0.0% | mart_jogador_temporada |
| `nome_exibicao` | string | Nome sem ambiguidade | texto | 353 valores distintos | 0.0% | dim_jogador |
| `time_principal` | string | Clube principal | texto | 20 valores distintos | 0.0% | dim_jogador |
| `minutos` | double | Minutos na temporada | >= 900 | [902.7 ; 3663] | 0.0% | mart_jogador_temporada |
| `z_np_shots_p90` | double | Z-score de np_shots_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.346 ; 2.953] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_np_goals_p90` | double | Z-score de np_goals_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-0.8104 ; 5.817] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_key_passes_p90` | double | Z-score de key_passes_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.405 ; 3.806] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_assists_p90` | double | Z-score de assists_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-0.8274 ; 4.663] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_through_balls_p90` | double | Z-score de through_balls_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-0.8491 ; 5.327] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_passes_into_box_p90` | double | Z-score de passes_into_box_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.164 ; 4.781] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_touches_inside_box_p90` | double | Z-score de touches_inside_box_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.303 ; 3.43] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_tackles_p90` | double | Z-score de tackles_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.016 ; 3.625] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_interceptions_p90` | double | Z-score de interceptions_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.735 ; 3.568] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_dribbles_p90` | double | Z-score de dribbles_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.172 ; 3.912] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_fouls_p90` | double | Z-score de fouls_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.839 ; 4.933] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_dispossessions_p90` | double | Z-score de dispossessions_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.399 ; 4.004] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_successful_long_balls_p90` | double | Z-score de successful_long_balls_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.658 ; 3.632] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_clearances_p90` | double | Z-score de clearances_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.204 ; 2.858] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_successful_aerials_p90` | double | Z-score de successful_aerials_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.434 ; 4.716] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_successful_passes_p90` | double | Z-score de successful_passes_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.883 ; 3.689] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_forward_passes_p90` | double | Z-score de forward_passes_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.752 ; 3.445] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_op_f3_passes_p90` | double | Z-score de op_f3_passes_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.819 ; 3.469] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_successful_crosses_p90` | double | Z-score de successful_crosses_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-1.027 ; 3.676] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_pressures_p90` | double | Z-score de pressures_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.159 ; 2.544] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_ball_recoveries_p90` | double | Z-score de ball_recoveries_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.235 ; 2.314] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_deep_progressions_p90` | double | Z-score de deep_progressions_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.072 ; 3.943] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_defensive_actions_p90` | double | Z-score de defensive_actions_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.267 ; 2.887] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_obv_p90` | double | Z-score de obv_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-3.52 ; 3.859] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_obv_pass_p90` | double | Z-score de obv_pass_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.306 ; 3.968] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_obv_defensive_action_p90` | double | Z-score de obv_defensive_action_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-4.325 ; 4.213] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_obv_dribble_carry_p90` | double | Z-score de obv_dribble_carry_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.967 ; 4.344] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `z_touches_p90` | double | Z-score de touches_p90 (per-90) na população elegível | real, média 0 e desvio 1 | [-2.088 ; 3.963] | 0.0% | (x - média) / desvio sobre jogadores elegíveis |
| `vetor_features` | array<double> | Vetor ordenado das 28 features z-score (ordem = colunas z_*) | ARRAY<DOUBLE> de 28 posições | array<double> | 0.0% | array(z_*) |
| `norma_vetor` | double | Norma euclidiana do vetor (pré-calculada para similaridade de cosseno) | > 0 | [2.571 ; 9.844] | 0.0% | sqrt(sum(z^2)) |

## `silver.jogador_partida`

Silver: estatísticas por jogador x partida tipadas e tratadas. Grão: match_id + player_id.

| Coluna | Tipo | Descrição | Domínio esperado | Domínio observado | % nulos | Linhagem |
|---|---|---|---|---|---|---|
| `match_id` | bigint | Identificador da partida | Categoria: Identificação \| Missing: Não se aplica | [3.989e+06 ; 3.989e+06] | 0.0% | bronze.match_id (try_cast) |
| `team_id` | bigint | Identificador da equipe | Categoria: Identificação \| Missing: Não se aplica | [1183 ; 5695] | 0.0% | bronze.team_id (try_cast) |
| `player_id` | bigint | Identificador do atleta | Categoria: Identificação \| Missing: Não se aplica | [2949 ; 5.311e+05] | 0.0% | bronze.player_id (try_cast) |
| `account_id` | bigint | Identificador da conta | Categoria: Identificação \| Missing: Não se aplica | [539 ; 539] | 0.0% | bronze.account_id (try_cast) |
| `team_name` | string | Nome padronizado do clube | 20 clubes | 20 valores distintos | 0.0% | silver.time_de_para via bronze.team_name |
| `team_name_fonte` | string | Nome do clube como na fonte | texto | 20 valores distintos | 0.0% | bronze.team_name |
| `player_name` | string | Nome do atleta | Categoria: Identificação \| Missing: Não se aplica | 689 valores distintos | 0.0% | bronze.player_name (try_cast) |
| `is_goleiro` | boolean | Jogador atuou como goleiro ao menos uma vez (tem métrica obv_gk) | true/false | {False, True} | 0.0% | derivado de player_match_obv_gk |
| `tem_cobertura_360` | boolean | Partida do jogador com cobertura StatsBomb 360 (360_minutes > 0) | true/false | {False, True} | 0.0% | derivado de player_match_360_minutes |
| `player_match_minutes` | double | Todo atleta possui minutos jogados | Categoria: Universal \| Missing: Investigar NA | [0.2833 ; 114] | 0.0% | bronze.player_match_minutes (try_cast) |
| `player_match_np_xg_per_shot` | double | Só existe quando houve finalização | Categoria: Condicional \| Missing: Manter NA | [0.003011 ; 0.95] | 52.9% | bronze.player_match_np_xg_per_shot (try_cast) |
| `player_match_np_xg` | double | Só existe quando houve chute | Categoria: Condicional \| Missing: Manter NA | [0 ; 1.919] | 0.0% | bronze.player_match_np_xg (try_cast) |
| `player_match_np_shots` | int | Contagem de finalizações | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 11] | 0.0% | bronze.player_match_np_shots (try_cast) |
| `player_match_goals` | int | Contagem de gols | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 3] | 0.0% | bronze.player_match_goals (try_cast) |
| `player_match_np_goals` | int | Contagem de gols sem pênaltis | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 3] | 0.0% | bronze.player_match_np_goals (try_cast) |
| `player_match_xa` | double | Depende da criação de chances | Categoria: Condicional \| Missing: Manter NA | [0 ; 1.508] | 0.0% | bronze.player_match_xa (try_cast) |
| `player_match_key_passes` | int | Contagem de passes-chave | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 9] | 0.0% | bronze.player_match_key_passes (try_cast) |
| `player_match_op_key_passes` | int | Passes-chave permitidos ao adversário | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 7] | 0.0% | bronze.player_match_op_key_passes (try_cast) |
| `player_match_assists` | int | Assistências | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 3] | 0.0% | bronze.player_match_assists (try_cast) |
| `player_match_through_balls` | int | Passes em profundidade | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 3] | 0.0% | bronze.player_match_through_balls (try_cast) |
| `player_match_passes_into_box` | int | Passes para a área | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 10] | 0.0% | bronze.player_match_passes_into_box (try_cast) |
| `player_match_op_passes_into_box` | int | Passes do adversário para a área | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 8] | 0.0% | bronze.player_match_op_passes_into_box (try_cast) |
| `player_match_touches_inside_box` | int | Toques na área | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 25] | 0.0% | bronze.player_match_touches_inside_box (try_cast) |
| `player_match_tackles` | int | Desarmes | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 10] | 0.0% | bronze.player_match_tackles (try_cast) |
| `player_match_interceptions` | int | Interceptações | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 8] | 0.0% | bronze.player_match_interceptions (try_cast) |
| `player_match_possession` | double | Participação na posse | Categoria: Universal \| Missing: VERIFICAR TIPO DE DADO | [0.2165 ; 0.7835] | 0.0% | bronze.player_match_possession (try_cast) |
| `player_match_dribbled_past` | int | Dribles sofridos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 8] | 0.0% | bronze.player_match_dribbled_past (try_cast) |
| `player_match_dribbles_faced` | int | Dribles enfrentados | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 12] | 0.0% | bronze.player_match_dribbles_faced (try_cast) |
| `player_match_dribbles` | int | Dribles realizados | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 9] | 0.0% | bronze.player_match_dribbles (try_cast) |
| `player_match_challenge_ratio` | double | Só existe quando houve disputa | Categoria: Condicional \| Missing: Manter NA | [0 ; 1] | 34.3% | bronze.player_match_challenge_ratio (try_cast) |
| `player_match_fouls` | int | Faltas cometidas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 9] | 0.0% | bronze.player_match_fouls (try_cast) |
| `player_match_dispossessions` | int | Perdas de posse | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 10] | 0.0% | bronze.player_match_dispossessions (try_cast) |
| `player_match_long_balls` | int | Lançamentos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 40] | 0.0% | bronze.player_match_long_balls (try_cast) |
| `player_match_successful_long_balls` | int | Lançamentos certos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 20] | 0.0% | bronze.player_match_successful_long_balls (try_cast) |
| `player_match_long_ball_ratio` | double | Depende de lançamentos | Categoria: Condicional \| Missing: Manter NA | [0 ; 1] | 22.0% | bronze.player_match_long_ball_ratio (try_cast) |
| `player_match_shots_blocked` | int | Chutes bloqueados | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 8] | 0.0% | bronze.player_match_shots_blocked (try_cast) |
| `player_match_clearances` | int | Cortes defensivos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 14] | 0.0% | bronze.player_match_clearances (try_cast) |
| `player_match_aerials` | int | Disputas aéreas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 22] | 0.0% | bronze.player_match_aerials (try_cast) |
| `player_match_successful_aerials` | int | Disputas aéreas vencidas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 14] | 0.0% | bronze.player_match_successful_aerials (try_cast) |
| `player_match_aerial_ratio` | double | Só existe quando houve disputa aérea | Categoria: Condicional \| Missing: Manter NA | [0 ; 1] | 32.8% | bronze.player_match_aerial_ratio (try_cast) |
| `player_match_passes` | int | Número de passes | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 144] | 0.0% | bronze.player_match_passes (try_cast) |
| `player_match_successful_passes` | int | Passes certos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 135] | 0.0% | bronze.player_match_successful_passes (try_cast) |
| `player_match_passing_ratio` | double | Razão calculada sobre passes | Categoria: Condicional \| Missing: Manter NA | [0 ; 1] | 0.9% | bronze.player_match_passing_ratio (try_cast) |
| `player_match_op_passes` | int | Passes do adversário relacionados ao atleta | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 144] | 0.0% | bronze.player_match_op_passes (try_cast) |
| `player_match_forward_passes` | int | Passes para frente | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 36] | 0.0% | bronze.player_match_forward_passes (try_cast) |
| `player_match_backward_passes` | int | Passes para trás | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 24] | 0.0% | bronze.player_match_backward_passes (try_cast) |
| `player_match_sideways_passes` | int | Passes laterais | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 123] | 0.0% | bronze.player_match_sideways_passes (try_cast) |
| `player_match_op_f3_passes` | int | Passes adversários no terço final | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 65] | 0.0% | bronze.player_match_op_f3_passes (try_cast) |
| `player_match_op_f3_forward_passes` | int | Passes adversários para frente no terço final | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 19] | 0.0% | bronze.player_match_op_f3_forward_passes (try_cast) |
| `player_match_op_f3_backward_passes` | int | Passes adversários para trás no terço final | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 12] | 0.0% | bronze.player_match_op_f3_backward_passes (try_cast) |
| `player_match_op_f3_sideways_passes` | int | Passes adversários laterais no terço final | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 45] | 0.0% | bronze.player_match_op_f3_sideways_passes (try_cast) |
| `player_match_np_shots_on_target` | int | Finalizações no alvo (sem pênaltis) | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 5] | 0.0% | bronze.player_match_np_shots_on_target (try_cast) |
| `player_match_crosses` | int | Cruzamentos realizados | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 12] | 0.0% | bronze.player_match_crosses (try_cast) |
| `player_match_successful_crosses` | int | Cruzamentos certos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 6] | 0.0% | bronze.player_match_successful_crosses (try_cast) |
| `player_match_crossing_ratio` | double | Só existe quando houve cruzamentos | Categoria: Condicional \| Missing: Manter NA | [0 ; 1] | 61.8% | bronze.player_match_crossing_ratio (try_cast) |
| `player_match_penalties_won` | int | Pênaltis sofridos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 1] | 0.0% | bronze.player_match_penalties_won (try_cast) |
| `player_match_passes_inside_box` | int | Passes dentro da área | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 5] | 0.0% | bronze.player_match_passes_inside_box (try_cast) |
| `player_match_op_xa` | double | xA do adversário depende da criação de chances | Categoria: Condicional \| Missing: Manter NA | [0 ; 1.432] | 0.0% | bronze.player_match_op_xa (try_cast) |
| `player_match_op_assists` | int | Assistências do adversário | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 3] | 0.0% | bronze.player_match_op_assists (try_cast) |
| `player_match_pressured_long_balls` | int | Lançamentos sob pressão | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 18] | 0.0% | bronze.player_match_pressured_long_balls (try_cast) |
| `player_match_unpressured_long_balls` | int | Lançamentos sem pressão | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 36] | 0.0% | bronze.player_match_unpressured_long_balls (try_cast) |
| `player_match_aggressive_actions` | int | Ações defensivas agressivas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 43] | 0.0% | bronze.player_match_aggressive_actions (try_cast) |
| `player_match_turnovers` | int | Perdas de posse | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 13] | 0.0% | bronze.player_match_turnovers (try_cast) |
| `player_match_crosses_into_box` | int | Cruzamentos para a área | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 6] | 0.0% | bronze.player_match_crosses_into_box (try_cast) |
| `player_match_sp_xa` | double | xA em bolas paradas | Categoria: Condicional \| Missing: Manter NA | [0 ; 0.546] | 0.0% | bronze.player_match_sp_xa (try_cast) |
| `player_match_op_shots` | int | Finalizações adversárias | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 7] | 0.0% | bronze.player_match_op_shots (try_cast) |
| `player_match_touches` | int | Toques na bola | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 282] | 0.0% | bronze.player_match_touches (try_cast) |
| `player_match_pressure_regains` | int | Recuperações após pressão | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 16] | 0.0% | bronze.player_match_pressure_regains (try_cast) |
| `player_match_box_cross_ratio` | double | Razão de cruzamentos para a área | Categoria: Condicional \| Missing: Manter NA | [0 ; 1] | 65.1% | bronze.player_match_box_cross_ratio (try_cast) |
| `player_match_deep_progressions` | int | Progressões profundas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 26] | 0.0% | bronze.player_match_deep_progressions (try_cast) |
| `player_match_shot_touch_ratio` | double | Depende de finalizações | Categoria: Condicional \| Missing: Manter NA | [0 ; 0.6667] | 0.4% | bronze.player_match_shot_touch_ratio (try_cast) |
| `player_match_fouls_won` | int | Faltas sofridas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 11] | 0.0% | bronze.player_match_fouls_won (try_cast) |
| `player_match_xgchain` | double | Participação em cadeias ofensivas | Categoria: Condicional \| Missing: Manter NA | [0 ; 3.278] | 0.3% | bronze.player_match_xgchain (try_cast) |
| `player_match_op_xgchain` | double | Cadeias ofensivas adversárias | Categoria: Condicional \| Missing: Manter NA | [0 ; 2.728] | 0.3% | bronze.player_match_op_xgchain (try_cast) |
| `player_match_xgbuildup` | double | Participação na construção ofensiva | Categoria: Condicional \| Missing: Manter NA | [0 ; 2.445] | 0.3% | bronze.player_match_xgbuildup (try_cast) |
| `player_match_op_xgbuildup` | double | Construção ofensiva adversária | Categoria: Condicional \| Missing: Manter NA | [0 ; 2.425] | 0.4% | bronze.player_match_op_xgbuildup (try_cast) |
| `player_match_xgchain_per_possession` | double | Média por posse | Categoria: Condicional \| Missing: Manter NA | [0 ; 0.891] | 0.3% | bronze.player_match_xgchain_per_possession (try_cast) |
| `player_match_op_xgchain_per_possession` | double | Média adversária por posse | Categoria: Condicional \| Missing: Manter NA | [0 ; 0.891] | 0.3% | bronze.player_match_op_xgchain_per_possession (try_cast) |
| `player_match_xgbuildup_per_possession` | double | Média por posse | Categoria: Condicional \| Missing: Manter NA | [0 ; 0.2768] | 0.3% | bronze.player_match_xgbuildup_per_possession (try_cast) |
| `player_match_op_xgbuildup_per_possession` | double | Média adversária por posse | Categoria: Condicional \| Missing: Manter NA | [0 ; 0.2768] | 0.4% | bronze.player_match_op_xgbuildup_per_possession (try_cast) |
| `player_match_pressures` | int | Pressões realizadas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 51] | 0.0% | bronze.player_match_pressures (try_cast) |
| `player_match_pressure_duration_total` | double | Só existe quando houve pressão | Categoria: Condicional \| Missing: Manter NA | [0.03984 ; 52.79] | 7.8% | bronze.player_match_pressure_duration_total (try_cast) |
| `player_match_pressure_duration_avg` | double | Média da duração das pressões | Categoria: Condicional \| Missing: Manter NA | [0.03984 ; 5] | 7.8% | bronze.player_match_pressure_duration_avg (try_cast) |
| `player_match_pressured_action_fails` | int | Falhas em ações sob pressão | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 11] | 0.0% | bronze.player_match_pressured_action_fails (try_cast) |
| `player_match_counterpressures` | int | Contra-pressões realizadas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 15] | 0.0% | bronze.player_match_counterpressures (try_cast) |
| `player_match_counterpressure_duration_total` | double | Só existe quando houve contra-pressão | Categoria: Condicional \| Missing: Manter NA | [0.01933 ; 16.75] | 26.1% | bronze.player_match_counterpressure_duration_total (try_cast) |
| `player_match_counterpressure_duration_avg` | double | Média calculada sobre contra-pressões | Categoria: Condicional \| Missing: Manter NA | [0.01933 ; 5] | 26.1% | bronze.player_match_counterpressure_duration_avg (try_cast) |
| `player_match_counterpressured_action_fails` | int | Falhas em ações sob contra-pressão | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 5] | 0.0% | bronze.player_match_counterpressured_action_fails (try_cast) |
| `player_match_obv` | double | Valor agregado total (OBV) | Categoria: Universal \| Missing: Preencher com 0 | [-2.858 ; 2.578] | 0.0% | bronze.player_match_obv (try_cast) |
| `player_match_obv_pass` | double | Valor agregado por passes | Categoria: Universal \| Missing: Preencher com 0 | [-0.4985 ; 1.168] | 0.0% | bronze.player_match_obv_pass (try_cast) |
| `player_match_obv_shot` | double | Só existe quando houve finalização | Categoria: Condicional \| Missing: Manter NA | [-0.9753 ; 1.435] | 52.8% | bronze.player_match_obv_shot (try_cast) |
| `player_match_obv_defensive_action` | double | Valor agregado por ações defensivas | Categoria: Universal \| Missing: Preencher com 0 | [-1.415 ; 1.161] | 0.0% | bronze.player_match_obv_defensive_action (try_cast) |
| `player_match_obv_dribble_carry` | double | Valor agregado por conduções/dribles | Categoria: Universal \| Missing: Preencher com 0 | [-0.6812 ; 1.118] | 0.0% | bronze.player_match_obv_dribble_carry (try_cast) |
| `player_match_obv_gk` | double | Métrica exclusiva de goleiros | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [-2.878 ; 2.505] | 93.7% | bronze.player_match_obv_gk (try_cast) |
| `player_match_deep_completions` | int | Passes completados em zonas profundas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 6] | 0.0% | bronze.player_match_deep_completions (try_cast) |
| `player_match_ball_recoveries` | int | Recuperações de bola | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 30] | 0.0% | bronze.player_match_ball_recoveries (try_cast) |
| `player_match_np_psxg` | double | PSxG depende de finalizações | Categoria: Condicional \| Missing: Manter NA | [0 ; 2.587] | 0.0% | bronze.player_match_np_psxg (try_cast) |
| `player_match_penalties_faced` | double | Somente goleiros enfrentam pênaltis | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0 ; 2] | 0.0% | bronze.player_match_penalties_faced (try_cast) |
| `player_match_penalties_conceded` | int | Pênaltis cometidos | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 2] | 0.0% | bronze.player_match_penalties_conceded (try_cast) |
| `player_match_fhalf_ball_recoveries` | int | Recuperações no primeiro tempo | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 19] | 0.0% | bronze.player_match_fhalf_ball_recoveries (try_cast) |
| `player_match_average_space_received_in` | double | Média calculada apenas quando recebe a bola | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [0.2262 ; 27.23] | 2.3% | bronze.player_match_average_space_received_in (try_cast) |
| `player_match_average_fhalf_space_received_in` | double | Média no primeiro tempo | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [0.2231 ; 26.8] | 11.5% | bronze.player_match_average_fhalf_space_received_in (try_cast) |
| `player_match_average_f3_space_received_in` | double | Média no último terço | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [0.22 ; 26.8] | 23.5% | bronze.player_match_average_f3_space_received_in (try_cast) |
| `player_match_ball_receipts_in_space_10` | double | Recebimentos em espaço ≥10 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 76] | 0.0% | bronze.player_match_ball_receipts_in_space_10 (try_cast) |
| `player_match_ball_receipts_in_space_2` | double | Recebimentos em espaço ≥2 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 119] | 0.0% | bronze.player_match_ball_receipts_in_space_2 (try_cast) |
| `player_match_ball_receipts_in_space_5` | double | Recebimentos em espaço ≥5 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 99] | 0.0% | bronze.player_match_ball_receipts_in_space_5 (try_cast) |
| `player_match_fhalf_ball_receipts_in_space_10` | double | Recebimentos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 35] | 0.0% | bronze.player_match_fhalf_ball_receipts_in_space_10 (try_cast) |
| `player_match_fhalf_ball_receipts_in_space_2` | double | Recebimentos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 102] | 0.0% | bronze.player_match_fhalf_ball_receipts_in_space_2 (try_cast) |
| `player_match_fhalf_ball_receipts_in_space_5` | double | Recebimentos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 85] | 0.0% | bronze.player_match_fhalf_ball_receipts_in_space_5 (try_cast) |
| `player_match_f3_ball_receipts_in_space_10` | double | Recebimentos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 21] | 0.0% | bronze.player_match_f3_ball_receipts_in_space_10 (try_cast) |
| `player_match_f3_ball_receipts_in_space_2` | double | Recebimentos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 43] | 0.0% | bronze.player_match_f3_ball_receipts_in_space_2 (try_cast) |
| `player_match_f3_ball_receipts_in_space_5` | double | Recebimentos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 37] | 0.0% | bronze.player_match_f3_ball_receipts_in_space_5 (try_cast) |
| `player_match_lbp` | double | Line Breaking Passes executados | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 33] | 0.0% | bronze.player_match_lbp (try_cast) |
| `player_match_lbp_completed` | double | Line Breaking Passes completos | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 21] | 0.0% | bronze.player_match_lbp_completed (try_cast) |
| `player_match_fhalf_lbp_completed` | double | LBP completos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 18] | 0.0% | bronze.player_match_fhalf_lbp_completed (try_cast) |
| `player_match_f3_lbp_completed` | double | LBP completos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 12] | 0.0% | bronze.player_match_f3_lbp_completed (try_cast) |
| `player_match_fhalf_lbp` | double | LBP no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 23] | 0.0% | bronze.player_match_fhalf_lbp (try_cast) |
| `player_match_f3_lbp` | double | LBP no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 17] | 0.0% | bronze.player_match_f3_lbp (try_cast) |
| `player_match_obv_lbp` | double | Valor agregado apenas quando há LBP | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [-0.2271 ; 0.9226] | 12.7% | bronze.player_match_obv_lbp (try_cast) |
| `player_match_fhalf_obv_lbp` | double | Valor agregado de LBP no primeiro tempo | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [-0.2271 ; 0.9226] | 30.0% | bronze.player_match_fhalf_obv_lbp (try_cast) |
| `player_match_f3_obv_lbp` | double | Valor agregado de LBP no terço final | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [-0.2285 ; 0.9197] | 48.9% | bronze.player_match_f3_obv_lbp (try_cast) |
| `player_match_lbp_received` | double | LBPs recebidos | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 23] | 0.0% | bronze.player_match_lbp_received (try_cast) |
| `player_match_fhalf_lbp_received` | double | LBPs recebidos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 21] | 0.0% | bronze.player_match_fhalf_lbp_received (try_cast) |
| `player_match_f3_lbp_received` | double | LBPs recebidos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 13] | 0.0% | bronze.player_match_f3_lbp_received (try_cast) |
| `player_match_average_lbp_to_space_distance` | double | Média calculada apenas quando houve LBP | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [2 ; 31.23] | 31.8% | bronze.player_match_average_lbp_to_space_distance (try_cast) |
| `player_match_fhalf_average_lbp_to_space_distance` | double | Média no primeiro tempo | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [2 ; 26.33] | 53.0% | bronze.player_match_fhalf_average_lbp_to_space_distance (try_cast) |
| `player_match_f3_average_lbp_to_space_distance` | double | Média no terço final | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [2 ; 23.06] | 74.6% | bronze.player_match_f3_average_lbp_to_space_distance (try_cast) |
| `player_match_lbp_to_space_10_received` | double | Recebimentos de LBP em espaço ≥10 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 4] | 0.0% | bronze.player_match_lbp_to_space_10_received (try_cast) |
| `player_match_fhalf_lbp_to_space_10_received` | double | Recebimentos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 4] | 0.0% | bronze.player_match_fhalf_lbp_to_space_10_received (try_cast) |
| `player_match_f3_lbp_to_space_10_received` | double | Recebimentos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 4] | 0.0% | bronze.player_match_f3_lbp_to_space_10_received (try_cast) |
| `player_match_lbp_to_space_2_received` | double | Recebimentos em espaço ≥2 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 18] | 0.0% | bronze.player_match_lbp_to_space_2_received (try_cast) |
| `player_match_fhalf_lbp_to_space_2_received` | double | Recebimentos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 16] | 0.0% | bronze.player_match_fhalf_lbp_to_space_2_received (try_cast) |
| `player_match_f3_lbp_to_space_2_received` | double | Recebimentos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 10] | 0.0% | bronze.player_match_f3_lbp_to_space_2_received (try_cast) |
| `player_match_lbp_to_space_5_received` | double | Recebimentos em espaço ≥5 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 9] | 0.0% | bronze.player_match_lbp_to_space_5_received (try_cast) |
| `player_match_fhalf_lbp_to_space_5_received` | double | Recebimentos no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 7] | 0.0% | bronze.player_match_fhalf_lbp_to_space_5_received (try_cast) |
| `player_match_f3_lbp_to_space_5_received` | double | Recebimentos no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 6] | 0.0% | bronze.player_match_f3_lbp_to_space_5_received (try_cast) |
| `player_match_average_lbp_to_space_received_distance` | double | Média da distância dos LBPs recebidos | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [0 ; 26.8] | 33.1% | bronze.player_match_average_lbp_to_space_received_distance (try_cast) |
| `player_match_fhalf_average_lbp_to_space_received_distance` | double | Média no primeiro tempo | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [0 ; 26.8] | 40.0% | bronze.player_match_fhalf_average_lbp_to_space_received_distance (try_cast) |
| `player_match_f3_average_lbp_to_space_received_distance` | double | Média no terço final | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [0 ; 26.8] | 50.8% | bronze.player_match_f3_average_lbp_to_space_received_distance (try_cast) |
| `player_match_lbp_to_space_10` | double | LBPs executados para espaço ≥10 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 5] | 0.0% | bronze.player_match_lbp_to_space_10 (try_cast) |
| `player_match_fhalf_lbp_to_space_10` | double | LBPs no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 4] | 0.0% | bronze.player_match_fhalf_lbp_to_space_10 (try_cast) |
| `player_match_f3_lbp_to_space_10` | double | LBPs no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 2] | 0.0% | bronze.player_match_f3_lbp_to_space_10 (try_cast) |
| `player_match_lbp_to_space_2` | double | LBPs executados para espaço ≥2 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 17] | 0.0% | bronze.player_match_lbp_to_space_2 (try_cast) |
| `player_match_fhalf_lbp_to_space_2` | double | LBPs no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 11] | 0.0% | bronze.player_match_fhalf_lbp_to_space_2 (try_cast) |
| `player_match_f3_lbp_to_space_2` | double | LBPs no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 8] | 0.0% | bronze.player_match_f3_lbp_to_space_2 (try_cast) |
| `player_match_lbp_to_space_5` | double | LBPs executados para espaço ≥5 m | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 10] | 0.0% | bronze.player_match_lbp_to_space_5 (try_cast) |
| `player_match_fhalf_lbp_to_space_5` | double | LBPs no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 8] | 0.0% | bronze.player_match_fhalf_lbp_to_space_5 (try_cast) |
| `player_match_f3_lbp_to_space_5` | double | LBPs no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 3] | 0.0% | bronze.player_match_f3_lbp_to_space_5 (try_cast) |
| `player_match_passes_360` | double | Passes registrados pelo StatsBomb 360 | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 141] | 0.0% | bronze.player_match_passes_360 (try_cast) |
| `player_match_obv_passes_360` | double | Valor agregado dos passes 360 | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [-0.5149 ; 1.05] | 1.7% | bronze.player_match_obv_passes_360 (try_cast) |
| `player_match_fhalf_passes_360` | double | Passes 360 no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 106] | 0.0% | bronze.player_match_fhalf_passes_360 (try_cast) |
| `player_match_fhalf_obv_passes_360` | double | Valor agregado dos passes 360 no primeiro tempo | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [-0.5038 ; 1.056] | 10.6% | bronze.player_match_fhalf_obv_passes_360 (try_cast) |
| `player_match_f3_passes_360` | double | Passes 360 no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 49] | 0.0% | bronze.player_match_f3_passes_360 (try_cast) |
| `player_match_f3_obv_passes_360` | double | Valor agregado dos passes 360 no terço final | Categoria: Condicional \| Missing: VERIFICAR COBERTURA 360 | [-0.4729 ; 1.062] | 22.1% | bronze.player_match_f3_obv_passes_360 (try_cast) |
| `player_match_ball_receipts_360` | double | Recebimentos registrados pelo 360 | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 123] | 0.0% | bronze.player_match_ball_receipts_360 (try_cast) |
| `player_match_fhalf_ball_receipts_360` | double | Recebimentos 360 no primeiro tempo | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 104] | 0.0% | bronze.player_match_fhalf_ball_receipts_360 (try_cast) |
| `player_match_f3_ball_receipts_360` | double | Recebimentos 360 no terço final | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 44] | 0.0% | bronze.player_match_f3_ball_receipts_360 (try_cast) |
| `player_match_360_minutes` | double | Minutos cobertos pelo sistema 360 | Categoria: Universal \| Missing: VERIFICAR COBERTURA 360 | [0 ; 114] | 0.0% | bronze.player_match_360_minutes (try_cast) |
| `player_match_defensive_actions` | int | Total de ações defensivas | Categoria: Universal \| Missing: Preencher com 0 | [0 ; 61] | 0.0% | bronze.player_match_defensive_actions (try_cast) |
| `player_match_ccaa` | double | Métrica avançada calculada a partir de eventos ofensivos | Categoria: Condicional \| Missing: Manter NA | [-0.628 ; 0.3643] | 2.4% | bronze.player_match_ccaa (try_cast) |
| `player_match_claim_success` | double | Exclusiva de goleiros | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [1 ; 1] | 96.2% | bronze.player_match_claim_success (try_cast) |
| `player_match_da_aggressive_distance` | double | Média de distância em ações defensivas agressivas | Categoria: Condicional \| Missing: Manter NA | [2.535 ; 106.1] | 2.1% | bronze.player_match_da_aggressive_distance (try_cast) |
| `player_match_goals_conceded` | double | Apenas goleiros sofrem gols diretamente | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0 ; 8] | 0.0% | bronze.player_match_goals_conceded (try_cast) |
| `player_match_gsaa` | double | Goals Saved Above Average é exclusivo de goleiros | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [-3.025 ; 3.039] | 0.0% | bronze.player_match_gsaa (try_cast) |
| `player_match_gk_positioning_error` | double | Erro de posicionamento do goleiro | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0.2016 ; 6.8] | 93.6% | bronze.player_match_gk_positioning_error (try_cast) |
| `player_match_positive_outcome_score` | double | Métrica de desempenho específica do goleiro | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0.00346 ; 1] | 13.7% | bronze.player_match_positive_outcome_score (try_cast) |
| `player_match_npot_psxg_faced` | double | PSxG enfrentado pelo goleiro | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0 ; 5.042] | 0.0% | bronze.player_match_npot_psxg_faced (try_cast) |
| `player_match_save_ratio` | double | Taxa de defesas do goleiro | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0 ; 1] | 0.0% | bronze.player_match_save_ratio (try_cast) |
| `player_match_gsaa_ratio` | double | Razão do GSAA, exclusiva de goleiros | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [-0.9966 ; 0.7149] | 93.8% | bronze.player_match_gsaa_ratio (try_cast) |
| `player_match_npot_shots_faced` | double | Finalizações enfrentadas pelo goleiro | Categoria: Específica de posição \| Missing: Manter NA + criar flag de posição | [0 ; 13] | 0.0% | bronze.player_match_npot_shots_faced (try_cast) |
| `_arquivo_origem` | string | Caminho do arquivo no volume | texto | {file:/mnt/user-data/uploads/files_yuri_mvp_2026/estatisticas_jogadores_partida_brasileirao2025.csv} | 0.0% | bronze |
| `_data_ingestao` | timestamp | Timestamp da ingestão Bronze | timestamp | timestamp | 0.0% | bronze |
| `_id_carga` | string | Identificador da execução de ingestão Bronze que originou o registro | texto yyyymmddThhmmss-hash | {20260926T024030-679f2d7d} | 0.0% | bronze |
| `_data_processamento` | timestamp | Timestamp do processamento Silver | timestamp | timestamp | 0.0% | silver |
