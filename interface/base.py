"""Auxiliares da interface: cores do tema, criação de widgets, barra de status e abas."""

import tkinter as tk
from tkinter import ttk

from nucleo.constantes import ESTILOS_BOTAO, FONTE, PALETAS
from nucleo.estado import S, T


# ======================================================================
# INTERFACE: AUXILIARES E TEMA CLARO/ESCURO
# Todo widget colorido é "registrado" com os nomes das cores que usa.
# Ao trocar de tema, o sistema reaplica as cores de todos os registrados.
# ======================================================================
def cor(chave):
    """Cor da paleta do tema atual."""
    return PALETAS[S.tema][chave]


def aplicar_opcoes(widget, opcoes):
    """Aplica em um widget as cores do tema atual."""
    try:
        widget.configure(**{opcao: cor(chave) for opcao, chave in opcoes.items()})
    except tk.TclError:
        pass                # o widget pode ter sido destruído


def registrar(widget, **opcoes):
    """Registra um widget para ser recolorido quando o tema mudar."""
    T.tematizaveis.append((widget, opcoes))
    aplicar_opcoes(widget, opcoes)
    return widget


def criar_quadro(pai, fundo="card", **extra):
    return registrar(tk.Frame(pai, **extra), bg=fundo)


def criar_rotulo(pai, texto="", fundo="card", cor_texto="texto",
                 fonte=(FONTE, 10), **extra):
    rotulo = tk.Label(pai, text=texto, font=fonte, **extra)
    return registrar(rotulo, bg=fundo, fg=cor_texto)


def criar_botao(pai, texto, comando, estilo="azul", largura=16):
    """Botão colorido, sem borda, que escurece quando o mouse passa por cima."""
    fundo, hover, cor_texto = ESTILOS_BOTAO[estilo]
    botao = tk.Button(pai, text=texto, command=comando, width=largura,
                      font=(FONTE, 10, "bold"), relief="flat", bd=0,
                      cursor="hand2", pady=7)
    registrar(botao, bg=fundo, fg=cor_texto, activebackground=hover,
              activeforeground=cor_texto)
    botao.bind("<Enter>", lambda e: botao.configure(bg=cor(hover)))
    botao.bind("<Leave>", lambda e: botao.configure(bg=cor(fundo)))
    return botao


def criar_campo_texto(pai, variavel):
    """Campo de texto limpo, com contorno que fica azul quando recebe o foco."""
    campo = tk.Entry(pai, textvariable=variavel, font=(FONTE, 11), relief="flat",
                     bd=0, highlightthickness=2)
    return registrar(campo, bg="campo", fg="texto", insertbackground="texto",
                     highlightbackground="borda", highlightcolor="azul")


def criar_lista(pai, variavel, valores, largura=None):
    """Lista de opções (somente leitura): o usuário só escolhe, não digita."""
    return ttk.Combobox(pai, textvariable=variavel, values=valores,
                        state="readonly", font=(FONTE, 10), width=largura)


def criar_cartao(pai, titulo):
    """
    Cria uma 'área' com borda e título (com uma barrinha azul).
    Retorna (cartão, conteúdo, rótulo do título).
    """
    cartao = tk.Frame(pai, highlightthickness=1)
    registrar(cartao, bg="card", highlightbackground="borda")
    topo = criar_quadro(cartao)
    topo.pack(fill="x", padx=12, pady=(8, 0))
    criar_quadro(topo, "azul", width=4, height=14).pack(side="left", padx=(0, 8))
    rotulo = criar_rotulo(topo, titulo, "card", "titulo", (FONTE, 10, "bold"))
    rotulo.pack(side="left")
    conteudo = criar_quadro(cartao)
    conteudo.pack(fill="both", expand=True, padx=12, pady=(4, 10))
    return cartao, conteudo, rotulo


def criar_tabela_simples(pai, colunas, altura=6):
    """
    Tabela de leitura com barra de rolagem.
    colunas = [(identificador, título, largura, alinhamento)].
    Retorna (quadro, tabela).
    """
    quadro = criar_quadro(pai)
    arvore = ttk.Treeview(quadro, columns=[c[0] for c in colunas],
                          show="headings", height=altura)
    for ident, titulo, largura, ancora in colunas:
        arvore.heading(ident, text=titulo)
        arvore.column(ident, width=largura, minwidth=40, anchor=ancora, stretch=True)
    barra = ttk.Scrollbar(quadro, orient="vertical", command=arvore.yview)
    arvore.configure(yscrollcommand=barra.set)
    arvore.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return quadro, arvore


def criar_texto(pai, altura=8, largura=30):
    """Caixa de texto somente leitura (para explicações e detalhes)."""
    texto = tk.Text(pai, height=altura, width=largura, wrap="word", relief="flat",
                    bd=0, highlightthickness=0, cursor="arrow", padx=6, pady=4,
                    font=(FONTE, 10), state="disabled")
    registrar(texto, bg="card", fg="texto", selectbackground="selecao",
              selectforeground="texto")
    T.textos.append(texto)
    configurar_tags_texto(texto)
    return texto


def escrever_texto(texto, partes):
    """Substitui o conteúdo de uma caixa de texto. partes = [(texto, estilo)]."""
    texto.configure(state="normal")
    texto.delete("1.0", tk.END)
    for conteudo, estilo in partes:
        texto.insert(tk.END, conteudo, estilo)
    texto.configure(state="disabled")


def configurar_estilo():
    """Define o visual dos componentes ttk (tabelas, listas, abas...)."""
    estilo = ttk.Style()
    estilo.theme_use("clam")        # tema que aceita cores personalizadas

    estilo.configure("Treeview", font=(FONTE, 10), rowheight=28,
                     background=cor("card"), fieldbackground=cor("card"),
                     foreground=cor("texto"), borderwidth=0)
    estilo.configure("Treeview.Heading", font=(FONTE, 10, "bold"),
                     background=cor("cabecalho"), foreground=cor("branco"),
                     relief="flat", padding=(8, 7))
    estilo.map("Treeview.Heading", background=[("active", cor("cabecalho_escuro"))])
    # Linha selecionada: fundo azul claro e texto legível
    estilo.map("Treeview", background=[("selected", cor("selecao"))],
               foreground=[("selected", cor("texto"))])

    estilo.configure("TNotebook", background=cor("fundo"), borderwidth=0,
                     tabmargins=(0, 0, 0, 0))
    estilo.configure("TNotebook.Tab", background=cor("aba"),
                     foreground=cor("suave"), padding=(14, 8),
                     font=(FONTE, 10, "bold"), borderwidth=0)
    estilo.map("TNotebook.Tab",
               background=[("selected", cor("card"))],
               foreground=[("selected", cor("titulo"))])

    estilo.configure("TCombobox", padding=5, fieldbackground=cor("campo"),
                     background=cor("cinza"), foreground=cor("texto"),
                     arrowcolor=cor("texto"), bordercolor=cor("borda"),
                     lightcolor=cor("campo"), darkcolor=cor("campo"))
    estilo.map("TCombobox",
               fieldbackground=[("readonly", cor("campo"))],
               foreground=[("readonly", cor("texto"))],
               selectbackground=[("readonly", cor("campo"))],
               selectforeground=[("readonly", cor("texto"))])
    T.janela.option_add("*TCombobox*Listbox.background", cor("campo"))
    T.janela.option_add("*TCombobox*Listbox.foreground", cor("texto"))
    T.janela.option_add("*TCombobox*Listbox.selectBackground", cor("selecao"))
    T.janela.option_add("*TCombobox*Listbox.selectForeground", cor("texto"))

    estilo.configure("TSpinbox", fieldbackground=cor("campo"),
                     foreground=cor("texto"), background=cor("cinza"),
                     arrowcolor=cor("texto"), bordercolor=cor("borda"))
    estilo.configure("TCheckbutton", background=cor("card"),
                     foreground=cor("texto"), font=(FONTE, 10))
    estilo.map("TCheckbutton", background=[("active", cor("card"))])
    estilo.configure("TScrollbar", background=cor("borda"),
                     troughcolor=cor("fundo"), bordercolor=cor("fundo"),
                     arrowcolor=cor("texto"), relief="flat")
    estilo.map("TScrollbar", background=[("active", cor("suave"))])


def configurar_tags_texto(texto):
    """Estilos de texto usados nas caixas de texto."""
    texto.tag_configure("chave", foreground=cor("suave"), font=(FONTE, 9))
    texto.tag_configure("valor", foreground=cor("texto"), font=(FONTE, 10, "bold"))
    texto.tag_configure("normal", foreground=cor("texto"), font=(FONTE, 10))
    texto.tag_configure("suave", foreground=cor("suave"), font=(FONTE, 9))
    texto.tag_configure("titulo", foreground=cor("titulo"), font=(FONTE, 11, "bold"))
    texto.tag_configure("alerta", foreground=cor("alerta_fg"), font=(FONTE, 10, "bold"))
    texto.tag_configure("ok", foreground=cor("verde"), font=(FONTE, 10, "bold"))
    texto.tag_configure("erro", foreground=cor("vermelho"), font=(FONTE, 10, "bold"))
    texto.tag_configure("codigo", foreground=cor("texto"), font=("Consolas", 10))


def configurar_tags_tabela():
    """Cores das linhas da tabela principal conforme a situação."""
    T.tabela.tag_configure("saiu", background=cor("saiu_bg"),
                           foreground=cor("saiu_fg"))
    T.tabela.tag_configure("dentro", background=cor("dentro_bg"),
                           foreground=cor("dentro_fg"), font=(FONTE, 10, "bold"))
    T.tabela.tag_configure("alerta", background=cor("alerta_bg"),
                           foreground=cor("alerta_fg"), font=(FONTE, 10, "bold"))


def mostrar_status(mensagem, tipo="ok"):
    """Mensagem discreta na barra de status (some sozinha depois de alguns segundos)."""
    cores = {"ok": "verde", "erro": "vermelho", "info": "suave"}
    T.rotulo_status.configure(text=mensagem, fg=cor(cores.get(tipo, "suave")))
    if S.id_status is not None:
        try:
            T.janela.after_cancel(S.id_status)
        except (ValueError, tk.TclError):
            pass
    S.id_status = T.janela.after(7000, lambda: T.rotulo_status.configure(
        text="Pronto.", fg=cor("suave")))


def preencher_tabela(tabela, linhas):
    """Substitui todas as linhas de uma tabela simples."""
    for item in tabela.get_children():
        tabela.delete(item)
    for linha in linhas:
        tabela.insert("", tk.END, values=linha)


def aba_atual():
    """Chave da aba selecionada (ex.: 'portaria')."""
    selecionada = str(T.abas.select())
    for chave, quadro in T.quadros_abas.items():
        if str(quadro) == selecionada:
            return chave
    return "portaria"


def ir_para_aba(chave):
    if aba_atual() != chave:
        T.abas.select(T.quadros_abas[chave])
