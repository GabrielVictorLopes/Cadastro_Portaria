"""Estado compartilhado do programa (registros, configurações e widgets)."""

from types import SimpleNamespace

from nucleo.constantes import CONFIG_PADRAO


# ======================================================================
# ESTADO DO PROGRAMA
# ======================================================================
registros = []                    # lista de dicionários (um por pessoa)
config = dict(CONFIG_PADRAO)      # configurações carregadas do arquivo

# Estado geral (em vez de várias variáveis globais soltas)
S = SimpleNamespace(
    proximo_id=1,                 # só aumenta: IDs excluídos não são reaproveitados
    id_em_edicao=None,            # None = cadastrando | número = editando
    coluna_ordenada="ID",
    ordem_decrescente=False,
    tema="claro",
    suspender_filtros=False,      # evita atualizar a tabela várias vezes seguidas
    extras_abertos=False,
    formulario_aberto=False,      # janela de cadastro/edição está aberta?
    avancados_abertos=False,
    id_status=None,               # temporizador da mensagem da barra de status
    ticks=0,
    dia_tabela=None,              # dia em que a tabela foi filtrada ("Hoje" muda à meia-noite)
    falha_historico=False,        # alguma linha do histórico não pôde ser gravada (avisar)
    trava=None,                   # arquivo de trava aberto enquanto o programa roda
)

# Widgets da interface (criados em criar_interface)
T = SimpleNamespace(tematizaveis=[], textos=[])
