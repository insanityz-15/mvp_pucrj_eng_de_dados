# Resultados de qualidade de dados

> Exportado de `governanca.dq_resultados` (notebook `05_qualidade_dados`). Colunas de completude sem nulos (117) foram omitidas.

| Camada | Tabela | Coluna | Dimensão | Regra | Avaliados | Falhas | % | Status | Tratamento |
|---|---|---|---|---|---|---|---|---|---|
| gold | mart_classificacao | gols_pro | Acurácia | gols pró derivados = gols pró oficiais (CBF) | 20 | 16 | 80.0% | ALERTA | Diferença = gols contra não creditados pela fonte; mart expõe colunas *_oficial |
| gold | mart_classificacao | pontos | Acurácia | pontos derivados = pontos oficiais (CBF) | 20 | 11 | 55.0% | ALERTA | Análises de pontos usam pontos_oficiais |
| silver | jogador_partida | player_match_obv | Acurácia | valores negativos em métricas OBV/GSAA (esperado: métrica de valor pode ser negativa) | 11,998 | 3,800 | 31.7% | ALERTA | Nenhum — OBV negativo é semanticamente válido (ação que reduziu a chance de gol) |
| silver | jogador_partida_quarentena | nan | Acurácia | linhas reprovadas nas regras de negócio da Silver (T6) | 11,998 | 0 | 0.0% | OK | Enviadas para silver.jogador_partida_quarentena |
| silver | jogador_partida | nan | Acurácia | reconciliação bronze = silver + quarentena - duplicatas | 11,998 | 0 | 0.0% | OK |  |
| silver | jogador_partida | player_match_minutes | Acurácia | minutos entre 0 e 130 | 11,998 | 0 | 0.0% | OK |  |
| gold | fato_time_partida | gols_pro | Acurácia | gols do time = gols sofridos registrados pelo goleiro adversário | 760 | 0 | 0.0% | OK |  |
| gold | fato_jogador_partida | gols | Acurácia | reconciliação de gols: soma bronze = soma gold | 1 | 0 | 0.0% | OK |  |
| gold | mart_classificacao | nan | Acurácia | cada clube com 38 jogos | 20 | 0 | 0.0% | OK |  |
| gold | mart_classificacao | nan | Acurácia | soma de vitórias = soma de derrotas | 1 | 0 | 0.0% | OK |  |
| gold | mart_classificacao | gols_contra | Acurácia | gols sofridos derivados <= gols sofridos oficiais | 20 | 0 | 0.0% | OK |  |
| gold | fato_time_partida | nan | Acurácia | partidas sem goleiro registrado | 760 | 0 | 0.0% | OK |  |
| bronze | statsbomb_jogador_partida_raw | player_match_claim_success | Completude | percentual de nulos | 11,998 | 11,544 | 96.2% | ALERTA | Mantido NULL + flag is_goleiro (métrica exclusiva de goleiro) |
| bronze | statsbomb_jogador_partida_raw | player_match_gsaa_ratio | Completude | percentual de nulos | 11,998 | 11,252 | 93.8% | ALERTA | Mantido NULL + flag is_goleiro (métrica exclusiva de goleiro) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_gk | Completude | percentual de nulos | 11,998 | 11,238 | 93.7% | ALERTA | Mantido NULL + flag is_goleiro (métrica exclusiva de goleiro) |
| bronze | statsbomb_jogador_partida_raw | player_match_gk_positioning_error | Completude | percentual de nulos | 11,998 | 11,228 | 93.6% | ALERTA | Mantido NULL + flag is_goleiro (métrica exclusiva de goleiro) |
| bronze | statsbomb_jogador_partida_raw | player_match_f3_average_lbp_to_space_distance | Completude | percentual de nulos | 11,998 | 8,946 | 74.6% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_box_cross_ratio | Completude | percentual de nulos | 11,998 | 7,816 | 65.1% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_crossing_ratio | Completude | percentual de nulos | 11,998 | 7,413 | 61.8% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_fhalf_average_lbp_to_space_distance | Completude | percentual de nulos | 11,998 | 6,361 | 53.0% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_np_xg_per_shot | Completude | percentual de nulos | 11,998 | 6,343 | 52.9% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_shot | Completude | percentual de nulos | 11,998 | 6,334 | 52.8% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_f3_average_lbp_to_space_received_distance | Completude | percentual de nulos | 11,998 | 6,101 | 50.9% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_f3_obv_lbp | Completude | percentual de nulos | 11,998 | 5,870 | 48.9% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_fhalf_average_lbp_to_space_received_distance | Completude | percentual de nulos | 11,998 | 4,794 | 40.0% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_challenge_ratio | Completude | percentual de nulos | 11,998 | 4,112 | 34.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_average_lbp_to_space_received_distance | Completude | percentual de nulos | 11,998 | 3,967 | 33.1% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_aerial_ratio | Completude | percentual de nulos | 11,998 | 3,933 | 32.8% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_average_lbp_to_space_distance | Completude | percentual de nulos | 11,998 | 3,815 | 31.8% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_fhalf_obv_lbp | Completude | percentual de nulos | 11,998 | 3,601 | 30.0% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_counterpressure_duration_total | Completude | percentual de nulos | 11,998 | 3,129 | 26.1% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_counterpressure_duration_avg | Completude | percentual de nulos | 11,998 | 3,129 | 26.1% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_average_f3_space_received_in | Completude | percentual de nulos | 11,998 | 2,820 | 23.5% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_f3_obv_passes_360 | Completude | percentual de nulos | 11,998 | 2,649 | 22.1% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_long_ball_ratio | Completude | percentual de nulos | 11,998 | 2,643 | 22.0% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_defensive_action | Completude | percentual de nulos | 11,998 | 1,684 | 14.0% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_positive_outcome_score | Completude | percentual de nulos | 11,998 | 1,638 | 13.7% | ALERTA | Mantido NULL + flag is_goleiro (métrica exclusiva de goleiro) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_lbp | Completude | percentual de nulos | 11,998 | 1,524 | 12.7% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_average_fhalf_space_received_in | Completude | percentual de nulos | 11,998 | 1,381 | 11.5% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_fhalf_obv_passes_360 | Completude | percentual de nulos | 11,998 | 1,270 | 10.6% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_pressures | Completude | percentual de nulos | 11,998 | 930 | 7.8% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_pressure_duration_total | Completude | percentual de nulos | 11,998 | 930 | 7.8% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_pressure_duration_avg | Completude | percentual de nulos | 11,998 | 930 | 7.8% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_pressured_action_fails | Completude | percentual de nulos | 11,998 | 930 | 7.8% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_counterpressures | Completude | percentual de nulos | 11,998 | 930 | 7.8% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_counterpressured_action_fails | Completude | percentual de nulos | 11,998 | 930 | 7.8% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_ccaa | Completude | percentual de nulos | 11,998 | 292 | 2.4% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_average_space_received_in | Completude | percentual de nulos | 11,998 | 271 | 2.3% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_da_aggressive_distance | Completude | percentual de nulos | 11,998 | 252 | 2.1% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_passes_360 | Completude | percentual de nulos | 11,998 | 202 | 1.7% | ALERTA | Mantido NULL + flag tem_cobertura_360; colunas fora da Gold |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_dribble_carry | Completude | percentual de nulos | 11,998 | 154 | 1.3% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv_pass | Completude | percentual de nulos | 11,998 | 106 | 0.9% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | player_match_passing_ratio | Completude | percentual de nulos | 11,998 | 103 | 0.9% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_shot_touch_ratio | Completude | percentual de nulos | 11,998 | 46 | 0.4% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_op_xgbuildup | Completude | percentual de nulos | 11,998 | 42 | 0.4% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_op_xgbuildup_per_possession | Completude | percentual de nulos | 11,998 | 42 | 0.4% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_op_xgchain | Completude | percentual de nulos | 11,998 | 40 | 0.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_op_xgchain_per_possession | Completude | percentual de nulos | 11,998 | 40 | 0.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_xgbuildup | Completude | percentual de nulos | 11,998 | 37 | 0.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_xgbuildup_per_possession | Completude | percentual de nulos | 11,998 | 37 | 0.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_xgchain | Completude | percentual de nulos | 11,998 | 34 | 0.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_xgchain_per_possession | Completude | percentual de nulos | 11,998 | 34 | 0.3% | ALERTA | Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização) |
| bronze | statsbomb_jogador_partida_raw | player_match_obv | Completude | percentual de nulos | 11,998 | 29 | 0.2% | ALERTA | Preenchido com 0 na Silver (contagem de ação não ocorrida) |
| bronze | statsbomb_jogador_partida_raw | team_name | Consistência | nome de time fora do padrão (exige de-para) | 20 | 4 | 20.0% | ALERTA | Padronizado via silver.time_de_para (ex.: 'Sc Do Recife' -> 'Sport Recife') |
| bronze | statsbomb_jogador_partida_raw | player_name | Consistência | nome de jogador compartilhado por player_ids distintos (homônimos) | 689 | 40 | 5.8% | ALERTA | player_id é a chave; dim_jogador.nome_exibicao acrescenta o clube |
| silver | jogador_partida | player_match_360_minutes | Consistência | partidas do jogador com cobertura 360 | 11,998 | 81 | 0.7% | ALERTA | Flag tem_cobertura_360; métricas 360 excluídas da Gold |
| silver | jogador_partida | team_name | Consistência | time sem mapeamento no de-para | 11,998 | 0 | 0.0% | OK |  |
| bronze | statsbomb_jogador_partida_raw | nan | Consistência | team_id com mais de um nome | 20 | 0 | 0.0% | OK |  |
| bronze | statsbomb_jogador_partida_raw | nan | Consistência | player_id com mais de um nome | 737 | 0 | 0.0% | OK |  |
| silver | jogador_partida | nan | Consistência | partida com exatamente 2 times | 380 | 0 | 0.0% | OK |  |
| silver | jogador_partida | player_match_possession | Consistência | posse idêntica para todos os jogadores do time na partida | 760 | 0 | 0.0% | OK | Posse é atributo do time; na Gold usa-se a média por time/partida |
| gold | fato_time_partida | posse | Consistência | posse do time + posse do adversário = 100% (±1 p.p.) | 760 | 0 | 0.0% | OK | Informativo |
| gold | mart_jogador_temporada | xg_sem_penalti_p90 | Outliers | outlier extremo (> Q3+3·IQR = 0.458) — todos os jogadores de linha | 687 | 12 | 1.7% | ALERTA | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | desarmes_p90 | Outliers | outlier extremo (> Q3+3·IQR = 5.474) — todos os jogadores de linha | 687 | 10 | 1.5% | ALERTA | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | obv_total_p90 | Outliers | outlier extremo (> Q3+3·IQR = 0.608) — todos os jogadores de linha | 687 | 5 | 0.7% | ALERTA | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | passes_decisivos_p90 | Outliers | outlier extremo (> Q3+3·IQR = 4.135) — todos os jogadores de linha | 687 | 4 | 0.6% | ALERTA | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | xg_sem_penalti_p90 | Outliers | outlier extremo (> Q3+3·IQR = 0.469) — >= 900 min | 353 | 2 | 0.6% | ALERTA | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | passes_decisivos_p90 | Outliers | outlier extremo (> Q3+3·IQR = 3.526) — >= 900 min | 353 | 0 | 0.0% | OK | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | desarmes_p90 | Outliers | outlier extremo (> Q3+3·IQR = 5.067) — >= 900 min | 353 | 0 | 0.0% | OK | Análises usam elegivel_analise (>= 900 min) |
| gold | mart_jogador_temporada | obv_total_p90 | Outliers | outlier extremo (> Q3+3·IQR = 0.487) — >= 900 min | 353 | 0 | 0.0% | OK | Análises usam elegivel_analise (>= 900 min) |
| bronze | statsbomb_jogador_partida_raw | nan | Unicidade | chave (match_id, player_id) única | 11,998 | 0 | 0.0% | OK | Deduplicação por row_number na Silver |
| bronze | statsbomb_jogador_partida_raw | nan | Unicidade | linhas 100% idênticas | 11,998 | 0 | 0.0% | OK | Deduplicação na Silver |
| silver | jogador_partida | nan | Unicidade | chave (match_id, player_id) única | 11,998 | 0 | 0.0% | OK |  |
| gold | dim_time | nan | Unicidade | chave primária (team_id) única | 20 | 0 | 0.0% | OK |  |
| gold | dim_jogador | nan | Unicidade | chave primária (player_id) única | 737 | 0 | 0.0% | OK |  |
| gold | dim_partida | nan | Unicidade | chave primária (match_id) única | 380 | 0 | 0.0% | OK |  |
| gold | fato_jogador_partida | nan | Unicidade | chave primária (match_id, player_id) única | 11,998 | 0 | 0.0% | OK |  |
| gold | fato_time_partida | nan | Unicidade | chave primária (match_id, team_id) única | 760 | 0 | 0.0% | OK |  |
| gold | mart_jogador_temporada | nan | Unicidade | chave primária (player_id) única | 737 | 0 | 0.0% | OK |  |
| gold | mart_classificacao | nan | Unicidade | chave primária (team_id) única | 20 | 0 | 0.0% | OK |  |
