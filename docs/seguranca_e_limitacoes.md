# Segurança e Limitações

Este documento descreve como o **Cadastro de Portaria** trata os dados
pessoais, quais proteções existem, quais não existem e quais cuidados
tomar com os arquivos locais. Também lista as limitações conhecidas da
versão atual.

## Sumário

1. [Dados tratados pelo sistema](#1-dados-tratados-pelo-sistema)
2. [Proteção dos dados pessoais](#2-proteção-dos-dados-pessoais)
3. [Cuidados com os arquivos locais](#3-cuidados-com-os-arquivos-locais)
4. [Limitações conhecidas](#4-limitações-conhecidas)

---

## 1. Dados tratados pelo sistema

O sistema registra **dados pessoais** de quem passa pela portaria:

| Dado | Onde fica |
|------|-----------|
| Nome da pessoa e da pessoa visitada | `registros.csv`, `historico.csv` (nome), exportações |
| Telefone | `registros.csv`, exportações |
| Empresa | `registros.csv`, exportações |
| Placa, modelo e cor do veículo | `registros.csv`, exportações |
| Datas e horários de entrada e saída | `registros.csv`, `historico.csv`, exportações |
| Observações (texto livre) | `registros.csv`, exportações |

Esses dados permitem identificar pessoas e saber quando estiveram no local.
No Brasil, o tratamento de dados pessoais está sujeito à **Lei Geral de
Proteção de Dados (LGPD, Lei nº 13.709/2018)**. A organização que usar o
sistema é responsável por definir a finalidade, o prazo de guarda e quem
pode acessar os dados.

## 2. Proteção dos dados pessoais

### 2.1 O que o sistema faz

| Proteção | Descrição |
|----------|-----------|
| Armazenamento local | Os dados ficam apenas na pasta `dados/` do computador. O sistema não acessa a internet nem envia dados a terceiros. |
| Campos opcionais | Só nome, tipo e entrada são obrigatórios. Os demais dados só são guardados se forem informados. |
| Validação na entrada | Máscaras, filtros e validações reduzem dados incorretos ou malformados. |
| Proteção contra injeção de fórmulas (CSV injection) | Em duas camadas. Na **entrada**, Empresa, Modelo e Observações não podem começar com `=`, `+`, `-` ou `@`. Na **exportação**, qualquer valor que comece assim recebe um apóstrofo. Um texto malicioso não é executado como fórmula ao abrir um CSV no Excel. Veja [Regras de negócio](regras_de_negocio.md#35-proteção-contra-injeção-de-fórmulas-csv-injection). |
| Proteção dos arquivos do sistema | A exportação recusa gravar por cima dos arquivos de dados, da trava e dos temporários do próprio sistema. |
| Integridade na gravação | Gravação em arquivo temporário e substituição atômica; backup da versão anterior; desfazer na memória se a gravação falhar. |
| Instância única | Uma trava do sistema operacional impede abrir duas cópias que apagariam as alterações uma da outra. |
| Erros visíveis | Falhas ao gravar o histórico e erros inesperados são informados ao usuário, em vez de passarem em silêncio. |
| Dados fora do Git | O `.gitignore` impede que a pasta `dados/` seja versionada daqui em diante. |
| Rastreabilidade | O histórico registra cadastros, edições (com os campos alterados), saídas, exclusões, exportações e mudanças de configuração. |

### 2.2 O que o sistema **não** faz

| Ausência | Consequência |
|----------|--------------|
| Não há login nem perfis de usuário | Qualquer pessoa com acesso ao computador pode abrir o sistema, ver, alterar, excluir e exportar dados. |
| Não há criptografia | Os arquivos CSV e JSON podem ser lidos por qualquer programa (Bloco de Notas, Excel) por quem tiver acesso à pasta. |
| O histórico não identifica o operador | Não é possível saber **quem** realizou cada ação, apenas o que e quando. |
| O histórico não é inviolável | Pode ser editado ou apagado por quem acessa a pasta. Não serve como auditoria formal. |
| Não há prazo de retenção automático | Registros e histórico ficam guardados até alguém apagá-los. |
| Excluir um registro não apaga o histórico | O nome da pessoa continua em `historico.csv` após a exclusão. |
| Não há controle sobre os arquivos exportados | Depois de exportado, o CSV fica onde o usuário salvou, fora do controle do sistema. |

### 2.3 Recomendações

**Acesso ao computador e à pasta**

- Use o sistema em uma conta do Windows protegida por senha e bloqueie a
  tela ao se ausentar (`Windows + L`).
- Restrinja as permissões da pasta do projeto às contas que operam a
  portaria.
- Se o computador for portátil ou compartilhado, considere ativar a
  criptografia de disco do Windows (BitLocker ou Criptografia de
  dispositivo).

**Nuvem e versionamento**

- Evite manter a pasta `dados/` em pastas sincronizadas com a nuvem
  (OneDrive, Google Drive etc.) sem avaliar quem tem acesso a elas. A
  sincronização também copia os dados pessoais para fora do computador.
- **Não publique a pasta `dados/` em repositórios Git**, principalmente
  públicos. O `.gitignore` do projeto já impede isso daqui em diante, mas
  **o commit `f78d6e8`, já enviado ao GitHub, contém dados reais**. Remover
  os arquivos do índice não os apaga de commits anteriores. Veja como
  limpar o histórico em
  [Instalação e manutenção](instalacao_e_manutencao.md#64-controle-de-versão-git).
- Em apresentações, demonstrações e capturas de tela, use **dados
  fictícios**.

**Coleta e uso**

- Preencha os campos opcionais apenas quando forem necessários para a
  finalidade da portaria.
- Não registre em **Observações** informações sensíveis (saúde, religião,
  dados de documentos etc.).
- Trate os CSVs exportados com o mesmo cuidado dos arquivos originais:
  guarde-os em local protegido e apague-os quando não forem mais
  necessários.

**Retenção e exclusão**

- Defina um prazo de guarda e, periodicamente, exclua os registros antigos
  pela aba Portaria (filtre por período e use **Excluir selecionado** com
  seleção múltipla).
- Para remover também o histórico desses registros, é preciso editar
  `historico.csv` manualmente, com o sistema fechado.
- Lembre-se de que `registros_backup.csv`, `registros_original_*.csv`,
  backups manuais e exportações também podem conter os dados excluídos.

**Atendimento a solicitações de titulares**

- Para localizar todos os registros de uma pessoa, use a **pesquisa** na aba
  Portaria e na aba Histórico. A exportação dos registros filtrados pode ser
  usada para fornecer uma cópia dos dados.

## 3. Cuidados com os arquivos locais

| Cuidado | Motivo |
|---------|--------|
| **Não use a mesma pasta de dados em dois computadores ao mesmo tempo.** | No mesmo computador, o sistema impede uma segunda cópia. Em uma pasta de rede compartilhada, a trava depende do servidor de arquivos e **não foi testada**. Se falhar, cada computador grava o arquivo inteiro e a última gravação apaga as alterações do outro. |
| **Não edite os arquivos com o sistema aberto.** | O sistema mantém os registros na memória e regrava o arquivo inteiro na próxima alteração, descartando edições externas. |
| **Feche o `registros.csv` no Excel antes de usar o sistema.** | Com o arquivo aberto no Excel, o Windows impede a gravação e as operações falham (são desfeitas com segurança, mas não são salvas). |
| **Prefira editar pelo sistema, e não pelo Excel.** | Ao salvar, o Excel pode alterar o formato das datas, o separador ou a codificação. Linhas que deixarem de ser válidas serão ignoradas na próxima abertura (com aviso e cópia do original). |
| **Se precisar editar manualmente**, faça antes um backup, mantenha o cabeçalho, o separador `;` e o formato `dd/mm/aaaa hh:mm`. | Garante que o arquivo continue sendo lido corretamente. |
| **Não renomeie nem mova arquivos de `dados/`.** | O sistema procura os arquivos pelos nomes fixos. Um `registros.csv` ausente faz o sistema abrir vazio. |
| **Não apague `configuracoes.json` nem `historico.csv` sem necessidade.** | Os dois guardam o maior ID já usado. Sem **ambos**, IDs de registros excluídos podem voltar a ser usados (veja a [seção 4](#4-limitações-conhecidas)). |
| **Faça backups manuais periódicos.** | O backup automático guarda só a versão anterior de `registros.csv`. Veja [Backups](instalacao_e_manutencao.md#5-backups). |
| **Mantenha o relógio do computador correto.** | Validações de data futura, permanência, alerta e filtros de período usam a data/hora do computador. |

## 4. Limitações conhecidas

### Uso e acesso

- Sistema **monousuário** e **local**: não há rede, servidor nem banco de
  dados. A trava impede duas cópias no mesmo computador; o uso por vários
  computadores numa pasta de rede não é suportado.
- Não há autenticação, perfis de acesso nem registro do operador nas
  ações.

### Dados e arquivos

- O backup automático guarda apenas a **versão imediatamente anterior** de
  `registros.csv`. `historico.csv` e `configuracoes.json` não têm backup
  automático.
- A exclusão não pode ser desfeita pela interface.
- Se a gravação do histórico falhar, a operação principal é mantida e o
  usuário é avisado, mas o evento **não** é gravado depois.
- Se `configuracoes.json` **e** `historico.csv` forem perdidos e os
  registros de maior ID tiverem sido excluídos, esses IDs podem ser
  reutilizados.
- As regras de leitura do CSV são menos rígidas que as do formulário. Um
  arquivo editado manualmente pode conter datas futuras, anteriores a 2000,
  nomes com números ou textos que começam com `=`, que serão aceitos. Esses
  textos continuam neutralizados na exportação.
- O sistema não oferece arquivamento nem limpeza do histórico.
- Todo o conteúdo dos arquivos é carregado na memória e a tabela é
  redesenhada a cada mudança de filtro. O desempenho com grandes volumes de
  registros não foi medido.

### Regras e interface

- A pesquisa não procura em Observações, Modelo e Cor.
- Nomes não são padronizados (maiúsculas e minúsculas são mantidas como
  digitadas). A verificação de duplicidade só considera registros com o
  mesmo nome, tipo **e** horário de entrada.
- Telefone e placa seguem apenas os formatos brasileiros.
- Registrar saída só usa o horário atual; outro horário exige edição.
- Interface desenvolvida e testada apenas no Windows (fonte Segoe UI;
  botão "Abrir pasta dos arquivos" depende do Windows).

### Escopo

- O controle de vagas de estacionamento não foi implementado.
- Os testes automatizados cobrem o núcleo. A interface gráfica é verificada
  pelos casos manuais de [Casos de teste](casos_de_teste.md).

As limitações resolvidas na versão 3.1 estão listadas no
[Relatório de auditoria](relatorio_auditoria.md).
