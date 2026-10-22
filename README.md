# Cadastro de Portaria

Sistema desktop para controlar a entrada e a saída de pessoas em uma portaria
(visitantes, moradores, entregadores e funcionários).

Trabalho da UC **Teoria da Computação e Compiladores**, da Faculdade UNA.

Feito em Python, usando só a biblioteca padrão (Tkinter, `csv`, `json`...).
Não precisa instalar nada além do Python.

---

## Como executar

**Requisito:** Python 3 com Tkinter (testado no Python 3.14, no Windows). O
instalador oficial do Python para Windows já inclui o Tkinter.

Abra um terminal na pasta do projeto e rode:

```bash
python index.py
```

Na primeira execução, o programa cria a pasta `dados/` e os arquivos de que
precisa.

---

## Funcionalidades

- **Cadastro de entrada:** nome, tipo de acesso, motivo e data/hora de entrada.
  Também aceita campos extras opcionais: telefone, empresa, pessoa visitada,
  observações e veículo (placa, modelo e cor).
- **Registro de saída:** com um clique, ou pelo atalho `Ctrl+R`, grava a
  data/hora atual como saída.
- **Edição e exclusão** de registros. A exclusão pede confirmação.
- **Situação e permanência calculadas na hora.** Mostra quem está no local, há
  quanto tempo está lá e quem já saiu.
- **Alerta de tempo máximo:** destaca quem passou do limite de permanência
  configurado. O padrão é 4 horas.
- **Pesquisa e filtros:**
  - texto livre (nome, ID, telefone, empresa, placa...);
  - tipo, situação, período e motivo;
  - empresa.

  Com o alerta ativo, o filtro de situação ganha as opções **No prazo** e
  **Excedido**.
- **Painel de indicadores:**
  - total de registros, quantos estão no local e quantos saíram;
  - entradas e entregadores de hoje;
  - quem está no local agora, separado por tipo.
- **Histórico de atividades:** registra cada cadastro, edição, saída,
  exclusão, exportação e mudança de configuração.
- **Exportação em CSV** (abre no Excel) dos registros filtrados ou do
  histórico de atividades. Para exportar tudo, basta limpar os filtros antes.
- **Tema claro e escuro**, e escolha das colunas exibidas na tabela.
- **Backup automático:** antes de cada salvamento, guarda uma cópia da versão
  anterior dos registros.

### Validações

Os dados são conferidos em duas etapas.

1. **Formato:** máscaras de digitação para datas e telefone, nome só com
   letras, placa no padrão antigo (`ABC1234`) ou Mercosul (`ABC1D23`), e
   limites de tamanho nos campos.
2. **Regras semânticas:**
   - a entrada e a saída não podem ser datas futuras;
   - a saída não pode ser anterior à entrada;
   - datas anteriores ao ano 2000 são recusadas.

---

## Atalhos de teclado

| Atalho        | Ação                                              |
|---------------|---------------------------------------------------|
| `Ctrl+N`      | Nova entrada                                      |
| `Ctrl+F`      | Ir para a pesquisa                                |
| `Ctrl+L`      | Limpar filtros                                    |
| `Ctrl+E`      | Editar o registro selecionado                     |
| `Ctrl+R`      | Registrar saída do selecionado                    |
| `Delete`      | Excluir o selecionado (com a tabela em foco)      |
| `Enter`       | Editar o selecionado / confirmar o formulário     |
| `Ctrl+S`      | Salvar (no formulário ou na aba Configurações)    |
| `Esc`         | Cancelar o formulário                             |

---

## Estrutura do projeto

```
Portaria/
├── index.py                  Ponto de entrada (inicia o programa)
├── nucleo/                   Dados e regras, sem interface gráfica
│   ├── constantes.py         Listas permitidas, limites, cores, colunas
│   ├── estado.py             Estado compartilhado (registros, config, widgets)
│   ├── utilitarios.py        Datas, textos, IDs, caminhos dos arquivos
│   ├── calculos.py           Situação, permanência e alerta
│   ├── persistencia.py       Leitura/gravação de CSV e JSON, backup, migração
│   ├── validacoes.py         Validações de formato e regras semânticas
│   ├── operacoes.py          Cadastrar, editar, registrar saída, excluir
│   ├── consultas.py          Pesquisa, filtros, ordenação, indicadores
│   └── exportacao.py         Montagem dos arquivos exportados
├── interface/                Telas em Tkinter
│   ├── base.py               Cores do tema, criação de widgets, status, abas
│   ├── janela.py             Janela principal, cabeçalho, troca de tema
│   ├── formulario.py         Janela de cadastro/edição
│   ├── mascaras.py           Máscaras e filtros de digitação
│   ├── filtros.py            Barra de pesquisa e filtros
│   ├── tabela.py             Aba Portaria: tabela, detalhes, menu de contexto
│   ├── dashboard.py          Painel de indicadores
│   ├── atualizacao.py        Atualização da tabela, detalhes e histórico
│   ├── acoes.py              Registrar saída, excluir, exportar
│   ├── aba_historico.py      Aba Histórico
│   ├── aba_configuracoes.py  Abas Configurações e Sobre/Ajuda
│   ├── navegacao.py          Criação das abas e atalhos de teclado
│   └── inicializacao.py      Montagem da interface e início do programa
└── dados/                    Arquivos de dados (criados automaticamente)
```

O código está dividido em duas camadas:

- `nucleo/` não usa Tkinter. Toda a lógica (validação, cálculos, gravação)
  fica nele e pode ser testada sem abrir a interface.
- `interface/` cuida só das telas. Ela chama as funções do núcleo e atualiza
  o que aparece na tela.

---

## Arquivos de dados (`dados/`)

| Arquivo                     | Conteúdo                                                        |
|-----------------------------|-----------------------------------------------------------------|
| `registros.csv`             | Registros principais (ID, nome, tipo, entrada, saída e extras)  |
| `registros_backup.csv`      | Cópia da versão anterior, atualizada a cada salvamento          |
| `registros_original_*.csv`  | Cópia guardada antes de uma migração ou correção do arquivo     |
| `historico.csv`             | Histórico de atividades                                         |
| `configuracoes.json`        | Tema, tempo máximo, alertas, colunas visíveis e último ID usado |

Os CSVs usam `;` como separador e codificação UTF-8, então abrem direto no
Excel.

A situação e a permanência **não** são gravadas no CSV. Elas são calculadas
sempre que o programa precisa delas.

---

## Observações

- O histórico é um registro local. Quem tem acesso à pasta pode editá-lo.
- O backup guarda só a versão imediatamente anterior dos registros.
- O controle de vagas de estacionamento não foi implementado.
