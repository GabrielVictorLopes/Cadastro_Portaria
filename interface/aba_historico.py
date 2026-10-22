"""Aba Histórico de atividades."""

import tkinter as tk

from nucleo.constantes import ACOES_HISTORICO, FONTE, MASCARA_DATA
from nucleo.estado import T
from interface.mascaras import aplicar_mascara
from interface.base import (
    criar_botao, criar_campo_texto, criar_cartao, criar_lista, criar_quadro,
    criar_rotulo, criar_tabela_simples)
from interface.atualizacao import atualizar_historico
from interface.acoes import exportar


# ======================================================================
# INTERFACE: ABA HISTÓRICO
# ======================================================================


def criar_aba_historico(aba):
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    T.var_hist_texto = tk.StringVar()
    T.var_hist_acao = tk.StringVar(value="Todas")
    T.var_hist_ini = tk.StringVar()
    T.var_hist_fim = tk.StringVar()

    cartao, conteudo, _ = criar_cartao(corpo, "Histórico de atividades")
    cartao.pack(fill="x", pady=(0, 8))
    linha = criar_quadro(conteudo)
    linha.pack(fill="x")
    linha.columnconfigure(1, weight=1)
    criar_rotulo(linha, "Pesquisar:").grid(row=0, column=0, sticky="w")
    campo = criar_campo_texto(linha, T.var_hist_texto)
    campo.grid(row=0, column=1, sticky="ew", ipady=4, padx=(8, 12))
    criar_rotulo(linha, "Ação:").grid(row=0, column=2, sticky="w")
    lista = criar_lista(linha, T.var_hist_acao, ["Todas"] + ACOES_HISTORICO, 12)
    lista.grid(row=0, column=3, padx=(6, 12))
    lista.bind("<<ComboboxSelected>>", lambda e: atualizar_historico())
    criar_rotulo(linha, "De:").grid(row=0, column=4, sticky="w")
    campo_ini = criar_campo_texto(linha, T.var_hist_ini)
    campo_ini.configure(width=11)
    campo_ini.grid(row=0, column=5, ipady=3, padx=(6, 10))
    criar_rotulo(linha, "Até:").grid(row=0, column=6, sticky="w")
    campo_fim = criar_campo_texto(linha, T.var_hist_fim)
    campo_fim.configure(width=11)
    campo_fim.grid(row=0, column=7, ipady=3, padx=(6, 12))
    criar_botao(linha, "Limpar", limpar_filtros_historico, "cinza", 9)\
        .grid(row=0, column=8, padx=(0, 6))
    criar_botao(linha, "Exportar", lambda: exportar("historico"), "azul", 10)\
        .grid(row=0, column=9)

    T.var_hist_texto.trace_add("write", lambda *a: atualizar_historico())
    for variavel, campo_data in ((T.var_hist_ini, campo_ini), (T.var_hist_fim, campo_fim)):
        variavel.trace_add("write", lambda *a, var=variavel, cp=campo_data:
                           (aplicar_mascara(var, cp, MASCARA_DATA[0], MASCARA_DATA[1]),
                            atualizar_historico()))

    criar_rotulo(corpo, "O histórico é um registro local: quem tem acesso à pasta do "
                        "programa pode editar o arquivo historico.csv. Não é uma "
                        "auditoria inviolável. Excluir um registro não apaga o seu histórico.",
                 "fundo", "suave", (FONTE, 9), wraplength=1000, justify="left")\
        .pack(side="bottom", anchor="w", pady=(6, 0))

    quadro, T.tabela_historico = criar_tabela_simples(
        corpo, [("data", "Data/Hora", 140, "center"), ("acao", "Ação", 90, "center"),
                ("id", "ID", 50, "center"), ("nome", "Nome", 180, "w"),
                ("descricao", "Descrição", 520, "w")], 12)
    quadro.pack(fill="both", expand=True)
    T.rotulo_hist = criar_rotulo(corpo, "", "fundo", "suave", (FONTE, 9))
    T.rotulo_hist.pack(side="bottom", anchor="e")


def limpar_filtros_historico():
    T.var_hist_texto.set("")
    T.var_hist_acao.set("Todas")
    T.var_hist_ini.set("")
    T.var_hist_fim.set("")
    atualizar_historico()
