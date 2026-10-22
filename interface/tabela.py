"""Aba Portaria: tabela principal, painel de detalhes, botões e menu de contexto."""

import tkinter as tk
from tkinter import ttk

from nucleo.constantes import COLUNAS_TABELA, FONTE
from nucleo.estado import T, config
from interface.base import (
    criar_botao, criar_cartao, criar_quadro, criar_rotulo, criar_texto, registrar)
from interface.dashboard import criar_dashboard
from interface.formulario import duplo_clique, editar, nova_entrada
from interface.filtros import criar_filtros
from interface.atualizacao import atualizar_detalhes, ordenar_por
from interface.acoes import excluir, exportar, registrar_saida


# ======================================================================
# INTERFACE: TABELA PRINCIPAL, PAINEL DE DETALHES E AÇÕES
# ======================================================================
def criar_tabela(pai):
    """Tabela de registros (ttk.Treeview) com rolagem vertical e horizontal."""
    cartao = tk.Frame(pai, highlightthickness=1)
    registrar(cartao, bg="card", highlightbackground="borda")
    cartao.grid(row=0, column=0, sticky="nsew")
    cartao.rowconfigure(0, weight=1)
    cartao.columnconfigure(0, weight=1)

    nomes = [coluna[0] for coluna in COLUNAS_TABELA]
    T.tabela = ttk.Treeview(cartao, columns=nomes, show="headings",
                            selectmode="extended")
    for nome, titulo, largura, minimo, alinhamento, estica in COLUNAS_TABELA:
        # Clicar no cabeçalho ordena a tabela por essa coluna
        T.tabela.heading(nome, text=titulo, command=lambda c=nome: ordenar_por(c))
        T.tabela.column(nome, width=largura, minwidth=minimo, anchor=alinhamento,
                        stretch=estica)

    barra_v = ttk.Scrollbar(cartao, orient="vertical", command=T.tabela.yview)
    barra_h = ttk.Scrollbar(cartao, orient="horizontal", command=T.tabela.xview)
    T.tabela.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
    T.tabela.grid(row=0, column=0, sticky="nsew")
    barra_v.grid(row=0, column=1, sticky="ns")
    barra_h.grid(row=1, column=0, sticky="ew")

    # Mensagem mostrada por cima da tabela quando não há linhas
    T.rotulo_vazio = criar_rotulo(T.tabela, "", "card", "suave", (FONTE, 11),
                                  justify="center")

    T.tabela.bind("<Double-1>", duplo_clique)                       # editar
    T.tabela.bind("<<TreeviewSelect>>", lambda e: atualizar_detalhes())
    T.tabela.bind("<Button-3>", abrir_menu_contexto)                # botão direito
    aplicar_colunas_visiveis()


def aplicar_colunas_visiveis():
    """Mostra ou esconde as colunas opcionais (Motivo e Veículo)."""
    visiveis = [c[0] for c in COLUNAS_TABELA
                if not (c[0] == "Motivo" and not config["mostrar_motivo"])
                and not (c[0] == "Veiculo" and not config["mostrar_veiculo"])]
    T.tabela.configure(displaycolumns=visiveis)


def criar_detalhes(pai):
    """Painel lateral com todos os dados do registro selecionado."""
    cartao, conteudo, _ = criar_cartao(pai, "Registro selecionado")
    cartao.grid(row=0, column=1, sticky="ns", padx=(10, 0))
    T.detalhes = criar_texto(conteudo, altura=10, largura=34)
    barra = ttk.Scrollbar(conteudo, orient="vertical", command=T.detalhes.yview)
    T.detalhes.configure(yscrollcommand=barra.set)
    T.detalhes.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")


def criar_barra_acoes(pai):
    """Barra de ações no topo da aba: o cadastro é aberto por aqui."""
    faixa = criar_quadro(pai, "fundo")
    faixa.pack(fill="x", pady=(0, 8))
    criar_botao(faixa, "+ Nova entrada", nova_entrada, "verde", 18).pack(side="left")
    criar_botao(faixa, "Registrar saída", registrar_saida, "azul", 16)\
        .pack(side="left", padx=8)
    criar_botao(faixa, "Editar selecionado", editar, "amarelo", 18).pack(side="left")
    criar_botao(faixa, "Excluir selecionado", excluir, "vermelho", 18)\
        .pack(side="left", padx=8)
    criar_botao(faixa, "Exportar filtrados", lambda: exportar("filtrados"), "cinza", 16)\
        .pack(side="left")
    criar_rotulo(faixa, "Ctrl+N nova • Ctrl+R saída • Ctrl+E editar • Del excluir • "
                        "Ctrl+F pesquisar", "fundo", "suave", (FONTE, 9)).pack(side="right")


def criar_aba_portaria(aba):
    """Aba principal: dashboard, ações, filtros e a tabela (que ocupa o espaço restante)."""
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    criar_dashboard(corpo)
    criar_barra_acoes(corpo)
    criar_filtros(corpo)
    area = criar_quadro(corpo, "fundo")
    area.pack(fill="both", expand=True)
    area.rowconfigure(0, weight=1)
    area.columnconfigure(0, weight=1)
    criar_tabela(area)
    criar_detalhes(area)


# ======================================================================
# MENU DE CONTEXTO (botão direito na tabela)
# ======================================================================
def criar_menu_contexto():
    """Menu com as ações principais sobre o registro."""
    T.menu_contexto = tk.Menu(T.janela, tearoff=0)
    registrar(T.menu_contexto, bg="card", fg="texto", activebackground="selecao",
              activeforeground="texto")
    T.menu_contexto.add_command(label="Editar", command=editar)
    T.menu_contexto.add_command(label="Registrar saída", command=registrar_saida)
    T.menu_contexto.add_separator()
    T.menu_contexto.add_command(label="Excluir", command=excluir)


def abrir_menu_contexto(evento):
    """Seleciona a linha clicada (se necessário) e abre o menu."""
    item = T.tabela.identify_row(evento.y)
    if not item:
        return
    if item not in T.tabela.selection():
        T.tabela.selection_set(item)
    try:
        T.menu_contexto.tk_popup(evento.x_root, evento.y_root)
    finally:
        T.menu_contexto.grab_release()
