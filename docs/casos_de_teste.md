# Casos de Teste

Roteiro de testes funcionais do **Cadastro de Portaria**, com os resultados
esperados e espaço para registrar os resultados obtidos. Os resultados
esperados seguem as [Regras de negócio](regras_de_negocio.md); os códigos
entre parênteses (RS1, AL2...) remetem a elas.

Há dois níveis de teste:

- **Testes automatizados do núcleo** (41 testes em
  [`testes/test_nucleo.py`](../testes/test_nucleo.py)): verificam regras,
  cálculos, arquivos e segurança em segundos, sem abrir janelas. Veja a
  [seção 14](#14-testes-automatizados-do-núcleo).
- **Casos funcionais manuais** (seções 1 a 13): verificam o sistema completo
  pela interface, como o usuário o utiliza.

A [seção 17](#17-matriz-de-rastreabilidade) liga cada funcionalidade às suas
regras e aos testes que a cobrem.

## Sumário

- [Como usar este documento](#como-usar-este-documento)
- [Preparação do ambiente](#preparação-do-ambiente)
1. [Inicialização](#1-inicialização)
2. [Cadastro de entrada](#2-cadastro-de-entrada)
3. [Validação de formato](#3-validação-de-formato)
4. [Validação semântica das datas](#4-validação-semântica-das-datas)
5. [Registro de saída](#5-registro-de-saída)
6. [Edição](#6-edição)
7. [Exclusão](#7-exclusão)
8. [Permanência e alerta](#8-permanência-e-alerta)
9. [Pesquisa, filtros e ordenação](#9-pesquisa-filtros-e-ordenação)
10. [Indicadores](#10-indicadores)
11. [Histórico e exportação](#11-histórico-e-exportação)
12. [Configurações](#12-configurações)
13. [Persistência, backup e recuperação](#13-persistência-backup-e-recuperação)
14. [Testes automatizados do núcleo](#14-testes-automatizados-do-núcleo)
15. [Registro de defeitos](#15-registro-de-defeitos)
16. [Resumo da execução](#16-resumo-da-execução)
17. [Matriz de rastreabilidade](#17-matriz-de-rastreabilidade)

---

## Como usar este documento

1. Preencha a ficha de execução abaixo.
2. Execute cada caso na ordem da seção, seguindo os passos.
3. Anote o que aconteceu na coluna **Obtido** (deixe em branco se foi igual
   ao esperado, ou descreva a diferença).
4. Marque o **Status**: ✅ passou · ❌ falhou · ⏸ bloqueado · ➖ não executado.
5. Registre cada falha na [seção 15](#15-registro-de-defeitos) e consolide
   os números na [seção 16](#16-resumo-da-execução).

### Ficha de execução

| Campo | Valor |
|-------|-------|
| Testador(a) | |
| Data da execução | |
| Versão do sistema (aba Sobre) | |
| Sistema operacional | |
| Versão do Python | |
| Observações | |

## Preparação do ambiente

> **Importante:** os testes criam, alteram e excluem registros. Antes de
> começar, faça uma cópia da pasta `dados/` (veja
> [Backups](instalacao_e_manutencao.md#5-backups)) ou execute os testes em
> uma cópia do projeto.

1. Feche o sistema.
2. Copie a pasta `dados/` para um local seguro.
3. Apague o conteúdo de `dados/` para começar com o sistema vazio
   (necessário para os casos CT-INI-01 e CT-IND-01).
4. Abra o sistema com `python index.py`.
5. Ao terminar, feche o sistema e restaure a cópia de `dados/`.

Nos passos, **agora** significa a data/hora atual do computador.

---

## 1. Inicialização

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-INI-01 | Primeira execução | Com `dados/` vazia ou inexistente, execute `python index.py`. | Janela abre na aba Portaria. Tabela mostra "Nenhum registro cadastrado ainda". Indicadores zerados. Pasta `dados/` existe. | | |
| CT-INI-02 | Relógio | Observe o cabeçalho por alguns segundos. | Data e hora são atualizadas a cada segundo. | | |
| CT-INI-03 | Reabrir com dados | Cadastre um registro, feche e abra o sistema. | O registro continua na tabela com o mesmo ID. | | |
| CT-INI-04 | Abas | Clique em cada aba. | Portaria, Histórico, Configurações e Sobre / Ajuda são exibidas sem erro. | | |
| CT-INI-05 | Segunda cópia (RE11) | Com o sistema aberto, execute `python index.py` de novo em outro terminal. | Aviso "O sistema já está aberto em outra janela"; nenhuma segunda janela principal. A primeira continua funcionando. Ao fechá-la, o sistema volta a abrir normalmente. | | |

## 2. Cadastro de entrada

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-CAD-01 | Cadastro mínimo | `Ctrl+N`. Nome: `Maria Souza`. Mantenha tipo e entrada. Clique em Cadastrar. | "Registro cadastrado com sucesso!". Janela fecha. Linha verde com ID `001`, situação "● No local", permanência "Em andamento — 00h 00min". | | |
| CT-CAD-02 | Valores iniciais do formulário | Clique em **+ Nova entrada**. | Tipo = Visitante; Entrada = agora; demais campos vazios; título "Nova entrada". | | |
| CT-CAD-03 | Cadastro completo | Nome `Carlos Pereira`, tipo Entregador, motivo Entrega. Em Informações adicionais: telefone `31987654321`, empresa `Loja X`, pessoa visitada `Ana Lima`, placa `abc1d23`, modelo `Fiorino`, cor `Branco`, observações `Caixa grande`. Cadastrar. | Registro criado. Painel de detalhes mostra telefone `(31) 98765-4321` e placa `ABC1D23`. | | |
| CT-CAD-04 | Cadastro com saída | Nome `Paula Dias`, entrada = ontem 08:00, saída = ontem 09:15. Cadastrar. | Linha cinza "○ Saiu", permanência `01h 15min`. | | |
| CT-CAD-05 | IDs sequenciais | Cadastre dois registros seguidos. | IDs consecutivos (ex.: `004` e `005`). | | |
| CT-CAD-06 | Duplicidade | Cadastre `Maria Souza`, Visitante, com a mesma entrada do CT-CAD-01. | Pergunta "Possível duplicidade". **Não**: nada é criado. **Sim**: registro criado com novo ID. | | |
| CT-CAD-07 | Cancelar com dados | Abra Nova entrada, digite um nome, pressione `Esc`. | Pergunta "Fechar sem salvar". **Não** mantém a janela; **Sim** fecha sem cadastrar. | | |
| CT-CAD-08 | Cancelar sem dados | Abra Nova entrada e clique em Cancelar sem digitar. | Janela fecha sem perguntar. | | |
| CT-CAD-09 | Botão Limpar | Preencha campos e clique em Limpar. | Campos voltam aos valores iniciais; entrada = agora. | | |
| CT-CAD-10 | Atalhos do formulário | Preencha um nome e pressione `Enter` em um campo; repita com `Ctrl+S`. | Ambos salvam o registro. | | |
| CT-CAD-11 | Janela modal | Com o formulário aberto, clique na janela principal. | A janela principal não responde até o formulário ser fechado. | | |

## 3. Validação de formato

Para cada caso, abra **+ Nova entrada**, preencha um nome válido (exceto nos
casos de nome) e altere apenas o campo indicado.

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-VAL-01 | Nome vazio | Deixe o nome em branco e clique em Cadastrar. | "O nome não pode ficar vazio." Cursor no campo Nome. | | |
| CT-VAL-02 | Nome curto | Nome `A`. | "O nome é muito curto..." | | |
| CT-VAL-03 | Filtro do nome | Digite `Jo4o!` no nome. | `4` e `!` são apagados ao digitar; aviso "Use apenas letras!" por alguns segundos. Campo fica `Joo`. | | |
| CT-VAL-04 | Nome composto válido | Nome `Ana D'Ávila-Souza`. | Aceito. | | |
| CT-VAL-05 | Limite do nome | Cole um texto de 70 letras no nome. | Campo é cortado em 60 caracteres; aviso "Máximo de 60 caracteres!". | | |
| CT-VAL-06 | Espaços repetidos | Nome `Ana    Maria`. | Ao digitar, espaços repetidos viram um só. Salvo como `Ana Maria`. | | |
| CT-VAL-07 | Máscara de data | Apague a entrada e digite `290920261030`. | Campo exibe `29/09/2026 10:30`; dica "Data/hora válida". | | |
| CT-VAL-08 | Data incompleta | Apague a entrada e digite `2909`. Clique em Cadastrar. | Dica "Faltam 8 dígito(s)". Ao salvar: "Entrada em formato inválido." | | |
| CT-VAL-09 | Data inexistente | Entrada `30/02/2026 10:00`. | Dica "Data/hora inexistente" em vermelho. Ao salvar: "Entrada em formato inválido." | | |
| CT-VAL-10 | Letras na data | Digite letras no campo Entrada. | Letras não aparecem no campo. | | |
| CT-VAL-11 | Telefone com 9 dígitos | Telefone `319876543`. | "O telefone deve ter 10 ou 11 dígitos, com DDD." A seção Informações adicionais é aberta e o cursor vai para o Telefone. | | |
| CT-VAL-12 | DDD inválido | Telefone `01987654321`. | "O DDD 01 não existe." | | |
| CT-VAL-13 | Celular sem 9 | Telefone `31887654321`. | "Telefone com 11 dígitos deve começar com 9 depois do DDD." | | |
| CT-VAL-14 | Telefone fixo | Telefone `3133334444`. | Aceito e salvo como `(31) 3333-4444`. | | |
| CT-VAL-15 | Placa antiga | Placa `abc1234`. | Campo exibe `ABC1234`; aceito; tabela mostra `ABC-1234`. | | |
| CT-VAL-16 | Placa inválida | Placa `AB12345`. | "Placa inválida". | | |
| CT-VAL-17 | Filtro da placa | Digite `abc-1d23x` na placa. | Campo exibe `ABC1D23` (sem hífen, máximo 7). | | |
| CT-VAL-18 | Cor com número | Digite `Azul2` na cor. | O `2` é apagado ao digitar. | | |
| CT-VAL-19 | Pessoa visitada inválida | Pessoa visitada `X`. | "Pessoa visitada inválida" (nome muito curto). | | |
| CT-VAL-20 | Limite de observações | Cole 250 caracteres em Observações. | Campo cortado em 200 caracteres. | | |
| CT-VAL-21 | DDD inexistente sem zero | Telefone `23987654321`. | "O DDD 23 não existe." | | |
| CT-VAL-22 | Injeção de fórmula (3.5) | Observações `=HYPERLINK("http://x","clique")`; depois Empresa `+5`. | "Texto não permitido": não pode começar com =, +, - ou @. Observações `Entrega - caixa` (hífen no meio) é aceita. | | |
| CT-VAL-23 | Motivo em branco | Escolha um motivo e depois a primeira opção (vazia) da lista. Cadastre. | Cadastro aceito com motivo vazio. | | |
| CT-VAL-24 | Dica de data futura e antiga | Entrada = amanhã; depois `01/01/1999 10:00`. | Dica em vermelho "Data/hora no futuro" e depois "Ano anterior a 2000", antes de clicar em Cadastrar. | | |

## 4. Validação semântica das datas

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-SEM-01 | Entrada futura (RS1) | Entrada = amanhã. | Erro (ícone vermelho) "Erro semântico: A entrada não pode ser uma data/hora futura." | | |
| CT-SEM-02 | Entrada antes de 2000 (RS2) | Entrada `31/12/1999 10:00`. | "Erro semântico: A entrada não pode ser anterior ao ano 2000." | | |
| CT-SEM-03 | Saída futura (RS3) | Entrada = ontem 08:00; saída = amanhã 08:00. | "Erro semântico: A saída não pode ser uma data/hora futura." | | |
| CT-SEM-04 | Saída antes da entrada (RS4) | Entrada = ontem 10:00; saída = ontem 09:59. | "Erro semântico: A saída não pode ser anterior à entrada." | | |
| CT-SEM-05 | Saída igual à entrada | Entrada e saída = ontem 10:00. | Aceito; permanência `00h 00min`. | | |
| CT-SEM-06 | Entrada em 01/01/2000 | Entrada `01/01/2000 00:00`. | Aceito. | | |

## 5. Registro de saída

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-SAI-01 | Saída pelo botão | Selecione um registro "No local" e clique em Registrar saída. | Saída = agora; linha fica cinza "○ Saiu"; barra de status mostra a permanência. | | |
| CT-SAI-02 | Saída por atalho e menu | Repita com `Ctrl+R` e com botão direito → Registrar saída. | Mesmo resultado do CT-SAI-01. | | |
| CT-SAI-03 | Registro que já saiu (RE4) | Selecione um registro "Saiu" e registre saída. | "Este registro já possui uma saída..." Nada muda. | | |
| CT-SAI-04 | Nenhum selecionado | Sem seleção, clique em Registrar saída. | "Selecione uma pessoa que esteja dentro." | | |
| CT-SAI-05 | Vários selecionados (RE5) | Selecione dois registros e registre saída. | "Selecione apenas uma pessoa para registrar a saída." | | |
| CT-SAI-06 | Histórico da saída | Após CT-SAI-01, abra a aba Histórico. | Evento "Saída" com "Saída registrada em ... (permanência ...)". | | |

## 6. Edição

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-EDI-01 | Abrir edição | Selecione um registro e clique em Editar selecionado. | Janela "Editando registro #NNN" com borda amarela e dados preenchidos; botões "Salvar alterações" e "Restaurar". | | |
| CT-EDI-02 | Outras formas de abrir | Teste `Ctrl+E`, `Enter` na tabela, duplo clique e botão direito → Editar. | Todas abrem a edição. | | |
| CT-EDI-03 | Salvar alteração | Mude a empresa e salve. | ID mantido; tabela e detalhes atualizados; histórico "Edição — Campos alterados: Empresa". | | |
| CT-EDI-04 | Restaurar | Altere campos e clique em Restaurar. | Campos voltam aos valores salvos. | | |
| CT-EDI-05 | Corrigir saída (RE6) | Edite um registro com saída e mude o horário da saída. | Nova saída salva; permanência recalculada. | | |
| CT-EDI-06 | Remover saída | Edite um registro com saída e apague a saída. | Registro volta a "● No local". | | |
| CT-EDI-07 | Validação na edição | Na edição, coloque saída antes da entrada. | Mesmo erro semântico do CT-SEM-04. Nada é salvo. | | |
| CT-EDI-08 | Sem alterações | Abra a edição e salve sem mudar nada. | Salvo; histórico "Nenhum campo foi alterado". | | |
| CT-EDI-09 | Fechar com alteração | Altere um campo e pressione `Esc`. | Pergunta "Fechar sem salvar". | | |
| CT-EDI-10 | Extras abertos | Edite um registro que tem telefone ou placa. | Seção Informações adicionais já aparece aberta. | | |

## 7. Exclusão

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-EXC-01 | Excluir um | Selecione um registro, clique em Excluir selecionado e confirme. | Registro removido; "Registro(s) excluído(s) com sucesso." | | |
| CT-EXC-02 | Cancelar exclusão | Repita e responda **Não**. | Nada é excluído. | | |
| CT-EXC-03 | Excluir vários (RE8) | Selecione 3 registros com `Ctrl+clique` e pressione `Delete`. | Confirmação lista os 3 nomes; todos são removidos. | | |
| CT-EXC-04 | ID não reaproveitado (RE1) | Exclua o registro de maior ID e cadastre outro. | Novo registro recebe o ID seguinte ao excluído, não o mesmo. | | |
| CT-EXC-05 | Histórico mantido | Após excluir, abra a aba Histórico. | Evento "Exclusão" e eventos anteriores do registro continuam lá. | | |
| CT-EXC-06 | Delete fora da tabela | Com o cursor no campo Pesquisar, pressione `Delete`. | Apaga texto do campo; nenhum registro é excluído. | | |

## 8. Permanência e alerta

Use **Configurações** para ajustar o tempo máximo quando indicado.

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-ALE-01 | Permanência concluída | Entrada ontem 09:30, saída ontem 11:05. | Permanência `01h 35min`. | | |
| CT-ALE-02 | Permanência em andamento | Entrada = agora − 2 h, sem saída. | `Em andamento — 02h 00min` (ou 02h 01min, conforme os segundos). | | |
| CT-ALE-03 | Atualização automática | Deixe o sistema aberto por 2 minutos. | Permanência dos registros "No local" aumenta sem nenhuma ação. | | |
| CT-ALE-04 | Excedido (AL2) | Limite 4 h. Cadastre entrada = agora − 5 h, sem saída. | Linha vermelha "⚠ Excedido"; detalhes "⚠ Tempo máximo (4h) excedido"; barra de status "⚠ 1 acima do tempo máximo (4h)". | | |
| CT-ALE-05 | Passagem para excedido (AL2) | Limite 1 h. Cadastre entrada = agora − 59 min (ex.: agora 15:30 → 14:31), sem saída. Aguarde 2 minutos. | Inicialmente "● No local". Na atualização automática seguinte ao limite, passa para "⚠ Excedido" sem nenhuma ação. | | |
| CT-ALE-06 | Quem saiu não é alertado (AL3) | Registro com entrada há 10 h e saída há 1 h. | "○ Saiu", sem alerta. | | |
| CT-ALE-07 | Alerta desligado (AL5) | Desmarque o alerta e salve. | Nenhum "⚠ Excedido"; filtro Situação mostra só Todos, No local, Saiu. | | |
| CT-ALE-08 | Mudança de limite | Com o registro do CT-ALE-04, mude o limite para 6 h e salve. | O registro deixa de estar excedido. | | |
| CT-ALE-09 | Refiltro automático (AL8) | Limite 1 h. Com o registro do CT-ALE-05 ainda no prazo, filtre Situação = "No prazo" e aguarde passar do limite. | O registro sai da tabela sozinho na atualização seguinte (passou a "Excedido"). | | |

## 9. Pesquisa, filtros e ordenação

Pré-condição: cadastre registros variados (tipos, motivos, empresas, datas
de hoje, ontem e de 10 dias atrás, com e sem saída).

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-FIL-01 | Pesquisa sem acento | Pesquise `joao` havendo "João". | "João" aparece. | | |
| CT-FIL-02 | Pesquisa por ID | Pesquise `7` e depois `007`. | O registro 007 aparece nos dois casos. | | |
| CT-FIL-03 | Pesquisa por telefone | Pesquise só os dígitos de um telefone cadastrado. | O registro aparece. | | |
| CT-FIL-04 | Pesquisa por placa | Pesquise `ABC-1234` e `abc1234`. | O registro aparece nos dois casos. | | |
| CT-FIL-05 | Campos não pesquisados | Pesquise uma palavra que existe só em Observações. | O registro **não** aparece por causa dessa palavra. | | |
| CT-FIL-06 | Filtro por tipo | Tipo = Entregador. | Só entregadores. | | |
| CT-FIL-07 | Situação No prazo/Excedido | Com alerta ligado, filtre "No prazo" e depois "Excedido". | No prazo: no local e não excedidos. Excedido: só os excedidos. "No local" mostra os dois grupos. | | |
| CT-FIL-08 | Período Hoje / Ontem | Escolha Hoje, depois Ontem. | Apenas entradas da data correspondente. | | |
| CT-FIL-09 | Últimos 7 dias | Escolha Últimos 7 dias. | Entradas de hoje e dos 6 dias anteriores; a de 10 dias atrás não aparece. | | |
| CT-FIL-10 | Período personalizado | Abra Filtros avançados e digite uma data em De. | Período muda para "Período personalizado"; tabela filtrada a partir da data. | | |
| CT-FIL-11 | Intervalo invertido | De = 10/10/2026, Até = 01/10/2026, clique em Aplicar. | "A data inicial não pode ser posterior à data final." | | |
| CT-FIL-12 | Período pronto apaga datas | Com De/Até preenchidos, escolha Período = Hoje. | Campos De e Até ficam vazios. | | |
| CT-FIL-13 | Motivo e empresa | Filtros avançados: Motivo = Entrega; Empresa = parte do nome. | Só registros que atendem aos dois filtros. | | |
| CT-FIL-14 | Combinação de filtros | Tipo = Visitante + Situação = Saiu + Período = Hoje. | Só visitantes que entraram hoje e já saíram. | | |
| CT-FIL-15 | Limpar filtros | `Ctrl+L`. | Todos os filtros voltam ao padrão; todos os registros aparecem. | | |
| CT-FIL-16 | Contagem | Aplique um filtro. | Barra de status mostra "Exibindo X de Y registros". | | |
| CT-FIL-17 | Ordenação | Clique em "Entrada" duas vezes. | 1º clique: mais antigas primeiro, seta ▲. 2º clique: inverte, seta ▼. | | |
| CT-FIL-18 | Ordenar por permanência | Clique em "Permanência". | Ordem pela duração (não pelo texto). | | |

## 10. Indicadores

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-IND-01 | Sistema vazio | Abra com `dados/` vazia. | Todos os indicadores = 0. | | |
| CT-IND-02 | Contagem geral | Cadastre 3 registros sem saída e 2 com saída. | Total 5, No local agora 3, Saíram 2. | | |
| CT-IND-03 | Somente hoje | Cadastre 1 entregador com entrada hoje e 1 com entrada ontem. | Entregadores (hoje) conta apenas o de hoje. | | |
| CT-IND-04 | Por tipo | Tenha no local 2 visitantes, 1 funcionário e 1 entregador. | Visitantes 2, Funcionários 1, Moradores 0; o entregador conta só em "No local agora". | | |
| CT-IND-05 | Independência dos filtros | Aplique um filtro de tipo. | Indicadores não mudam. | | |

## 11. Histórico e exportação

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-HIS-01 | Eventos registrados | Faça um cadastro, uma edição, uma saída, uma exclusão e salve uma configuração. Abra a aba Histórico. | Um evento de cada ação, do mais recente para o mais antigo. | | |
| CT-HIS-02 | Filtro por ação | Ação = Edição. | Só eventos de edição; contagem "N evento(s) exibido(s)" atualizada. | | |
| CT-HIS-03 | Filtro por data | De/Até = hoje. | Só eventos de hoje. | | |
| CT-HIS-04 | Pesquisa no histórico | Pesquise um nome. | Eventos com esse nome ou com o texto na descrição. | | |
| CT-HIS-05 | Falha ao gravar o histórico (RE10) | Abra `dados/historico.csv` no Excel e cadastre um registro. | Cadastro salvo; barra de status em vermelho: "Atenção: a última atividade não pôde ser gravada no histórico...". | | |
| CT-EXP-01 | Exportar filtrados | Filtre Tipo = Visitante e clique em Exportar filtrados. Salve. | Arquivo criado com só os visitantes, colunas Permanência e Situação; abre no Excel com acentos corretos; evento "Exportação" no histórico. | | |
| CT-EXP-02 | Exportar sem dados | Aplique um filtro sem resultados e exporte. | "Registros filtrados: não há dados para exportar." | | |
| CT-EXP-03 | Proteção dos arquivos (EX6) | Exporte escolhendo `dados/registros.csv` como destino (confirme a substituição se o Windows perguntar). | "Escolha outro nome: este arquivo é usado pelo próprio sistema..." Arquivo original intacto. | | |
| CT-EXP-04 | Exportar histórico | Na aba Histórico, clique em Exportar. | CSV com Data/Hora, Ação, ID, Nome, Descrição dos eventos exibidos. | | |
| CT-EXP-05 | Proteção contra fórmulas (EX5) | Feche o sistema e, no Bloco de Notas, coloque `=1+1` na coluna Observações de uma linha de `registros.csv` (simula dado antigo ou editado à mão; o formulário não aceita mais esse valor). Abra o sistema e exporte. | No CSV exportado, o valor aparece como `'=1+1` (com apóstrofo) e não é calculado pelo Excel. | | |
| CT-EXP-06 | Cancelar exportação | Clique em Exportar e cancele a janela de salvar. | Nada é gravado; nenhum evento no histórico. | | |
| CT-EXP-07 | Situação exportada (AL7) | Com um registro excedido, exporte os registros. | A coluna Situação traz "Excedido" para ele, "No local" e "Saiu" para os demais. | | |

## 12. Configurações

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-CFG-01 | Trocar tema | Tema = Escuro, Salvar configurações. | Todas as telas ficam escuras, inclusive o formulário. | | |
| CT-CFG-02 | Botão de tema | Clique em "Tema escuro / Tema claro" no cabeçalho. | Tema alterna; a lista Tema da aba Configurações acompanha; evento "Configuração" no histórico. | | |
| CT-CFG-03 | Tempo inválido (CF1) | Tempo máximo = `0`, depois `80`, depois `abc`. Salve cada um. | "Informe um número inteiro de horas entre 1 e 72." Nada é salvo. | | |
| CT-CFG-04 | Colunas opcionais | Desmarque Motivo e Veículo e salve. | Colunas somem da tabela; ao marcar de novo, voltam. | | |
| CT-CFG-05 | Persistência | Mude o tema e o tempo, feche e abra o sistema. | As escolhas são mantidas. | | |
| CT-CFG-06 | Filtro volta para Todos (CF3) | Filtre Situação = Excedido; desligue o alerta e salve. | Filtro volta para "Todos". | | |
| CT-CFG-07 | Ctrl+S na aba | Na aba Configurações, altere algo e pressione `Ctrl+S`. | Configurações salvas ("Configurações salvas." na barra de status). | | |

## 13. Persistência, backup e recuperação

Feche o sistema antes de editar arquivos manualmente.

| ID | Cenário | Passos / dados | Resultado esperado | Obtido | Status |
|----|---------|----------------|--------------------|--------|--------|
| CT-PER-01 | Backup automático | Cadastre um registro e depois outro. Compare `registros_backup.csv` com `registros.csv`. | O backup tem a versão anterior (sem o último registro). | | |
| CT-PER-02 | Arquivo aberto no Excel | Abra `registros.csv` no Excel e tente cadastrar. | "Erro ao salvar... A operação foi DESFEITA"; o registro **não** aparece na tabela. Ao fechar o Excel e tentar de novo, funciona. | | |
| CT-PER-03 | Linha inválida (CA4) | Edite `registros.csv` e troque o tipo de uma linha para `Gerente`. Abra o sistema. | Aviso "Linha N: tipo de acesso inválido (Gerente) (ignorada)"; cópia `registros_original_*.csv` criada; demais registros carregados. | | |
| CT-PER-04 | ID repetido (CA6) | Duplique uma linha no CSV (mesmo ID). Abra o sistema. | Aviso de ID repetido; a cópia recebe um novo ID. | | |
| CT-PER-05 | Formato antigo (CA3) | Crie um `registros.csv` sem cabeçalho com a linha `Ana Lima;Visitante;01/10/2026 09:00;01/10/2026 10:00`. Abra o sistema. | Registro carregado com novo ID; aviso de atualização do formato; cópia do original guardada. | | |
| CT-PER-06 | Configuração corrompida (CF4) | Escreva texto qualquer em `configuracoes.json`. Abra o sistema. | Sistema abre com as configurações padrão, sem erro. | | |
| CT-PER-07 | Arquivo ilegível (CA9) | Substitua `registros.csv` por um arquivo binário (ex.: uma imagem renomeada). Abra. | O sistema abre sem fechar sozinho, mostra aviso(s) e guarda uma cópia do original em `registros_original_*.csv`. | | |
| CT-PER-08 | Fechar com formulário aberto | Abra Nova entrada, digite um nome e feche a janela principal. | Pergunta "Sair do sistema". | | |
| CT-PER-09 | Tipo sem acento (CA4a) | No CSV, troque o tipo de uma linha para `funcionario`. Abra o sistema. | Registro carregado como "Funcionário" (não é descartado). | | |
| CT-PER-10 | ID preservado sem configurações (RE1) | Exclua o registro de maior ID, feche, apague `configuracoes.json`, abra e cadastre. | O novo registro **não** recebe o ID excluído. | | |

## 14. Testes automatizados do núcleo

A suíte [`testes/test_nucleo.py`](../testes/test_nucleo.py) usa apenas o
`unittest` da biblioteca padrão. Os testes de arquivos rodam em uma **pasta
temporária**: a pasta `dados/` real nunca é lida nem alterada.

Na pasta do projeto, execute:

```bash
python -m unittest discover -s testes -t . -v
```

Resultado esperado: `Ran 41 tests` e `OK`.

| Grupo (classe) | O que verifica | Regras |
|----------------|----------------|--------|
| `TesteValidacaoDatas` | Entrada/saída futuras, ano mínimo, saída antes da entrada, saída igual à entrada, data inexistente, entrada obrigatória. | RS1–RS4 |
| `TesteValidacaoCampos` | Normalização, nomes, tipo, motivo, telefone e DDD, placa, cor, limites, bloqueio de fórmulas, duplicidade. | 3.2, 3.4, 3.5 |
| `TesteCalculos` | Permanência, alerta em minutos inteiros, alerta desligado, filtro de situação. | AL1–AL5 |
| `TesteConsultas` | Pesquisa sem acento e por ID, telefone e placa; filtros combinados; períodos; indicadores; ordenação. | 7, 8 |
| `TesteExportacao` | Proteção de fórmulas, arquivos protegidos, situação exportada, gravação UTF-8. | EX5–EX7, AL7 |
| `TestePersistencia` | Gravação e recarga, backup, desfazer em caso de falha, saída, edição, IDs não reaproveitados, tipo sem acento, linha inválida, migração, IDs repetidos, configuração inválida, falha no histórico, trava de instância única. | RE1, RE4, RE9–RE11, CA3–CA8, CF4 |

Execute a suíte **antes de cada entrega** e após qualquer alteração no
código. A interface gráfica continua coberta pelos casos manuais.

| ID | Cenário | Resultado esperado | Obtido | Status |
|----|---------|--------------------|--------|--------|
| CT-NUC-01 | Execução da suíte automatizada | `Ran 41 tests ... OK`, sem `FAIL` nem `ERROR`. | | |

## 15. Registro de defeitos

| Nº | Caso de teste | Descrição do problema | Passos para reproduzir | Gravidade (alta/média/baixa) | Situação |
|----|---------------|-----------------------|------------------------|------------------------------|----------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 16. Resumo da execução

| Seção | Total de casos | ✅ Passou | ❌ Falhou | ⏸ Bloqueado | ➖ Não executado |
|-------|---------------:|---------:|---------:|------------:|----------------:|
| 1. Inicialização | 5 | | | | |
| 2. Cadastro | 11 | | | | |
| 3. Validação de formato | 24 | | | | |
| 4. Validação semântica | 6 | | | | |
| 5. Registro de saída | 6 | | | | |
| 6. Edição | 10 | | | | |
| 7. Exclusão | 6 | | | | |
| 8. Permanência e alerta | 9 | | | | |
| 9. Filtros e ordenação | 18 | | | | |
| 10. Indicadores | 5 | | | | |
| 11. Histórico e exportação | 12 | | | | |
| 12. Configurações | 7 | | | | |
| 13. Persistência | 10 | | | | |
| 14. Núcleo (suíte automatizada) | 1 | | | | |
| **Total** | **130** | | | | |

## 17. Matriz de rastreabilidade

Liga cada funcionalidade às regras de negócio e aos testes que a cobrem. Uma
funcionalidade alterada exige executar novamente os testes da sua linha.

| Funcionalidade | Regras ([Regras de negócio](regras_de_negocio.md)) | Casos manuais | Testes automatizados |
|----------------|------------------|---------------|----------------------|
| Inicialização e instância única | RE11, CA1–CA10 | CT-INI-01 a 05 | `test_trava_impede_segunda_copia` |
| Cadastro de entrada | RE1–RE3, 3.4 | CT-CAD-01 a 11 | `test_cadastro_grava_e_recarrega`, `test_duplicidade` |
| Validação de formato | 3.1, 3.2 | CT-VAL-01 a 21, 23, 24 | `TesteValidacaoCampos` |
| Segurança: injeção de fórmulas | 3.5, EX5 | CT-VAL-22, CT-EXP-05 | `test_texto_que_vira_formula_recusado`, `test_protecao_de_formula` |
| Validação semântica | RS1–RS4 | CT-SEM-01 a 06 | `TesteValidacaoDatas` |
| Registro de saída | RE4–RE6 | CT-SAI-01 a 06 | `test_registrar_saida` |
| Edição | RE7 | CT-EDI-01 a 10 | `test_edicao_registra_campos_alterados` |
| Exclusão e IDs | RE1, RE8 | CT-EXC-01 a 06, CT-PER-10 | `test_id_nao_reaproveitado_mesmo_sem_configuracoes` |
| Permanência e alerta | 5, AL1–AL8 | CT-ALE-01 a 09 | `TesteCalculos` |
| Pesquisa, filtros e ordenação | 7 | CT-FIL-01 a 18 | `TesteConsultas` |
| Indicadores | 8 | CT-IND-01 a 05 | `test_indicadores` |
| Histórico | 10, RE10 | CT-HIS-01 a 05 | `test_falha_no_historico_e_sinalizada` |
| Exportação | 11 | CT-EXP-01 a 07 | `TesteExportacao` |
| Configurações | 12 | CT-CFG-01 a 07 | `test_configuracao_invalida_usa_padrao` |
| Gravação segura e backup | RE9 | CT-PER-01, 02 | `test_backup_guarda_versao_anterior`, `test_falha_ao_gravar_desfaz_na_memoria` |
| Carregamento e migração | CA1–CA10 | CT-PER-03 a 07, 09 | `test_migracao_de_formato_antigo`, `test_linha_invalida_ignorada_e_original_preservado`, `test_ids_repetidos_recebem_novo_id`, `test_tipo_sem_acento_e_corrigido` |
