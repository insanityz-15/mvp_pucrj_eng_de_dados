"""Executa os notebooks Databricks (formato source .py) localmente com PySpark, para validar a lógica do pipeline.

Não faz parte do pipeline de produção: é um teste de fumaça. Diferenças em relação ao Databricks:
- catálogo `spark_catalog` (metastore Hive local) no lugar do Unity Catalog;
- formato parquet (Delta não disponível offline); comandos exclusivos do UC/Delta são ignorados
  (CREATE CATALOG/VOLUME, PRIMARY/FOREIGN KEY, CHECK, SET NOT NULL).

Uso: python tests/run_local.py <pasta_com_os_csv> [notebook ...]
"""
import re
import sys
import tempfile
import time
from pathlib import Path

from pyspark.sql import SparkSession

RAIZ = Path(__file__).resolve().parents[1] / "notebooks"
LANDING = sys.argv[1]
SELECAO = sys.argv[2:] or ["01_setup_ambiente", "02_bronze_ingestao", "03_silver_transformacao", "04_gold_modelagem",
                           "05_qualidade_dados", "06_catalogo_dados", "07_analise_perguntas"]
IGNORAR = re.compile(r"CREATE CATALOG|CREATE VOLUME|COMMENT ON CATALOG|USE CATALOG|PRIMARY KEY|FOREIGN KEY|"
                     r"ADD CONSTRAINT|DROP CONSTRAINT|SET NOT NULL", re.I)

spark_real = (SparkSession.builder.master("local[4]").appName("mvp-local")
              .config("spark.sql.warehouse.dir", str(Path(tempfile.gettempdir()) / "mvp_wh"))
              .config("spark.sql.shuffle.partitions", "8")
              .config("spark.ui.enabled", "false").config("spark.ui.showConsoleProgress", "false")
              .enableHiveSupport().getOrCreate())
spark_real.sparkContext.setLogLevel("ERROR")


class SparkProxy:
    def __getattr__(self, k):
        return getattr(spark_real, k)

    def sql(self, q, *a, **kw):
        if IGNORAR.search(q):
            return spark_real.createDataFrame([], "x INT")
        return spark_real.sql(q, *a, **kw)


class Widgets:
    vals = {"catalogo": "spark_catalog"}

    def text(self, nome, default, *_):
        self.vals.setdefault(nome, default)

    def get(self, nome):
        return self.vals[nome]


class DBUtils:
    widgets = Widgets()

    class fs:
        @staticmethod
        def mkdirs(p):
            pass

        @staticmethod
        def ls(p):
            class F:
                def __init__(s, n): s.name = n
            return [F(x.name) for x in Path(LANDING).iterdir()]


SAIDAS = []


def display(df, n=40):
    if hasattr(df, "toPandas"):
        pdf = df.limit(n).toPandas()
        txt = pdf.to_string(max_colwidth=60)
    else:
        txt = str(df)
    SAIDAS.append(txt)
    print(txt)


def executar(nome, ns):
    src = (RAIZ / f"{nome}.py").read_text(encoding="utf-8")
    for i, cel in enumerate(src.split("# COMMAND ----------")):
        linhas = [l for l in cel.strip().splitlines() if l.strip() != "# Databricks notebook source"]
        if not linhas:
            continue
        if linhas[0].startswith("# MAGIC"):
            corpo = "\n".join(re.sub(r"^# MAGIC ?", "", l) for l in linhas)
            if corpo.startswith("%md"):
                continue
            if corpo.startswith("%run"):
                executar(corpo.split("./")[1].strip(), ns)
                continue
            if corpo.startswith("%sql"):
                sql = corpo[4:].strip()
                print(f"\n--- [{nome} cel {i}] SQL")
                display(ns["spark"].sql(sql))
                continue
        code = "\n".join(linhas)
        exec(compile(code, f"{nome}[cel{i}]", "exec"), ns)
        if nome == "00_config":  # overrides locais
            ns["TABLE_FORMAT"] = "parquet"
            ns["LANDING_PATH"] = LANDING


for nb in SELECAO:
    ns = {"spark": SparkProxy(), "dbutils": DBUtils(), "display": display}
    t0 = time.time()
    print(f"\n==================== {nb} ====================")
    executar(nb, ns)
    print(f"==== {nb} OK em {time.time() - t0:.1f}s")
