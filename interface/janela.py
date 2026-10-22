"""Janela principal, cabeçalho, barra de status e troca de tema."""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox

from nucleo.constantes import FONTE
from nucleo.estado import S, T, config
from nucleo.persistencia import registrar_historico, salvar_configuracoes
from interface.base import (
    aplicar_opcoes, configurar_estilo, configurar_tags_tabela, configurar_tags_texto,
    cor, criar_quadro, criar_rotulo, mostrar_status, registrar)
from interface.formulario import (
    atualizar_modo_formulario, formulario_tem_alteracoes, pai_mensagens)
from interface.atualizacao import atualizar_tempos


def aplicar_tema():
    """Aplica o tema escolhido (config['tema']) em TODOS os componentes."""
    S.tema = config["tema"]
    configurar_estilo()
    T.janela.configure(bg=cor("fundo"))
    for widget, opcoes in T.tematizaveis:
        aplicar_opcoes(widget, opcoes)
    for texto in T.textos:
        configurar_tags_texto(texto)
    configurar_tags_tabela()
    T.botao_tema.configure(text="Tema claro" if S.tema == "escuro" else "Tema escuro")
    atualizar_modo_formulario()        # reaplica o destaque de edição (amarelo) sobre o novo tema


def alternar_tema():
    """Botão do cabeçalho: alterna entre tema claro e escuro."""
    anterior = config["tema"]
    config["tema"] = "escuro" if anterior == "claro" else "claro"
    aplicar_tema()
    T.var_config_tema.set(config["tema"].capitalize())
    salvar_configuracoes()
    registrar_historico("Configuração", "", "",
                        f"Tema alterado de {anterior} para {config['tema']}")
    mostrar_status(f"Tema {config['tema']} ativado.", "info")


# ======================================================================
# INTERFACE: JANELA, CABEÇALHO E BARRA DE STATUS
# ======================================================================
def criar_janela():
    janela = tk.Tk()
    T.janela = janela
    janela.title("Cadastro de Portaria - Controle de entrada e saída")
    largura = min(1280, janela.winfo_screenwidth() - 40)
    altura = min(860, janela.winfo_screenheight() - 90)
    janela.geometry(f"{largura}x{altura}+20+10")
    janela.minsize(min(1000, largura), min(640, altura))
    S.tema = config["tema"]
    janela.configure(bg=cor("fundo"))
    configurar_estilo()
    janela.protocol("WM_DELETE_WINDOW", ao_fechar)


def criar_cabecalho():
    """Faixa do cabeçalho: nome do sistema à esquerda; identificação, tema e relógio à direita."""
    faixa = criar_quadro(T.janela, "cabecalho")
    faixa.pack(fill="x")
    interno = criar_quadro(faixa, "cabecalho")
    interno.pack(fill="x", padx=20, pady=10)

    esquerda = criar_quadro(interno, "cabecalho")
    esquerda.pack(side="left")
    criar_rotulo(esquerda, "Cadastro de Portaria", "cabecalho", "branco",
                 (FONTE, 20, "bold")).pack(anchor="w")
    criar_rotulo(esquerda, "Controle de entrada e saída", "cabecalho",
                 "cabecalho_texto", (FONTE, 11)).pack(anchor="w")

    direita = criar_quadro(interno, "cabecalho")
    direita.pack(side="right")
    linha = criar_quadro(direita, "cabecalho")
    linha.pack(anchor="e")
    criar_rotulo(linha, "CONTROLE DE ACESSO", "cabecalho_escuro", "branco",
                 (FONTE, 9, "bold"), padx=12, pady=4).pack(side="left")
    T.botao_tema = tk.Button(linha, text="Tema escuro", command=alternar_tema,
                             font=(FONTE, 9, "bold"), relief="flat", bd=0,
                             cursor="hand2", padx=10, pady=4)
    registrar(T.botao_tema, bg="cabecalho_escuro", fg="branco",
              activebackground="azul_h", activeforeground="branco")
    T.botao_tema.pack(side="left", padx=(8, 0))
    T.rotulo_relogio = criar_rotulo(direita, "", "cabecalho", "cabecalho_texto",
                                    (FONTE, 10))
    T.rotulo_relogio.pack(anchor="e", pady=(6, 0))

    criar_quadro(T.janela, "azul", height=4).pack(fill="x")     # faixa de destaque


def criar_barra_status():
    """Barra inferior: mensagens discretas à esquerda e contagem à direita."""
    barra = criar_quadro(T.janela, "card")
    barra.pack(side="bottom", fill="x")
    T.rotulo_status = criar_rotulo(barra, "Pronto.", "card", "suave", (FONTE, 9))
    T.rotulo_status.pack(side="left", padx=14, pady=4)
    T.rotulo_contagem = criar_rotulo(barra, "", "card", "suave", (FONTE, 9))
    T.rotulo_contagem.pack(side="right", padx=14)


def atualizar_relogio():
    """Atualiza data e hora a cada segundo; a cada minuto atualiza os tempos."""
    T.rotulo_relogio.configure(text=datetime.now().strftime("%d/%m/%Y   %H:%M:%S"))
    S.ticks += 1
    if S.ticks % 60 == 0:
        atualizar_tempos()
    T.janela.after(1000, atualizar_relogio)


def ao_fechar():
    """Pede confirmação se a janela de cadastro estiver aberta com dados não salvos."""
    if S.formulario_aberto and formulario_tem_alteracoes() and not messagebox.askyesno(
            "Sair do sistema",
            "Há dados no formulário que ainda não foram salvos.\n"
            "Deseja sair mesmo assim?", parent=pai_mensagens()):
        return
    T.janela.destroy()
