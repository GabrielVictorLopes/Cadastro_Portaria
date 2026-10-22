"""Criação das abas e atalhos de teclado."""

import tkinter as tk
from tkinter import ttk

from nucleo.estado import T
from interface.base import aba_atual, criar_quadro, ir_para_aba
from interface.formulario import editar, nova_entrada, salvar_formulario
from interface.filtros import limpar_filtros
from interface.atualizacao import atualizar_historico
from interface.tabela import criar_aba_portaria
from interface.acoes import excluir, registrar_saida
from interface.aba_historico import criar_aba_historico
from interface.aba_configuracoes import (
    criar_aba_configuracoes, criar_aba_sobre, salvar_configuracoes_da_tela)


# ======================================================================
# NAVEGAÇÃO (abas)
# ======================================================================
ABAS = [("portaria", "  Portaria  ", criar_aba_portaria),
        ("historico", "  Histórico  ", criar_aba_historico),
        ("configuracoes", "  Configurações  ", criar_aba_configuracoes),
        ("sobre", "  Sobre / Ajuda  ", criar_aba_sobre)]


def criar_abas():
    T.abas = ttk.Notebook(T.janela)
    T.abas.pack(fill="both", expand=True, padx=14, pady=(10, 4))
    T.quadros_abas = {}
    for chave, titulo, construtor in ABAS:
        quadro = criar_quadro(T.abas, "fundo")
        T.abas.add(quadro, text=titulo)
        T.quadros_abas[chave] = quadro
        construtor(quadro)
    T.abas.bind("<<NotebookTabChanged>>", lambda e: ao_mudar_aba())


def ao_mudar_aba():
    chave = aba_atual()
    if chave == "historico":
        atualizar_historico()


# ======================================================================
# ATALHOS DE TECLADO
# ======================================================================
def focar_pesquisa(evento=None):
    """Ctrl+F: leva o cursor para o campo de pesquisa."""
    ir_para_aba("portaria")
    T.campo_pesquisa.focus_set()
    T.campo_pesquisa.select_range(0, tk.END)


def atalho_salvar(evento=None):
    """Ctrl+S na janela principal: salva as configurações (o cadastro tem o seu próprio Ctrl+S)."""
    if aba_atual() == "configuracoes":
        salvar_configuracoes_da_tela()


def atalho_limpar_filtros(evento=None):
    ir_para_aba("portaria")
    limpar_filtros()


def configurar_atalhos():
    """
    Liga as teclas às funções. Delete só funciona com a tabela em foco, para
    não apagar letras de quem está digitando em um campo de texto.
    """
    atalhos = {"n": nova_entrada, "f": focar_pesquisa, "s": atalho_salvar,
               "e": editar, "r": registrar_saida, "l": atalho_limpar_filtros}
    for letra, funcao in atalhos.items():
        T.janela.bind(f"<Control-{letra}>", funcao)
        T.janela.bind(f"<Control-{letra.upper()}>", funcao)

    T.tabela.bind("<Delete>", excluir)
    T.tabela.bind("<Return>", editar)
    for campo in T.campos.values():
        campo.bind("<Return>", salvar_formulario)       # Enter confirma o formulário
    T.campo_pesquisa.bind("<Return>", lambda e: T.tabela.focus_set())
