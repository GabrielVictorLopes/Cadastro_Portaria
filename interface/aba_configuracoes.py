"""Abas Configurações e Sobre/Ajuda."""

import os
import tkinter as tk
from tkinter import messagebox, ttk

from nucleo.constantes import (
    ARQ_BACKUP, ARQ_CONFIG, ARQ_HISTORICO, ARQ_REGISTROS, FONTE, PASTA_DADOS, VERSAO)
from nucleo.estado import T, config
from nucleo.calculos import opcoes_filtro_situacao
from nucleo.persistencia import registrar_historico, salvar_configuracoes
from interface.base import (
    criar_botao, criar_cartao, criar_lista, criar_quadro, criar_rotulo, criar_texto,
    escrever_texto, mostrar_status)
from interface.janela import aplicar_tema
from interface.atualizacao import atualizar_historico, atualizar_tabela
from interface.tabela import aplicar_colunas_visiveis


# ======================================================================
# INTERFACE: ABAS CONFIGURAÇÕES E SOBRE
# ======================================================================
def criar_aba_configuracoes(aba):
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    cartao, conteudo, _ = criar_cartao(corpo, "Configurações")
    cartao.pack(fill="x")

    T.var_config_tema = tk.StringVar(value=config["tema"].capitalize())
    T.var_config_tempo = tk.StringVar(value=str(config["tempo_max_horas"]))
    T.var_config_alerta = tk.BooleanVar(value=config["alerta_ativo"])
    T.var_config_motivo = tk.BooleanVar(value=config["mostrar_motivo"])
    T.var_config_veiculo = tk.BooleanVar(value=config["mostrar_veiculo"])

    criar_rotulo(conteudo, "Tema:").grid(row=0, column=0, sticky="w", pady=6)
    criar_lista(conteudo, T.var_config_tema, ["Claro", "Escuro"], 12)\
        .grid(row=0, column=1, sticky="w", padx=10)
    criar_rotulo(conteudo, "Tempo máximo de permanência (horas):")\
        .grid(row=1, column=0, sticky="w", pady=6)
    ttk.Spinbox(conteudo, from_=1, to=72, width=6, textvariable=T.var_config_tempo)\
        .grid(row=1, column=1, sticky="w", padx=10)
    ttk.Checkbutton(conteudo, text="Alertar quando a permanência passar do tempo máximo",
                    variable=T.var_config_alerta).grid(row=2, column=0, columnspan=3,
                                                       sticky="w", pady=6)
    criar_rotulo(conteudo, "Colunas opcionais da tabela:")\
        .grid(row=3, column=0, sticky="w", pady=(10, 0))
    ttk.Checkbutton(conteudo, text="Mostrar a coluna Motivo",
                    variable=T.var_config_motivo).grid(row=4, column=0, columnspan=3,
                                                       sticky="w")
    ttk.Checkbutton(conteudo, text="Mostrar a coluna Veículo (placa)",
                    variable=T.var_config_veiculo).grid(row=5, column=0, columnspan=3,
                                                        sticky="w")
    criar_botao(conteudo, "Salvar configurações", salvar_configuracoes_da_tela,
                "verde", 22).grid(row=6, column=0, sticky="w", pady=(14, 0))
    criar_rotulo(conteudo, f"As configurações ficam em {ARQ_CONFIG}, na pasta:\n"
                           f"{PASTA_DADOS}", "card", "suave", (FONTE, 9), justify="left")\
        .grid(row=7, column=0, columnspan=3, sticky="w", pady=(12, 0))


def salvar_configuracoes_da_tela():
    """Valida e aplica as configurações escolhidas."""
    try:
        horas = int(T.var_config_tempo.get())
    except ValueError:
        horas = 0
    if not 1 <= horas <= 72:
        messagebox.showwarning("Tempo máximo inválido",
                               "Informe um número inteiro de horas entre 1 e 72.")
        return

    novas = {"tema": T.var_config_tema.get().lower(), "tempo_max_horas": horas,
             "alerta_ativo": bool(T.var_config_alerta.get()),
             "mostrar_motivo": bool(T.var_config_motivo.get()),
             "mostrar_veiculo": bool(T.var_config_veiculo.get())}
    alteracoes = [f"{chave}: {config[chave]} → {valor}"
                  for chave, valor in novas.items() if config[chave] != valor]
    config.update(novas)
    atualizar_opcoes_situacao()

    if not salvar_configuracoes():
        messagebox.showerror("Erro ao salvar",
                             "Não foi possível gravar o arquivo de configurações. "
                             "As mudanças valem apenas até fechar o programa.")
    else:
        mostrar_status("Configurações salvas.")
    if alteracoes:
        registrar_historico("Configuração", "", "", "; ".join(alteracoes))
    aplicar_tema()
    aplicar_colunas_visiveis()
    atualizar_tabela()
    atualizar_historico()


def atualizar_opcoes_situacao():
    """Troca as opções do filtro de situação quando o alerta é ligado/desligado."""
    opcoes = opcoes_filtro_situacao()
    T.lista_situacao.configure(values=opcoes)
    if T.var_filtro_situacao.get() not in opcoes:
        T.var_filtro_situacao.set("Todos")


def criar_aba_sobre(aba):
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    cartao, conteudo, _ = criar_cartao(corpo, "Sobre o sistema e ajuda")
    cartao.pack(fill="both", expand=True)
    texto = criar_texto(conteudo, altura=20, largura=80)
    texto.pack(fill="both", expand=True)
    escrever_texto(texto, [
        (f"Cadastro de Portaria - Controle de entrada e saída (versão {VERSAO})\n", "titulo"),
        ("Trabalho da UC Teoria da Computação e Compiladores - Faculdade UNA.\n"
         "Sistema local feito apenas com bibliotecas do Python (Tkinter, csv, json...).\n\n",
         "normal"),
        ("Atalhos de teclado\n", "titulo"),
        ("Ctrl+N  nova entrada (abre a janela)   Ctrl+F  pesquisar   Ctrl+L  limpar filtros\n"
         "Ctrl+E  editar selecionado     Ctrl+R  registrar saída\n"
         "Delete  excluir (com a tabela em foco)   Enter  confirmar/editar\n"
         "Na janela de cadastro: Ctrl+S ou Enter salvam; Esc cancela.\n\n",
         "codigo"),
        ("Arquivos criados (na pasta dados/ do programa)\n", "titulo"),
        (f"{ARQ_REGISTROS}: registros principais (ID, nome, tipo, entrada, saída e dados extras).\n"
         f"{ARQ_BACKUP}: cópia do arquivo anterior, atualizada a cada salvamento.\n"
         "registros_original_*.csv: cópia do arquivo original guardada antes de migração ou correção.\n"
         f"{ARQ_HISTORICO}: histórico de atividades (cadastro, edição, saída, exclusão...).\n"
         f"{ARQ_CONFIG}: tema, tempo máximo, alertas, colunas e último ID usado.\n"
         "Arquivos exportados: no local e com o nome que você escolher.\n\n", "normal"),
        ("Observações\n", "titulo"),
        ("• Situação e permanência são calculadas na hora; não são salvas no CSV.\n"
         "• O histórico é um registro local e pode ser editado por quem acessa a pasta.\n"
         "• O backup guarda sempre a versão imediatamente anterior do arquivo.\n"
         "• O controle de vagas de estacionamento não foi implementado.\n", "normal"),
    ])
    criar_botao(conteudo, "Abrir pasta dos arquivos", abrir_pasta_dados, "cinza", 24)\
        .pack(anchor="w", pady=(8, 0))


def abrir_pasta_dados():
    """Abre a pasta dos arquivos no Explorador do Windows."""
    try:
        os.startfile(PASTA_DADOS)                 # só existe no Windows
    except (AttributeError, OSError):
        messagebox.showinfo("Pasta dos arquivos", PASTA_DADOS)
