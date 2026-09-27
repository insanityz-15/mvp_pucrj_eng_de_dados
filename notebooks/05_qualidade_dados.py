# Databricks notebook source
# MAGIC %md
# MAGIC # 05 Qualidade de dados
# MAGIC
# MAGIC Checagens nas 5 dimensões pedidas no MVP: completude, consistência, unicidade, acurácia e outliers, rodando
# MAGIC sobre Bronze, Silver e Gold. Todo resultado vai para `governanca.dq_resultados` com histórico por `id_execucao`,
# MAGIC então dá para acompanhar a base a cada carga nova.
# MAGIC
# MAGIC Sobre o `status`:
# MAGIC - **OK**: nenhuma falha;
# MAGIC - **ALERTA**: falha esperada ou já tratada no pipeline;
# MAGIC - **ERRO**: falha não tratada. Se aparecer algum, o notebook quebra no final.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# ================================================================================
# SETUP DA EXECUÇÃO
# ================================================================================

ID_EXEC = novo_id_carga()
resultados = []  # cada checagem vira um dict aqui, gravado tudo de uma vez no final


def registrar(camada, tabela, dimensao, regra, avaliados, falhas, tratamento="", severidade_se_falha="ERRO", coluna=None):
    """
    Registra o resultado de uma checagem de qualidade na lista `resultados`.

    Args:
        camada: Camada da tabela avaliada (bronze, silver ou gold)
        tabela: Nome completo da tabela (só o último trecho é gravado)
        dimensao: Dimensão de qualidade (Completude, Unicidade, Consistência, Acurácia, Outliers)
        regra: Descrição da regra checada
        avaliados: Quantidade de registros avaliados
        falhas: Quantidade de registros que falharam na regra
        tratamento: O que o pipeline faz com a falha, se fizer algo
        severidade_se_falha: Status quando há falha (ERRO ou ALERTA)
        coluna: Coluna avaliada, quando a regra é de uma coluna só

    Returns:
        None: o resultado é adicionado em `resultados`
    """
    falhas = int(falhas or 0)
    avaliados = int(avaliados or 0)
    resultados.append({
        "id_execucao": ID_EXEC,
        "camada": camada,
        "tabela": tabela.split(".")[-1],
        "coluna": coluna,
        "dimensao": dimensao,
        "regra": regra,
        "registros_avaliados": avaliados,
        "registros_com_falha": falhas,
        "pct_falha": round(falhas / avaliados, 6) if avaliados else 0.0,
        "status": "OK" if falhas == 0 else severidade_se_falha,
        "tratamento": tratamento,
    })


# ── Tabelas e contagens usadas em várias checagens ─────────────────────────────
bronze = spark.table(T_BRONZE_ESTAT)
silver = spark.table(T_SILVER_ESTAT)
dic = {r["variavel"]: r.asDict() for r in spark.table(T_SILVER_DIC).collect()}  # dicionário indexado pela variável
n_bronze, n_silver = bronze.count(), silver.count()
n_quar = spark.table(T_SILVER_QUARENTENA).count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Completude
# MAGIC
# MAGIC Conto os nulos por coluna **na Bronze**, que é o dado original, e cruzo com a regra do dicionário:
# MAGIC - coluna `Preencher com 0`: o nulo foi tratado na Silver, fica ALERTA;
# MAGIC - coluna `Manter NA`, de goleiro ou 360: o nulo é estrutural, também ALERTA (informativo);
# MAGIC - nulo em identificador ou minutos é ERRO.

# COMMAND ----------

# ================================================================================
# COMPLETUDE
# ================================================================================

# ── Nulos por coluna na Bronze ──────────────────────────────────────────────────
cols_neg = [c for c in bronze.columns if not c.startswith("_")]  # ignora colunas técnicas (_id_carga etc.)
nulos = bronze.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in cols_neg]).first().asDict()

# ação recomendada no dicionário -> tratamento aplicado no pipeline
TRAT = {
    "Preencher com 0": "Preenchido com 0 na Silver (contagem de ação não ocorrida)",
    "Manter NA": "Mantido NULL: métrica condicionada a evento (ex.: xG sem finalização)",
    "Manter NA + criar flag de posição": "Mantido NULL + flag is_goleiro (métrica exclusiva de goleiro)",
    "VERIFICAR COBERTURA 360": "Mantido NULL + flag tem_cobertura_360; colunas fora da Gold",
    "VERIFICAR TIPO DE DADO": "Confirmado: razão 0-1 (posse do time); mantido DOUBLE",
}
for c, n in nulos.items():
    acao = dic.get(c, {}).get("acao_recomendada")
    # coluna sem ação conhecida no dicionário: nulo ali não era esperado
    sev = "ALERTA" if acao in TRAT else "ERRO"
    registrar("bronze", T_BRONZE_ESTAT, "Completude", "percentual de nulos", n_bronze, n, TRAT.get(acao, "Nenhum — investigar"), sev, c)

# ── Depois do tratamento ────────────────────────────────────────────────────────
# colunas 'Preencher com 0' não podem ter nenhum nulo na Silver
cols_fz = [c for c, r in dic.items() if r["acao_recomendada"] == "Preencher com 0"]
nulos_por_coluna = [F.col(c).isNull().cast("int") for c in cols_fz]
nulos_silver = silver.select(sum(nulos_por_coluna).alias("n")).first()["n"]  # soma linha a linha, depois total
registrar("silver", T_SILVER_ESTAT, "Completude", "colunas 'Preencher com 0' sem nulos após tratamento", n_silver, nulos_silver)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Unicidade
# MAGIC
# MAGIC Na Bronze duplicata é esperada (a Silver deduplica). Da Silver para frente, toda chave tem que ser única.

# COMMAND ----------

# ================================================================================
# UNICIDADE
# ================================================================================

def duplicatas(df, chaves):
    """Retorna quantas linhas sobram além da primeira ocorrência de cada chave."""
    return df.count() - df.dropDuplicates(chaves).count()


# ── Bronze e Silver ─────────────────────────────────────────────────────────────
registrar("bronze", T_BRONZE_ESTAT, "Unicidade", "chave (match_id, player_id) única", n_bronze,
          duplicatas(bronze, ["match_id", "player_id"]), "Deduplicação por row_number na Silver", "ALERTA")
registrar("bronze", T_BRONZE_ESTAT, "Unicidade", "linhas 100% idênticas", n_bronze, duplicatas(bronze, cols_neg),
          "Deduplicação na Silver", "ALERTA")
registrar("silver", T_SILVER_ESTAT, "Unicidade", "chave (match_id, player_id) única", n_silver, duplicatas(silver, ["match_id", "player_id"]))

# ── Gold: chave primária de cada tabela ─────────────────────────────────────────
CHAVES_GOLD = [
    (T_DIM_TIME, ["team_id"]),
    (T_DIM_JOGADOR, ["player_id"]),
    (T_DIM_PARTIDA, ["match_id"]),
    (T_FATO_JOG, ["match_id", "player_id"]),
    (T_FATO_TIME, ["match_id", "team_id"]),
    (T_MART_JOG, ["player_id"]),
    (T_MART_CLASS, ["team_id"]),
]
for t, k in CHAVES_GOLD:
    d = spark.table(t)
    registrar("gold", t, "Unicidade", f"chave primária ({', '.join(k)}) única", d.count(), duplicatas(d, k))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Consistência
# MAGIC
# MAGIC Nomes de time e jogador, estrutura das partidas e coerência da posse de bola.

# COMMAND ----------

# ================================================================================
# CONSISTÊNCIA
# ================================================================================

def q(sql):
    """Executa um SQL e retorna o primeiro valor da primeira linha (atalho para as contagens)."""
    return spark.sql(sql).first()[0]


# ── Nomes de time ───────────────────────────────────────────────────────────────
registrar("bronze", T_BRONZE_ESTAT, "Consistência", "nome de time fora do padrão (exige de-para)",
          q(f"SELECT COUNT(DISTINCT team_name) FROM {T_BRONZE_ESTAT}"),
          q(f"SELECT COUNT(*) FROM {T_SILVER_TIME_DE_PARA} WHERE nome_fonte <> nome_time"),
          "Padronizado via silver.time_de_para (ex.: 'Sc Do Recife' -> 'Sport Recife')", "ALERTA", "team_name")
registrar("silver", T_SILVER_ESTAT, "Consistência", "time sem mapeamento no de-para", n_silver,
          q(f"SELECT COUNT(*) FROM {T_SILVER_ESTAT} WHERE team_name IS NULL"), coluna="team_name")
registrar("bronze", T_BRONZE_ESTAT, "Consistência", "team_id com mais de um nome",
          q(f"SELECT COUNT(DISTINCT team_id) FROM {T_BRONZE_ESTAT}"),
          q(f"""
            SELECT COUNT(*)
            FROM (
                SELECT team_id
                FROM {T_BRONZE_ESTAT}
                GROUP BY team_id
                HAVING COUNT(DISTINCT team_name) > 1
            )
          """))

# ── Nomes de jogador ────────────────────────────────────────────────────────────
registrar("bronze", T_BRONZE_ESTAT, "Consistência", "player_id com mais de um nome",
          q(f"SELECT COUNT(DISTINCT player_id) FROM {T_BRONZE_ESTAT}"),
          q(f"""
            SELECT COUNT(*)
            FROM (
                SELECT player_id
                FROM {T_BRONZE_ESTAT}
                GROUP BY player_id
                HAVING COUNT(DISTINCT player_name) > 1
            )
          """))
registrar("bronze", T_BRONZE_ESTAT, "Consistência", "nome de jogador compartilhado por player_ids distintos (homônimos)",
          q(f"SELECT COUNT(DISTINCT player_name) FROM {T_BRONZE_ESTAT}"),
          q(f"""
            SELECT COUNT(*)
            FROM (
                SELECT player_name
                FROM {T_BRONZE_ESTAT}
                GROUP BY player_name
                HAVING COUNT(DISTINCT player_id) > 1
            )
          """),
          "player_id é a chave; dim_jogador.nome_exibicao acrescenta o clube", "ALERTA", "player_name")

# ── Estrutura da partida e posse ────────────────────────────────────────────────
registrar("silver", T_SILVER_ESTAT, "Consistência", "partida com exatamente 2 times",
          q(f"SELECT COUNT(DISTINCT match_id) FROM {T_SILVER_ESTAT}"),
          q(f"""
            SELECT COUNT(*)
            FROM (
                SELECT match_id
                FROM {T_SILVER_ESTAT}
                GROUP BY match_id
                HAVING COUNT(DISTINCT team_id) <> 2
            )
          """))
# posse vem repetida em cada jogador; aqui confiro se é a mesma para todo o time na partida
registrar("silver", T_SILVER_ESTAT, "Consistência", "posse idêntica para todos os jogadores do time na partida",
          q(f"SELECT COUNT(DISTINCT match_id, team_id) FROM {T_SILVER_ESTAT}"),
          q(f"""
            SELECT COUNT(*)
            FROM (
                SELECT match_id, team_id
                FROM {T_SILVER_ESTAT}
                GROUP BY ALL
                HAVING MAX(player_match_possession) - MIN(player_match_possession) > 0.001
            )
          """),
          "Posse é atributo do time; na Gold usa-se a média por time/partida", "ALERTA", "player_match_possession")
registrar("gold", T_FATO_TIME, "Consistência", "posse do time + posse do adversário = 100% (±1 p.p.)",
          q(f"SELECT COUNT(*) FROM {T_FATO_TIME}"),
          q(f"""
            SELECT COUNT(*)
            FROM {T_FATO_TIME} a
            JOIN {T_FATO_TIME} b
                ON a.match_id = b.match_id
                AND a.adversario_id = b.team_id
            WHERE ABS(a.posse + b.posse - 1) > 0.01
          """),
          "Informativo", "ALERTA", "posse")
registrar("silver", T_SILVER_ESTAT, "Consistência", "partidas do jogador com cobertura 360", n_silver,
          q(f"SELECT COUNT(*) FROM {T_SILVER_ESTAT} WHERE NOT tem_cobertura_360"),
          "Flag tem_cobertura_360; métricas 360 excluídas da Gold", "ALERTA", "player_match_360_minutes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Acurácia (regras de negócio e reconciliações)
# MAGIC
# MAGIC Aqui entram as regras de negócio da Silver e as reconciliações de número: linhas que entram e saem de cada
# MAGIC camada, gols batendo entre Bronze e Gold, e a classificação derivada comparada com a oficial da CBF.

# COMMAND ----------

# ================================================================================
# ACURÁCIA
# ================================================================================

# ── Silver: regras de negócio e reconciliação de linhas ─────────────────────────
registrar("silver", T_SILVER_QUARENTENA, "Acurácia", "linhas reprovadas nas regras de negócio da Silver (T6)", n_bronze, n_quar,
          "Enviadas para silver.jogador_partida_quarentena", "ALERTA")

# toda linha da Bronze tem que estar na Silver, na quarentena ou ter sido descartada como duplicata
n_dup_bronze = duplicatas(bronze, ["match_id", "player_id"])
diferenca_linhas = abs(n_bronze - n_dup_bronze - (n_silver + n_quar))
registrar("silver", T_SILVER_ESTAT, "Acurácia", "reconciliação bronze = silver + quarentena - duplicatas", n_bronze,
          diferenca_linhas)

registrar("silver", T_SILVER_ESTAT, "Acurácia", f"minutos entre 0 e {MAX_MINUTOS_PARTIDA}", n_silver,
          q(f"""
            SELECT COUNT(*)
            FROM {T_SILVER_ESTAT}
            WHERE player_match_minutes <= 0
               OR player_match_minutes > {MAX_MINUTOS_PARTIDA}
          """),
          coluna="player_match_minutes")
registrar("silver", T_SILVER_ESTAT, "Acurácia", "valores negativos em métricas OBV/GSAA (esperado: métrica de valor pode ser negativa)", n_silver,
          q(f"SELECT COUNT(*) FROM {T_SILVER_ESTAT} WHERE player_match_obv < 0"),
          "Nenhum — OBV negativo é semanticamente válido (ação que reduziu a chance de gol)", "ALERTA", "player_match_obv")

# ── Gold: gols ──────────────────────────────────────────────────────────────────
registrar("gold", T_FATO_TIME, "Acurácia", "gols do time = gols sofridos registrados pelo goleiro adversário",
          q(f"SELECT COUNT(*) FROM {T_FATO_TIME}"),
          q(f"""
            SELECT COUNT(*)
            FROM {T_FATO_TIME} f
            JOIN (
                SELECT match_id, team_id, SUM(gols_sofridos_gk) AS gs
                FROM {T_FATO_JOG}
                GROUP BY ALL
            ) g
                ON f.match_id = g.match_id
                AND f.adversario_id = g.team_id
            WHERE f.gols_pro <> g.gs
          """),
          coluna="gols_pro")

# checagem de 1 registro só: 1 se a soma de gols não bate entre Bronze e Gold, 0 se bate
gols_bronze = q(f"SELECT SUM(CAST(player_match_goals AS DOUBLE)) FROM {T_BRONZE_ESTAT}")
gols_gold = q(f"SELECT SUM(gols) FROM {T_FATO_JOG}")
registrar("gold", T_FATO_JOG, "Acurácia", "reconciliação de gols: soma bronze = soma gold",
          1, int(gols_bronze != gols_gold),
          coluna="gols")

# ── Gold: classificação ─────────────────────────────────────────────────────────
registrar("gold", T_MART_CLASS, "Acurácia", "cada clube com 38 jogos", 20, q(f"SELECT COUNT(*) FROM {T_MART_CLASS} WHERE jogos <> 38"))
registrar("gold", T_MART_CLASS, "Acurácia", "soma de vitórias = soma de derrotas", 1,
          int(q(f"SELECT SUM(vitorias) <> SUM(derrotas) FROM {T_MART_CLASS}")))
registrar("gold", T_MART_CLASS, "Acurácia", "gols pró derivados = gols pró oficiais (CBF)", 20,
          q(f"SELECT COUNT(*) FROM {T_MART_CLASS} WHERE gols_pro <> gols_pro_oficial"),
          "Diferença = gols contra não creditados pela fonte; mart expõe colunas *_oficial", "ALERTA", "gols_pro")
registrar("gold", T_MART_CLASS, "Acurácia", "pontos derivados = pontos oficiais (CBF)", 20,
          q(f"SELECT COUNT(*) FROM {T_MART_CLASS} WHERE pontos <> pontos_oficiais"),
          "Análises de pontos usam pontos_oficiais", "ALERTA", "pontos")
registrar("gold", T_MART_CLASS, "Acurácia", "gols sofridos derivados <= gols sofridos oficiais", 20,
          q(f"SELECT COUNT(*) FROM {T_MART_CLASS} WHERE gols_contra > gols_contra_oficial"), coluna="gols_contra")

# time/partida em que nenhum jogador tem gols_sofridos_gk preenchido = ficou sem goleiro registrado
registrar("gold", T_FATO_TIME, "Acurácia", "partidas sem goleiro registrado", q(f"SELECT COUNT(*) FROM {T_FATO_TIME}"),
          q(f"""
            SELECT COUNT(*)
            FROM (
                SELECT match_id, team_id
                FROM {T_FATO_JOG}
                GROUP BY ALL
                HAVING MAX(CAST(gols_sofridos_gk IS NOT NULL AS INT)) = 0
            )
          """))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Outliers
# MAGIC
# MAGIC Métrica per-90 explode quando o denominador (minutos) é pequeno. Pelo critério de Tukey (Q3 + 3·IQR), medi quantos
# MAGIC jogadores são outliers extremos em `xg_sem_penalti_p90` (e em mais três métricas) **com e sem** o corte de 900 min.
# MAGIC Essa é a evidência em número que justifica a flag `elegivel_analise`.

# COMMAND ----------

# ================================================================================
# OUTLIERS
# ================================================================================

mart = spark.table(T_MART_JOG).filter("tipo_jogador = 'Linha'")

for metrica in ["xg_sem_penalti_p90", "passes_decisivos_p90", "desarmes_p90", "obv_total_p90"]:
    # mesma métrica, uma vez com todo mundo e outra só com quem passou do corte de minutos
    for rotulo, df_ in [("todos os jogadores de linha", mart), (f">= {MIN_MINUTOS_ANALISE} min", mart.filter("elegivel_analise"))]:
        q1, q3 = df_.approxQuantile(metrica, [0.25, 0.75], 0.001)
        lim = q3 + 3 * (q3 - q1)  # cerca superior de Tukey para outlier extremo
        registrar("gold", T_MART_JOG, "Outliers", f"outlier extremo (> Q3+3·IQR = {lim:.3f}) — {rotulo}",
                  df_.count(), df_.filter(F.col(metrica) > lim).count(),
                  f"Análises usam elegivel_analise (>= {MIN_MINUTOS_ANALISE} min)", "ALERTA", metrica)

# ── Como o xG p90 se comporta por faixa de minutos ──────────────────────────────
display(spark.sql(f"""
SELECT
    CASE
        WHEN minutos < 300 THEN '1. < 300'
        WHEN minutos < 900 THEN '2. 300-899'
        ELSE '3. >= 900'
    END AS faixa_minutos,
    COUNT(*) AS jogadores,
    ROUND(MAX(xg_sem_penalti_p90), 2) AS max_xg_p90,
    ROUND(STDDEV(xg_sem_penalti_p90), 3) AS desvio_xg_p90
FROM {T_MART_JOG}
WHERE tipo_jogador = 'Linha'
GROUP BY 1
ORDER BY 1"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Persistência e resumo
# MAGIC
# MAGIC Grava tudo em modo append (o histórico fica separado por `id_execucao`) e mostra o resumo por dimensão e status.

# COMMAND ----------

# ================================================================================
# GRAVAÇÃO EM governanca.dq_resultados
# ================================================================================

SCHEMA_DQ = ("id_execucao STRING, camada STRING, tabela STRING, coluna STRING, dimensao STRING, regra STRING, "
             "registros_avaliados BIGINT, registros_com_falha BIGINT, pct_falha DOUBLE, status STRING, tratamento STRING")

df_dq = (spark.createDataFrame(resultados, SCHEMA_DQ)
         .withColumn("data_execucao", F.current_timestamp()))

(df_dq.write
    .format(TABLE_FORMAT)
    .mode("append")
    .option("mergeSchema", "true")
    .saveAsTable(T_DQ))
print(f"[OK] {len(resultados)} checagens gravadas em {T_DQ} (id_execucao={ID_EXEC})")

display(df_dq.groupBy("dimensao", "status").count().orderBy("dimensao", "status"))

# COMMAND ----------

# Visão executiva: tudo que não é completude coluna a coluna, mais as colunas que têm nulo
display(df_dq.filter("dimensao <> 'Completude' OR registros_com_falha > 0")
        .select("camada", "tabela", "coluna", "dimensao", "regra", "registros_avaliados", "registros_com_falha", "pct_falha", "status", "tratamento")
        .orderBy(F.desc("pct_falha")))

# COMMAND ----------

# ── Trava do pipeline: qualquer ERRO para a execução aqui ───────────────────────
erros = df_dq.filter("status = 'ERRO'").count()
assert erros == 0, f"{erros} checagens com status ERRO - ver {T_DQ}"
print("[OK] Nenhuma checagem com status ERRO")
