# Relatório de Auditoria — Versão 3.1

Auditoria de qualidade (QA), segurança, análise de requisitos e
documentação do **Cadastro de Portaria**. O relatório lista cada problema
encontrado, a evidência, a correção aplicada e o teste que comprova a
correção. Ao final, estão os riscos que permanecem e as recomendações.

## Sumário

1. [Resumo executivo](#1-resumo-executivo)
2. [Escopo e método](#2-escopo-e-método)
3. [Achados no sistema](#3-achados-no-sistema)
4. [Achados na documentação](#4-achados-na-documentação)
5. [Verificação das correções](#5-verificação-das-correções)
6. [Riscos residuais e recomendações](#6-riscos-residuais-e-recomendações)
7. [Notas da versão 3.1](#7-notas-da-versão-31)

---

## 1. Resumo executivo

| Severidade | Achados | Corrigidos | Pendentes |
|------------|--------:|-----------:|----------:|
| Crítica | 1 | 1 (parcial) | 1 ação externa |
| Alta | 2 | 2 | 0 |
| Média | 5 | 5 | 0 |
| Baixa | 8 | 8 | 0 |
| **Total** | **16** | **16** | **1** |

Os pontos mais importantes:

- **Dados pessoais reais publicados no GitHub** (crítico). A pasta `dados/`
  estava versionada e foi enviada ao repositório remoto. O projeto deixou de
  versioná-la, mas o commit já publicado ainda contém os dados. **A limpeza
  do histórico remoto depende de uma decisão do responsável** (veja a
  [seção 6](#6-riscos-residuais-e-recomendações)).
- **Injeção de fórmulas (CSV injection)** e **perda de dados com duas
  cópias abertas** (altos): corrigidos.
- O projeto passou a ter **41 testes automatizados**. Executados contra a
  versão anterior do código, eles detectam 14 falhas; na versão 3.1, todos
  passam.

**Severidade:** *Crítica*: exposição de dados pessoais. *Alta*: perda de
dados ou risco de segurança explorável. *Média*: dado incorreto ou perdido
em situação plausível. *Baixa*: inconsistência, usabilidade ou robustez.

## 2. Escopo e método

**Escopo:** todo o código de `nucleo/` e `interface/`, `index.py`, os
arquivos de `dados/`, o repositório Git e os documentos de `docs/` e o
`README.md`.

| Técnica | Como foi aplicada |
|---------|-------------------|
| Análise estática | `pyflakes` (sem avisos) e busca por construções perigosas (`eval`, `exec`, `subprocess`, `pickle`, `shell=`): nenhuma encontrada. |
| Revisão manual de código | Leitura de todos os módulos, com foco em validação de entrada, gravação de arquivos, concorrência, tratamento de erros e coerência entre tela, arquivo e exportação. |
| Reprodução empírica | Cada suspeita foi reproduzida em uma **cópia isolada** do projeto, com dados fictícios, antes de ser corrigida. |
| Testes de regressão | Suíte automatizada executada na versão antiga (deve falhar) e na nova (deve passar). |
| Teste de fumaça da interface | Sistema aberto de verdade na cópia isolada para verificar trava, dicas, motivo em branco, refiltro, avisos e tratador de erros. |
| Revisão do repositório | `git ls-files`, `git log`, remotos e branches publicadas. |
| Revisão da documentação | Conferência de cada afirmação contra o código e análise de lacunas para uso, manutenção, testes e apresentação. |

A pasta `dados/` real **não foi alterada** durante a auditoria (conferido
por soma de verificação antes e depois dos testes).

## 3. Achados no sistema

### A-01 — Dados pessoais reais versionados e publicados · **Crítica** · Segurança

| | |
|-|-|
| **Problema** | `dados/registros.csv`, `historico.csv` e o backup, com nomes e telefones reais, estavam versionados no Git. O commit `f78d6e8` está em `origin/main` (GitHub). |
| **Risco** | Exposição de dados pessoais a qualquer pessoa com acesso ao repositório (LGPD). |
| **Correção** | Criado o [`.gitignore`](../.gitignore) (`dados/`, `__pycache__/`, `*.tmp`) e removidos do índice com `git rm --cached` (os arquivos continuam no disco). |
| **Pendente** | Reescrever o histórico remoto. É uma ação destrutiva e afeta outras pessoas, por isso não foi executada sem autorização. Veja a [seção 6](#6-riscos-residuais-e-recomendações). |

### A-02 — Injeção de fórmulas no arquivo de registros · **Alta** · Segurança

| | |
|-|-|
| **Problema** | Empresa, Modelo e Observações aceitavam textos como `=HYPERLINK("http://...","clique")`. A exportação já neutralizava fórmulas, mas o `registros.csv` era gravado sem proteção, e o próprio sistema orienta que ele "abre direto no Excel". |
| **Evidência** | `validar_dados(observacoes='=HYPERLINK(...)')` retornava sem erro. |
| **Correção** | Nova regra 21: esses campos não podem começar com `=`, `+`, `-`, `@`, tabulação ou retorno de carro (`INICIO_FORMULA`). A exportação mantém a segunda camada de proteção. |
| **Arquivos** | `nucleo/constantes.py`, `nucleo/validacoes.py`, `nucleo/exportacao.py` |
| **Testes** | `test_texto_que_vira_formula_recusado`, `test_protecao_de_formula`; CT-VAL-22, CT-EXP-05 |

### A-03 — Duas cópias abertas apagam dados uma da outra · **Alta** · Integridade

| | |
|-|-|
| **Problema** | Nada impedia abrir o sistema duas vezes. Cada cópia mantém os registros na memória e regrava o arquivo inteiro: a última gravação apagava, em silêncio, o que a outra cópia tinha salvo. Os IDs também podiam se repetir. |
| **Correção** | `obter_trava()` trava `dados/portaria.lock` com o mecanismo do sistema operacional (`msvcrt`/`fcntl`). A segunda cópia mostra um aviso e não abre. A trava é liberada automaticamente quando o processo termina, mesmo em caso de queda, então nunca fica "presa". |
| **Arquivos** | `nucleo/persistencia.py`, `nucleo/estado.py`, `interface/inicializacao.py` |
| **Testes** | `test_trava_impede_segunda_copia`; teste de fumaça com um segundo processo; CT-INI-05 |

### A-04 — ID excluído reaproveitado · **Média** · Integridade

| | |
|-|-|
| **Problema** | O próximo ID dependia só de `configuracoes.json`. Se ele se perdesse, um ID excluído voltava a ser usado e passava a identificar outra pessoa no histórico. |
| **Evidência** | Reproduzido: registro 2 excluído; sem `configuracoes.json`, o cadastro seguinte recebeu o ID 2. |
| **Correção** | Ao abrir, o próximo ID também considera o maior ID citado no histórico (`maior_id_historico()`). |
| **Testes** | `test_id_nao_reaproveitado_mesmo_sem_configuracoes`; CT-PER-10 |

### A-05 — Registro descartado por tipo sem acento · **Média** · Integridade

| | |
|-|-|
| **Problema** | Uma linha com `Funcionario` (sem acento, comum após salvar pelo Excel ou digitar à mão) era **ignorada** ao abrir. O código já tinha um mapa para corrigir isso (`TIPOS_NORMALIZADOS`), mas ele nunca era usado (código morto). |
| **Evidência** | Reproduzido: "Linha 2: tipo de acesso inválido (Funcionario) (ignorada)"; 0 registros carregados. |
| **Correção** | O tipo é normalizado antes da validação (regra CA4a). |
| **Testes** | `test_tipo_sem_acento_e_corrigido`; CT-PER-09 |

### A-06 — Falha ao gravar o histórico passava em silêncio · **Média** · Rastreabilidade

| | |
|-|-|
| **Problema** | Se `historico.csv` estivesse bloqueado (por exemplo, aberto no Excel), o evento se perdia sem nenhum aviso. |
| **Correção** | A falha é sinalizada (`S.falha_historico`) e a barra de status mostra um aviso em vermelho. |
| **Testes** | `test_falha_no_historico_e_sinalizada`; teste de fumaça; CT-HIS-05 |

### A-07 — Filtro "No prazo" mostrava pessoas já excedidas · **Média** · QA

| | |
|-|-|
| **Problema** | A atualização de cada minuto recalculava os tempos sem refiltrar. Com o filtro "No prazo", uma pessoa que passava do limite continuava listada (em vermelho) até outra ação do usuário. |
| **Correção** | Com o filtro em "No prazo" ou "Excedido", a atualização periódica refiltra a tabela (regra AL8). |
| **Arquivos** | `interface/atualizacao.py` |
| **Testes** | Teste de fumaça; CT-ALE-09 |

### A-08 — "04h 00min" na tela, mas classificado como excedido · **Baixa** · Consistência

| | |
|-|-|
| **Problema** | A permanência era exibida em minutos inteiros, mas o alerta comparava segundos. |
| **Evidência** | Reproduzido: com 4h00min30s, a tela mostrava `04h 00min` e o registro já aparecia como "Excedido". |
| **Correção** | O alerta compara minutos inteiros, a mesma precisão da tela (regra AL2). |
| **Testes** | `test_alerta_compara_minutos_inteiros` |

### A-09 — Exportação omitia a situação "Excedido" · **Baixa** · Consistência

| | |
|-|-|
| **Problema** | A tela mostrava "⚠ Excedido", mas o CSV exportado trazia "No local". |
| **Correção** | `situacao_exportada()`: exporta "No local", "Excedido" ou "Saiu", igual à tela. |
| **Testes** | `test_situacao_exportada_igual_a_tela`; CT-EXP-07 |

### A-10 — DDD inexistente aceito · **Baixa** · Validação

| | |
|-|-|
| **Problema** | A validação só recusava DDDs com o dígito 0; DDDs inexistentes como 23, 25 ou 36 eram aceitos. |
| **Correção** | Lista oficial de 67 DDDs (`DDDS_VALIDOS`) e mensagem "O DDD NN não existe." |
| **Testes** | `test_telefone`; CT-VAL-21 |

### A-11 — Motivo não podia voltar a ficar em branco · **Baixa** · Usabilidade

| | |
|-|-|
| **Problema** | O campo é opcional, mas a lista não tinha opção vazia: depois de escolhido, o motivo não podia ser removido na edição. |
| **Correção** | Opção em branco no início da lista. |
| **Testes** | Teste de fumaça; CT-VAL-23 |

### A-12 — Dica "Data/hora válida" para data futura · **Baixa** · Usabilidade

| | |
|-|-|
| **Problema** | A dica ficava verde para datas futuras ou anteriores a 2000, que seriam recusadas ao salvar. |
| **Correção** | Dicas em vermelho "Data/hora no futuro" e "Ano anterior a 2000". |
| **Testes** | Teste de fumaça; captura [05](imagens/05_erro_semantico.png); CT-VAL-24 |

### A-13 — Erros inesperados invisíveis · **Baixa** · Robustez

| | |
|-|-|
| **Problema** | Uma exceção em um botão só aparecia no terminal. Ao abrir com `pythonw` ou com duplo clique, a ação simplesmente "não fazia nada". |
| **Correção** | `report_callback_exception` exibe uma mensagem amigável e mantém o rastreamento no terminal. |
| **Testes** | Teste de fumaça |

### A-14 — Exportação podia sobrescrever temporários e a trava · **Baixa** · Segurança

| | |
|-|-|
| **Problema** | A lista de arquivos protegidos não incluía `*.tmp` nem a nova trava. |
| **Correção** | Proteção ampliada em `eh_arquivo_do_sistema()`. |
| **Testes** | `test_arquivos_do_sistema_protegidos` |

### A-15 — Ausência de testes automatizados · **Média** · QA

| | |
|-|-|
| **Problema** | Toda verificação era manual; não havia como confirmar rapidamente que uma alteração não quebrou outra regra. Havia apenas um `.pyc` órfão de um teste inexistente. |
| **Correção** | [`testes/test_nucleo.py`](../testes/test_nucleo.py): 41 testes com `unittest`, isolados em pasta temporária. |

### A-16 — Arquivos gerados versionados · **Baixa** · Manutenção

| | |
|-|-|
| **Problema** | 26 arquivos `.pyc` em `__pycache__/` estavam no Git, inclusive `test_index.cpython-314.pyc`, sem fonte correspondente. |
| **Correção** | Ignorados pelo `.gitignore` e removidos do índice. |

## 4. Achados na documentação

| ID | Problema | Correção |
|----|----------|----------|
| D-01 | O "teste do núcleo" era um script para copiar e colar dentro do documento: frágil e fácil de desatualizar. | Substituído pela suíte real, com tabela do que cada grupo cobre ([Casos de teste §14](casos_de_teste.md#14-testes-automatizados-do-núcleo)). |
| D-02 | Não havia ligação entre funcionalidades, regras e testes, o que dificulta a manutenção e a apresentação acadêmica. | Nova [matriz de rastreabilidade](casos_de_teste.md#17-matriz-de-rastreabilidade). |
| D-03 | O manual descrevia as telas, mas não o uso no dia a dia. | Nova seção "Rotina típica de um turno" no [manual](manual_usuario.md#rotina-típica-de-um-turno). |
| D-04 | Vários documentos descreviam limitações e comportamentos que mudaram (motivo, alerta, DDD, exportação, histórico, Git). | Os seis documentos foram atualizados; novos casos de teste foram incluídos (de 120 para 130). |
| D-05 | O tratamento de erros estava espalhado. | Nova seção 8.6 na [documentação técnica](documentacao_tecnica.md#86-tratamento-de-erros). |
| D-06 | A proteção contra injeção de fórmulas não estava explicada como regra. | Nova seção 3.5 em [Regras de negócio](regras_de_negocio.md#35-proteção-contra-injeção-de-fórmulas-csv-injection). |
| D-07 | As capturas de tela mostravam a versão 3.0. | Recapturadas na versão 3.1, com dados fictícios. |
| D-08 | O README não indicava como rodar os testes nem a versão. | README atualizado com a versão, o comando de testes e o link para este relatório. |

## 5. Verificação das correções

| Verificação | Resultado |
|-------------|-----------|
| `python -m unittest discover -s testes -t .` (versão 3.1) | **41 testes, OK** |
| Mesma suíte na versão anterior do código | **14 falhas detectadas** (7 *failures*, 7 *errors*): cada correção é coberta por um teste que falharia sem ela |
| `python -m pyflakes nucleo interface testes index.py` | Sem avisos |
| Teste de fumaça da interface (trava com 2º processo, motivo em branco, dicas de data, refiltro, aviso do histórico, tratador de erros) | 6/6 conforme esperado |
| Regressão visual (abertura de todas as telas para as capturas) | Sem erros |
| Pasta `dados/` real | Inalterada (mesma soma MD5 antes e depois) |
| Links e âncoras entre os documentos | Todos válidos |

## 6. Riscos residuais e recomendações

Em ordem de prioridade:

| # | Recomendação | Motivo | Esforço |
|---|--------------|--------|---------|
| 1 | **Remover `dados/` do histórico publicado no GitHub** (`git filter-repo --path dados --invert-paths` + `git push --force`, combinando antes com a equipe). Enquanto isso, tornar o repositório privado. | Completa o A-01: o `.gitignore` não apaga commits antigos. | Baixo, mas exige coordenação |
| 2 | Fazer commit do `.gitignore` e da remoção dos arquivos do índice. | Sem o commit, a correção do A-01 fica só local. | Baixo |
| 3 | Backup automático **rotativo** (por exemplo, as últimas 7 versões) e backup de `historico.csv`. | Hoje, só a versão anterior de `registros.csv` é guardada. | Baixo |
| 4 | Política de retenção: opção para excluir registros com mais de N dias, incluindo o histórico deles. | Atende ao princípio de necessidade da LGPD sem trabalho manual. | Médio |
| 5 | Identificação do operador (login simples) gravada no histórico. | Hoje não se sabe quem fez cada ação. | Médio |
| 6 | Avisar, ao carregar o CSV, sobre dados que o formulário recusaria (datas futuras, fórmulas) sem descartá-los. | Alinha a leitura às regras do formulário. | Baixo |
| 7 | Executar os testes automaticamente a cada envio (GitHub Actions). | Evita regressões. | Baixo |
| 8 | Testes automatizados da interface. | Hoje a interface depende dos casos manuais. | Alto |

## 7. Notas da versão 3.1

**Segurança**
- Bloqueio de fórmulas no início de Empresa, Modelo e Observações.
- Instância única com trava do sistema operacional.
- `.gitignore` para dados pessoais e arquivos gerados.
- Exportação protege também `*.tmp` e `portaria.lock`.

**Correções**
- Tipos sem acento no CSV são corrigidos em vez de descartados.
- IDs excluídos não são reaproveitados, mesmo sem `configuracoes.json`.
- Falha ao gravar o histórico é avisada.
- Filtros "No prazo"/"Excedido" se atualizam sozinhos.
- Alerta de tempo máximo coerente com a permanência exibida.
- Exportação inclui a situação "Excedido".

**Melhorias**
- Validação de DDD pela lista oficial.
- Opção em branco no Motivo.
- Dicas de data futura e de ano anterior a 2000.
- Mensagem amigável para erros inesperados.
- 41 testes automatizados.
