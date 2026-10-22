"""Painel de indicadores (dashboard)."""

import tkinter as tk

from nucleo.constantes import FONTE
from nucleo.estado import T
from interface.base import criar_quadro, criar_rotulo, registrar


# ======================================================================
# INTERFACE: DASHBOARD (indicadores)
# ======================================================================
# (título do grupo, cor do título, [(indicador, rótulo, cor do número)])
GRUPOS_INDICADORES = [
    ("TODOS OS REGISTROS", "suave",
     [("total", "TOTAL", "azul"), ("dentro", "NO LOCAL AGORA", "verde"),
      ("saiu", "SAÍRAM", "suave")]),
    ("SOMENTE HOJE", "amarelo_h",
     [("entradas_hoje", "ENTRADAS", "azul"),
      ("entregadores_hoje", "ENTREGADORES", "azul")]),
    ("NO LOCAL AGORA, POR TIPO", "verde",
     [("visitantes", "VISITANTES", "verde"),
      ("funcionarios", "FUNCIONÁRIOS", "verde"),
      ("moradores", "MORADORES", "verde")]),
]


def criar_dashboard(pai):
    """Indicadores no topo. Os três grupos deixam claro o que cada número mede."""
    T.var_ind = {chave: tk.StringVar(value="0")
                 for _, _, itens in GRUPOS_INDICADORES for chave, _, _ in itens}
    faixa = criar_quadro(pai, "fundo")
    faixa.pack(fill="x", pady=(0, 8))

    for coluna, (titulo, cor_titulo, itens) in enumerate(GRUPOS_INDICADORES):
        caixa = tk.Frame(faixa, highlightthickness=1)
        registrar(caixa, bg="card", highlightbackground="borda")
        caixa.grid(row=0, column=coluna, sticky="nsew",
                   padx=(0 if coluna == 0 else 8, 0))
        faixa.columnconfigure(coluna, weight=len(itens))
        criar_rotulo(caixa, titulo, "card", cor_titulo,
                     (FONTE, 8, "bold")).pack(anchor="w", padx=10, pady=(6, 0))
        interno = criar_quadro(caixa)
        interno.pack(fill="x", padx=10, pady=(0, 6))
        for posicao, (chave, rotulo, cor_numero) in enumerate(itens):
            interno.columnconfigure(posicao, weight=1, uniform=f"grupo{coluna}")
            mini = criar_quadro(interno)
            mini.grid(row=0, column=posicao, sticky="w")
            criar_rotulo(mini, rotulo, "card", "suave",
                         (FONTE, 8, "bold")).pack(anchor="w")
            criar_rotulo(mini, "", "card", cor_numero, (FONTE, 18, "bold"),
                         textvariable=T.var_ind[chave]).pack(anchor="w")
