"""Montagem da interface e inicialização do programa."""

from tkinter import messagebox

from nucleo.estado import T
from nucleo.persistencia import carregar_configuracoes, carregar_registros
from interface.janela import (
    aplicar_tema, atualizar_relogio, criar_barra_status, criar_cabecalho,
    criar_janela)
from interface.formulario import criar_janela_formulario, limpar_formulario
from interface.atualizacao import (
    atualizar_cabecalhos, atualizar_historico, atualizar_tabela)
from interface.tabela import criar_menu_contexto
from interface.navegacao import configurar_atalhos, criar_abas


# ======================================================================
# FECHAMENTO E INICIALIZAÇÃO
# ======================================================================


def mostrar_avisos_carregamento(avisos):
    """Mostra, de forma amigável, os avisos encontrados ao abrir o CSV."""
    detalhes = avisos[:8]
    if len(avisos) > 8:
        detalhes.append(f"... e mais {len(avisos) - 8} aviso(s).")
    messagebox.showwarning("Atenção ao carregar os registros",
                           "\n\n".join(detalhes))


def criar_interface():
    """Monta a tela inteira."""
    criar_janela()
    criar_cabecalho()
    criar_barra_status()
    criar_abas()
    criar_janela_formulario()
    criar_menu_contexto()
    aplicar_tema()


def iniciar():
    carregar_configuracoes()
    criar_interface()
    avisos = carregar_registros()
    limpar_formulario()
    atualizar_cabecalhos()
    atualizar_tabela()
    atualizar_historico()
    configurar_atalhos()
    atualizar_relogio()
    if avisos:
        mostrar_avisos_carregamento(avisos)
    T.janela.mainloop()
