# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Catálogo de dados e chaves do modelo
# MAGIC
# MAGIC Esse notebook documenta tudo que o pipeline gerou no Unity Catalog. O que ele faz, na ordem:
# MAGIC
# MAGIC 1. Aplica comentário em todas as tabelas e colunas (aparece no Catalog Explorer), com descrição, domínio esperado e linhagem.
# MAGIC 2. Mede o domínio observado de cada coluna direto nos dados (mín/máx para numéricas, categorias para texto).
# MAGIC 3. Grava tudo em `governanca.catalogo_dados`, que dá pra consultar por SQL e é de onde sai o catálogo do README.
# MAGIC 4. Declara as chaves primárias e estrangeiras (informativas), daí o Catalog Explorer desenha o diagrama ER sozinho.
# MAGIC
# MAGIC Na Silver não reescrevi descrição nenhuma: as 167 colunas StatsBomb pegam o texto do próprio dicionário de dados
# MAGIC (tabela `silver.dicionario_dados`).

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Definições de negócio das colunas Gold
# MAGIC
# MAGIC Aqui ficam os textos que viram COMMENT no catálogo. Cada coluna tem descrição, domínio esperado e de onde veio (linhagem).

# COMMAND ----------

# ================================================================================
# DEFINIÇÕES DE NEGÓCIO (GOLD)
# ================================================================================

# ── Métricas do fato jogador x partida ──────────────────────────────────────────
# coluna -> (descrição, domínio esperado)
METRICA = {
    "minutos": ("Minutos jogados pelo atleta na partida (inclui acréscimos)", "0 < x <= 130"),
    "gols": ("Gols marcados (inclui pênaltis; gols contra não são creditados)", "inteiro >= 0"),
    "gols_sem_penalti": ("Gols marcados excluindo pênaltis", "inteiro >= 0, <= gols"),
    "assistencias": ("Assistências para gol", "inteiro >= 0"),
    "finalizacoes_sem_penalti": ("Finalizações excluindo pênaltis", "inteiro >= 0"),
    "finalizacoes_no_alvo": ("Finalizações sem pênalti no alvo", "inteiro >= 0, <= finalizacoes_sem_penalti"),
    "xg_sem_penalti": ("Gols esperados (xG StatsBomb) das finalizações sem pênalti; NULL = não finalizou", "0 <= x; NULL permitido"),
    "xg_por_finalizacao": ("xG médio por finalização sem pênalti; NULL = não finalizou", "0 <= x <= 1; NULL permitido"),
    "xa": ("Assistências esperadas: soma do xG das finalizações originadas de passes do jogador", "0 <= x; NULL permitido"),
    "passes_decisivos": ("Passes que resultaram em finalização (key passes)", "inteiro >= 0"),
    "passes_em_profundidade": ("Passes em profundidade (through balls)", "inteiro >= 0"),
    "passes": ("Passes tentados", "inteiro >= 0"),
    "passes_certos": ("Passes completados", "inteiro >= 0, <= passes"),
    "passes_para_frente": ("Passes para frente", "inteiro >= 0"),
    "passes_terco_final": ("Passes em jogo aberto no terço final", "inteiro >= 0"),
    "passes_para_area": ("Passes completados para dentro da área", "inteiro >= 0"),
    "progressoes_profundas": ("Passes/conduções que chegam ao terço final (deep progressions)", "inteiro >= 0"),
    "cruzamentos": ("Cruzamentos tentados", "inteiro >= 0"),
    "cruzamentos_certos": ("Cruzamentos completados", "inteiro >= 0, <= cruzamentos"),
    "bolas_longas": ("Bolas longas tentadas", "inteiro >= 0"),
    "bolas_longas_certas": ("Bolas longas completadas", "inteiro >= 0, <= bolas_longas"),
    "dribles_certos": ("Dribles bem-sucedidos", "inteiro >= 0"),
    "toques": ("Toques na bola", "inteiro >= 0"),
    "toques_na_area": ("Toques na bola dentro da área adversária", "inteiro >= 0"),
    "desarmes": ("Desarmes", "inteiro >= 0"),
    "interceptacoes": ("Interceptações", "inteiro >= 0"),
    "recuperacoes": ("Recuperações de bola", "inteiro >= 0"),
    "pressoes": ("Pressões sobre o portador da bola", "inteiro >= 0"),
    "contrapressoes": ("Pressões nos 5 s após perda da posse (counterpressures)", "inteiro >= 0"),
    "recuperacoes_pos_pressao": ("Recuperações de bola até 5 s após uma pressão", "inteiro >= 0"),
    "acoes_defensivas": ("Total de ações defensivas", "inteiro >= 0"),
    "cortes": ("Cortes/afastamentos (clearances)", "inteiro >= 0"),
    "duelos_aereos": ("Duelos aéreos disputados", "inteiro >= 0"),
    "duelos_aereos_vencidos": ("Duelos aéreos vencidos", "inteiro >= 0, <= duelos_aereos"),
    "vezes_driblado": ("Vezes em que o jogador foi driblado", "inteiro >= 0"),
    "faltas_cometidas": ("Faltas cometidas", "inteiro >= 0"),
    "faltas_sofridas": ("Faltas sofridas", "inteiro >= 0"),
    "perdas_de_posse": ("Desarmado com a bola (dispossessed)", "inteiro >= 0"),
    "erros_com_bola": ("Perdas de posse por erro (turnovers)", "inteiro >= 0"),
    "xg_chain": ("xG das posses em que o jogador participou", ">= 0; NULL permitido"),
    "xg_buildup": ("xG Chain excluindo o chute e o passe para o chute", ">= 0; NULL permitido"),
    "obv_total": ("On-Ball Value total: variação da probabilidade de gol causada pelas ações com bola", "real (pode ser negativo)"),
    "obv_passe": ("OBV de passes", "real (pode ser negativo)"),
    "obv_conducao": ("OBV de dribles e conduções", "real (pode ser negativo)"),
    "obv_defesa": ("OBV de ações defensivas", "real (pode ser negativo)"),
    "obv_finalizacao": ("OBV de finalizações; NULL = não finalizou", "real; NULL permitido"),
    "posse_time": ("Posse de bola do time do jogador na partida", "0 <= x <= 1"),
    "gols_sofridos_gk": ("Gols sofridos enquanto goleiro; NULL = não atuou no gol", "inteiro >= 0; NULL p/ jogador de linha"),
    "gsaa_gk": ("Gols evitados acima do esperado (goleiro); NULL = não atuou no gol", "real; NULL p/ jogador de linha"),
}

# ── Chaves e flags que se repetem em várias tabelas ─────────────────────────────
ID = {
    "match_id": ("Identificador StatsBomb da partida", "inteiro; 380 valores"),
    "player_id": ("Identificador StatsBomb do jogador", "inteiro; 737 valores"),
    "team_id": ("Identificador StatsBomb do clube", "inteiro; 20 valores"),
    "adversario_id": ("team_id do adversário na partida (derivado do self-join por match_id)", "inteiro; FK dim_time"),
    "is_goleiro": ("Jogador atuou como goleiro ao menos uma vez (tem métrica obv_gk)", "true/false"),
    "tem_cobertura_360": ("Partida do jogador com cobertura StatsBomb 360 (360_minutes > 0)", "true/false"),
    "_id_carga": ("Identificador da execução de ingestão Bronze que originou o registro", "texto yyyymmddThhmmss-hash"),
}
# linhagem do fato: coluna gold -> coluna de origem na silver (mesmo de-para do 04)
L_FATO = {dst: f"silver.jogador_partida.{src}" for src, dst in MAPA_FATO_JOG.items()}

# ── Dimensões e fato jogador ────────────────────────────────────────────────────
# tabela -> (descrição da tabela, {coluna: (descrição, domínio esperado, linhagem)})
CATALOGO = {
    T_DIM_TIME: ("Dimensão de clubes. Grão: 1 linha por clube. Fonte: silver.jogador_partida + silver.time_de_para.", {
        "team_id": (*ID["team_id"], "silver.jogador_partida.team_id"),
        "nome_time": ("Nome padronizado do clube", "20 clubes da Série A 2025", "silver.time_de_para.nome_time"),
        "nome_curto": ("Nome curto para exibição", "texto", "silver.time_de_para.nome_curto"),
        "sigla": ("Sigla de 3 letras", "texto de 3 caracteres", "silver.time_de_para.sigla (manual)"),
        "uf": ("Unidade federativa da sede", "UF brasileira", "silver.time_de_para.uf (manual)"),
        "nome_fonte": ("Nome do clube como veio da StatsBomb", "texto", "bronze.team_name"),
    }),
    T_DIM_JOGADOR: ("Dimensão de jogadores. Grão: 1 linha por player_id.", {
        "player_id": (*ID["player_id"], "silver.jogador_partida.player_id"),
        "nome_jogador": ("Nome do jogador como na fonte", "texto", "silver.jogador_partida.player_name"),
        "nome_exibicao": ("Nome sem ambiguidade: homônimos recebem o clube principal entre parênteses", "texto único", "derivado de nome_jogador + time_principal"),
        "tipo_jogador": ("Goleiro ou Linha", "{Goleiro, Linha}", "derivado de is_goleiro"),
        "is_goleiro": (*ID["is_goleiro"], "silver.jogador_partida.is_goleiro"),
        "time_principal_id": ("Clube em que o jogador somou mais minutos na temporada", "FK dim_time", "silver: argmax(soma minutos) por team_id"),
        "time_principal": ("Nome curto do clube principal", "texto", "dim_time.nome_curto"),
        "qtd_times": ("Quantidade de clubes pelos quais atuou na temporada", "1 ou 2", "silver: count distinct team_id"),
        "nome_homonimo": ("Existe outro player_id com o mesmo nome", "true/false", "derivado"),
    }),
    T_DIM_PARTIDA: ("Dimensão de partidas. Grão: 1 linha por partida. Placar derivado da soma dos gols dos jogadores (fonte sem placar, data ou mando).", {
        "match_id": (*ID["match_id"], "silver.jogador_partida.match_id"),
        "time_a_id": ("Clube de menor team_id no confronto (não indica mando)", "FK dim_time", "silver.team_id"),
        "time_a": ("Nome curto do time A", "texto", "dim_time"),
        "time_b_id": ("Clube de maior team_id no confronto", "FK dim_time", "silver.team_id"),
        "time_b": ("Nome curto do time B", "texto", "dim_time"),
        "gols_time_a": ("Gols do time A", "inteiro >= 0", "SUM(silver.player_match_goals) do time A"),
        "gols_time_b": ("Gols do time B", "inteiro >= 0", "SUM(silver.player_match_goals) do time B"),
        "total_gols": ("Total de gols na partida", "inteiro >= 0", "gols_time_a + gols_time_b"),
        "confronto": ("Texto 'Time A gols x gols Time B'", "texto", "derivado"),
        "vencedor": ("Nome do vencedor ou 'Empate'", "texto", "derivado"),
        "temporada": ("Temporada", "2025", "parâmetro do pipeline"),
    }),
    T_FATO_JOG: ("Fato de desempenho do jogador por partida. Grão: match_id + player_id. Métricas StatsBomb renomeadas em português.", {
        "match_id": (*ID["match_id"], "silver.jogador_partida.match_id"),
        "player_id": (*ID["player_id"], "silver.jogador_partida.player_id"),
        "team_id": (*ID["team_id"], "silver.jogador_partida.team_id"),
        "adversario_id": (*ID["adversario_id"], "gold.dim_partida (time_a_id/time_b_id)"),
        **{c: (*METRICA[c], L_FATO[c]) for c in MAPA_FATO_JOG.values()},
        "is_goleiro": (*ID["is_goleiro"], "silver.jogador_partida.is_goleiro"),
        "tem_cobertura_360": (*ID["tem_cobertura_360"], "silver.jogador_partida.tem_cobertura_360"),
        "_id_carga": (*ID["_id_carga"], "bronze._id_carga"),
    }),
}

# ── Fato time x partida ─────────────────────────────────────────────────────────
# pró = soma dos jogadores do time; contra = mesma métrica, só que do adversário
ft_cols = {
    "match_id": (*ID["match_id"], "gold.fato_jogador_partida.match_id"),
    "team_id": (*ID["team_id"], "gold.fato_jogador_partida.team_id"),
    "adversario_id": (*ID["adversario_id"], "gold.fato_jogador_partida.adversario_id"),
}
PARES_PRO_CONTRA = [
    ("gols", "Gols"),
    ("gols_sem_penalti", "Gols sem pênalti"),
    ("xg_sem_penalti", "xG sem pênalti"),
    ("finalizacoes", "Finalizações sem pênalti"),
    ("finalizacoes_no_alvo", "Finalizações no alvo"),
]
for base, desc in PARES_PRO_CONTRA:
    # no fato do jogador a coluna se chama finalizacoes_sem_penalti, no do time ficou só finalizacoes
    src = "finalizacoes_sem_penalti" if base == "finalizacoes" else base
    ft_cols[f"{base}_pro"] = (f"{desc} do time", ">= 0", f"SUM(fato_jogador_partida.{src}) do time")
    ft_cols[f"{base}_contra"] = (f"{desc} do adversário (sofridos)", ">= 0", f"SUM(fato_jogador_partida.{src}) do adversário")

# métricas que só somam os jogadores do time (reaproveita a descrição do METRICA)
SOMAS_DO_TIME = ["passes", "passes_certos", "passes_decisivos", "toques_na_area", "pressoes", "contrapressoes",
                 "recuperacoes", "desarmes", "interceptacoes", "obv_total"]
for c in SOMAS_DO_TIME:
    ft_cols[c] = (f"{METRICA[c][0]} - soma do time", METRICA[c][1], f"SUM(fato_jogador_partida.{c})")
ft_cols.update({
    "pct_passes_certos": ("Percentual de passes certos do time", "0 a 1", "passes_certos / passes"),
    "posse": ("Posse de bola do time", "0 a 1", "AVG(fato_jogador_partida.posse_time)"),
    "jogadores_utilizados": ("Jogadores que entraram em campo", "11 a 16", "COUNT(fato_jogador_partida)"),
    "resultado": ("Resultado para o time", "{V, E, D}", "gols_pro vs gols_contra"),
    "pontos": ("Pontos conquistados", "{0, 1, 3}", "V=3, E=1, D=0"),
})
CATALOGO[T_FATO_TIME] = ("Fato de desempenho do time por partida. Grão: match_id + team_id.", ft_cols)

# ── Mart de classificação ───────────────────────────────────────────────────────
mc = {
    "posicao": ("Posição na classificação derivada (pontos, vitórias, saldo, gols pró)", "1 a 20", "ROW_NUMBER sobre fato_time_partida"),
    "team_id": (*ID["team_id"], "fato_time_partida.team_id"),
    "time": ("Nome curto do clube", "texto", "dim_time.nome_curto"),
    "jogos": ("Jogos disputados", "38", "COUNT(fato_time_partida)"),
    "pontos": ("Pontos", "0 a 114", "SUM(pontos)"),
    "vitorias": ("Vitórias", "0 a 38", "SUM(resultado='V')"),
    "empates": ("Empates", "0 a 38", "SUM(resultado='E')"),
    "derrotas": ("Derrotas", "0 a 38", "SUM(resultado='D')"),
    "gols_pro": ("Gols marcados", ">= 0", "SUM(gols_pro)"),
    "gols_contra": ("Gols sofridos", ">= 0", "SUM(gols_contra)"),
    "saldo_gols": ("Saldo de gols", "inteiro", "gols_pro - gols_contra"),
    "aproveitamento": ("Aproveitamento de pontos", "0 a 1", "pontos / (jogos*3)"),
    "xg_sem_penalti_pro": ("xG sem pênalti gerado", ">= 0", "SUM(xg_sem_penalti_pro)"),
    "xg_sem_penalti_contra": ("xG sem pênalti cedido", ">= 0", "SUM(xg_sem_penalti_contra)"),
    "saldo_xg": ("Saldo de xG sem pênalti", "real", "pro - contra"),
    "gols_menos_xg_pro": ("Gols sem pênalti menos xG gerado (>0 = finalização acima do esperado)", "real", "gols_sem_penalti_pro - xg_sem_penalti_pro"),
    "gols_menos_xg_contra": ("Gols sem pênalti sofridos menos xG cedido (<0 = defesa/goleiro acima do esperado)", "real", "gols_sem_penalti_contra - xg_sem_penalti_contra"),
    "finalizacoes_pro_por_jogo": ("Finalizações por jogo", ">= 0", "AVG(finalizacoes_pro)"),
    "finalizacoes_contra_por_jogo": ("Finalizações cedidas por jogo", ">= 0", "AVG(finalizacoes_contra)"),
    "pressoes_por_jogo": ("Pressões por jogo", ">= 0", "AVG(pressoes)"),
    "recuperacoes_por_jogo": ("Recuperações por jogo", ">= 0", "AVG(recuperacoes)"),
    "posse_media": ("Posse média", "0 a 1", "AVG(posse)"),
    "pct_passes_certos": ("Percentual de passes certos", "0 a 1", "SUM(passes_certos)/SUM(passes)"),
    "obv_total": ("OBV total da temporada", "real", "SUM(obv_total)"),
    "posicao_oficial": ("Posição na classificação oficial CBF", "1 a 20", "silver.classificacao_oficial_referencia.posicao"),
    "pontos_oficiais": ("Pontos na classificação oficial CBF", "0 a 114", "silver.classificacao_oficial_referencia.pontos"),
    "gols_pro_oficial": ("Gols pró oficiais (inclui gols contra do adversário)", ">= gols_pro", "silver.classificacao_oficial_referencia.gols_pro"),
    "gols_contra_oficial": ("Gols sofridos oficiais", ">= gols_contra", "silver.classificacao_oficial_referencia.gols_contra"),
    "gols_contra_a_favor_nao_creditados": ("Gols contra marcados pelo adversário a favor do clube (não creditados na StatsBomb)", "inteiro >= 0", "gols_pro_oficial - gols_pro"),
}
CATALOGO[T_MART_CLASS] = ("Mart: classificação derivada do Brasileirão 2025 e indicadores de xG por clube. Grão: 1 linha por clube.", mc)

# ── Mart jogador x temporada ────────────────────────────────────────────────────
mj = {
    "player_id": (*ID["player_id"], "fato_jogador_partida.player_id"),
    "nome_jogador": ("Nome do jogador", "texto", "dim_jogador"),
    "nome_exibicao": ("Nome sem ambiguidade", "texto", "dim_jogador"),
    "tipo_jogador": ("Goleiro ou Linha", "{Goleiro, Linha}", "dim_jogador"),
    "time_principal_id": ("Clube principal", "FK dim_time", "dim_jogador"),
    "time_principal": ("Nome curto do clube principal", "texto", "dim_jogador"),
    "qtd_times": ("Clubes na temporada", "1 ou 2", "dim_jogador"),
    "partidas": ("Partidas disputadas", "1 a 38", "COUNT DISTINCT match_id"),
    "minutos": ("Minutos na temporada", ">= 0", "SUM(minutos)"),
    "minutos_por_partida": ("Média de minutos por partida", "0 a 130", "minutos / partidas"),
    "elegivel_analise": (f"Jogador de linha com >= {MIN_MINUTOS_ANALISE} minutos (amostra estável para per-90)", "true/false", "regra de negócio"),
    "gols": ("Gols na temporada", ">= 0", "SUM(gols)"),
    "gols_sem_penalti": ("Gols sem pênalti", ">= 0", "SUM"),
    "assistencias": ("Assistências", ">= 0", "SUM"),
    "xg_sem_penalti": ("xG sem pênalti", ">= 0", "SUM"),
    "xa": ("xA", ">= 0", "SUM"),
    "gols_menos_xg": ("Gols sem pênalti - xG sem pênalti (>0 = finalizou acima do esperado)", "real", "derivado"),
    "finalizacoes_sem_penalti": ("Finalizações sem pênalti", ">= 0", "SUM"),
    "pct_finalizacoes_no_alvo": ("% de finalizações no alvo", "0 a 1; NULL se 0 finalizações", "no_alvo / finalizações"),
    "pct_passes_certos": ("% de passes certos", "0 a 1", "passes_certos / passes"),
    "pct_duelos_aereos_vencidos": ("% de duelos aéreos vencidos", "0 a 1; NULL se 0 duelos", "vencidos / disputados"),
}
# as colunas per-90 são geradas no 04, então lê direto da tabela em vez de repetir a lista aqui
for c in spark.table(T_MART_JOG).columns:
    if c.endswith("_p90"):
        b = c[:-4]  # tira o sufixo _p90 pra achar a métrica base
        mj[c] = (f"{METRICA[b][0]} por 90 minutos", ">= 0 (OBV pode ser negativo)", f"SUM(fato_jogador_partida.{b}) / SUM(minutos) * 90")
CATALOGO[T_MART_JOG] = ("Mart: jogador x temporada com totais e métricas per-90. Grão: 1 linha por jogador.", mj)

# ── Feature store de similaridade ───────────────────────────────────────────────
fs = {
    "player_id": (*ID["player_id"], "mart_jogador_temporada"),
    "nome_exibicao": ("Nome sem ambiguidade", "texto", "dim_jogador"),
    "time_principal": ("Clube principal", "texto", "dim_jogador"),
    "minutos": ("Minutos na temporada", f">= {MIN_MINUTOS_ANALISE}", "mart_jogador_temporada"),
    "vetor_features": ("Vetor ordenado das 28 features z-score (ordem = colunas z_*)", "ARRAY<DOUBLE> de 28 posições", "array(z_*)"),
    "norma_vetor": ("Norma euclidiana do vetor (pré-calculada para similaridade de cosseno)", "> 0", "sqrt(sum(z^2))"),
}
# mesma ideia do mart: as colunas z_* saem da tabela
for c in spark.table(T_FEATURES).columns:
    if c.startswith("z_"):
        fs[c] = (f"Z-score de {c[2:]} (per-90) na população elegível", "real, média 0 e desvio 1", "(x - média) / desvio sobre jogadores elegíveis")
CATALOGO[T_FEATURES] = ("Feature store: 28 métricas per-90 padronizadas por jogador elegível (linha, >= 900 min). Insumo do modelo de similaridade.", fs)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Silver: descrições vindas do dicionário de dados
# MAGIC
# MAGIC As colunas StatsBomb usam a justificativa do dicionário como descrição e a categoria + ação de missing como domínio.
# MAGIC As colunas que a gente criou na Silver (de-para de time, flags e controle de carga) são descritas na mão logo abaixo.

# COMMAND ----------

# ================================================================================
# CATÁLOGO DA SILVER
# ================================================================================

# indexa o dicionário pelo nome da variável pra achar cada coluna rápido
dic = {r["variavel"]: r for r in spark.table(T_SILVER_DIC).collect()}

silver_cols = {}
for c in spark.table(T_SILVER_ESTAT).columns:
    if c in dic:
        r = dic[c]
        silver_cols[c] = (r["justificativa"], f"Categoria: {r['categoria']} | Missing: {r['acao_recomendada']}", f"bronze.{c} (try_cast)")

# colunas derivadas e de controle (não existem no dicionário StatsBomb)
silver_cols.update({
    "team_name": ("Nome padronizado do clube", "20 clubes", "silver.time_de_para via bronze.team_name"),
    "team_name_fonte": ("Nome do clube como na fonte", "texto", "bronze.team_name"),
    "is_goleiro": ID["is_goleiro"] + ("derivado de player_match_obv_gk",),
    "tem_cobertura_360": ID["tem_cobertura_360"] + ("derivado de player_match_360_minutes",),
    "_arquivo_origem": ("Caminho do arquivo no volume", "texto", "bronze"),
    "_data_ingestao": ("Timestamp da ingestão Bronze", "timestamp", "bronze"),
    "_id_carga": ID["_id_carga"] + ("bronze",),
    "_data_processamento": ("Timestamp do processamento Silver", "timestamp", "silver"),
})
CATALOGO[T_SILVER_ESTAT] = ("Silver: estatísticas por jogador x partida tipadas e tratadas. Grão: match_id + player_id.", silver_cols)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Aplicar comentários e medir o domínio observado
# MAGIC
# MAGIC Pra cada tabela do catálogo: grava o COMMENT da tabela e das colunas e mede o domínio real numa agregação só
# MAGIC (mín/máx das numéricas, distintos das textuais e contagem de nulos). Coluna textual com até 6 valores sai listada,
# MAGIC acima disso só a quantidade. No fim grava tudo em `governanca.catalogo_dados`.

# COMMAND ----------

# ================================================================================
# APLICAR COMENTÁRIOS NO UNITY CATALOG
# ================================================================================

def esc(s):
    """
    Escapa barra invertida e aspas simples para usar o texto dentro de um literal Spark SQL.

    Args:
        s: Texto (ou qualquer valor, que vira str) a ser escapado

    Returns:
        str: Texto pronto pra ir entre aspas simples num COMMENT
    """
    return str(s).replace("\\", "\\\\").replace("'", "\\'")  # escape de aspas em literais Spark SQL


linhas = []
for tabela, (desc_tab, cols) in CATALOGO.items():
    df = spark.table(tabela)
    spark.sql(f"COMMENT ON TABLE {tabela} IS '{esc(desc_tab)}'")

    # ── Separa as colunas por tipo ──────────────────────────────────────────────
    tipos = dict(df.dtypes)
    numericas = [c for c in cols if c in tipos and tipos[c] in ("int", "bigint", "double", "float")]
    textuais = [c for c in cols if c in tipos and tipos[c] in ("string", "boolean")]

    # ── Mede o domínio observado numa passada só pela tabela ────────────────────
    exprs_min = [F.min(c).alias(f"min__{c}") for c in numericas]
    exprs_max = [F.max(c).alias(f"max__{c}") for c in numericas]
    exprs_distintos = [F.countDistinct(c).alias(f"nd__{c}") for c in textuais]
    exprs_nulos = [F.sum(F.col(c).isNull().cast("int")).alias(f"nul__{c}") for c in cols if c in tipos]
    agg = df.select(*exprs_min, *exprs_max, *exprs_distintos, *exprs_nulos).first().asDict()
    n = df.count()

    for c, (desc, dominio, linhagem) in cols.items():
        if c not in tipos:
            continue  # coluna documentada mas que não existe na tabela, ignora

        if c in numericas:
            observado = f"[{agg[f'min__{c}']:.4g} ; {agg[f'max__{c}']:.4g}]" if agg[f"min__{c}"] is not None else "todos NULL"
        elif c in textuais:
            nd = agg[f"nd__{c}"]
            if nd <= 6:
                # poucas categorias: vale a pena listar os valores
                vals = [str(r[0]) for r in df.select(c).distinct().orderBy(c).collect()]
                observado = "{" + ", ".join(vals) + "}"
            else:
                observado = f"{nd} valores distintos"
        else:
            observado = tipos[c]  # array, timestamp etc.: registra só o tipo

        comentario = f"{desc} | Domínio: {dominio} | Origem: {linhagem}"
        spark.sql(f"ALTER TABLE {tabela} ALTER COLUMN `{c}` COMMENT '{esc(comentario)}'")

        pct_nulos = round(agg[f"nul__{c}"] / n, 4) if n else 0.0
        linhas.append((tabela.split(".", 1)[1], c, tipos[c], desc, dominio, observado, pct_nulos, linhagem))

    print(f"[OK] {tabela} - {len(cols)} colunas documentadas")

# ── Grava o catálogo consultável ────────────────────────────────────────────────
catalogo_df = spark.createDataFrame(linhas, "tabela STRING, coluna STRING, tipo STRING, descricao STRING, dominio_esperado STRING, "
                                            "dominio_observado STRING, pct_nulos DOUBLE, linhagem STRING")
salvar_tabela(catalogo_df, T_CATALOGO, "Catálogo de dados do MVP: descrição, tipo, domínio esperado/observado, % nulos e linhagem por coluna.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Chaves primárias e estrangeiras
# MAGIC
# MAGIC No Unity Catalog as PKs e FKs são só informativas (não bloqueiam carga), mas é com elas que o Catalog Explorer
# MAGIC monta o diagrama ER. Quem realmente barra dado inválido são as CHECK constraints do final da célula.

# COMMAND ----------

# ================================================================================
# CHAVES E CONSTRAINTS
# ================================================================================

# ── Definição das chaves ────────────────────────────────────────────────────────
PKS = {
    T_DIM_TIME: ["team_id"],
    T_DIM_JOGADOR: ["player_id"],
    T_DIM_PARTIDA: ["match_id"],
    T_FATO_JOG: ["match_id", "player_id"],
    T_FATO_TIME: ["match_id", "team_id"],
    T_MART_JOG: ["player_id"],
    T_MART_CLASS: ["team_id"],
}
FKS = [  # (tabela, nome, coluna, tabela referenciada)
    (T_DIM_JOGADOR, "fk_dim_jogador_time", "time_principal_id", T_DIM_TIME),
    (T_DIM_PARTIDA, "fk_dim_partida_time_a", "time_a_id", T_DIM_TIME),
    (T_DIM_PARTIDA, "fk_dim_partida_time_b", "time_b_id", T_DIM_TIME),
    (T_FATO_JOG, "fk_fjp_partida", "match_id", T_DIM_PARTIDA),
    (T_FATO_JOG, "fk_fjp_jogador", "player_id", T_DIM_JOGADOR),
    (T_FATO_JOG, "fk_fjp_time", "team_id", T_DIM_TIME),
    (T_FATO_JOG, "fk_fjp_adversario", "adversario_id", T_DIM_TIME),
    (T_FATO_TIME, "fk_ftp_partida", "match_id", T_DIM_PARTIDA),
    (T_FATO_TIME, "fk_ftp_time", "team_id", T_DIM_TIME),
    (T_FATO_TIME, "fk_ftp_adversario", "adversario_id", T_DIM_TIME),
    (T_MART_JOG, "fk_mart_jog_jogador", "player_id", T_DIM_JOGADOR),
    (T_MART_CLASS, "fk_mart_class_time", "team_id", T_DIM_TIME),
]
# ── Recria PKs e FKs ────────────────────────────────────────────────────────────
# derruba as FKs primeiro, senão o DROP da PK referenciada falha na re-execução
for t, nome, _, _ in FKS:
    spark.sql(f"ALTER TABLE {t} DROP CONSTRAINT IF EXISTS {nome}")

for t, cols in PKS.items():
    pk = "pk_" + t.split(".")[-1]
    spark.sql(f"ALTER TABLE {t} DROP CONSTRAINT IF EXISTS {pk}")
    for c in cols:
        spark.sql(f"ALTER TABLE {t} ALTER COLUMN {c} SET NOT NULL")  # PK no UC exige NOT NULL
    spark.sql(f"ALTER TABLE {t} ADD CONSTRAINT {pk} PRIMARY KEY ({', '.join(cols)})")

for t, nome, col, ref in FKS:
    spark.sql(f"ALTER TABLE {t} ADD CONSTRAINT {nome} FOREIGN KEY ({col}) REFERENCES {ref}")

print(f"[OK] {len(PKS)} PKs e {len(FKS)} FKs declaradas")
print("[INFO] Diagrama ER no Catalog Explorer: gold > tabela > aba 'Relationships'")

# ── Regras de negócio na Gold (CHECK constraints do Delta) ──────────────────────
# essas sim bloqueiam cargas futuras com dado inválido
CHECKS = [
    (T_FATO_JOG, "ck_minutos", f"minutos > 0 AND minutos <= {MAX_MINUTOS_PARTIDA}"),
    (T_FATO_JOG, "ck_passes", "passes_certos <= passes"),
    (T_FATO_TIME, "ck_pontos", "pontos IN (0, 1, 3)"),
]
for t, nome, expr in CHECKS:
    spark.sql(f"ALTER TABLE {t} DROP CONSTRAINT IF EXISTS {nome}")
    spark.sql(f"ALTER TABLE {t} ADD CONSTRAINT {nome} CHECK ({expr})")
print(f"[OK] {len(CHECKS)} CHECK constraints aplicadas")

# COMMAND ----------

# confere o catálogo da Gold
display(spark.table(T_CATALOGO).filter("tabela LIKE 'gold.%'").orderBy("tabela", "coluna"))
