# SIRCA — Ciclo 2

Esta versão reúne o componente de organização e consulta, o tratamento da base, a estrutura do banco e as consultas PN-01 a PN-05. A forma mais simples de começar é pelo Colab.

## Como executar no Colab

1. [Abra o notebook](https://colab.research.google.com/github/gomesrian241-tech/RIAN-1PROJETO/blob/main/sirca/SIRCA_Equipe_E_Ciclo_2.ipynb).
2. Execute a primeira célula para preparar o ambiente.
3. Execute os testes sem a base. São esperados 49 testes aprovados e dois testes de integração não selecionados.
4. Envie os três arquivos originais juntos ou o pacote `SIRCA_EQUIPE_E_CICLO_2.zip` na etapa de envio.
5. Continue para tratar os dados, rodar os 51 testes, conferir o banco e abrir o menu do componente.

O notebook está salvo sem saídas de execução. Os scripts foram conferidos localmente; a execução em uma sessão real do Colab ainda precisa ser validada pela equipe. Para carregar uma versão nova do código, reinicie o ambiente de execução e abra novamente o notebook atualizado.

## Como executar no computador

São necessários Python 3.11 ou superior e Node 18 ou superior para a conferência SQL. Dentro da pasta `sirca`, instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Coloque os seguintes arquivos em `dados/brutos/`:

- `Instituto_Semear_planilhas_operacionais_2024-2026.xlsx`
- `frequencia_export_sistema_antigo.csv`
- `doacoes_2026.csv`

Depois execute:

```bash
python scripts/tratar_dados.py
python -m pytest componente/testes -q
python componente/src/main.py --resumo
python componente/src/main.py
npm install
npm run test:banco
python scripts/conferir_resultados.py
python estudo/calcular.py
```

O menu fica aberto até a opção de saída. Depois de encerrá-lo, continue com os demais comandos.

Para testar apenas as funções que não dependem da base:

```bash
python -m pytest componente/testes -q -k 'not test_csv_igual_modelo_etl and not test_carga_balanco_sem_descartes_ocultos'
```

## Tratamento e banco

O tratamento usa a referência de 22/10/2026 e mantém os arquivos brutos sem alterações. Cada linha recebe uma decisão. O relatório de rejeições informa o motivo de cada descarte, e as conversões de presença ficam registradas em arquivo próprio.

A carga gera os CSV tratados, as evidências e `banco/02_carregar_dados.sql`. O notebook também gera `banco/semear_dump.sql`, reunindo a criação e a carga para restauração em um banco vazio.

Para usar PostgreSQL instalado, execute os scripts de criação, carga e consulta nessa ordem, com `psql -v ON_ERROR_STOP=1`. Use um banco vazio ou um esquema dedicado. A carga não deve ser repetida sobre registros já existentes.

A conferência automatizada usa PostgreSQL 17.5 embarcado no PGlite 0.3.14. Ela contém 17 verificações. As cinco consultas também são comparadas com cálculos feitos em Python. Essa conferência não substitui a validação no PostgreSQL 16 do laboratório.

## Como o componente funciona

- A lista guarda os registros carregados dos CSV tratados.
- O índice por código permite localizar cadastros; a busca por nome usa uma lista ordenada e considera o nome completo após normalização.
- Duas pilhas controlam desfazer e refazer lançamentos da sessão.
- Duas filas organizam o atendimento, preservando a ordem de chegada dentro dos grupos prioritário e comum.

O componente lê os CSV e não acessa diretamente o banco. Os novos lançamentos ficam em memória. Para guardá-los, use a opção 11 do menu antes de sair; a exportação gera um JSON e não altera automaticamente o banco ou os CSV.

## Arquivos para citar no PDF

| Material | Caminho neste repositório |
|---|---|
| Notebook | `sirca/SIRCA_Equipe_E_Ciclo_2.ipynb` |
| Código do componente | `sirca/componente/src/` |
| Testes | `sirca/componente/testes/` |
| Tratamento dos dados | `sirca/scripts/tratar_dados.py` |
| Estrutura do banco | `sirca/banco/01_criar_tabelas.sql` |
| Consultas de negócio | `sirca/banco/consultas/` |
| Conferência do banco | `sirca/scripts/verificar_banco.mjs` |
| Cálculo quantitativo | `sirca/estudo/calcular.py` |

Dados, carga SQL, dump, resultados, planilha preenchida e PDF ficam no local autorizado pelo professor. Indique também esse link e os respectivos caminhos no documento. A planilha preenchida e o PDF estão no pacote técnico da equipe; o notebook não recria esses dois documentos.

## Antes de entregar

Confira os nomes completos, os papéis do ciclo, os links, as atas e os registros de participação. A composição da folha de rosto precisa corresponder à equipe atual. Os tempos humanos e custos do estudo são cenários ilustrativos e devem permanecer identificados dessa forma.

A nota de proveniência da base, item 1, restringe sua publicação. Não envie os dados a este repositório público. O `.gitignore` ajuda no uso local do Git, mas não bloqueia uploads manuais. Revise as saídas do Colab antes de compartilhar ou salvar uma cópia.

Houve apoio de ChatGPT/Codex na preparação e revisão, conforme a declaração do PDF.
