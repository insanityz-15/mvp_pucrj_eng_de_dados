# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Bronze: ingestão dos dados brutos
# MAGIC
# MAGIC Aqui os arquivos saem do volume de landing e viram tabelas Delta, sem alterar o conteúdo.
# MAGIC
# MAGIC Algumas decisões que valem explicar:
# MAGIC - Todas as colunas são lidas como `STRING` (`inferSchema=false`). Quem tipa é a Silver. Na Bronze a gente
# MAGIC   quer guardar a evidência: se a fonte mandar `"1,5"` ou `"N/A"`, isso fica registrado do jeito que veio.
# MAGIC - Entram metadados de controle: `_arquivo_origem`, `_data_modificacao_arquivo`, `_data_ingestao`,
# MAGIC   `_id_carga` e `_fonte`.
# MAGIC - A carga é completa (overwrite). A temporada 2025 já fechou, então rodar de novo dá sempre o mesmo resultado.
# MAGIC - No dicionário de dados, a única mudança é renomear os cabeçalhos para snake_case sem acento, porque o
# MAGIC   Delta não aceita espaço e parênteses em nome de coluna sem *column mapping*. O conteúdo fica intacto.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# ================================================================================
# LEITURA DOS ARQUIVOS BRUTOS
# ================================================================================

# mesmo id para as duas tabelas desta execução
ID_CARGA = novo_id_carga()
print("[INFO] id_carga:", ID_CARGA)


def ler_csv_bruto(caminho: str) -> DataFrame:
    """
    Lê um CSV da landing mantendo tudo como texto e adiciona os metadados de ingestão.

    Os dados do arquivo (caminho e data de modificação) vêm da coluna oculta _metadata do Spark.

    Args:
        caminho: Caminho completo do CSV dentro do volume

    Returns:
        DataFrame: Colunas originais como STRING mais _arquivo_origem, _data_modificacao_arquivo,
            _data_ingestao, _id_carga e _fonte
    """
    return (spark.read
            .option("header", "true")
            .option("inferSchema", "false")   # tudo STRING na Bronze
            .option("encoding", "UTF-8")
            .option("mode", "PERMISSIVE")     # não descarta linhas malformadas
            .csv(caminho)
            .select("*",
                    F.col("_metadata.file_path").alias("_arquivo_origem"),
                    F.col("_metadata.file_modification_time").alias("_data_modificacao_arquivo"))
            .withColumn("_data_ingestao", F.current_timestamp())
            .withColumn("_id_carga", F.lit(ID_CARGA))
            .withColumn("_fonte", F.lit("StatsBomb IQ — export por jogador/partida (licença corporativa)")))

# COMMAND ----------

# MAGIC %md ## 1. Estatísticas por jogador x partida

# COMMAND ----------

# ── Estatísticas ────────────────────────────────────────────────────────────────

df_estat_raw = ler_csv_bruto(f"{LANDING_PATH}/{ARQUIVO_ESTATISTICAS}")
# desconta as 5 colunas de metadados que a ler_csv_bruto adiciona
print(f"[INFO] Colunas de negócio: {len(df_estat_raw.columns) - 5} | Linhas: {df_estat_raw.count():,}")

salvar_tabela(
    df_estat_raw, T_BRONZE_ESTAT,
    "Bronze: estatísticas StatsBomb por jogador x partida do Brasileirão Série A 2025, exatamente como exportadas "
    "(todas as colunas STRING) + metadados de ingestão. Grão: 1 linha por jogador por partida.",
)

# COMMAND ----------

# MAGIC %md ## 2. Dicionário de dados (feito no MVP anterior, de ML & Analytics)

# COMMAND ----------

# ── Dicionário ──────────────────────────────────────────────────────────────────

# cabeçalho original do CSV -> nome aceito pelo Delta
RENOMEAR_DIC = {
    "Variável": "variavel",
    "Categoria": "categoria",
    "Tratamento Missing": "tratamento_missing",
    "Justificativa": "justificativa",
    "Ação Recomendada (revisão)": "acao_recomendada",
    "Nota de Revisão": "nota_revisao",
}

df_dic_raw = ler_csv_bruto(f"{LANDING_PATH}/{ARQUIVO_DICIONARIO}")
for antigo, novo in RENOMEAR_DIC.items():
    df_dic_raw = df_dic_raw.withColumnRenamed(antigo, novo)

salvar_tabela(
    df_dic_raw, T_BRONZE_DIC,
    "Bronze: dicionário de dados das 167 variáveis StatsBomb com regra de tratamento de missing por variável "
    "(artefato do MVP de ML). Cabeçalhos convertidos para snake_case; conteúdo intacto.",
)

# COMMAND ----------

# ================================================================================
# CONFERÊNCIA ORIGEM X BRONZE
# ================================================================================

# evidência de que tudo chegou: volume de linhas, partidas, jogadores e times
display(spark.sql(f"""
  SELECT '{T_BRONZE_ESTAT}' AS tabela, COUNT(*) AS linhas, COUNT(DISTINCT match_id) AS partidas,
         COUNT(DISTINCT player_id) AS jogadores, COUNT(DISTINCT team_id) AS times,
         MIN(_data_ingestao) AS ingestao
  FROM {T_BRONZE_ESTAT}
  UNION ALL
  SELECT '{T_BRONZE_DIC}', COUNT(*), NULL, NULL, NULL, MIN(_data_ingestao) FROM {T_BRONZE_DIC}
"""))
