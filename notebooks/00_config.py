# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Configuração compartilhada
# MAGIC
# MAGIC Esse notebook não roda sozinho, ele é chamado via `%run ./00_config` por todos os outros. Aqui fica tudo
# MAGIC que é comum ao pipeline:
# MAGIC - nomes de catálogo, schemas e volume no Unity Catalog;
# MAGIC - caminho de landing dos arquivos brutos;
# MAGIC - parâmetros de negócio, como o corte de minutos e o time de referência;
# MAGIC - funções utilitárias de escrita e leitura, pra manter o mesmo padrão entre as camadas.
# MAGIC
# MAGIC A ideia é não ter número mágico espalhado pelos notebooks. Se precisar trocar o catálogo (por exemplo
# MAGIC para `workspace`, caso a conta Free Edition não deixe criar catálogo), é só mudar num lugar.

# COMMAND ----------

# ================================================================================
# IMPORTS
# ================================================================================

import uuid
from datetime import datetime, timezone

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import Window

# ================================================================================
# PARÂMETROS (WIDGETS)
# ================================================================================

# Valores padrão; o Job ou o orquestrador podem sobrescrever
# Se a conta não deixar criar catálogo, usar: dbutils.widgets.text("catalogo", "workspace", ...)
dbutils.widgets.text("catalogo", "mvp_brasileirao", "Catálogo Unity Catalog")
dbutils.widgets.text("temporada", "2025", "Temporada")

CATALOG = dbutils.widgets.get("catalogo")
TEMPORADA = int(dbutils.widgets.get("temporada"))

# ── Schemas ─────────────────────────────────────────────────────────────────────

# um schema por camada do medalhão, mais o de governança
SCHEMA_BRONZE = "bronze"
SCHEMA_SILVER = "silver"
SCHEMA_GOLD = "gold"
SCHEMA_GOV = "governanca"

# ── Landing ─────────────────────────────────────────────────────────────────────

# volume gerenciado onde os CSVs brutos são colocados (upload pela UI)
VOLUME_LANDING = "landing"
LANDING_PATH = f"/Volumes/{CATALOG}/{SCHEMA_BRONZE}/{VOLUME_LANDING}/statsbomb/brasileirao_{TEMPORADA}"
ARQUIVO_ESTATISTICAS = "estatisticas_jogadores_partida_brasileirao2025.csv"
ARQUIVO_DICIONARIO = "dicionario_dados.csv"

# Delta é o padrão do Lakehouse no Databricks
TABLE_FORMAT = "delta"

# ================================================================================
# PARÂMETROS DE NEGÓCIO
# ================================================================================

MIN_MINUTOS_ANALISE = 900                 # ~10 jogos completos, abaixo disso o per-90 fica instável
TIME_REFERENCIA     = "Botafogo"          # clube foco das análises comparativas
JOGADOR_REFERENCIA  = "Alexander Barboza" # referência pra busca de similaridade (P6)
MAX_MINUTOS_PARTIDA = 130                 # 90 + acréscimos com folga, acima disso é erro de dado


# ================================================================================
# NOMES DAS TABELAS
# ================================================================================

def tbl(schema: str, nome: str) -> str:
    """
    Monta o nome completo da tabela no Unity Catalog (catalogo.schema.tabela).

    Args:
        schema: Schema da camada (bronze, silver, gold, governanca)
        nome: Nome da tabela dentro do schema

    Returns:
        str: Nome totalmente qualificado, no namespace de 3 níveis do UC
    """
    return f"{CATALOG}.{schema}.{nome}"


# Todos os notebooks usam essas constantes, não escrever nome de tabela na mão
T_BRONZE_ESTAT = tbl(SCHEMA_BRONZE, "statsbomb_jogador_partida_raw")
T_BRONZE_DIC = tbl(SCHEMA_BRONZE, "dicionario_dados_raw")

T_SILVER_ESTAT = tbl(SCHEMA_SILVER, "jogador_partida")
T_SILVER_QUARENTENA = tbl(SCHEMA_SILVER, "jogador_partida_quarentena")
T_SILVER_DIC = tbl(SCHEMA_SILVER, "dicionario_dados")
T_SILVER_TIME_DE_PARA = tbl(SCHEMA_SILVER, "time_de_para")
T_SILVER_CLASS_OFICIAL = tbl(SCHEMA_SILVER, "classificacao_oficial_referencia")

T_DIM_TIME = tbl(SCHEMA_GOLD, "dim_time")
T_DIM_JOGADOR = tbl(SCHEMA_GOLD, "dim_jogador")
T_DIM_PARTIDA = tbl(SCHEMA_GOLD, "dim_partida")
T_FATO_JOG = tbl(SCHEMA_GOLD, "fato_jogador_partida")
T_FATO_TIME = tbl(SCHEMA_GOLD, "fato_time_partida")
T_MART_JOG = tbl(SCHEMA_GOLD, "mart_jogador_temporada")
T_MART_CLASS = tbl(SCHEMA_GOLD, "mart_classificacao")
T_FEATURES = tbl(SCHEMA_GOLD, "feature_similaridade_jogador")

T_DQ = tbl(SCHEMA_GOV, "dq_resultados")
T_CATALOGO = tbl(SCHEMA_GOV, "catalogo_dados")


# ── De-para de colunas Silver -> Gold ───────────────────────────────────────────

# coluna StatsBomb (Silver) -> coluna da fato_jogador_partida (Gold)
# usado tanto no ETL da Gold quanto na linhagem do catálogo, então só mexer aqui
MAPA_FATO_JOG = {
    "player_match_minutes": "minutos",
    "player_match_goals": "gols",
    "player_match_np_goals": "gols_sem_penalti",
    "player_match_assists": "assistencias",
    "player_match_np_shots": "finalizacoes_sem_penalti",
    "player_match_np_shots_on_target": "finalizacoes_no_alvo",
    "player_match_np_xg": "xg_sem_penalti",
    "player_match_np_xg_per_shot": "xg_por_finalizacao",
    "player_match_xa": "xa",
    "player_match_key_passes": "passes_decisivos",
    "player_match_through_balls": "passes_em_profundidade",
    "player_match_passes": "passes",
    "player_match_successful_passes": "passes_certos",
    "player_match_forward_passes": "passes_para_frente",
    "player_match_op_f3_passes": "passes_terco_final",
    "player_match_passes_into_box": "passes_para_area",
    "player_match_deep_progressions": "progressoes_profundas",
    "player_match_crosses": "cruzamentos",
    "player_match_successful_crosses": "cruzamentos_certos",
    "player_match_long_balls": "bolas_longas",
    "player_match_successful_long_balls": "bolas_longas_certas",
    "player_match_dribbles": "dribles_certos",
    "player_match_touches": "toques",
    "player_match_touches_inside_box": "toques_na_area",
    "player_match_tackles": "desarmes",
    "player_match_interceptions": "interceptacoes",
    "player_match_ball_recoveries": "recuperacoes",
    "player_match_pressures": "pressoes",
    "player_match_counterpressures": "contrapressoes",
    "player_match_pressure_regains": "recuperacoes_pos_pressao",
    "player_match_defensive_actions": "acoes_defensivas",
    "player_match_clearances": "cortes",
    "player_match_aerials": "duelos_aereos",
    "player_match_successful_aerials": "duelos_aereos_vencidos",
    "player_match_dribbled_past": "vezes_driblado",
    "player_match_fouls": "faltas_cometidas",
    "player_match_fouls_won": "faltas_sofridas",
    "player_match_dispossessions": "perdas_de_posse",
    "player_match_turnovers": "erros_com_bola",
    "player_match_xgchain": "xg_chain",
    "player_match_xgbuildup": "xg_buildup",
    "player_match_obv": "obv_total",
    "player_match_obv_pass": "obv_passe",
    "player_match_obv_dribble_carry": "obv_conducao",
    "player_match_obv_defensive_action": "obv_defesa",
    "player_match_obv_shot": "obv_finalizacao",
    "player_match_possession": "posse_time",
    "player_match_goals_conceded": "gols_sofridos_gk",
    "player_match_gsaa": "gsaa_gk",
}


# ================================================================================
# FUNÇÕES UTILITÁRIAS
# ================================================================================

def salvar_tabela(df: DataFrame, nome_tabela: str, comentario: str | None = None) -> None:
    """
    Grava uma tabela gerenciada no Unity Catalog com carga completa (full refresh).

    Usa overwrite + overwriteSchema, então rodar o pipeline de novo sempre chega no mesmo estado final.
    Como a temporada 2025 é um conjunto fechado, carga completa é mais simples e segura que incremental.

    Args:
        df: DataFrame a ser gravado
        nome_tabela: Nome completo da tabela (usar as constantes T_* ou tbl())
        comentario: Descrição da tabela, vira o COMMENT no catálogo (opcional)

    Returns:
        None: só grava e imprime a contagem de linhas
    """
    (df.write
       .format(TABLE_FORMAT)
       .mode("overwrite")
       .option("overwriteSchema", "true")
       .saveAsTable(nome_tabela))
    if comentario:
        # escapa aspas simples pra não quebrar o COMMENT ON TABLE
        spark.sql(f"COMMENT ON TABLE {nome_tabela} IS '{comentario.replace(chr(39), chr(92) + chr(39))}'")
    n = spark.table(nome_tabela).count()
    print(f"[OK] {nome_tabela} - {n:,} linhas gravadas")


def novo_id_carga() -> str:
    """
    Gera um ID único para a carga, usado na rastreabilidade das tabelas Bronze.

    Returns:
        str: Timestamp UTC + 8 caracteres de um uuid, ex.: 20250925T143012-a1b2c3d4
    """
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"


print(f"[INFO] Catálogo: {CATALOG} | Temporada: {TEMPORADA} | Landing: {LANDING_PATH}")
