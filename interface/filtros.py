"""Barra de pesquisa e filtros da aba Portaria."""

import tkinter as tk
from tkinter import messagebox

from nucleo.constantes import FILTRO_MOTIVOS, FILTRO_TIPOS, MASCARA_DATA, PERIODOS
from nucleo.estado import S, T
from nucleo.utilitarios import converter_data_simples
from nucleo.calculos import opcoes_filtro_situacao
from interface.mascaras import aplicar_mascara
from interface.base import (
    criar_botao, criar_campo_texto, criar_cartao, criar_lista, criar_quadro,
    criar_rotulo, mostrar_status)
from interface.atualizacao import atualizar_tabela, criterios_atuais


# ======================================================================
# INTERFACE: PESQUISA E FILTROS
# ======================================================================
def criar_filtros(pai):
    """Pesquisa e filtros (os filtros avançados ficam recolhidos)."""
    cartao, conteudo, _ = criar_cartao(pai, "Pesquisa e filtros")
    cartao.pack(fill="x", pady=(0, 8))

    T.var_pesquisa = tk.StringVar()
    T.var_empresa = tk.StringVar()
    T.var_data_ini = tk.StringVar()
    T.var_data_fim = tk.StringVar()
    T.var_filtro_tipo = tk.StringVar(value="Todos")
    T.var_filtro_situacao = tk.StringVar(value="Todos")
    T.var_filtro_periodo = tk.StringVar(value="Todos")
    T.var_filtro_motivo = tk.StringVar(value="Todos")

    linha1 = criar_quadro(conteudo)
    linha1.pack(fill="x")
    linha1.columnconfigure(1, weight=1)
    criar_rotulo(linha1, "Pesquisar:").grid(row=0, column=0, sticky="w")
    T.campo_pesquisa = criar_campo_texto(linha1, T.var_pesquisa)
    T.campo_pesquisa.grid(row=0, column=1, sticky="ew", ipady=4, padx=(8, 12))

    def lista(coluna, texto, variavel, valores, largura, ao_selecionar=ao_filtro_mudou):
        criar_rotulo(linha1, texto).grid(row=0, column=coluna, sticky="w")
        caixa = criar_lista(linha1, variavel, valores, largura)
        caixa.grid(row=0, column=coluna + 1, padx=(6, 12))
        caixa.bind("<<ComboboxSelected>>", lambda e: ao_selecionar())
        return caixa

    lista(2, "Tipo:", T.var_filtro_tipo, FILTRO_TIPOS, 11)
    T.lista_situacao = lista(4, "Situação:", T.var_filtro_situacao,
                             opcoes_filtro_situacao(), 10)
    T.lista_periodo = lista(6, "Período:", T.var_filtro_periodo, PERIODOS, 19,
                            ao_mudar_periodo)

    T.botao_avancado = criar_botao(linha1, "Filtros avançados ▸", alternar_avancados,
                                   "cinza", 18)
    T.botao_avancado.grid(row=0, column=8, padx=(0, 6))
    criar_botao(linha1, "Aplicar", aplicar_filtros, "azul", 9).grid(row=0, column=9,
                                                                    padx=(0, 6))
    criar_botao(linha1, "Limpar filtros", limpar_filtros, "cinza", 13)\
        .grid(row=0, column=10)

    # --- Filtros avançados (recolhidos) ---
    T.frame_avancado = criar_quadro(conteudo)
    T.frame_avancado.pack(fill="x", pady=(8, 0))
    T.frame_avancado.columnconfigure(7, weight=1)
    criar_rotulo(T.frame_avancado, "De:").grid(row=0, column=0, sticky="w")
    T.campo_data_ini = criar_campo_texto(T.frame_avancado, T.var_data_ini)
    T.campo_data_ini.configure(width=11)
    T.campo_data_ini.grid(row=0, column=1, ipady=3, padx=(6, 12))
    criar_rotulo(T.frame_avancado, "Até:").grid(row=0, column=2, sticky="w")
    T.campo_data_fim = criar_campo_texto(T.frame_avancado, T.var_data_fim)
    T.campo_data_fim.configure(width=11)
    T.campo_data_fim.grid(row=0, column=3, ipady=3, padx=(6, 12))
    criar_rotulo(T.frame_avancado, "Motivo:").grid(row=0, column=4, sticky="w")
    caixa = criar_lista(T.frame_avancado, T.var_filtro_motivo, FILTRO_MOTIVOS, 12)
    caixa.grid(row=0, column=5, padx=(6, 12))
    caixa.bind("<<ComboboxSelected>>", lambda e: ao_filtro_mudou())
    criar_rotulo(T.frame_avancado, "Empresa:").grid(row=0, column=6, sticky="w")
    criar_campo_texto(T.frame_avancado, T.var_empresa)\
        .grid(row=0, column=7, sticky="ew", ipady=3, padx=(6, 0))
    T.frame_avancado.pack_forget()
    S.avancados_abertos = False

    T.var_pesquisa.trace_add("write", lambda *a: ao_filtro_mudou())
    T.var_empresa.trace_add("write", lambda *a: ao_filtro_mudou())
    for variavel, campo in ((T.var_data_ini, T.campo_data_ini),
                            (T.var_data_fim, T.campo_data_fim)):
        variavel.trace_add("write", lambda *a, var=variavel, cp=campo:
                           ao_digitar_data_filtro(var, cp))


def alternar_avancados(abrir=None):
    """Mostra ou esconde os filtros avançados."""
    S.avancados_abertos = (not S.avancados_abertos) if abrir is None else abrir
    if S.avancados_abertos:
        T.frame_avancado.pack(fill="x", pady=(8, 0))
        T.botao_avancado.configure(text="Filtros avançados ▾")
    else:
        T.frame_avancado.pack_forget()
        T.botao_avancado.configure(text="Filtros avançados ▸")


def ao_filtro_mudou():
    """Qualquer filtro mudou: atualiza a tabela (a menos que seja uma mudança em lote)."""
    if not S.suspender_filtros:
        atualizar_tabela()


def ao_mudar_periodo():
    """Escolheu um período pronto: apaga as datas. Personalizado: abre os campos de data."""
    if T.var_filtro_periodo.get() == "Período personalizado":
        alternar_avancados(True)
    else:
        S.suspender_filtros = True
        T.var_data_ini.set("")
        T.var_data_fim.set("")
        S.suspender_filtros = False
    atualizar_tabela()


def ao_digitar_data_filtro(variavel, campo):
    """Máscara (só números) nas datas do filtro; digitar uma data ativa o período personalizado."""
    aplicar_mascara(variavel, campo, MASCARA_DATA[0], MASCARA_DATA[1])
    if S.suspender_filtros:
        return
    if variavel.get() != "" and T.var_filtro_periodo.get() != "Período personalizado":
        T.var_filtro_periodo.set("Período personalizado")
    atualizar_tabela()


def aplicar_filtros():
    """Botão Aplicar: confere o período personalizado e atualiza a tabela."""
    c = criterios_atuais()
    if c["data_ini"] and c["data_fim"] and c["data_ini"] > c["data_fim"]:
        messagebox.showwarning("Período inválido",
                               "A data inicial não pode ser posterior à data final.")
        return
    for texto, campo in ((T.var_data_ini.get(), "inicial"),
                         (T.var_data_fim.get(), "final")):
        if texto != "" and converter_data_simples(texto) is None:
            messagebox.showwarning("Data inválida",
                                   f"A data {campo} do filtro é inválida (use dd/mm/aaaa).")
            return
    atualizar_tabela()
    mostrar_status("Filtros aplicados.", "info")


def limpar_filtros(evento=None):
    """Volta todos os filtros ao padrão e mostra todos os registros."""
    S.suspender_filtros = True
    T.var_pesquisa.set("")
    T.var_empresa.set("")
    T.var_data_ini.set("")
    T.var_data_fim.set("")
    T.var_filtro_tipo.set("Todos")
    T.var_filtro_situacao.set("Todos")
    T.var_filtro_periodo.set("Todos")
    T.var_filtro_motivo.set("Todos")
    S.suspender_filtros = False
    atualizar_tabela()
    mostrar_status("Filtros limpos.", "info")
