# Databricks notebook source
# MAGIC %md
# MAGIC # 99 - Orquestrador do pipeline
# MAGIC Roda o pipeline inteiro, na ordem das dependências, dentro da mesma sessão (via `%run`):
# MAGIC
# MAGIC `01_setup` > `02_bronze` > `03_silver` > `04_gold` > `05_qualidade` > `06_catalogo` > `07_analise`
# MAGIC
# MAGIC > **Decisão de projeto:** usei `%run` no lugar de `dbutils.notebook.run` porque o Databricks Free Edition
# MAGIC > só permite 1 execução ativa por vez. O `dbutils.notebook.run` abre execuções-filhas, que ficam esperando
# MAGIC > para sempre a execução-pai terminar. Com `%run` tudo roda no mesmo contexto. Se quiser tarefas com
# MAGIC > dependência explícita, tem o Job `jobs/job_pipeline_mvp.yml` (Lakeflow Jobs), onde cada tarefa roda em sequência.

# COMMAND ----------

# ================================================================================
# PARÂMETROS
# ================================================================================

dbutils.widgets.text("catalogo", "mvp_brasileirao", "Catálogo Unity Catalog")
import time
T0 = time.time()  # marca o início pra mostrar o tempo acumulado a cada etapa

# COMMAND ----------

# MAGIC %run ./01_setup_ambiente

# COMMAND ----------

print(f"[OK] 01_setup_ambiente concluído ({time.time() - T0:.0f}s acumulados)")

# COMMAND ----------

# MAGIC %run ./02_bronze_ingestao

# COMMAND ----------

print(f"[OK] 02_bronze_ingestao concluído ({time.time() - T0:.0f}s acumulados)")

# COMMAND ----------

# MAGIC %run ./03_silver_transformacao

# COMMAND ----------

print(f"[OK] 03_silver_transformacao concluído ({time.time() - T0:.0f}s acumulados)")

# COMMAND ----------

# MAGIC %run ./04_gold_modelagem

# COMMAND ----------

print(f"[OK] 04_gold_modelagem concluído ({time.time() - T0:.0f}s acumulados)")

# COMMAND ----------

# MAGIC %run ./05_qualidade_dados

# COMMAND ----------

print(f"[OK] 05_qualidade_dados concluído ({time.time() - T0:.0f}s acumulados)")

# COMMAND ----------

# MAGIC %run ./06_catalogo_dados

# COMMAND ----------

print(f"[OK] 06_catalogo_dados concluído ({time.time() - T0:.0f}s acumulados)")

# COMMAND ----------

# MAGIC %run ./07_analise_perguntas

# COMMAND ----------

print(f"[OK] Pipeline completo em {time.time() - T0:.0f}s")
