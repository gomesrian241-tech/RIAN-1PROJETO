# SIRCA — Equipe E — Ciclo 2

Código do componente, tratamento auditável, estrutura PostgreSQL e consultas PN-01 a PN-05. Preparado com apoio de ChatGPT/Codex; revisão e responsabilidade acadêmica cabem à equipe. Este commit de preparação não comprova contribuições dos demais integrantes.

## Executar no Colab

[Abrir notebook](https://colab.research.google.com/github/gomesrian241-tech/RIAN-1PROJETO/blob/main/sirca/SIRCA_Equipe_E_Ciclo_2.ipynb). Execute as células em ordem. O notebook recebe os três arquivos brutos no ambiente temporário ou extrai apenas esses arquivos do pacote técnico ZIP fornecido à equipe. Não contém dados nem saídas previamente executadas. Não compartilhe uma cópia com dados ou saídas sem observar a autorização institucional. A execução em sessão real do Colab precisa ser conferida pela equipe.

A base do caso, inclusive sintética, tem publicação restrita pela nota de proveniência, item 1. Dados, carga SQL, dump, planilhas preenchidas, resultados identificáveis e PDF com dados ficam no ambiente autorizado pelo professor. O GitHub público contém apenas os fontes. O `.gitignore` é uma prevenção local; não impede uploads manuais.

## Executar localmente

Requer Python 3.11+ e, para conferir SQL, Node 18+. Da pasta `sirca`:

```bash
python -m pip install -r requirements.txt
# Disponibilize os três arquivos autorizados em dados/brutos/ antes do tratamento.
python scripts/tratar_dados.py
python -m pytest componente/testes -q
python componente/src/main.py --resumo
python componente/src/main.py
npm install
npm run test:banco
python scripts/conferir_resultados.py
python estudo/calcular.py
```

Sem a base é possível rodar 49 testes de unidade:

```bash
python -m pytest componente/testes -q -k 'not test_csv_igual_modelo_etl and not test_carga_balanco_sem_descartes_ocultos'
```

Os dois testes restantes conferem a integração da carga e exigem a base. Após o tratamento, a suíte completa contém 51 testes. A conferência SQL usa PostgreSQL embarcado PGlite 0.3.14; não equivale a testar o PostgreSQL 16 do laboratório.

Arquivos esperados em `dados/brutos/`: `Instituto_Semear_planilhas_operacionais_2024-2026.xlsx`, `frequencia_export_sistema_antigo.csv` e `doacoes_2026.csv`. A referência de tratamento é 22/10/2026. O tratamento gera CSV, relatório de rejeições, conversões de presença, evidências e `banco/02_carregar_dados.sql` localmente. Não publique esses arquivos neste repositório público. O dump pode ser gerado localmente concatenando a criação e a carga, em banco vazio.

## Caminhos para citar no PDF

| Material | Caminho neste repositório |
|---|---|
| Notebook | `sirca/SIRCA_Equipe_E_Ciclo_2.ipynb` |
| Código | `sirca/componente/src/` |
| Testes | `sirca/componente/testes/` |
| Tratamento e rejeições | `sirca/scripts/tratar_dados.py` |
| Estrutura do banco | `sirca/banco/01_criar_tabelas.sql` |
| Consultas | `sirca/banco/consultas/` |
| Conferência SQL | `sirca/scripts/verificar_banco.mjs` |
| Modelo quantitativo | `sirca/estudo/calcular.py` |

Para dados, carga, dump, planilha preenchida, atas e PDF, informe no documento o link real da pasta autorizada pelo professor e o respectivo caminho. Os antigos caminhos sem `sirca/` precisam desse prefixo quando apontarem para este GitHub. A equipe ainda precisa atualizar os links no PDF, confirmar nomes completos, papéis, atas e evidências de participação. O README anterior lista Higor; confirme a composição efetiva e ajuste a folha de rosto antes da entrega.

## Limites do componente

O terminal lê os CSV tratados; não se conecta diretamente ao banco. Novos lançamentos ficam em memória e precisam ser exportados pelo menu antes de sair. A busca por nome é exata após normalização. As duas pilhas oferecem desfazer/refazer; as duas filas mantêm prioridade e ordem de chegada. Tempos humanos e custos do estudo são hipóteses ilustrativas, não medições da equipe.
