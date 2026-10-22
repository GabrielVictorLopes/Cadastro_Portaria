"""Janela do formulário de cadastro e edição, e o fluxo de salvar."""

import tkinter as tk
from tkinter import messagebox

from nucleo.constantes import (
    CARACTERES_INVALIDOS_NOME, CHAVES_TEXTO, FONTE, MASCARA_DATA_HORA, MAX_EMPRESA,
    MAX_MODELO, MAX_NOME, MAX_OBSERVACOES, MOTIVOS, TIPOS)
from nucleo.estado import S, T
from nucleo.utilitarios import agora_texto, buscar_registro, formatar_id, limpar_espacos
from nucleo.validacoes import existe_duplicado, validar_dados
from nucleo.operacoes import operacao_cadastrar, operacao_editar
from interface.mascaras import (
    aplicar_filtro_texto, aplicar_mascara, limpar_placa, limpar_texto_cor,
    limpar_texto_livre, limpar_texto_nome, modelo_telefone)
from interface.base import (
    cor, criar_botao, criar_campo_texto, criar_cartao, criar_lista, criar_quadro,
    criar_rotulo, ir_para_aba, mostrar_status, registrar)
from interface.atualizacao import (
    atualizar_historico, atualizar_tabela, selecionar_registro)


# ======================================================================
# INTERFACE: FORMULÁRIO DE CADASTRO
# ======================================================================
DICAS_FORMULARIO = {
    "nome": "Somente letras (ex.: João da Silva)",
    "tipo": "Escolha uma opção",
    "motivo": "Opcional",
    "entrada": "Somente números: dd/mm/aaaa hh:mm",
    "saida": "Opcional • somente números",
}
CHAVES_EXTRAS = ("telefone", "empresa", "visitado", "observacoes", "placa",
                 "modelo", "cor")


def criar_formulario(pai):
    """
    Formulário (dentro da janela de cadastro): campos principais sempre visíveis;
    os extras ficam em 'Informações adicionais'.
    """
    cartao, conteudo, T.titulo_formulario = criar_cartao(pai, "Nova entrada")
    T.cartao_formulario = cartao
    cartao.pack(fill="both", expand=True, padx=14, pady=14)
    for coluna in range(2):
        conteudo.columnconfigure(coluna, weight=1, uniform="formulario", minsize=290)

    T.vars = {chave: tk.StringVar() for chave in CHAVES_TEXTO}
    T.campos, T.dicas = {}, {}

    # (chave, rótulo, opções da lista ou None, linha, coluna, colunas ocupadas)
    principais = [("nome", "Nome da pessoa", None, 0, 0, 2),
                  ("tipo", "Tipo de acesso", TIPOS, 3, 0, 1),
                  ("motivo", "Motivo da entrada", MOTIVOS, 3, 1, 1),
                  ("entrada", "Data/hora de entrada", None, 6, 0, 1),
                  ("saida", "Data/hora de saída (opcional)", None, 6, 1, 1)]
    for chave, texto, valores, linha, coluna, largura in principais:
        margem = (0, 12) if (coluna == 0 and largura == 1) else (0, 0)
        criar_rotulo(conteudo, texto).grid(row=linha, column=coluna,
                                           columnspan=largura, sticky="w")
        if valores:
            campo = criar_lista(conteudo, T.vars[chave], valores)
            campo.grid(row=linha + 1, column=coluna, columnspan=largura,
                       sticky="ew", padx=margem)
        else:
            campo = criar_campo_texto(conteudo, T.vars[chave])
            campo.grid(row=linha + 1, column=coluna, columnspan=largura,
                       sticky="ew", ipady=6, padx=margem)
        T.campos[chave] = campo
        T.dicas[chave] = criar_rotulo(conteudo, DICAS_FORMULARIO[chave], "card",
                                      "suave", (FONTE, 8))
        T.dicas[chave].grid(row=linha + 2, column=coluna, columnspan=largura,
                            sticky="w", pady=(3, 8))

    # --- Informações adicionais (escondidas até o usuário abrir) ---
    T.frame_extra = criar_quadro(conteudo)
    T.frame_extra.grid(row=9, column=0, columnspan=2, sticky="ew")
    for coluna in range(2):
        T.frame_extra.columnconfigure(coluna, weight=1, uniform="extras")
    extras = [("telefone", "Telefone (opcional)", 0, 0, 1),
              ("empresa", "Empresa (opcional)", 0, 1, 1),
              ("visitado", "Pessoa que deseja encontrar", 2, 0, 1),
              ("placa", "Placa do veículo", 2, 1, 1),
              ("modelo", "Modelo do veículo", 4, 0, 1),
              ("cor", "Cor do veículo", 4, 1, 1),
              ("observacoes", "Observações", 6, 0, 2)]
    for chave, texto, linha, coluna, largura in extras:
        margem = (0, 12) if (coluna == 0 and largura == 1) else (0, 0)
        criar_rotulo(T.frame_extra, texto).grid(row=linha, column=coluna,
                                                columnspan=largura, sticky="w")
        campo = criar_campo_texto(T.frame_extra, T.vars[chave])
        campo.grid(row=linha + 1, column=coluna, columnspan=largura, sticky="ew",
                   ipady=5, padx=margem, pady=(0, 8))
        T.campos[chave] = campo
    T.frame_extra.grid_remove()
    S.extras_abertos = False

    barra = criar_quadro(conteudo)
    barra.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    T.botao_cadastrar = criar_botao(barra, "Cadastrar", salvar_formulario, "verde", 18)
    T.botao_cadastrar.pack(side="left")
    T.botao_limpar = criar_botao(barra, "Limpar", limpar_ou_restaurar, "cinza", 12)
    T.botao_limpar.pack(side="left", padx=8)
    criar_botao(barra, "Cancelar", fechar_formulario, "cinza", 12).pack(side="left")
    T.botao_extras = criar_botao(barra, "Informações adicionais ▸", alternar_extras,
                                 "cinza", 24)
    T.botao_extras.pack(side="right")

    ligar_filtros_de_digitacao()


def criar_janela_formulario():
    """
    Cria (escondida) a janela de cadastro/edição. Ela é aberta pelo botão
    '+ Nova entrada' ou por 'Editar' e fecha sozinha depois de salvar.
    """
    janela = tk.Toplevel(T.janela)
    T.janela_form = janela
    registrar(janela, bg="fundo")
    janela.title("Nova entrada")
    janela.transient(T.janela)              # fica sempre por cima da janela principal
    janela.resizable(False, False)
    janela.protocol("WM_DELETE_WINDOW", fechar_formulario)
    janela.bind("<Escape>", fechar_formulario)
    janela.bind("<Control-s>", salvar_formulario)
    janela.bind("<Control-S>", salvar_formulario)
    criar_formulario(janela)
    janela.withdraw()
    S.formulario_aberto = False


def centralizar_janela(janela):
    """Posiciona uma janela no centro da janela principal."""
    janela.update_idletasks()
    largura, altura = janela.winfo_reqwidth(), janela.winfo_reqheight()
    x = T.janela.winfo_rootx() + (T.janela.winfo_width() - largura) // 2
    y = T.janela.winfo_rooty() + (T.janela.winfo_height() - altura) // 2
    janela.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def abrir_formulario():
    """Mostra a janela de cadastro/edição e bloqueia a principal até fechá-la."""
    atualizar_modo_formulario()
    centralizar_janela(T.janela_form)
    T.janela_form.deiconify()
    T.janela_form.lift()
    try:
        T.janela_form.wait_visibility()
        T.janela_form.grab_set()            # janela "modal": só ela recebe cliques
    except tk.TclError:
        pass
    T.campos["nome"].focus_set()
    S.formulario_aberto = True


def ocultar_formulario():
    """Esconde a janela de cadastro e deixa o formulário pronto para o próximo uso."""
    limpar_formulario()
    alternar_extras(False)
    S.formulario_aberto = False
    try:
        T.janela_form.grab_release()
    except tk.TclError:
        pass
    T.janela_form.withdraw()
    T.janela.focus_set()


def fechar_formulario(evento=None, confirmar=True):
    """Fecha a janela de cadastro (botão Cancelar, X ou Esc), avisando se há dados digitados."""
    if confirmar and formulario_tem_alteracoes() and not messagebox.askyesno(
            "Fechar sem salvar",
            "Há dados digitados que ainda não foram salvos.\n"
            "Deseja descartá-los e fechar?", parent=pai_mensagens()):
        return
    ocultar_formulario()


def pai_mensagens():
    """Janela que deve ficar 'por baixo' das mensagens (a de cadastro, se estiver aberta)."""
    return T.janela_form if S.formulario_aberto else T.janela


def limpar_ou_restaurar():
    """Botão Limpar (novo cadastro) ou Restaurar (edição: volta aos dados salvos)."""
    if S.id_em_edicao is None:
        limpar_formulario()
    else:
        registro = buscar_registro(S.id_em_edicao)
        if registro is not None:
            for chave in CHAVES_TEXTO:
                T.vars[chave].set(registro[chave])
    T.campos["nome"].focus_set()


def alternar_extras(abrir=None):
    """Mostra ou esconde os campos de informações adicionais."""
    S.extras_abertos = (not S.extras_abertos) if abrir is None else abrir
    if S.extras_abertos:
        T.frame_extra.grid()
        T.botao_extras.configure(text="Informações adicionais ▾")
    else:
        T.frame_extra.grid_remove()
        T.botao_extras.configure(text="Informações adicionais ▸")


def mostrar_aviso(rotulo, mensagem, texto_padrao):
    """Aviso vermelho curto sob um campo (volta ao texto normal sozinho)."""
    rotulo.configure(text=mensagem, fg=cor("vermelho"))
    T.janela.after(1800, lambda: rotulo.configure(text=texto_padrao, fg=cor("suave")))


def aviso_nome(texto_digitado):
    """Explica por que o campo Nome apagou o que foi digitado."""
    if CARACTERES_INVALIDOS_NOME.search(texto_digitado):
        mostrar_aviso(T.dicas["nome"], "Use apenas letras!", DICAS_FORMULARIO["nome"])
    elif len(texto_digitado) > MAX_NOME:
        mostrar_aviso(T.dicas["nome"], f"Máximo de {MAX_NOME} caracteres!",
                      DICAS_FORMULARIO["nome"])


def ligar_filtros_de_digitacao():
    """A cada tecla digitada, filtros e máscaras corrigem o texto do campo."""
    v, c = T.vars, T.campos

    def filtro(chave, limpar, aviso=None):
        v[chave].trace_add("write", lambda *a: aplicar_filtro_texto(
            v[chave], c[chave], limpar, aviso))

    filtro("nome", limpar_texto_nome, aviso_nome)
    filtro("visitado", limpar_texto_nome)
    filtro("cor", limpar_texto_cor)
    filtro("placa", limpar_placa)
    filtro("empresa", lambda t: limpar_texto_livre(t, MAX_EMPRESA))
    filtro("modelo", lambda t: limpar_texto_livre(t, MAX_MODELO))
    filtro("observacoes", lambda t: limpar_texto_livre(t, MAX_OBSERVACOES))

    for chave in ("entrada", "saida"):
        v[chave].trace_add("write", lambda *a, k=chave: aplicar_mascara(
            v[k], c[k], MASCARA_DATA_HORA[0], MASCARA_DATA_HORA[1],
            T.dicas[k], DICAS_FORMULARIO[k]))
    v["telefone"].trace_add("write", lambda *a: aplicar_mascara(
        v["telefone"], c["telefone"], modelo_telefone, 11))


# ======================================================================
# FLUXO: CADASTRO E EDIÇÃO (formulário)
# ======================================================================
def dados_do_formulario():
    """Lê os textos digitados no formulário."""
    return {chave: T.vars[chave].get() for chave in CHAVES_TEXTO}


def mostrar_erro_de_validacao(erro):
    """Mostra a mensagem de validação e leva o cursor ao campo que precisa de correção."""
    campo, titulo, mensagem = erro
    if campo in CHAVES_EXTRAS:
        alternar_extras(True)
    if titulo.startswith("Erro semântico"):
        messagebox.showerror(titulo, mensagem, parent=pai_mensagens())
    else:
        messagebox.showwarning(titulo, mensagem, parent=pai_mensagens())
    T.campos[campo].focus_set()


def avisar_falha_ao_salvar(detalhe):
    """Mensagem de erro quando o CSV não pôde ser gravado (a operação foi desfeita)."""
    messagebox.showerror(
        "Erro ao salvar",
        "Não foi possível salvar o arquivo registros.csv.\n"
        f"Detalhe: {detalhe}\n\n"
        "A operação foi DESFEITA e nenhum dado foi alterado.\n"
        "Se o arquivo estiver aberto em outro programa (como o Excel), "
        "feche-o e tente novamente.", parent=pai_mensagens())


def depois_de_alterar_dados():
    """Atualiza as telas que dependem dos registros e do histórico."""
    atualizar_tabela()
    atualizar_historico()


def salvar_formulario(evento=None):
    """Botão principal: cadastra (modo normal) ou salva alterações (edição)."""
    if S.id_em_edicao is None:
        cadastrar()
    else:
        salvar_edicao()


def validar_formulario(ignorar_id=None):
    """Valida o formulário e pergunta sobre duplicidade. Retorna os dados ou None."""
    dados, erro = validar_dados(dados_do_formulario())
    if erro is not None:
        mostrar_erro_de_validacao(erro)
        return None
    if existe_duplicado(dados, ignorar_id) and not messagebox.askyesno(
            "Possível duplicidade",
            "Já existe um registro com o mesmo nome, tipo e data/hora de entrada.\n\n"
            "Deseja continuar mesmo assim?", parent=pai_mensagens()):
        return None
    return dados


def cadastrar():
    """Cria um novo registro com ID automático e fecha a janela de cadastro."""
    dados = validar_formulario()
    if dados is None:
        return
    ok, resultado = operacao_cadastrar(dados)
    if not ok:
        avisar_falha_ao_salvar(resultado)
        return
    depois_de_alterar_dados()
    selecionar_registro(resultado["id"])
    messagebox.showinfo("Cadastro", "Registro cadastrado com sucesso!",
                        parent=pai_mensagens())
    mostrar_status(f"Entrada de {resultado['nome']} registrada "
                   f"(ID {formatar_id(resultado['id'])}).")
    ocultar_formulario()


def nova_entrada(evento=None):
    """Botão '+ Nova entrada': abre a janela de cadastro com o formulário limpo."""
    ir_para_aba("portaria")
    T.tabela.selection_set(())
    limpar_formulario()
    abrir_formulario()


def limpar_formulario(evento=None):
    """Entrada = agora, saída vazia e modo de cadastro."""
    S.id_em_edicao = None
    for chave in CHAVES_TEXTO:
        T.vars[chave].set("")
    T.vars["tipo"].set(TIPOS[0])
    T.vars["entrada"].set(agora_texto())
    atualizar_modo_formulario()


def atualizar_modo_formulario():
    """Ajusta títulos, textos e cores conforme esteja cadastrando ou editando."""
    if S.id_em_edicao is None:
        titulo = "Nova entrada"
        T.titulo_formulario.configure(text=titulo, fg=cor("titulo"))
        T.cartao_formulario.configure(highlightbackground=cor("borda"),
                                      highlightthickness=1)
        T.botao_cadastrar.configure(text="Cadastrar")
        T.botao_limpar.configure(text="Limpar")
    else:
        titulo = f"Editando registro #{formatar_id(S.id_em_edicao)}"
        T.titulo_formulario.configure(text=titulo, fg=cor("amarelo_h"))
        T.cartao_formulario.configure(highlightbackground=cor("amarelo"),
                                      highlightthickness=2)
        T.botao_cadastrar.configure(text="Salvar alterações")
        T.botao_limpar.configure(text="Restaurar")
    T.janela_form.title(titulo)


def editar(evento=None):
    """Carrega no formulário o registro selecionado na tabela."""
    ir_para_aba("portaria")
    selecionados = T.tabela.selection()
    if len(selecionados) == 0:
        messagebox.showwarning("Atenção", "Selecione um registro para editar.")
        return
    if len(selecionados) > 1:
        messagebox.showwarning("Atenção", "Selecione apenas um registro para editar.")
        return
    registro = buscar_registro(int(selecionados[0]))
    if registro is None:
        return
    for chave in CHAVES_TEXTO:
        T.vars[chave].set(registro[chave])
    S.id_em_edicao = registro["id"]
    if any(registro[chave] for chave in CHAVES_EXTRAS):
        alternar_extras(True)               # mostra as informações adicionais
    abrir_formulario()


def duplo_clique(evento):
    """Duplo clique em uma linha da tabela abre o registro para edição."""
    if T.tabela.identify_region(evento.x, evento.y) == "cell":
        editar()


def salvar_edicao():
    """Atualiza o registro existente (mantém o mesmo ID) e fecha a janela."""
    dados = validar_formulario(ignorar_id=S.id_em_edicao)
    if dados is None:
        return
    numero_id = S.id_em_edicao
    ok, resultado = operacao_editar(numero_id, dados)
    if not ok:
        if isinstance(resultado, str) and "não existe" in resultado:
            messagebox.showerror("Erro", resultado, parent=pai_mensagens())
            ocultar_formulario()
        else:
            avisar_falha_ao_salvar(resultado)
        return
    depois_de_alterar_dados()
    selecionar_registro(numero_id)
    mostrar_status(f"Registro #{formatar_id(numero_id)} atualizado com sucesso.")
    ocultar_formulario()


def formulario_tem_alteracoes():
    """True se há uma edição não salva ou um cadastro começado e não concluído."""
    if S.id_em_edicao is not None:
        registro = buscar_registro(S.id_em_edicao)
        if registro is None:
            return False
        return any(limpar_espacos(T.vars[k].get()) != limpar_espacos(registro[k])
                   for k in CHAVES_TEXTO)
    return any(T.vars[k].get().strip() for k in
               ("nome", "motivo", "saida", "telefone", "empresa", "visitado",
                "observacoes", "placa", "modelo", "cor"))
