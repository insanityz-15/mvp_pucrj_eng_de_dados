# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Gold: modelo dimensional (esquema estrela) e marts
# MAGIC
# MAGIC Aqui a Silver vira o modelo que as análises e o catálogo consomem. O desenho é um esquema estrela simples,
# MAGIC com duas fatos (jogador e time por partida) em volta das dimensões de clube, jogador e partida:
# MAGIC
# MAGIC ```
# MAGIC                 dim_time ◄──────────────┐
# MAGIC                    ▲  ▲                  │
# MAGIC   dim_jogador ─────┘  │          fato_time_partida ──► dim_partida
# MAGIC        ▲              │                  ▲
# MAGIC        └──── fato_jogador_partida ───────┘ (match_id)
# MAGIC ```
# MAGIC
# MAGIC | Tabela | Grão | Uso |
# MAGIC |---|---|---|
# MAGIC | `dim_time` | 1 linha por clube | Atributos do clube (nome padronizado, sigla, UF) |
# MAGIC | `dim_jogador` | 1 linha por jogador | Nome, nome de exibição sem ambiguidade, goleiro, clube principal |
# MAGIC | `dim_partida` | 1 linha por partida | Confronto e placar (derivado da soma de gols) |
# MAGIC | `fato_jogador_partida` | jogador × partida | ~45 métricas renomeadas em português |
# MAGIC | `fato_time_partida` | time × partida | Métricas agregadas pró/contra, resultado e pontos |
# MAGIC | `mart_jogador_temporada` | jogador × temporada | Totais e métricas per-90 (P3, P4, P5) |
# MAGIC | `mart_classificacao` | time × temporada | Classificação derivada + xG (P1, P2) |
# MAGIC | `feature_similaridade_jogador` | jogador elegível | Vetor padronizado (z-score) de 28 features per-90 (P6 e MVP de ML) |
# MAGIC
# MAGIC > **Limitação conhecida da fonte:** não tem data/rodada nem mando de campo. Por isso não existe `dim_data` e a
# MAGIC > `dim_partida` identifica os clubes como `time_a`/`time_b` (ordenados por `team_id`).

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# ================================================================================
# LIMPEZA DE CONSTRAINTS ANTES DO OVERWRITE
# ================================================================================
# O notebook 06 cria PK/FK/CHECK nas tabelas Gold. Se deixar elas lá, o overwrite daqui conflita,
# então removo tudo antes. O 06 recria ao final, o pipeline continua idempotente.

FKS = {
    T_DIM_JOGADOR: ["fk_dim_jogador_time"],
    T_DIM_PARTIDA: ["fk_dim_partida_time_a", "fk_dim_partida_time_b"],
    T_FATO_JOG: ["fk_fjp_partida", "fk_fjp_jogador", "fk_fjp_time", "fk_fjp_adversario"],
    T_FATO_TIME: ["fk_ftp_partida", "fk_ftp_time", "fk_ftp_adversario"],
    T_MART_JOG: ["fk_mart_jog_jogador"],
    T_MART_CLASS: ["fk_mart_class_time"],
}
CHECKS = {T_FATO_JOG: ["ck_minutos", "ck_passes"], T_FATO_TIME: ["ck_pontos"]}

# ── Primeiro as FKs e CHECKs (são dependentes das PKs) ─────────────────────────
for tabela, fks in FKS.items():
    if spark.catalog.tableExists(tabela):
        for fk in fks + CHECKS.get(tabela, []):
            spark.sql(f"ALTER TABLE {tabela} DROP CONSTRAINT IF EXISTS {fk}")

# ── Depois as PKs (nome padrão pk_<tabela>) ─────────────────────────────────────
for tabela in [T_DIM_TIME, T_DIM_JOGADOR, T_DIM_PARTIDA, T_FATO_JOG, T_FATO_TIME, T_MART_JOG, T_MART_CLASS]:
    if spark.catalog.tableExists(tabela):
        spark.sql(f"ALTER TABLE {tabela} DROP CONSTRAINT IF EXISTS pk_{tabela.split('.')[-1]}")

# Views temporárias para os SQLs abaixo ficarem mais curtos
spark.table(T_SILVER_ESTAT).createOrReplaceTempView("silver_jp")
spark.table(T_SILVER_TIME_DE_PARA).createOrReplaceTempView("de_para")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Dimensões
# MAGIC
# MAGIC Começa pela `dim_time`, que as outras dimensões usam para trazer o nome curto do clube.

# COMMAND ----------

# ================================================================================
# DIM_TIME
# ================================================================================

dim_time = spark.sql("""
SELECT DISTINCT
    s.team_id,
    d.nome_time,
    d.nome_curto,
    d.sigla,
    d.uf,
    s.team_name_fonte AS nome_fonte
FROM silver_jp s
JOIN de_para d
    ON s.team_name_fonte = d.nome_fonte
""")

# Se o de-para estiver furado, o mesmo team_id aparece com dois nomes e a dimensão duplica
assert dim_time.count() == dim_time.select("team_id").distinct().count(), "team_id com mais de um nome"

salvar_tabela(dim_time, T_DIM_TIME, "Gold: dimensão de clubes do Brasileirão 2025 (1 linha por team_id).")
dim_time.createOrReplaceTempView("dim_time")

# COMMAND ----------

# MAGIC %md
# MAGIC Na `dim_jogador` o clube principal é o que o jogador tem **mais minutos** na temporada, porque 25 jogadores
# MAGIC atuaram por 2 clubes. O `nome_exibicao` resolve os homônimos (ex.: dois "Vitinho") colocando o clube entre parênteses.

# COMMAND ----------

# ================================================================================
# DIM_JOGADOR
# ================================================================================

dim_jogador = spark.sql("""
WITH por_time AS (
    -- minutos e partidas de cada jogador por clube
    SELECT
        player_id,
        player_name,
        team_id,
        SUM(player_match_minutes) AS minutos,
        COUNT(*) AS partidas,
        MAX(CAST(is_goleiro AS INT)) AS gk
    FROM silver_jp
    GROUP BY player_id, player_name, team_id
),
rank_time AS (
    -- rn = 1 é o clube com mais minutos (empate desempata pelo team_id)
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY minutos DESC, team_id) AS rn,
        COUNT(*) OVER (PARTITION BY player_id) AS qtd_times
    FROM por_time
),
base AS (
    SELECT
        r.player_id,
        r.player_name AS nome_jogador,
        r.team_id AS time_principal_id,
        t.nome_curto AS time_principal,
        r.qtd_times,
        CAST(r.gk AS BOOLEAN) AS is_goleiro
    FROM rank_time r
    JOIN dim_time t
        ON r.team_id = t.team_id
    WHERE r.rn = 1
)
SELECT
    player_id,
    nome_jogador,
    CASE
        WHEN COUNT(*) OVER (PARTITION BY nome_jogador) > 1
            THEN CONCAT(nome_jogador, ' (', time_principal, ')')
        ELSE nome_jogador
    END AS nome_exibicao,
    CASE WHEN is_goleiro THEN 'Goleiro' ELSE 'Linha' END AS tipo_jogador,
    is_goleiro,
    time_principal_id,
    time_principal,
    qtd_times,
    COUNT(*) OVER (PARTITION BY nome_jogador) > 1 AS nome_homonimo
FROM base
""")
salvar_tabela(dim_jogador, T_DIM_JOGADOR, "Gold: dimensão de jogadores (1 linha por player_id) com clube principal e nome de exibição sem ambiguidade.")

# COMMAND ----------

# ================================================================================
# DIM_PARTIDA
# ================================================================================

# A fonte não traz placar, então gols do time na partida = soma dos gols dos jogadores dele
spark.sql("""
SELECT
    match_id,
    team_id,
    SUM(player_match_goals) AS gols
FROM silver_jp
GROUP BY match_id, team_id
""").createOrReplaceTempView("gols_time")

# time_a é sempre o de menor team_id (a fonte não diz quem é mandante)
dim_partida = spark.sql("""
WITH par AS (
    SELECT
        a.match_id,
        a.team_id AS time_a_id,
        a.gols AS gols_time_a,
        b.team_id AS time_b_id,
        b.gols AS gols_time_b
    FROM gols_time a
    JOIN gols_time b
        ON a.match_id = b.match_id
        AND a.team_id < b.team_id
)
SELECT
    p.match_id,
    p.time_a_id,
    ta.nome_curto AS time_a,
    p.time_b_id,
    tb.nome_curto AS time_b,
    CAST(p.gols_time_a AS INT) AS gols_time_a,
    CAST(p.gols_time_b AS INT) AS gols_time_b,
    CAST(p.gols_time_a + p.gols_time_b AS INT) AS total_gols,
    CONCAT(ta.nome_curto, ' ', p.gols_time_a, ' x ', p.gols_time_b, ' ', tb.nome_curto) AS confronto,
    CASE
        WHEN p.gols_time_a > p.gols_time_b THEN ta.nome_curto
        WHEN p.gols_time_a < p.gols_time_b THEN tb.nome_curto
        ELSE 'Empate'
    END AS vencedor,
    %d AS temporada
FROM par p
JOIN dim_time ta
    ON p.time_a_id = ta.team_id
JOIN dim_time tb
    ON p.time_b_id = tb.team_id
""" % TEMPORADA)
salvar_tabela(dim_partida, T_DIM_PARTIDA, "Gold: dimensão de partidas (1 linha por match_id); placar derivado da soma de gols dos jogadores.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Fato jogador × partida
# MAGIC
# MAGIC Separei umas 45 métricas que interessam para as perguntas e renomeei em português. As ~60 métricas de
# MAGIC cobertura 360 continuam na Silver, mas não entram na Gold porque a cobertura é parcial (ver notebook de Qualidade).

# COMMAND ----------

# ================================================================================
# FATO_JOGADOR_PARTIDA
# ================================================================================

# O de-para MAPA_FATO_JOG (coluna silver -> coluna gold) fica no 00_config, porque o catálogo de dados também usa

# adversário = o outro time da partida
col_adversario = (
    F.when(F.col("team_id") == F.col("p.time_a_id"), F.col("p.time_b_id"))
     .otherwise(F.col("p.time_a_id"))
     .alias("adversario_id")
)
metricas_renomeadas = [F.col(f"s.{src}").alias(dst) for src, dst in MAPA_FATO_JOG.items()]

fato_jog = (spark.table(T_SILVER_ESTAT).alias("s")
    .join(spark.table(T_DIM_PARTIDA).alias("p"), "match_id")
    .select(
        "match_id", "player_id", "team_id",
        col_adversario,
        *metricas_renomeadas,
        "is_goleiro", "tem_cobertura_360", "_id_carga"))

salvar_tabela(fato_jog, T_FATO_JOG, "Gold: fato de desempenho por jogador x partida (grão match_id + player_id).")
fato_jog.createOrReplaceTempView("fato_jog")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Fato time × partida
# MAGIC
# MAGIC As métricas **pró** são a soma dos jogadores do time. As métricas **contra** saem de um self-join com o
# MAGIC adversário na mesma partida. Pontuação padrão: vitória 3, empate 1, derrota 0.

# COMMAND ----------

# ================================================================================
# FATO_TIME_PARTIDA
# ================================================================================

fato_time = spark.sql("""
WITH pro AS (
    -- agrega os jogadores de cada time na partida
    SELECT
        match_id,
        team_id,
        FIRST(adversario_id) AS adversario_id,
        SUM(gols) AS gols,
        SUM(gols_sem_penalti) AS gols_sem_penalti,
        ROUND(SUM(xg_sem_penalti), 4) AS xg_sem_penalti,
        SUM(finalizacoes_sem_penalti) AS finalizacoes,
        SUM(finalizacoes_no_alvo) AS finalizacoes_no_alvo,
        SUM(passes) AS passes,
        SUM(passes_certos) AS passes_certos,
        SUM(passes_decisivos) AS passes_decisivos,
        SUM(toques_na_area) AS toques_na_area,
        SUM(pressoes) AS pressoes,
        SUM(contrapressoes) AS contrapressoes,
        SUM(recuperacoes) AS recuperacoes,
        SUM(desarmes) AS desarmes,
        SUM(interceptacoes) AS interceptacoes,
        ROUND(SUM(obv_total), 4) AS obv_total,
        ROUND(AVG(posse_time), 4) AS posse,
        COUNT(*) AS jogadores_utilizados
    FROM fato_jog
    GROUP BY match_id, team_id
)
SELECT
    p.match_id,
    p.team_id,
    p.adversario_id,
    CAST(p.gols AS INT) AS gols_pro,
    CAST(c.gols AS INT) AS gols_contra,
    CAST(p.gols_sem_penalti AS INT) AS gols_sem_penalti_pro,
    CAST(c.gols_sem_penalti AS INT) AS gols_sem_penalti_contra,
    p.xg_sem_penalti AS xg_sem_penalti_pro,
    c.xg_sem_penalti AS xg_sem_penalti_contra,
    CAST(p.finalizacoes AS INT) AS finalizacoes_pro,
    CAST(c.finalizacoes AS INT) AS finalizacoes_contra,
    CAST(p.finalizacoes_no_alvo AS INT) AS finalizacoes_no_alvo_pro,
    CAST(c.finalizacoes_no_alvo AS INT) AS finalizacoes_no_alvo_contra,
    CAST(p.passes AS INT) AS passes,
    CAST(p.passes_certos AS INT) AS passes_certos,
    ROUND(try_divide(p.passes_certos, p.passes), 4) AS pct_passes_certos,
    CAST(p.passes_decisivos AS INT) AS passes_decisivos,
    CAST(p.toques_na_area AS INT) AS toques_na_area,
    CAST(p.pressoes AS INT) AS pressoes,
    CAST(p.contrapressoes AS INT) AS contrapressoes,
    CAST(p.recuperacoes AS INT) AS recuperacoes,
    CAST(p.desarmes AS INT) AS desarmes,
    CAST(p.interceptacoes AS INT) AS interceptacoes,
    p.obv_total,
    p.posse,
    CAST(p.jogadores_utilizados AS INT) AS jogadores_utilizados,
    CASE WHEN p.gols > c.gols THEN 'V' WHEN p.gols = c.gols THEN 'E' ELSE 'D' END AS resultado,
    CASE WHEN p.gols > c.gols THEN 3 WHEN p.gols = c.gols THEN 1 ELSE 0 END AS pontos
FROM pro p
-- self-join: c é o adversário na mesma partida
JOIN pro c
    ON p.match_id = c.match_id
    AND p.adversario_id = c.team_id
""")
salvar_tabela(fato_time, T_FATO_TIME, "Gold: fato de desempenho por time x partida (grão match_id + team_id) com métricas pró/contra e pontos.")
fato_time.createOrReplaceTempView("fato_time")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Marts analíticos

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.1 `mart_classificacao`
# MAGIC
# MAGIC Critérios de desempate da CBF, nessa ordem: pontos, vitórias, saldo de gols, gols pró.
# MAGIC
# MAGIC As colunas `*_oficial` vêm da tabela de referência. A `gols_contra_a_favor_nao_creditados` é a diferença entre
# MAGIC gols oficiais e gols derivados, ou seja, os gols contra marcados pelo adversário, que a StatsBomb não credita a nenhum jogador.

# COMMAND ----------

# ================================================================================
# MART_CLASSIFICACAO
# ================================================================================

spark.table(T_SILVER_CLASS_OFICIAL).createOrReplaceTempView("oficial")

mart_class = spark.sql("""
WITH agg AS (
    -- consolida a temporada de cada clube a partir da fato_time
    SELECT
        team_id,
        COUNT(*) AS jogos,
        SUM(pontos) AS pontos,
        SUM(CASE WHEN resultado = 'V' THEN 1 ELSE 0 END) AS vitorias,
        SUM(CASE WHEN resultado = 'E' THEN 1 ELSE 0 END) AS empates,
        SUM(CASE WHEN resultado = 'D' THEN 1 ELSE 0 END) AS derrotas,
        SUM(gols_pro) AS gols_pro,
        SUM(gols_contra) AS gols_contra,
        SUM(gols_sem_penalti_pro) AS gols_sem_penalti_pro,
        SUM(gols_sem_penalti_contra) AS gols_sem_penalti_contra,
        ROUND(SUM(xg_sem_penalti_pro), 2) AS xg_sem_penalti_pro,
        ROUND(SUM(xg_sem_penalti_contra), 2) AS xg_sem_penalti_contra,
        ROUND(AVG(finalizacoes_pro), 2) AS finalizacoes_pro_por_jogo,
        ROUND(AVG(finalizacoes_contra), 2) AS finalizacoes_contra_por_jogo,
        ROUND(AVG(pressoes), 1) AS pressoes_por_jogo,
        ROUND(AVG(recuperacoes), 1) AS recuperacoes_por_jogo,
        ROUND(AVG(posse), 4) AS posse_media,
        ROUND(try_divide(SUM(passes_certos), SUM(passes)), 4) AS pct_passes_certos,
        ROUND(SUM(obv_total), 2) AS obv_total
    FROM fato_time
    GROUP BY team_id
)
SELECT
    -- posição pelos critérios de desempate da CBF
    ROW_NUMBER() OVER (
        ORDER BY a.pontos DESC, a.vitorias DESC, (a.gols_pro - a.gols_contra) DESC, a.gols_pro DESC
    ) AS posicao,
    a.team_id,
    t.nome_curto AS time,
    a.jogos,
    a.pontos,
    a.vitorias,
    a.empates,
    a.derrotas,
    a.gols_pro,
    a.gols_contra,
    a.gols_pro - a.gols_contra AS saldo_gols,
    ROUND(a.pontos / (a.jogos * 3), 4) AS aproveitamento,
    a.xg_sem_penalti_pro,
    a.xg_sem_penalti_contra,
    ROUND(a.xg_sem_penalti_pro - a.xg_sem_penalti_contra, 2) AS saldo_xg,
    ROUND(a.gols_sem_penalti_pro - a.xg_sem_penalti_pro, 2) AS gols_menos_xg_pro,
    ROUND(a.gols_sem_penalti_contra - a.xg_sem_penalti_contra, 2) AS gols_menos_xg_contra,
    a.finalizacoes_pro_por_jogo,
    a.finalizacoes_contra_por_jogo,
    a.pressoes_por_jogo,
    a.recuperacoes_por_jogo,
    a.posse_media,
    a.pct_passes_certos,
    a.obv_total,
    -- referência oficial, para comparar com o que derivamos
    o.posicao AS posicao_oficial,
    o.pontos AS pontos_oficiais,
    o.gols_pro AS gols_pro_oficial,
    o.gols_contra AS gols_contra_oficial,
    o.gols_pro - a.gols_pro AS gols_contra_a_favor_nao_creditados
FROM agg a
JOIN dim_time t
    ON a.team_id = t.team_id
LEFT JOIN oficial o
    ON t.nome_time = o.nome_time
""")
salvar_tabela(mart_class, T_MART_CLASS, "Gold: classificação derivada do Brasileirão 2025 + métricas de xG sem pênalti pró/contra por clube.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2 `mart_jogador_temporada`
# MAGIC
# MAGIC As divisões usam `try_divide`: no ANSI SQL a divisão por zero dá erro, com ele vira NULL (ex.: goleiro sem finalizações).
# MAGIC
# MAGIC > **Regra crítica:** somar os totais da temporada **antes** de dividir por minutos. Nunca fazer média das razões por partida.
# MAGIC
# MAGIC `elegivel_analise` marca jogador de linha com pelo menos 900 minutos.

# COMMAND ----------

# ================================================================================
# MART_JOGADOR_TEMPORADA
# ================================================================================

# ── Métricas que viram per-90 ───────────────────────────────────────────────────
METRICAS_P90 = ["gols_sem_penalti", "xg_sem_penalti", "xa", "assistencias", "finalizacoes_sem_penalti",
                "passes_decisivos", "passes_terco_final", "passes_para_area", "progressoes_profundas",
                "dribles_certos", "toques_na_area", "desarmes", "interceptacoes", "recuperacoes", "pressoes",
                "contrapressoes", "duelos_aereos_vencidos", "cortes", "xg_chain", "xg_buildup", "obv_total",
                "obv_passe", "obv_conducao", "obv_defesa"]

# ── Totais da temporada por jogador ─────────────────────────────────────────────
# além das per-90, preciso somar as colunas usadas nos percentuais (passes, cruzamentos, etc.)
colunas_extras = ["gols", "passes", "passes_certos", "finalizacoes_no_alvo",
                  "duelos_aereos", "cruzamentos", "cruzamentos_certos"]
colunas_soma = sorted(set(METRICAS_P90 + colunas_extras))
soma = [F.sum(c).alias(c) for c in colunas_soma]

agg_jog = (spark.table(T_FATO_JOG).groupBy("player_id")
           .agg(F.countDistinct("match_id").alias("partidas"), F.sum("minutos").alias("minutos"), *soma))

# ── Colunas derivadas ───────────────────────────────────────────────────────────
elegivel = ((F.col("minutos") >= MIN_MINUTOS_ANALISE) & ~F.col("is_goleiro")).alias("elegivel_analise")

# per-90 = total da temporada / minutos da temporada * 90
metricas_p90 = [F.round(F.col(m) / F.col("minutos") * 90, 4).alias(f"{m}_p90") for m in METRICAS_P90]

mart_jog = (agg_jog.join(spark.table(T_DIM_JOGADOR), "player_id")
    .select("player_id", "nome_jogador", "nome_exibicao", "tipo_jogador", "time_principal_id", "time_principal",
            "qtd_times", "partidas", F.round("minutos", 1).alias("minutos"),
            F.round(F.try_divide("minutos", "partidas"), 1).alias("minutos_por_partida"),
            elegivel,
            F.col("gols").cast("int").alias("gols"),
            F.col("gols_sem_penalti").cast("int").alias("gols_sem_penalti"),
            F.col("assistencias").cast("int").alias("assistencias"),
            F.round("xg_sem_penalti", 3).alias("xg_sem_penalti"),
            F.round("xa", 3).alias("xa"),
            F.round(F.col("gols_sem_penalti") - F.col("xg_sem_penalti"), 3).alias("gols_menos_xg"),
            F.col("finalizacoes_sem_penalti").cast("int").alias("finalizacoes_sem_penalti"),
            F.round(F.try_divide("finalizacoes_no_alvo", "finalizacoes_sem_penalti"), 4).alias("pct_finalizacoes_no_alvo"),
            F.round(F.try_divide("passes_certos", "passes"), 4).alias("pct_passes_certos"),
            F.round(F.try_divide("duelos_aereos_vencidos", "duelos_aereos"), 4).alias("pct_duelos_aereos_vencidos"),
            *metricas_p90))
salvar_tabela(mart_jog, T_MART_JOG, "Gold: jogador x temporada com totais e métricas por 90 minutos; flag de elegibilidade (linha, >=900 min).")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.3 `feature_similaridade_jogador`
# MAGIC
# MAGIC É o mesmo conjunto de 28 features per-90 do MVP de ML (Similaridade de Jogadores), padronizado por z-score
# MAGIC **só sobre a população elegível**. O vetor também fica guardado como `ARRAY<DOUBLE>` (`vetor_features`), daí já dá
# MAGIC para calcular similaridade de cosseno direto em SQL ou jogar no `scikit-learn`/`MLflow`.

# COMMAND ----------

# ================================================================================
# FEATURE_SIMILARIDADE_JOGADOR
# ================================================================================

# nome no fato -> nome da feature (mantém paridade com o MVP de ML)
FEATURES_SIM = {
    "finalizacoes_sem_penalti": "np_shots", "gols_sem_penalti": "np_goals", "passes_decisivos": "key_passes",
    "assistencias": "assists", "passes_em_profundidade": "through_balls", "passes_para_area": "passes_into_box",
    "toques_na_area": "touches_inside_box", "desarmes": "tackles", "interceptacoes": "interceptions",
    "dribles_certos": "dribbles", "faltas_cometidas": "fouls", "perdas_de_posse": "dispossessions",
    "bolas_longas_certas": "successful_long_balls", "cortes": "clearances",
    "duelos_aereos_vencidos": "successful_aerials", "passes_certos": "successful_passes",
    "passes_para_frente": "forward_passes", "passes_terco_final": "op_f3_passes",
    "cruzamentos_certos": "successful_crosses", "pressoes": "pressures", "recuperacoes": "ball_recoveries",
    "progressoes_profundas": "deep_progressions", "acoes_defensivas": "defensive_actions", "obv_total": "obv",
    "obv_passe": "obv_pass", "obv_defesa": "obv_defensive_action", "obv_conducao": "obv_dribble_carry",
    "toques": "touches",
}

# ── Per-90 dos elegíveis ────────────────────────────────────────────────────────
elegiveis = spark.table(T_MART_JOG).filter("elegivel_analise").select("player_id", "nome_exibicao", "time_principal", "minutos")

somas_features = [F.sum(c).alias(c) for c in FEATURES_SIM]
features_p90 = [(F.col(c) / F.col("_min") * 90).alias(f"{f}_p90") for c, f in FEATURES_SIM.items()]

p90 = (spark.table(T_FATO_JOG).groupBy("player_id")
       .agg(F.sum("minutos").alias("_min"), *somas_features)
       .select("player_id", *features_p90)
       .join(elegiveis, "player_id"))

# ── Z-score ─────────────────────────────────────────────────────────────────────
cols_p90 = [f"{f}_p90" for f in FEATURES_SIM.values()]

# média e desvio de cada feature numa única passada (m_<col> e s_<col>)
medias = [F.mean(c).alias(f"m_{c}") for c in cols_p90]
desvios = [F.stddev(c).alias(f"s_{c}") for c in cols_p90]
stats = p90.select(*medias, *desvios).first()

z = p90.select("player_id", "nome_exibicao", "time_principal", "minutos",
               *[F.round((F.col(c) - stats[f"m_{c}"]) / stats[f"s_{c}"], 6).alias(f"z_{c}") for c in cols_p90])

# ── Vetor e norma (para o cosseno) ──────────────────────────────────────────────
z = z.withColumn("vetor_features", F.array(*[F.col(f"z_{c}") for c in cols_p90]))
z = z.withColumn("norma_vetor", F.expr("sqrt(aggregate(vetor_features, 0D, (acc, x) -> acc + x * x))"))

salvar_tabela(z, T_FEATURES, "Gold: vetor de 28 features per-90 padronizadas (z-score) por jogador elegível - insumo de similaridade/ML.")
