# Scripts de Análise do Cascade - Guia do Cliente

## Visão Geral
Estes dois scripts Python permitem coletar e analisar dados de uso do Cascade, gerando relatórios detalhados sobre linhas de código sugeridas vs aceitas, uso de modelos e ferramentas por usuário.

## PASSO 1: CascadeLinesPerUser.py
**Coleta de Dados da API**

### O que faz:
- Conecta-se à API de analytics do Codeium usando sua chave de serviço
- Processa uma lista de endereços de email (um por vez)
- Coleta três tipos de dados para cada usuário:
  - **cascade_lines**: Linhas sugeridas vs aceitas
  - **cascade_runs**: Uso de modelos, mensagens enviadas, prompts utilizados
  - **cascade_tool_usage**: Estatísticas de uso de ferramentas (CODE_ACTION, VIEW_FILE, etc.)
- Salva todos os resultados em `cascade_analytics_results.json`

### Configuração necessária:
- **Chave de Serviço**: Criar em https://windsurf.com/team/settings
  - Ir para Service Key Configuration → Configure → Add service key
  - Usar Role: admin OU criar role personalizada com acesso somente leitura:
    - https://windsurf.com/team/settings → Role Management → Configure → Create role
    - Atribuir permissões "Analytics Read" à nova role
- Arquivo `.env` com `SERVICE_KEY=sua_chave_aqui`
- Lista de emails no código (função `main()`)
- Período de análise: Atualmente configurado de 1º de agosto de 2025 até hoje

### Como executar:
```bash
python3 CascadeLinesPerUser.py
```

## PASSO 2: generate_csv_reports.py
**Geração de Relatórios CSV**

### O que faz:
- Lê o arquivo JSON gerado pelo script anterior
- Cria dois relatórios CSV estruturados:

#### 1. Relatório Diário (`daily_user_analytics_YYYYMMDD.csv`)
- Uma linha por usuário/data
- Colunas: email, data, linhas aceitas/sugeridas, % aceitação, modelos usados, mensagens, prompts

#### 2. Relatório Agregado (`aggregated_user_analytics_YYYYMMDD.csv`)
- Uma linha por usuário com totais
- Colunas: email, totais de linhas/mensagens/prompts, mais uma coluna para cada ferramenta do Cascade

### Como executar:
```bash
python3 generate_csv_reports.py
```

## Fluxo de Trabalho Completo
1. **Configurar**: Adicionar chave de serviço no arquivo `.env`
2. **Personalizar**: Editar lista de emails em `CascadeLinesPerUser.py`
3. **Coletar**: Executar `python3 CascadeLinesPerUser.py`
4. **Analisar**: Executar `python3 generate_csv_reports.py`
5. **Visualizar**: Importar os CSVs no Excel, Tableau ou outra ferramenta de análise

## Dependências
```bash
pip install requests python-dotenv pandas
```

## Arquivos de Saída
- `cascade_analytics_results.json` - Dados brutos da API
- `daily_user_analytics_YYYYMMDD.csv` - Relatório diário
- `aggregated_user_analytics_YYYYMMDD.csv` - Relatório agregado

Os relatórios CSV são ideais para análise de padrões de uso, produtividade dos usuários e adoção de ferramentas do Cascade.
