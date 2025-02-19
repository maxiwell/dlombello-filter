# dlombello-filter

Este projeto é uma ferramenta de linha de comando para filtrar e manipular dados de transações financeiras usando queries personalizadas.

## Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/seu-usuario/dlombello-filter.git
cd dlombello-filter
pip install -r requirements.txt
```

## Uso

### Comandos

#### `operacoes`

Filtra e manipula dados de operações financeiras.

```bash
./main.py operacoes [OPTIONS]
```

#### `proventos`

Filtra e manipula dados de proventos financeiros.

```bash
./main.py proventos [OPTIONS]
```

### Opções

- `-l`, `--list`: Lista todos os filtros salvos.
- `-f`, `--filter`: Aplica um filtro salvo.
- `-q`, `--query`: Query JQL para filtrar transações.
- `-a`, `--append`: Adiciona mais condições ao filtro chamado por `-f`.
- `-c`, `--columns`: Colunas a serem exibidas na saída.
- `-r`, `--replace`: Substitui a primeira palavra mágica.
- `--fetch`: Busca dados da API para popular os arquivos de sandbox.
- `--csv`: Salva a saída em um arquivo CSV.

### Exemplos de Uso

#### Listar todos os filtros salvos

Todos os filtros são salvos no arquivo `filters.json` e eles podem ser chamados tanto pela opção `operacoes` quanto pela opção `proventos`

```bash
./main.py operacoes --list
./main.py proventos --list
```

Saída esperada:

```
operacoes_cash_flow:
    corretora in ['nubank', 'inter', 'mercadopago', 'itau'] and {this_year},

ativos_desde_06_2024:
    ativo in ['IRDM11', 'VALE3'] and date > '01/06/2024'

trans_diff_itau:
    not (corretora ~ 'itau') and {last_month}
```

#### Aplicar um filtro salvo e exibir colunas específicas

```bash
./main.py operacoes --filter operacoes_cash_flow --columns "date, ativo, preco"
```

Saída esperada:

```
query: corretora in ['nubank', 'inter', 'mercadopago', 'itau'] and date >= '01/01/2025' and date <= '31/12/2025'
{'date': '2025-01-02', 'ativo': 'LCA JOHN DEERE', 'preco': 0.0},
{'date': '2025-01-02', 'ativo': 'LCA JOHN DEERE', 'preco': -1},
{'date': '2025-01-03', 'ativo': 'MERCADO PAGO', 'preco': -8},
{'date': '2025-01-03', 'ativo': 'TD:PRE2027', 'preco': 13},
{'date': '2025-01-03', 'ativo': 'TD:IPCA2029', 'preco': 27},
{'date': '2025-01-09', 'ativo': 'VALE3', 'preco': 65},
{'date': '2025-01-24', 'ativo': 'NUBANK', 'preco': -72},
{'date': '2025-01-31', 'ativo': 'NUBANK', 'preco': 19.45},
{'date': '2025-01-31', 'ativo': 'NUBANK', 'preco': -11.0},
{'date': '2025-02-05', 'ativo': 'NUBANK', 'preco': -63.0},
{'date': '2025-02-07', 'ativo': 'NUBANK', 'preco': -16.0},
{'date': '2025-02-10', 'ativo': 'ITAU CDB 100% CDI', 'preco': -48.89}
{
    "transactions": 12,
    "qtd": {
        "ITAU CDB 100% CDI": -1.0,
        "LCA JOHN DEERE": -1.0,
        "MERCADO PAGO": -1.0,
        "NUBANK": -3.0,
        "TD:IPCA2029": 1.5,
        "TD:PRE2027": 4.3,
        "VALE3": 100.0,
        "__total__": 99.8
    },
    "fluxo_caixa": {
        "INTER": -48.89,
        "ITAU": 48.89,
        "MERCADOPAGO": 8.0,
        "NUBANK": -142.55,
        "__total__": -134.55
    }
}
```

#### Adicionar condições a um filtro salvo

```bash
./main.py operacoes --filter filtro1 --append "OR preco > 100"
```

#### Salvar a saída em um arquivo CSV

```bash
./main.py operacoes --filter filtro1 --csv output.csv
```

## Arquivo de Configuração

O arquivo config.json é usado para configurar os endpoints da API, autorizações e totalizadores. Aqui está um exemplo de como o arquivo config.json pode ser estruturado:

```json
{
    "authorization": "DLP-xxxx",
    "operacoes": {
        "sandbox": "sandbox_operacoes.json",
        "endpoint": "https://users.dlombelloplanilhas.com/operacoes",
        "columns": "date, corretora, ativo, qtd, evento, preco, qtd_atual, qtd_ant, fluxo_caixa",
        "totalizers": [
            {
                "column": "qtd",
                "group_by": "ativo"
            },
            {
                "column": "fluxo_caixa",
                "group_by": "corretora"
            }
        ]
    },
    "proventos": {
        "sandbox": "sandbox_proventos.json",
        "endpoint": "https://users.dlombelloplanilhas.com/proventos",
        "columns": "date, corretora, ativo, evento, valor"
    }
}
```

### Detalhamento das Opções de Configuração

- `endpoint`: URL do endpoint da API.
- `authorization`: Chave de autorização para acessar a API.
- `sandbox`: Arquivo de sandbox para armazenar dados localmente.
- `columns`: Colunas padrão a serem exibidas na saída. A opção --column sobreescreve esse valor.
- `totalizers`: Configurações para calcular totalizadores caso queira. A opção `group_by` é opção.

## Opções de Queries

As queries são escritas em uma linguagem de consulta semelhante ao JQL do Jira. Aqui estão algumas opções de queries que você pode usar:

- `ativo = 'AAPL'`: Filtra transações onde o ativo é 'AAPL'.
- `preco > 100 OR NOT corretora ~ 'inter'`: Filtra transações onde o preço é maior que 100.
- `date >= '01/01/2025' AND date <= '31/12/2025'`: Filtra transações dentro de um intervalo de datas.

Você pode combinar múltiplas condições usando operadores lógicos como `AND`, `OR` and trocar a prioridade de expressões usando `( )`.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.