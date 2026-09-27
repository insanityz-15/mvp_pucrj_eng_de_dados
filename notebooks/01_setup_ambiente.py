# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Setup do ambiente (Unity Catalog)
# MAGIC
# MAGIC Aqui é criada a estrutura do Lakehouse. É idempotente, então pode rodar quantas vezes precisar.
# MAGIC
# MAGIC | Objeto | Nome | Papel |
# MAGIC |---|---|---|
# MAGIC | Catálogo | `mvp_brasileirao` | Isola o projeto do restante do workspace |
# MAGIC | Schema | `bronze` | Dado exatamente como chegou da fonte, mais os metadados de ingestão |
# MAGIC | Volume | `bronze.landing` | Área de pouso dos arquivos brutos (CSV) |
# MAGIC | Schema | `silver` | Dado tipado, padronizado, com missing tratado e regras de qualidade |
# MAGIC | Schema | `gold` | Modelo dimensional (esquema estrela) e marts para as perguntas de negócio |
# MAGIC | Schema | `governanca` | Resultados de qualidade de dados e catálogo de dados consultável |
# MAGIC
# MAGIC > **Free Edition:** se a conta não deixar rodar `CREATE CATALOG`, é só mudar o widget `catalogo` para
# MAGIC > `workspace` (catálogo padrão). O resto funciona igual.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# ================================================================================
# CATÁLOGO
# ================================================================================

try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
    spark.sql(f"COMMENT ON CATALOG {CATALOG} IS 'MVP Engenharia de Dados PUC-Rio: Lakehouse de desempenho de jogadores do Brasileirão {TEMPORADA} (StatsBomb)'")
except Exception as e:  # a Free Edition pode bloquear a criação de catálogo
    raise RuntimeError(
        f"Não foi possível criar o catálogo '{CATALOG}'. Re-execute com o widget catalogo=workspace.\n{e}"
    )

# ================================================================================
# SCHEMAS E VOLUME
# ================================================================================

# uma entrada por camada, o texto vira o COMMENT do schema
schemas = {
    SCHEMA_BRONZE: "Camada Bronze: dados brutos da StatsBomb, sem alteração de conteúdo, + metadados de ingestão",
    SCHEMA_SILVER: "Camada Silver: dados tipados, padronizados, deduplicados, com missing tratado conforme dicionário",
    SCHEMA_GOLD: "Camada Gold: esquema estrela (dimensões/fatos) e marts analíticos prontos para consumo",
    SCHEMA_GOV: "Governança: resultados de checagens de qualidade e catálogo de dados",
}
for schema, comentario in schemas.items():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{schema} COMMENT '{comentario}'")
    print(f"[OK] schema {CATALOG}.{schema}")

# volume onde vão os CSVs brutos
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA_BRONZE}.{VOLUME_LANDING} "
          f"COMMENT 'Área de pouso dos arquivos brutos (CSV StatsBomb e dicionário de dados)'")
print(f"[OK] volume {CATALOG}.{SCHEMA_BRONZE}.{VOLUME_LANDING}")

# COMMAND ----------

# cria a pasta de destino dentro do volume (se já existir, não faz nada)
dbutils.fs.mkdirs(LANDING_PATH)
print(f"[INFO] Faça o upload dos dois CSVs para: {LANDING_PATH}")
display(dbutils.fs.ls(LANDING_PATH))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload dos arquivos brutos
# MAGIC
# MAGIC Esse passo é manual, só precisa fazer uma vez:
# MAGIC
# MAGIC 1. No menu **Catalog**, entra em `mvp_brasileirao` > `bronze` > **Volumes** > `landing`.
# MAGIC 2. Navega até `statsbomb/brasileirao_2025/` e clica em **Upload to this volume**.
# MAGIC 3. Sobe os dois arquivos: `estatisticas_jogadores_partida_brasileirao2025.csv` e `dicionario_dados.csv`.
# MAGIC 4. Roda a célula abaixo pra confirmar que chegaram.
# MAGIC
# MAGIC Se preferir pela CLI: `databricks fs cp ./data/*.csv dbfs:/Volumes/mvp_brasileirao/bronze/landing/statsbomb/brasileirao_2025/`

# COMMAND ----------

# ── Conferência dos arquivos no volume ──────────────────────────────────────────

arquivos = {f.name for f in dbutils.fs.ls(LANDING_PATH)}
faltando = {ARQUIVO_ESTATISTICAS, ARQUIVO_DICIONARIO} - arquivos
assert not faltando, f"Arquivos ausentes no volume: {faltando}"
print("[OK] Arquivos brutos presentes no volume:", sorted(arquivos))
