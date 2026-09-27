# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Silver: limpeza, tipagem e padronização
# MAGIC
# MAGIC Esse é o notebook que mais mexe no dado. As transformações estão numeradas de T1 a T6 e cada uma é
# MAGIC explicada na sua célula:
# MAGIC
# MAGIC | # | Transformação | Motivo |
# MAGIC |---|---|---|
# MAGIC | T1 | Tipagem explícita guiada pelo dicionário (`try_cast`) | Bronze é 100% STRING; valor que não converte vira NULL e é contado, sem quebrar o pipeline |
# MAGIC | T2 | Tratamento de missing pela regra do dicionário | `Preencher com 0` = contagem de ação que não aconteceu; `Manter NA` = métrica que depende de um evento (o NA é informativo) |
# MAGIC | T3 | Padronização dos nomes de times via tabela de-para | A fonte traz `Sc Do Recife`, `EC Juventude`, `Mirassol Futebol Clube`, etc. |
# MAGIC | T4 | Flags derivadas: `is_goleiro`, `tem_cobertura_360` | Não existe coluna de posição, e as métricas de goleiro e de cobertura 360 são esparsas por natureza |
# MAGIC | T5 | Deduplicação por (`match_id`, `player_id`) | Garante o grão 1 jogador x 1 partida mesmo se o arquivo for reenviado |
# MAGIC | T6 | Regras de qualidade com quarentena | Linha que viola regra de negócio não contamina a Silver, mas continua rastreável |

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md ## 1. Dicionário de dados tipado (dirige as regras T1 e T2)

# COMMAND ----------

# ================================================================================
# DICIONÁRIO DE DADOS
# ================================================================================

COLS_DIC = ["variavel", "categoria", "tratamento_missing", "justificativa", "acao_recomendada", "nota_revisao"]
cols_dic_trim = [F.trim(F.col(c)).alias(c) for c in COLS_DIC]

# tira espaços, descarta linha sem variável e garante 1 linha por variável
df_dic = (spark.table(T_BRONZE_DIC)
          .select(*cols_dic_trim, "_id_carga")
          .filter(F.col("variavel").isNotNull())
          .dropDuplicates(["variavel"]))

salvar_tabela(df_dic, T_SILVER_DIC,
              "Silver: dicionário de dados StatsBomb (1 linha por variável) com categoria e regra de tratamento de missing.")

# dicionário em memória, variável -> linha com as regras (usado na tipagem e no missing)
regras = {r["variavel"]: r for r in df_dic.collect()}
display(df_dic.groupBy("categoria", "acao_recomendada").count().orderBy(F.desc("count")))

# COMMAND ----------

# MAGIC %md ## 2. Tabela de-para de times (T3)
# MAGIC O de-para é manual e fica versionado aqui no código: nome padronizado, nome curto, sigla e UF. Se chegar
# MAGIC algum time da fonte que não esteja na lista, a regra `time_nao_mapeado` barra a linha.

# COMMAND ----------

# ================================================================================
# DE-PARA DE TIMES
# ================================================================================

DE_PARA_TIMES = [
    # (nome na fonte,          nome padronizado,     nome curto,     sigla, UF)
    ("Atlético Mineiro",       "Atlético Mineiro",   "Atlético-MG",  "CAM", "MG"),
    ("Bahia",                  "Bahia",              "Bahia",        "BAH", "BA"),
    ("Botafogo",               "Botafogo",           "Botafogo",     "BOT", "RJ"),
    ("Ceará",                  "Ceará",              "Ceará",        "CEA", "CE"),
    ("Corinthians",            "Corinthians",        "Corinthians",  "COR", "SP"),
    ("Cruzeiro",               "Cruzeiro",           "Cruzeiro",     "CRU", "MG"),
    ("EC Juventude",           "Juventude",          "Juventude",    "JUV", "RS"),
    ("EC Vitória",             "Vitória",            "Vitória",      "VIT", "BA"),
    ("Flamengo",               "Flamengo",           "Flamengo",     "FLA", "RJ"),
    ("Fluminense",             "Fluminense",         "Fluminense",   "FLU", "RJ"),
    ("Fortaleza",              "Fortaleza",          "Fortaleza",    "FOR", "CE"),
    ("Grêmio",                 "Grêmio",             "Grêmio",       "GRE", "RS"),
    ("Internacional",          "Internacional",      "Internacional", "INT", "RS"),
    ("Mirassol Futebol Clube", "Mirassol",           "Mirassol",     "MIR", "SP"),
    ("Palmeiras",              "Palmeiras",          "Palmeiras",    "PAL", "SP"),
    ("Red Bull Bragantino",    "Red Bull Bragantino", "Bragantino",  "RBB", "SP"),
    ("Santos",                 "Santos",             "Santos",       "SAN", "SP"),
    ("Sc Do Recife",           "Sport Recife",       "Sport",        "SPT", "PE"),
    ("São Paulo",              "São Paulo",          "São Paulo",    "SAO", "SP"),
    ("Vasco da Gama",          "Vasco da Gama",      "Vasco",        "VAS", "RJ"),
]
df_de_para = spark.createDataFrame(
    DE_PARA_TIMES, "nome_fonte STRING, nome_time STRING, nome_curto STRING, sigla STRING, uf STRING")
salvar_tabela(df_de_para, T_SILVER_TIME_DE_PARA,
              "Silver: de-para manual dos nomes de times da fonte StatsBomb para nomes padronizados + sigla e UF.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2b. Classificação oficial (referência para reconciliação)
# MAGIC A StatsBomb não traz o placar das partidas. O placar é derivado somando os gols dos jogadores, só que gol
# MAGIC contra não é creditado a nenhum jogador do time que se beneficiou. Pra medir (e corrigir) essa diferença,
# MAGIC carrego a classificação final oficial como tabela de referência. Fonte: CBF, compilada na Wikipédia
# MAGIC ("2025 Campeonato Brasileiro Série A"), consultada em 25/09/2026. Ela é usada no notebook de Qualidade,
# MAGIC na reconciliação, e para mostrar os pontos oficiais no mart de classificação.

# COMMAND ----------

# ================================================================================
# CLASSIFICAÇÃO OFICIAL
# ================================================================================

CLASSIFICACAO_OFICIAL = [
    # (nome_time, posicao, pontos, V, E, D, gols_pro, gols_contra)
    ("Flamengo", 1, 79, 23, 10, 5, 78, 27), ("Palmeiras", 2, 76, 23, 7, 8, 66, 33),
    ("Cruzeiro", 3, 70, 19, 13, 6, 55, 31), ("Mirassol", 4, 67, 18, 13, 7, 63, 39),
    ("Fluminense", 5, 64, 19, 7, 12, 50, 39), ("Botafogo", 6, 63, 17, 12, 9, 58, 38),
    ("Bahia", 7, 60, 17, 9, 12, 50, 47), ("São Paulo", 8, 51, 14, 9, 15, 43, 47),
    ("Grêmio", 9, 49, 13, 10, 15, 47, 50), ("Red Bull Bragantino", 10, 48, 14, 6, 18, 45, 57),
    ("Atlético Mineiro", 11, 48, 12, 12, 14, 43, 44), ("Santos", 12, 47, 12, 11, 15, 45, 50),
    ("Corinthians", 13, 47, 12, 11, 15, 42, 47), ("Vasco da Gama", 14, 45, 13, 6, 19, 55, 60),
    ("Vitória", 15, 45, 11, 12, 15, 35, 52), ("Internacional", 16, 44, 11, 11, 16, 44, 57),
    ("Ceará", 17, 43, 11, 10, 17, 34, 40), ("Fortaleza", 18, 43, 11, 10, 17, 44, 58),
    ("Juventude", 19, 35, 9, 8, 21, 35, 69), ("Sport Recife", 20, 17, 2, 11, 25, 28, 75),
]
df_oficial = spark.createDataFrame(
    CLASSIFICACAO_OFICIAL,
    "nome_time STRING, posicao INT, pontos INT, vitorias INT, empates INT, derrotas INT, gols_pro INT, gols_contra INT")
salvar_tabela(df_oficial, T_SILVER_CLASS_OFICIAL,
              "Silver: classificação final oficial do Brasileirão 2025 (CBF via Wikipédia, consultada em 25/09/2026): referência de reconciliação.")

# COMMAND ----------

# MAGIC %md ## 3. Tipagem (T1)
# MAGIC Os tipos saem do dicionário, seguindo essa regra:
# MAGIC - identificadores viram `BIGINT` e nomes ficam `STRING` (com `trim`);
# MAGIC - variáveis com ação `Preencher com 0` (contagens de ação) viram `INT`, menos as de OBV, que são valor contínuo e ficam `DOUBLE`;
# MAGIC - todo o resto (xG, razões, durações, métricas 360, goleiro) vira `DOUBLE`.
# MAGIC
# MAGIC O `try_cast` passa por `DOUBLE` primeiro porque, em alguns casos, a fonte grava contagem como `"3.0"`.

# COMMAND ----------

# ================================================================================
# TIPAGEM (T1)
# ================================================================================

bronze = spark.table(T_BRONZE_ESTAT)

# ── Grupos de colunas ───────────────────────────────────────────────────────────

COLS_ID = ["account_id", "match_id", "team_id", "player_id"]
COLS_TEXTO = ["team_name", "player_name"]
COLS_METADADOS = ["_arquivo_origem", "_data_ingestao", "_id_carga"]
COLS_METRICAS = [c for c in bronze.columns if c.startswith("player_match_")]

# toda métrica precisa ter regra no dicionário, senão não tem como decidir o tipo
faltando_no_dic = set(COLS_METRICAS) - set(regras)
assert not faltando_no_dic, f"Colunas sem regra no dicionário: {faltando_no_dic}"

# contagem -> INT, só que OBV é contínuo mesmo com "Preencher com 0"
COLS_INT = [c for c in COLS_METRICAS
            if regras[c]["acao_recomendada"] == "Preencher com 0" and "obv" not in c]
COLS_DOUBLE = [c for c in COLS_METRICAS if c not in COLS_INT]
print(f"[INFO] INT: {len(COLS_INT)} | DOUBLE: {len(COLS_DOUBLE)} | ID: {len(COLS_ID)} | STRING: {len(COLS_TEXTO)}")

# ── Conversão ───────────────────────────────────────────────────────────────────

exprs = (
    [F.expr(f"try_cast(try_cast({c} AS DOUBLE) AS BIGINT)").alias(c) for c in COLS_ID]
    + [F.trim(F.col(c)).alias(c) for c in COLS_TEXTO]
    + [F.expr(f"try_cast(try_cast({c} AS DOUBLE) AS INT)").alias(c) for c in COLS_INT]
    + [F.expr(f"try_cast({c} AS DOUBLE)").alias(c) for c in COLS_DOUBLE]
    + [F.col(c) for c in COLS_METADADOS]
)
df = bronze.select(*exprs)

# ── Auditoria da tipagem ────────────────────────────────────────────────────────

# se estava preenchido na Bronze e virou NULL, é falha de conversão
exprs_falha = []
for c in COLS_ID + COLS_INT + COLS_DOUBLE:
    falhou = F.col(c).isNotNull() & F.expr(f"try_cast({c} AS DOUBLE)").isNull()
    exprs_falha.append(F.sum(F.when(falhou, 1).otherwise(0)).alias(c))

falhas_tipagem = bronze.select(exprs_falha).collect()[0].asDict()
falhas_tipagem = {k: v for k, v in falhas_tipagem.items() if v}  # só as colunas que tiveram falha
print("[INFO] Falhas de conversão de tipo:", falhas_tipagem or "nenhuma")

# COMMAND ----------

# MAGIC %md ## 4. Tratamento de missing (T2)

# COMMAND ----------

# ================================================================================
# TRATAMENTO DE MISSING (T2)
# ================================================================================

COLS_FILL_ZERO = [c for c in COLS_METRICAS if regras[c]["acao_recomendada"] == "Preencher com 0"]
# conta os nulos antes de preencher, pra ter o registro do que foi alterado
nulos_antes = df.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in COLS_FILL_ZERO]).collect()[0].asDict()
print(f"[INFO] {len(COLS_FILL_ZERO)} colunas 'Preencher com 0' | nulos preenchidos: {sum(nulos_antes.values()):,}")
print("[INFO] Top colunas preenchidas:", sorted(((v, k) for k, v in nulos_antes.items() if v), reverse=True)[:8])

df = df.fillna(0, subset=COLS_FILL_ZERO)
# 'Manter NA' (condicionais), 'Específica de posição' (goleiro) e 'VERIFICAR COBERTURA 360' continuam NULL,
# porque aqui o NULL quer dizer alguma coisa: "não houve finalização", "não é goleiro", "partida sem cobertura 360"

# COMMAND ----------

# MAGIC %md ## 5. Padronização de times (T3) e flags derivadas (T4)

# COMMAND ----------

# ================================================================================
# PADRONIZAÇÃO DE TIMES (T3)
# ================================================================================

# guarda o nome original em team_name_fonte e traz o nome padronizado do de-para
df = (df.withColumnRenamed("team_name", "team_name_fonte")
        .join(F.broadcast(spark.table(T_SILVER_TIME_DE_PARA)
                          .select(F.col("nome_fonte").alias("team_name_fonte"),
                                  F.col("nome_time").alias("team_name"))),
              on="team_name_fonte", how="left"))

# ================================================================================
# FLAGS DERIVADAS (T4)
# ================================================================================

# obv_gk só vem preenchido pra quem jogou no gol pelo menos uma vez, então serve pra marcar goleiro
goleiros = (df.filter(F.col("player_match_obv_gk").isNotNull())
              .select("player_id").distinct().withColumn("is_goleiro", F.lit(True)))
df = (df.join(F.broadcast(goleiros), "player_id", "left")
        .withColumn("is_goleiro", F.coalesce("is_goleiro", F.lit(False)))
        # partida com minutos de 360 > 0 tem cobertura; NULL conta como sem cobertura
        .withColumn("tem_cobertura_360", F.coalesce(F.col("player_match_360_minutes") > 0, F.lit(False))))
print("[INFO] Goleiros identificados:", goleiros.count())

# COMMAND ----------

# MAGIC %md ## 6. Deduplicação (T5)

# COMMAND ----------

# ================================================================================
# DEDUPLICAÇÃO (T5)
# ================================================================================

# se tiver mais de uma linha pro mesmo jogador na mesma partida, fica a ingestão mais recente
w = Window.partitionBy("match_id", "player_id").orderBy(F.col("_data_ingestao").desc())
antes = df.count()
df = df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")
print(f"[INFO] Duplicatas removidas por (match_id, player_id): {antes - df.count()}")

# COMMAND ----------

# MAGIC %md ## 7. Regras de qualidade e quarentena (T6)
# MAGIC Cada regra é uma expressão que tem que dar verdadeiro. Se a linha viola qualquer uma, ela vai para
# MAGIC `silver.jogador_partida_quarentena` junto com a lista de motivos. O que passa em todas segue para a Silver.

# COMMAND ----------

# ================================================================================
# REGRAS DE QUALIDADE (T6)
# ================================================================================

# gsaa_ratio fica de fora, ela não é limitada ao intervalo 0-1
RATIOS_0_1 = [c for c in COLS_METRICAS if c.endswith("_ratio") and c != "player_match_gsaa_ratio"]
REGRAS_QUALIDADE = {
    "id_nulo": "match_id IS NOT NULL AND player_id IS NOT NULL AND team_id IS NOT NULL",
    "time_nao_mapeado": "team_name IS NOT NULL",
    "minutos_invalidos": f"player_match_minutes IS NOT NULL AND player_match_minutes > 0 AND player_match_minutes <= {MAX_MINUTOS_PARTIDA}",
    "razao_fora_0_1": " AND ".join(f"({c} IS NULL OR {c} BETWEEN 0 AND 1)" for c in RATIOS_0_1),
    "posse_fora_0_1": "player_match_possession IS NULL OR player_match_possession BETWEEN 0 AND 1",
    "passes_certos_gt_total": "player_match_successful_passes <= player_match_passes",
    "bolas_longas_certas_gt_total": "player_match_successful_long_balls <= player_match_long_balls",
    "aereos_vencidos_gt_total": "player_match_successful_aerials <= player_match_aerials",
    "cruzamentos_certos_gt_total": "player_match_successful_crosses <= player_match_crosses",
    "gols_sem_penalti_gt_gols": "player_match_np_goals <= player_match_goals",
    "chutes_no_alvo_gt_chutes": "player_match_np_shots_on_target <= player_match_np_shots",
    "valor_negativo_em_contagem": " AND ".join(f"{c} >= 0" for c in COLS_INT),
}

# ── Montagem dos motivos ────────────────────────────────────────────────────────

# pra cada regra: se a expressão der False (ou NULL, que conta como reprovada), marca o nome da regra;
# se passar, o when sem otherwise devolve NULL
marcacoes = []
for nome_regra, expr_regra in REGRAS_QUALIDADE.items():
    regra_ok = F.coalesce(F.expr(expr_regra), F.lit(False))
    marcacoes.append(F.when(~regra_ok, F.lit(nome_regra)))

# junta tudo num array e tira os NULL, sobra só a lista de regras violadas
motivos = F.filter(F.array(*marcacoes), lambda x: x.isNotNull())
df = df.withColumn("_motivos_quarentena", motivos)

# ── Separação Silver x quarentena ───────────────────────────────────────────────

df_quarentena = df.filter(F.size("_motivos_quarentena") > 0).withColumn("_data_processamento", F.current_timestamp())
df_silver = (df.filter(F.size("_motivos_quarentena") == 0).drop("_motivos_quarentena")
               .withColumn("_data_processamento", F.current_timestamp()))

resumo = (df_quarentena.select(F.explode("_motivos_quarentena").alias("regra")).groupBy("regra").count())
print("[INFO] Linhas em quarentena:", df_quarentena.count())
display(resumo)

# COMMAND ----------

# MAGIC %md ## 8. Persistência

# COMMAND ----------

# ================================================================================
# PERSISTÊNCIA
# ================================================================================

# ordem final das colunas: chaves, descritivos, flags, métricas e metadados
ordem = (["match_id", "team_id", "player_id", "account_id", "team_name", "team_name_fonte", "player_name",
          "is_goleiro", "tem_cobertura_360"] + COLS_METRICAS + ["_arquivo_origem", "_data_ingestao", "_id_carga",
                                                                "_data_processamento"])
salvar_tabela(df_silver.select(*ordem), T_SILVER_ESTAT,
              "Silver: estatísticas StatsBomb por jogador x partida: tipadas, missing tratado conforme dicionário, "
              "times padronizados, flags de goleiro/cobertura 360, deduplicadas e aprovadas nas regras de qualidade.")
# quarentena usa a mesma ordem (sem _data_processamento) e acrescenta os motivos
salvar_tabela(df_quarentena.select(*ordem[:-1], "_motivos_quarentena", "_data_processamento"), T_SILVER_QUARENTENA,
              "Silver: registros reprovados em ao menos uma regra de qualidade, com a lista de motivos.")

# COMMAND ----------

# conferência do de-para: nome padronizado x nome da fonte
display(spark.sql(f"""
SELECT team_name, team_name_fonte, COUNT(DISTINCT player_id) AS jogadores, COUNT(DISTINCT match_id) AS partidas
FROM {T_SILVER_ESTAT} GROUP BY ALL ORDER BY team_name"""))
