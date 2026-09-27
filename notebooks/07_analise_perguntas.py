# Databricks notebook source
# MAGIC %md
# MAGIC # 07 - Análise: respondendo às perguntas de negócio
# MAGIC
# MAGIC Todas as respostas aqui são consultas SQL em cima da camada Gold. Pra ver o gráfico sugerido em cada célula SQL,
# MAGIC é só usar o botão **+ > Visualization** do Databricks no resultado.
# MAGIC
# MAGIC | # | Pergunta |
# MAGIC |---|---|
# MAGIC | P1 | Como o Botafogo se compara à média da liga e ao melhor clube em volume ofensivo e defensivo por jogo? |
# MAGIC | P2 | A criação/concessão de chances (xG) explica os pontos? Quem terminou acima/abaixo do que o xG indicava? |
# MAGIC | P3 | Quais jogadores de linha (>= 900 min) lideram finalização e criação por 90 min, e onde estão os do Botafogo? |
# MAGIC | P4 | Quais jogadores converteram muito acima/abaixo do esperado (gols sem pênalti - xG)? |
# MAGIC | P5 | Como os clubes distribuem minutos no elenco (dependência de titulares x rotação)? |
# MAGIC | P6 | Quais jogadores da liga têm perfil estatístico mais parecido com um jogador de referência (A. Barboza)? |

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# ── Contexto da sessão SQL ──────────────────────────────────────────────────────
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql("USE SCHEMA gold")

# variáveis de sessão SQL: o time e o jogador de referência vêm do 00_config,
# assim as queries abaixo ficam parametrizadas sem concatenar string
spark.sql(f"DECLARE OR REPLACE VARIABLE time_ref STRING DEFAULT '{TIME_REFERENCIA}'")
spark.sql(f"DECLARE OR REPLACE VARIABLE jogador_ref STRING DEFAULT '{JOGADOR_REFERENCIA}'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## P1 - Botafogo x liga (por jogo)
# MAGIC
# MAGIC Como o Botafogo se compara à média da liga e ao melhor clube, por jogo, em ataque, defesa, pressão e posse?
# MAGIC
# MAGIC A query calcula as métricas por jogo de cada clube a partir do `mart_classificacao`, ranqueia os 20 e monta
# MAGIC quatro linhas: Botafogo, média da liga, melhor da liga e a posição do Botafogo. Na linha da posição, 1 = maior valor,
# MAGIC e nas métricas "contra" (xG e finalizações cedidas) 1 = menor valor.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH base AS (
# MAGIC   SELECT
# MAGIC     time,
# MAGIC     pontos,
# MAGIC     gols_pro / jogos AS gols_pro_j,
# MAGIC     gols_contra / jogos AS gols_contra_j,
# MAGIC     xg_sem_penalti_pro / jogos AS xg_pro_j,
# MAGIC     xg_sem_penalti_contra / jogos AS xg_contra_j,
# MAGIC     finalizacoes_pro_por_jogo AS final_pro_j,
# MAGIC     finalizacoes_contra_por_jogo AS final_contra_j,
# MAGIC     pressoes_por_jogo,
# MAGIC     recuperacoes_por_jogo,
# MAGIC     posse_media,
# MAGIC     pct_passes_certos
# MAGIC   FROM mart_classificacao
# MAGIC ),
# MAGIC rk AS (
# MAGIC   SELECT
# MAGIC     *,
# MAGIC     RANK() OVER (ORDER BY xg_pro_j DESC) AS r_xg_pro,
# MAGIC     RANK() OVER (ORDER BY xg_contra_j) AS r_xg_contra,
# MAGIC     RANK() OVER (ORDER BY final_pro_j DESC) AS r_fin_pro,
# MAGIC     RANK() OVER (ORDER BY final_contra_j) AS r_fin_contra,
# MAGIC     RANK() OVER (ORDER BY pressoes_por_jogo DESC) AS r_press,
# MAGIC     RANK() OVER (ORDER BY recuperacoes_por_jogo DESC) AS r_rec,
# MAGIC     RANK() OVER (ORDER BY posse_media DESC) AS r_posse,
# MAGIC     RANK() OVER (ORDER BY pct_passes_certos DESC) AS r_pass
# MAGIC   FROM base
# MAGIC )
# MAGIC -- 1. Botafogo
# MAGIC SELECT
# MAGIC   '1. Botafogo' AS referencia,
# MAGIC   ROUND(xg_pro_j, 2) AS xg_pro_jogo,
# MAGIC   ROUND(xg_contra_j, 2) AS xg_contra_jogo,
# MAGIC   ROUND(final_pro_j, 1) AS finalizacoes_jogo,
# MAGIC   ROUND(final_contra_j, 1) AS finalizacoes_cedidas_jogo,
# MAGIC   ROUND(pressoes_por_jogo, 0) AS pressoes_jogo,
# MAGIC   ROUND(recuperacoes_por_jogo, 1) AS recuperacoes_jogo,
# MAGIC   ROUND(posse_media * 100, 1) AS posse_pct,
# MAGIC   ROUND(pct_passes_certos * 100, 1) AS passes_certos_pct
# MAGIC FROM rk
# MAGIC WHERE time = time_ref
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- 2. Média da liga
# MAGIC SELECT
# MAGIC   '2. Média da liga',
# MAGIC   ROUND(AVG(xg_pro_j), 2),
# MAGIC   ROUND(AVG(xg_contra_j), 2),
# MAGIC   ROUND(AVG(final_pro_j), 1),
# MAGIC   ROUND(AVG(final_contra_j), 1),
# MAGIC   ROUND(AVG(pressoes_por_jogo), 0),
# MAGIC   ROUND(AVG(recuperacoes_por_jogo), 1),
# MAGIC   ROUND(AVG(posse_media) * 100, 1),
# MAGIC   ROUND(AVG(pct_passes_certos) * 100, 1)
# MAGIC FROM rk
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- 3. Melhor da liga (MAX nas métricas "pró", MIN nas métricas "contra")
# MAGIC SELECT
# MAGIC   '3. Melhor da liga',
# MAGIC   ROUND(MAX(xg_pro_j), 2),
# MAGIC   ROUND(MIN(xg_contra_j), 2),
# MAGIC   ROUND(MAX(final_pro_j), 1),
# MAGIC   ROUND(MIN(final_contra_j), 1),
# MAGIC   ROUND(MAX(pressoes_por_jogo), 0),
# MAGIC   ROUND(MAX(recuperacoes_por_jogo), 1),
# MAGIC   ROUND(MAX(posse_media) * 100, 1),
# MAGIC   ROUND(MAX(pct_passes_certos) * 100, 1)
# MAGIC FROM rk
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC -- 4. Posição do Botafogo no ranking dos 20
# MAGIC SELECT
# MAGIC   '4. Posição do Botafogo (1-20)',
# MAGIC   r_xg_pro,
# MAGIC   r_xg_contra,
# MAGIC   r_fin_pro,
# MAGIC   r_fin_contra,
# MAGIC   r_press,
# MAGIC   r_rec,
# MAGIC   r_posse,
# MAGIC   r_pass
# MAGIC FROM rk
# MAGIC WHERE time = time_ref
# MAGIC ORDER BY referencia

# COMMAND ----------

# MAGIC %md
# MAGIC ## P2 - xG x pontos
# MAGIC
# MAGIC A criação e a concessão de chances (xG) explicam os pontos? Quem terminou acima ou abaixo do que o xG indicava?
# MAGIC
# MAGIC A primeira query calcula as correlações e a regressão de pontos sobre o saldo de xG. A segunda usa essa reta pra
# MAGIC prever os pontos de cada clube e mostra a diferença (resíduo). Uso `pontos_oficiais` porque a pontuação derivada
# MAGIC da StatsBomb difere em alguns clubes por causa de gols contra (ver notebook de Qualidade).
# MAGIC
# MAGIC Gráfico sugerido: dispersão com `saldo_xg` no x, `pontos` no y e rótulo = `time`.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   ROUND(CORR(saldo_xg, pontos_oficiais), 3) AS corr_saldo_xg_pontos,
# MAGIC   ROUND(CORR(gols_pro_oficial - gols_contra_oficial, pontos_oficiais), 3) AS corr_saldo_gols_pontos,
# MAGIC   ROUND(CORR(xg_sem_penalti_pro, gols_pro), 3) AS corr_xg_pro_gols_pro,
# MAGIC   ROUND(CORR(xg_sem_penalti_contra, gols_contra), 3) AS corr_xg_contra_gols_contra,
# MAGIC   ROUND(REGR_SLOPE(pontos_oficiais, saldo_xg), 3) AS pontos_por_1_xg_de_saldo,
# MAGIC   ROUND(REGR_R2(pontos_oficiais, saldo_xg), 3) AS r2_pontos_saldo_xg
# MAGIC FROM mart_classificacao

# COMMAND ----------

# MAGIC %sql
# MAGIC -- pontos "esperados" pela reta de regressão pontos ~ saldo_xg
# MAGIC -- resíduo = quantos pontos o clube fez acima/abaixo do que o xG sugere
# MAGIC WITH reg AS (
# MAGIC   SELECT
# MAGIC     REGR_SLOPE(pontos_oficiais, saldo_xg) AS b,
# MAGIC     REGR_INTERCEPT(pontos_oficiais, saldo_xg) AS a
# MAGIC   FROM mart_classificacao
# MAGIC )
# MAGIC SELECT
# MAGIC   posicao_oficial AS posicao,
# MAGIC   time,
# MAGIC   pontos_oficiais AS pontos,
# MAGIC   saldo_xg,
# MAGIC   ROUND(a + b * saldo_xg, 1) AS pontos_previstos_pelo_xg,
# MAGIC   ROUND(pontos_oficiais - (a + b * saldo_xg), 1) AS pontos_acima_do_xg,
# MAGIC   gols_menos_xg_pro AS ataque_gols_menos_xg,
# MAGIC   gols_menos_xg_contra AS defesa_gols_sofridos_menos_xg
# MAGIC FROM mart_classificacao
# MAGIC CROSS JOIN reg
# MAGIC ORDER BY posicao_oficial

# COMMAND ----------

# MAGIC %md
# MAGIC ## P3 - Líderes per-90 (jogadores de linha, >= 900 min)
# MAGIC
# MAGIC Quais jogadores de linha lideram finalização e criação por 90 minutos, e onde estão os do Botafogo?
# MAGIC
# MAGIC A primeira query pega só os elegíveis (`elegivel_analise`) e traz o top 10 em npxG/90, xA/90 e passes decisivos/90.
# MAGIC A segunda calcula o percentil de cada jogador na liga (0-100) em algumas métricas-chave e filtra os do Botafogo.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH e AS (
# MAGIC   SELECT *
# MAGIC   FROM mart_jogador_temporada
# MAGIC   WHERE elegivel_analise
# MAGIC ),
# MAGIC r AS (
# MAGIC   SELECT
# MAGIC     nome_exibicao,
# MAGIC     time_principal,
# MAGIC     minutos,
# MAGIC     xg_sem_penalti_p90,
# MAGIC     xa_p90,
# MAGIC     passes_decisivos_p90,
# MAGIC     ROW_NUMBER() OVER (ORDER BY xg_sem_penalti_p90 DESC) AS rk_xg,
# MAGIC     ROW_NUMBER() OVER (ORDER BY xa_p90 DESC) AS rk_xa,
# MAGIC     ROW_NUMBER() OVER (ORDER BY passes_decisivos_p90 DESC) AS rk_pd
# MAGIC   FROM e
# MAGIC )
# MAGIC SELECT
# MAGIC   'npxG/90' AS ranking,
# MAGIC   rk_xg AS pos,
# MAGIC   nome_exibicao,
# MAGIC   time_principal,
# MAGIC   ROUND(minutos) AS minutos,
# MAGIC   ROUND(xg_sem_penalti_p90, 3) AS valor
# MAGIC FROM r
# MAGIC WHERE rk_xg <= 10
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'xA/90',
# MAGIC   rk_xa,
# MAGIC   nome_exibicao,
# MAGIC   time_principal,
# MAGIC   ROUND(minutos),
# MAGIC   ROUND(xa_p90, 3)
# MAGIC FROM r
# MAGIC WHERE rk_xa <= 10
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Passes decisivos/90',
# MAGIC   rk_pd,
# MAGIC   nome_exibicao,
# MAGIC   time_principal,
# MAGIC   ROUND(minutos),
# MAGIC   ROUND(passes_decisivos_p90, 3)
# MAGIC FROM r
# MAGIC WHERE rk_pd <= 10
# MAGIC ORDER BY ranking, pos

# COMMAND ----------

# MAGIC %sql
# MAGIC -- jogadores do Botafogo: percentil na liga (0-100, população elegível) em métricas-chave
# MAGIC WITH p AS (
# MAGIC   SELECT
# MAGIC     nome_exibicao,
# MAGIC     time_principal,
# MAGIC     ROUND(minutos) AS minutos,
# MAGIC     ROUND(100 * PERCENT_RANK() OVER (ORDER BY xg_sem_penalti_p90), 0) AS pct_npxg,
# MAGIC     ROUND(100 * PERCENT_RANK() OVER (ORDER BY xa_p90), 0) AS pct_xa,
# MAGIC     ROUND(100 * PERCENT_RANK() OVER (ORDER BY progressoes_profundas_p90), 0) AS pct_progressoes,
# MAGIC     ROUND(100 * PERCENT_RANK() OVER (ORDER BY pressoes_p90), 0) AS pct_pressoes,
# MAGIC     ROUND(100 * PERCENT_RANK() OVER (ORDER BY recuperacoes_p90), 0) AS pct_recuperacoes,
# MAGIC     ROUND(100 * PERCENT_RANK() OVER (ORDER BY obv_total_p90), 0) AS pct_obv
# MAGIC   FROM mart_jogador_temporada
# MAGIC   WHERE elegivel_analise
# MAGIC )
# MAGIC SELECT *
# MAGIC FROM p
# MAGIC WHERE time_principal = time_ref
# MAGIC ORDER BY pct_obv DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## P4 - Finalização acima/abaixo do esperado
# MAGIC
# MAGIC Quais jogadores converteram muito acima ou abaixo do esperado (gols sem pênalti - xG)?
# MAGIC
# MAGIC A query traz os 10 mais acima e os 10 mais abaixo do esperado entre os jogadores de linha. Filtrei quem tem pelo
# MAGIC menos 30 finalizações sem pênalti na temporada, que é a amostra mínima pra diferença ter algum significado.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH b AS (
# MAGIC   SELECT
# MAGIC     nome_exibicao,
# MAGIC     time_principal,
# MAGIC     finalizacoes_sem_penalti,
# MAGIC     gols_sem_penalti,
# MAGIC     ROUND(xg_sem_penalti, 2) AS xg_sem_penalti,
# MAGIC     ROUND(gols_menos_xg, 2) AS gols_menos_xg,
# MAGIC     ROUND(gols_sem_penalti / xg_sem_penalti, 2) AS gols_por_xg,
# MAGIC     ROUND(xg_sem_penalti / finalizacoes_sem_penalti, 3) AS xg_por_finalizacao
# MAGIC   FROM mart_jogador_temporada
# MAGIC   WHERE tipo_jogador = 'Linha'
# MAGIC     AND finalizacoes_sem_penalti >= 30
# MAGIC )
# MAGIC (
# MAGIC   SELECT 'Acima do esperado' AS grupo, *
# MAGIC   FROM b
# MAGIC   ORDER BY gols_menos_xg DESC
# MAGIC   LIMIT 10
# MAGIC )
# MAGIC UNION ALL
# MAGIC (
# MAGIC   SELECT 'Abaixo do esperado', *
# MAGIC   FROM b
# MAGIC   ORDER BY gols_menos_xg ASC
# MAGIC   LIMIT 10
# MAGIC )

# COMMAND ----------

# MAGIC %md
# MAGIC ## P5 - Concentração de minutos por elenco
# MAGIC
# MAGIC Como os clubes distribuem os minutos no elenco, mais dependentes dos titulares ou com mais rotação?
# MAGIC
# MAGIC A query soma os minutos de cada jogador por clube, ordena do maior para o menor e acumula o percentual.
# MAGIC `jogadores_para_80pct` é quantos atletas somam 80% dos minutos do clube: quanto menor, mais o time depende de um
# MAGIC núcleo fixo. `pct_minutos_top11` é o quanto os 11 que mais jogaram concentram.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH m AS (
# MAGIC   SELECT
# MAGIC     t.nome_curto AS time,
# MAGIC     f.player_id,
# MAGIC     SUM(f.minutos) AS minutos
# MAGIC   FROM fato_jogador_partida f
# MAGIC   JOIN dim_time t USING (team_id)
# MAGIC   GROUP BY ALL
# MAGIC ),
# MAGIC acc AS (
# MAGIC   SELECT
# MAGIC     *,
# MAGIC     -- minutos acumulados (do maior para o menor) / total de minutos do clube
# MAGIC     SUM(minutos) OVER (PARTITION BY time ORDER BY minutos DESC ROWS UNBOUNDED PRECEDING)
# MAGIC       / SUM(minutos) OVER (PARTITION BY time) AS pct_acum,
# MAGIC     ROW_NUMBER() OVER (PARTITION BY time ORDER BY minutos DESC) AS ordem
# MAGIC   FROM m
# MAGIC )
# MAGIC SELECT
# MAGIC   a.time,
# MAGIC   COUNT(*) AS jogadores_utilizados,
# MAGIC   MIN(CASE WHEN pct_acum >= 0.8 THEN ordem END) AS jogadores_para_80pct,
# MAGIC   ROUND(100 * MAX(CASE WHEN ordem = 11 THEN pct_acum END), 1) AS pct_minutos_top11,
# MAGIC   c.posicao_oficial AS posicao,
# MAGIC   c.pontos_oficiais AS pontos
# MAGIC FROM acc a
# MAGIC JOIN mart_classificacao c
# MAGIC   ON a.time = c.time
# MAGIC GROUP BY
# MAGIC   a.time,
# MAGIC   c.posicao_oficial,
# MAGIC   c.pontos_oficiais
# MAGIC ORDER BY pct_minutos_top11 DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## P6 - Similaridade de perfil
# MAGIC
# MAGIC Quais jogadores da liga têm o perfil estatístico mais parecido com o jogador de referência (A. Barboza)?
# MAGIC
# MAGIC A Gold já entrega o vetor z-score de 28 features pronto, então a similaridade de cosseno é calculada em SQL puro
# MAGIC com funções de array (`zip_with` + `aggregate`). É o mesmo método do MVP de ML, só que agora servido pelo Lakehouse.
# MAGIC A primeira query traz os 10 mais parecidos; a segunda compara a referência com os 3 mais similares nas features
# MAGIC em que a referência tem maior |z|.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH ref AS (
# MAGIC   SELECT
# MAGIC     player_id,
# MAGIC     vetor_features AS v,
# MAGIC     norma_vetor AS n
# MAGIC   FROM feature_similaridade_jogador
# MAGIC   WHERE nome_exibicao = jogador_ref
# MAGIC )
# MAGIC SELECT
# MAGIC   f.nome_exibicao,
# MAGIC   f.time_principal,
# MAGIC   ROUND(f.minutos) AS minutos,
# MAGIC   -- cosseno = produto escalar / (norma do jogador * norma da referência)
# MAGIC   ROUND(
# MAGIC     aggregate(zip_with(f.vetor_features, ref.v, (x, y) -> x * y), 0D, (acc, x) -> acc + x)
# MAGIC       / (f.norma_vetor * ref.n),
# MAGIC     4
# MAGIC   ) AS similaridade_cosseno
# MAGIC FROM feature_similaridade_jogador f
# MAGIC CROSS JOIN ref
# MAGIC WHERE f.player_id <> ref.player_id
# MAGIC ORDER BY similaridade_cosseno DESC
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %sql
# MAGIC -- perfil comparado: referência x 3 mais similares nas features de maior |z| da referência
# MAGIC WITH ref AS (
# MAGIC   SELECT *
# MAGIC   FROM feature_similaridade_jogador
# MAGIC   WHERE nome_exibicao = jogador_ref
# MAGIC )
# MAGIC SELECT
# MAGIC   nome_exibicao,
# MAGIC   time_principal,
# MAGIC   ROUND(z_successful_aerials_p90, 2) AS z_aereos_vencidos,
# MAGIC   ROUND(z_clearances_p90, 2) AS z_cortes,
# MAGIC   ROUND(z_successful_long_balls_p90, 2) AS z_bolas_longas_certas,
# MAGIC   ROUND(z_successful_passes_p90, 2) AS z_passes_certos,
# MAGIC   ROUND(z_interceptions_p90, 2) AS z_interceptacoes,
# MAGIC   ROUND(z_touches_inside_box_p90, 2) AS z_toques_area,
# MAGIC   ROUND(z_dribbles_p90, 2) AS z_dribles
# MAGIC FROM feature_similaridade_jogador f
# MAGIC WHERE nome_exibicao = jogador_ref
# MAGIC    OR player_id IN (
# MAGIC      -- top 3 por similaridade de cosseno (mesma conta da query anterior)
# MAGIC      SELECT f2.player_id
# MAGIC      FROM feature_similaridade_jogador f2
# MAGIC      CROSS JOIN ref
# MAGIC      WHERE f2.player_id <> ref.player_id
# MAGIC      ORDER BY aggregate(zip_with(f2.vetor_features, ref.vetor_features, (x, y) -> x * y), 0D, (acc, x) -> acc + x)
# MAGIC               / (f2.norma_vetor * ref.norma_vetor) DESC
# MAGIC      LIMIT 3
# MAGIC    )
