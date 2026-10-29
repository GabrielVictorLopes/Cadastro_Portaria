# Instalação e Manutenção

Guia para instalar, executar e manter o **Cadastro de Portaria**: requisitos,
localização dos arquivos, backups, ajustes comuns e solução de problemas.
Para a organização do código, veja a
[Documentação técnica](documentacao_tecnica.md).

## Sumário

1. [Requisitos](#1-requisitos)
2. [Instalação](#2-instalação)
3. [Execução](#3-execução)
4. [Localização dos arquivos](#4-localização-dos-arquivos)
5. [Backups](#5-backups)
6. [Manutenção](#6-manutenção)
7. [Solução de problemas](#7-solução-de-problemas)

---

## 1. Requisitos

| Item | Requisito |
|------|-----------|
| Sistema operacional | Windows 10 ou 11 (ambiente em que o sistema foi desenvolvido e testado). |
| Python | Python 3 com Tkinter. Testado no **Python 3.14**. |
| Bibliotecas externas | Nenhuma. Só a biblioteca padrão. |
| Tela | Recomendado 1280 × 860 ou maior. A janela abre ajustada à tela e aceita no mínimo 1000 × 640. |
| Disco | Poucos kilobytes por centena de registros. A pasta do projeto precisa permitir gravação. |
| Programa para planilhas (opcional) | Excel ou similar para abrir os CSVs exportados. |

**Outros sistemas operacionais:** o código usa apenas recursos portáveis do
Python, com duas particularidades do Windows: a fonte **Segoe UI** (em outro
sistema o Tkinter usa uma fonte substituta) e o botão **Abrir pasta dos
arquivos** (fora do Windows, ele apenas mostra o caminho da pasta). Em
distribuições Linux, o Tkinter costuma ser instalado à parte (por exemplo,
pacote `python3-tk`). Esses ambientes não foram testados.

## 2. Instalação

1. Instale o Python pelo site oficial (<https://www.python.org/downloads/>).
   O instalador para Windows já inclui o Tkinter. Marque a opção **Add
   python.exe to PATH**.
2. Confirme a instalação em um terminal:

   ```bash
   python --version
   python -c "import tkinter; print(tkinter.TkVersion)"
   ```

   O segundo comando deve mostrar um número (por exemplo, `8.6`).
3. Copie a pasta do projeto para o computador (ou clone o repositório com
   `git clone`).

Não há etapa de compilação nem instalação de pacotes.

## 3. Execução

Na pasta do projeto:

```bash
python index.py
```

Alternativas no Windows:

| Forma | Observação |
|-------|------------|
| `py index.py` | Usa o inicializador do Python para Windows. |
| `python "C:\caminho\para\Portaria\index.py"` | Funciona a partir de qualquer pasta; os dados ficam sempre em `dados/` dentro do projeto. |
| `pythonw index.py` | Abre o sistema sem a janela de terminal. |
| Duplo clique em `index.py` | Funciona se os arquivos `.py` estiverem associados ao Python. |

Na primeira execução, a pasta `dados/` é criada automaticamente quando o
sistema precisa gravar algo.

## 4. Localização dos arquivos

Todos os arquivos de dados ficam na pasta **`dados/`**, dentro da pasta do
projeto. O caminho é calculado a partir da localização do código
(`PASTA_DADOS` em [`nucleo/constantes.py`](../nucleo/constantes.py)), e não
da pasta de onde o comando foi executado. O caminho completo aparece na aba
**Configurações**, e o botão **Abrir pasta dos arquivos** (aba Sobre / Ajuda)
abre a pasta.

| Arquivo | Conteúdo | Criado / atualizado |
|---------|----------|---------------------|
| `registros.csv` | Registros de entrada e saída. | A cada cadastro, edição, saída ou exclusão. |
| `registros_backup.csv` | Versão anterior de `registros.csv`. | Antes de cada gravação de `registros.csv`. |
| `registros_original_AAAAMMDD_HHMMSS.csv` | Cópia do arquivo antes de uma migração ou correção automática. | Só quando o carregamento precisa corrigir o arquivo. Nunca sobrescrita. |
| `historico.csv` | Histórico de atividades. | Uma linha a cada atividade. |
| `configuracoes.json` | Tema, tempo máximo, alerta, colunas visíveis e próximo ID. | Ao salvar configurações, trocar o tema e cadastrar. |
| `portaria.lock` | Trava que impede duas cópias abertas. Vazio. | Mantido aberto enquanto o sistema roda. A trava é liberada pelo sistema operacional ao fechar o programa, mesmo após uma queda. Não é preciso apagá-lo. |
| `*.tmp` | Arquivos temporários de gravação. | Existem por instantes durante a gravação. Se sobrar algum após uma falha, pode ser apagado com o sistema fechado. |
| CSVs exportados | Registros filtrados ou histórico. | No local escolhido pelo usuário (a pasta sugerida é `dados/`). |

### Formato dos arquivos

- **CSV**: separador `;`, codificação UTF-8 com BOM, datas no formato
  `dd/mm/aaaa hh:mm` (histórico: `dd/mm/aaaa hh:mm:ss`). Abrem diretamente no
  Excel.
- **JSON**: UTF-8, com indentação.

Exemplo de `registros.csv`:

```text
ID;Nome;Tipo de acesso;Entrada;Saída;Telefone;Empresa;Pessoa visitada;Motivo;Observações;Placa;Modelo;Cor
1;Mariana Lopes;Visitante;29/10/2026 13:08;;(31) 98765-4321;;Carlos Menezes;Visita;;;;
2;Rafael Duarte;Entregador;29/10/2026 16:28;29/10/2026 16:36;;Rápido Express;;Entrega;;;;
```

Exemplo de `configuracoes.json`:

```json
{
  "tema": "claro",
  "tempo_max_horas": 4,
  "alerta_ativo": true,
  "mostrar_motivo": true,
  "mostrar_veiculo": false,
  "proximo_id": 3
}
```

### Outros arquivos do projeto

| Caminho | Pode apagar? |
|---------|--------------|
| `__pycache__/` (em qualquer pasta) | Sim. São arquivos compilados que o Python recria sozinho. |
| `_backup/index_antigo.py` | Não é usado pelo sistema; mantido como referência da versão anterior. |
| `docs/` | Documentação; não interfere no funcionamento. |
| `testes/` | Testes automatizados; não interferem no funcionamento. Mantenha para a manutenção. |
| `.gitignore` | Impede que `dados/` e arquivos gerados sejam enviados ao Git. Não apague. |

## 5. Backups

### 5.1 O que o sistema faz sozinho

| Proteção | Alcance |
|----------|---------|
| `registros_backup.csv` | Guarda **somente a versão imediatamente anterior**. É sobrescrito a cada gravação. |
| `registros_original_*.csv` | Guardado apenas antes de correções/migrações automáticas na abertura. |
| Gravação segura | O arquivo principal é substituído só depois que o novo foi gravado por completo. Uma falha no meio não corrompe o arquivo. |

O sistema **não** faz cópia de `historico.csv` nem de `configuracoes.json`, e
não mantém versões antigas além da anterior.

### 5.2 Backup manual (recomendado)

1. Feche o sistema.
2. Copie a pasta `dados/` inteira para outro local (pendrive, outro disco ou
   pasta de backups), renomeando com a data, por exemplo
   `dados_2026-10-29`.
3. Mantenha mais de uma cópia (por exemplo, a de cada semana).

Defina a frequência conforme o volume de movimento da portaria. Se os
backups forem guardados em nuvem, observe os cuidados em
[Segurança e limitações](seguranca_e_limitacoes.md#2-proteção-dos-dados-pessoais).

### 5.3 Restauração

**A partir de um backup manual:**

1. Feche o sistema.
2. Copie os arquivos da cópia de segurança para dentro de `dados/`,
   substituindo os atuais.
3. Abra o sistema e confira os registros.

**A partir de `registros_backup.csv`** (para desfazer a última alteração):

1. Feche o sistema **sem fazer nenhuma outra alteração**. Cada gravação
   sobrescreve o backup.
2. Guarde uma cópia do `registros.csv` atual, por segurança.
3. **Copie** `registros_backup.csv` sobre `registros.csv`.
4. Abra o sistema.

Após restaurar, os IDs não são reaproveitados, porque o próximo ID salvo em
`configuracoes.json` continua valendo. O histórico de atividades não é
alterado pela restauração.

## 6. Manutenção

### 6.1 Ajustes por constantes

A maior parte dos parâmetros fica em
[`nucleo/constantes.py`](../nucleo/constantes.py). Feche o sistema antes de
editar o código.

| Parâmetro | Constante | Cuidados |
|-----------|-----------|----------|
| Tipos de acesso | `TIPOS` | Registros com um tipo que deixou de existir serão **ignorados** ao abrir (com aviso e cópia do original). Os indicadores por tipo usam os nomes "Visitante", "Funcionário", "Morador" e "Entregador" em [`consultas.py`](../nucleo/consultas.py). |
| Motivos | `MOTIVOS` | Registros com motivo removido continuam carregando, mas a edição exigirá escolher um motivo válido. |
| Limites de tamanho | `MAX_NOME`, `MAX_EMPRESA`, `MAX_MODELO`, `MAX_COR`, `MAX_OBSERVACOES` | Valem para novos cadastros e edições. |
| Ano mínimo | `ANO_MINIMO` | Valor padrão: 2000. |
| DDDs aceitos | `DDDS_VALIDOS` | Lista oficial da Anatel; atualize se novos DDDs forem criados. |
| Caracteres bloqueados no início de textos livres | `INICIO_FORMULA` | Proteção contra injeção de fórmulas; não remova itens. |
| Configurações padrão | `CONFIG_PADRAO` | Usadas quando `configuracoes.json` não existe ou tem valores inválidos. |
| Faixa do tempo máximo | 1 a 72 | Definida em `aba_configuracoes.py` (tela) e `persistencia.py` (carregamento). Altere nos dois lugares. |
| Cores dos temas | `PALETAS` | As chaves `azul`/`azul_h` guardam a cor principal (laranja). |
| Colunas da tabela | `COLUNAS_TABELA` | Larguras e alinhamentos. |
| Versão exibida | `VERSAO` | Atualize ao publicar uma nova versão. |

### 6.2 Incluir um novo campo no cadastro

Um novo campo exige alterações em vários pontos. Consulte a
[Documentação técnica](documentacao_tecnica.md) e revise, no mínimo:

1. `CHAVES_TEXTO`, `ROTULOS` e `COLUNAS_CSV` em `constantes.py`.
2. A validação em `validar_dados()` (`validacoes.py`).
3. O formulário em `interface/formulario.py` (lista `extras` ou
   `principais`, e `CHAVES_EXTRAS` se for adicional).
4. O painel de detalhes em `interface/atualizacao.py` e a exportação em
   `nucleo/exportacao.py`.
5. Pesquisa (`filtrar_registros()`), se o campo deve ser pesquisável.

Arquivos existentes continuam abrindo: o carregamento identifica as colunas
pelo título e regrava o arquivo no novo formato (guardando o original).

### 6.3 Rotina sugerida

| Frequência | Tarefa |
|------------|--------|
| Conforme o uso | Backup manual da pasta `dados/` ([5.2](#52-backup-manual-recomendado)). |
| Mensal | Verificar se há arquivos `registros_original_*.csv` acumulados; conferir o motivo nos avisos e arquivá-los. |
| Mensal | Avaliar o tamanho de `historico.csv` e, se necessário, exportar e arquivar o histórico (veja a observação abaixo). |
| A cada alteração no código | Executar a suíte automatizada ([6.5](#65-testes-automatizados)) e os [casos manuais](casos_de_teste.md) afetados (veja a matriz de rastreabilidade). |

> O sistema não tem função para arquivar ou limpar o histórico. Para
> reduzir o `historico.csv`, feche o sistema, guarde uma cópia do arquivo e
> remova linhas antigas em um editor de texto, mantendo a primeira linha
> (cabeçalho).

### 6.4 Controle de versão (Git)

O projeto tem um arquivo [`.gitignore`](../.gitignore) que impede versionar
a pasta `dados/` (dados pessoais), as pastas `__pycache__/` e os arquivos
temporários. Assim, um `git add .` não envia mais os dados de uso real.

> **Atenção:** o commit `f78d6e8`, já publicado no GitHub, ainda contém a
> pasta `dados/` com dados reais. O `.gitignore` não altera commits antigos.
> Para remover os dados do histórico publicado, é preciso reescrever o
> histórico (por exemplo, com `git filter-repo --path dados --invert-paths`)
> e enviar com `git push --force`, combinando antes com todos que usam o
> repositório. Se o repositório for público, considere torná-lo privado
> enquanto isso. Veja [Segurança e limitações](seguranca_e_limitacoes.md).

### 6.5 Testes automatizados

Na pasta do projeto:

```bash
python -m unittest discover -s testes -t . -v
```

Os 41 testes rodam em poucos segundos, usam uma pasta temporária e não
alteram `dados/`. Ao corrigir um defeito, acrescente um teste que o
reproduza em [`testes/test_nucleo.py`](../testes/test_nucleo.py). Detalhes em
[Casos de teste](casos_de_teste.md#14-testes-automatizados-do-núcleo).

## 7. Solução de problemas

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| `python` não é reconhecido como comando | Python não instalado ou fora do PATH. | Reinstale marcando **Add python.exe to PATH**, ou use `py index.py`. |
| `ModuleNotFoundError: No module named 'tkinter'` | Python sem Tkinter. | No Windows, reinstale pelo instalador oficial com a opção "tcl/tk and IDLE". No Linux, instale o pacote do Tkinter (ex.: `python3-tk`). |
| `ModuleNotFoundError: No module named 'nucleo'` ou `'interface'` | Estrutura de pastas incompleta ou `index.py` movido. | Mantenha `index.py`, `nucleo/` e `interface/` juntos na mesma pasta. |
| "Erro ao salvar ... A operação foi DESFEITA" | `registros.csv` aberto no Excel, pasta sem permissão de gravação, disco cheio ou arquivo bloqueado pela sincronização de nuvem (OneDrive). | Feche o arquivo no Excel, aguarde a sincronização ou verifique as permissões e tente novamente. Nada foi perdido. |
| "Não foi possível gravar o arquivo de configurações" | Mesmas causas acima, para `configuracoes.json`. | Corrija a causa e salve as configurações de novo. |
| Aviso "Atenção ao carregar os registros" | O arquivo tinha linhas inválidas, formato antigo ou IDs repetidos. | Leia os avisos. Linhas ignoradas continuam no arquivo `registros_original_*.csv` indicado; corrija-as lá e copie-as de volta para `registros.csv` com o sistema fechado. |
| Registro sumiu depois de editar o CSV no Excel | A linha ficou inválida (data em outro formato, tipo inexistente, nome vazio). | Veja o aviso ao abrir e o arquivo `registros_original_*.csv`. Prefira editar pelo sistema. |
| Acentos estranhos ao abrir um CSV | Arquivo salvo por outro programa em outra codificação. | O sistema lê UTF-8 e CP-1252 automaticamente. Para exportações, abra pelo Excel normalmente (o arquivo tem BOM). |
| Alerta "Excedido" não aparece | Alerta desligado ou tempo máximo maior que a permanência. | Confira a aba Configurações. |
| Opções "No prazo"/"Excedido" não aparecem no filtro | Alerta desligado. | Ligue o alerta e salve. |
| Tabela vazia, mas há registros | Filtros ativos. | Clique em **Limpar filtros** (`Ctrl+L`). |
| Permanência mostra só "Em andamento" ou "—" | Data/hora do computador anterior à entrada do registro. | Corrija o relógio do Windows ou a data do registro. |
| Janela não cabe na tela | Resolução baixa ou escala do Windows alta. | Reduza a escala de exibição do Windows ou use uma resolução de pelo menos 1000 × 640. |
| "O sistema já está aberto em outra janela", mas nenhuma janela aparece | Outra cópia está rodando sem janela visível (por exemplo, aberta com `pythonw`) ou a janela está minimizada. | Procure a janela na barra de tarefas. Se não houver, finalize o processo `python`/`pythonw` no Gerenciador de Tarefas e abra de novo. A trava nunca fica presa depois que o programa fecha. |
| Mensagem "Erro inesperado" | Defeito não previsto no código. | Os dados já salvos não são afetados. Anote o detalhe, execute pelo terminal (`python index.py`) para ver o rastreamento completo e registre o defeito. |
| "Abrir pasta dos arquivos" só mostra um caminho | Sistema operacional diferente do Windows. | Abra a pasta manualmente pelo caminho exibido. |
