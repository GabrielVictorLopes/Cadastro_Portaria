"""Montagem da interface e inicialização do programa."""

import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from nucleo.estado import T
from nucleo.persistencia import carregar_configuracoes, carregar_registros, obter_trava
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


def mostrar_erro_inesperado(tipo, valor, rastro):
    """
    Erro não previsto em um botão ou atalho: em vez de falhar em silêncio
    (o que acontece ao abrir sem terminal), avisa o usuário. Os dados já
    salvos não são afetados.
    """
    traceback.print_exception(tipo, valor, rastro, file=sys.stderr)
    messagebox.showerror("Erro inesperado",
                         "Ocorreu um erro inesperado nesta ação.\n"
                         "Os dados já salvos não foram afetados.\n\n"
                         f"Detalhe: {tipo.__name__}: {valor}")


def avisar_ja_aberto():
    """Mostra o aviso de que outra cópia do programa já está aberta."""
    raiz = tk.Tk()
    raiz.withdraw()
    messagebox.showerror("Cadastro de Portaria",
                         "O sistema já está aberto em outra janela.\n\n"
                         "Use a janela que já está aberta: duas cópias abertas "
                         "ao mesmo tempo apagariam as alterações uma da outra.",
                         parent=raiz)
    raiz.destroy()


def iniciar():
    if not obter_trava():
        avisar_ja_aberto()
        return
    carregar_configuracoes()
    criar_interface()
    T.janela.report_callback_exception = mostrar_erro_inesperado
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
