# Evidências (screenshots)

Prints capturados do workspace Databricks Free Edition após a execução do pipeline (job `mvp_brasileirao_pipeline`, 7 tarefas, sucesso).

| Arquivo | Conteúdo | Status |
|---|---|---|
| `01_volume_landing.jpg` | Volume `bronze.landing` com os 2 CSVs | ✔ |
| `02_bronze_tabelas.jpg` | Tabela Bronze (todas as colunas STRING) — Sample Data | ✔ |
| `03_catalogo_colunas.jpg` | `gold.mart_classificacao`: comentários de coluna (descrição, domínio, origem) + PK/FK | ✔ |
| `04_diagrama_er.jpg` | Diagrama ER do Unity Catalog para `fato_jogador_partida` | ✔ |
| `05_pipeline_execucao.jpg` | Execução do job: 7 tarefas com sucesso e duração | ✔ |
| `06_gold_tabelas.jpg` | Schema `gold` com as 8 tabelas | ✔ |
| `07_dq_resultados.jpg` | Resumo das 207 checagens de qualidade (dimensão × status) | ✔ |
| `08_p1.png` | P1: Botafogo × liga (por jogo) | ✔ |
| `09_p2.png` | P2: correlação xG × pontos e pontos previstos pelo xG | ✔ |
| `10_p3.png` | P3: líderes per-90 e percentis do Botafogo | ✔ |
| `11_p4.png` | P4: finalização acima/abaixo do esperado | ✔ |
| `12_p5.png` | P5: concentração de minutos por elenco | ✔ |
| `13_p6.png` | P6: similaridade com Alexander Barboza | ✔ |
| `15_job_grafo.jpg` | Grafo de dependências do job | ✔ |
