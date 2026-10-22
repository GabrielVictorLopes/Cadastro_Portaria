"""Máscaras e filtros de digitação (impedem o erro antes de ele acontecer)."""

import re
import tkinter as tk

from nucleo.constantes import CARACTERES_INVALIDOS_NOME, MAX_COR, MAX_NOME
from nucleo.utilitarios import converter_data, converter_data_simples
from interface.base import cor


# ======================================================================
# MÁSCARAS E FILTROS DE DIGITAÇÃO (impedem o erro ANTES de ele acontecer)
# ======================================================================
def limpar_texto_nome(texto):
    """
    Deixa só o permitido em um nome: letras (com acentos), espaço, hífen e
    apóstrofo. Remove números e símbolos, junta espaços repetidos e limita o tamanho.
    """
    texto = CARACTERES_INVALIDOS_NOME.sub("", texto)
    texto = re.sub(r" {2,}", " ", texto).lstrip()
    return texto[:MAX_NOME]


def limpar_texto_cor(texto):
    """Cor do veículo: só letras."""
    return limpar_texto_nome(texto)[:MAX_COR]


def limpar_texto_livre(texto, maximo):
    """Texto livre: sem quebras de linha, sem espaços repetidos, com limite."""
    texto = re.sub(r"[\r\n\t]", " ", texto)
    texto = re.sub(r" {2,}", " ", texto).lstrip()
    return texto[:maximo]


def limpar_placa(texto):
    """Placa: só letras e números, em maiúsculas, no máximo 7 caracteres."""
    return re.sub(r"[^A-Za-z0-9]", "", texto).upper()[:7]


def modelo_telefone(digitos):
    """Telefone fixo (10 dígitos) ou celular (11 dígitos)."""
    return "(##) ####-####" if len(digitos) <= 10 else "(##) #####-####"


def formatar_mascara(texto, modelo, maximo, cursor=None):
    """
    Mantém só os números (até 'maximo') e coloca os separadores do modelo:
    ('061020260930', '##/##/#### ##:##') -> '06/10/2026 09:30'
    Se o campo já estava cheio e um número foi digitado no meio, o número novo
    SUBSTITUI o seguinte (em vez de empurrar o resto).
    """
    digitos = "".join(c for c in texto if c.isdigit())
    if len(digitos) > maximo:
        if cursor is not None:
            antes = sum(1 for c in texto[:cursor] if c.isdigit())
            excesso = len(digitos) - maximo
            digitos = digitos[:antes] + digitos[antes + excesso:]
        digitos = digitos[:maximo]

    padrao = modelo(digitos) if callable(modelo) else modelo
    resultado, usados = "", 0
    for simbolo in padrao:
        if usados >= len(digitos):
            break
        if simbolo == "#":
            resultado += digitos[usados]
            usados += 1
        else:
            resultado += simbolo
    return resultado


def posicao_do_cursor(texto, quantidade_digitos):
    """Posição do cursor logo depois do N-ésimo dígito do texto."""
    if quantidade_digitos == 0:
        return 0
    contados = 0
    for posicao, caractere in enumerate(texto):
        if caractere.isdigit():
            contados += 1
            if contados == quantidade_digitos:
                return posicao + 1
    return len(texto)


def aplicar_filtro_texto(variavel, campo, limpar, aviso=None):
    """Roda a cada tecla: apaga do campo o que não for permitido."""
    texto = variavel.get()
    novo = limpar(texto)
    if novo == texto:
        return
    cursor = campo.index(tk.INSERT)
    variavel.set(novo)
    campo.icursor(len(limpar(texto[:cursor])))
    if aviso is not None:
        aviso(texto)


def aplicar_mascara(variavel, campo, modelo, maximo, rotulo_dica=None,
                    dica_padrao="", com_hora=True):
    """Roda a cada tecla: aceita só números e formata o texto sozinho."""
    texto = variavel.get()
    cursor = campo.index(tk.INSERT)
    novo = formatar_mascara(texto, modelo, maximo, cursor)
    if novo != texto:
        digitos_antes = sum(1 for c in texto[:cursor] if c.isdigit())
        variavel.set(novo)
        # Dentro deste trace o campo ainda mostra o texto antigo (mais curto, sem os
        # separadores) e o Tk limitaria o cursor a esse tamanho, deixando-o uma casa
        # atrás. Por isso o texto novo é colocado no campo ANTES de mover o cursor.
        if campo.get() != novo:
            campo.delete(0, tk.END)
            campo.insert(0, novo)
        campo.icursor(posicao_do_cursor(novo, digitos_antes))
    if rotulo_dica is not None:
        atualizar_dica_data(rotulo_dica, novo, dica_padrao, com_hora)


def atualizar_dica_data(rotulo, texto, dica_padrao, com_hora=True):
    """Texto de ajuda que acompanha a digitação da data."""
    tamanho, maximo = (16, 12) if com_hora else (10, 8)
    if texto == "":
        rotulo.configure(text=dica_padrao, fg=cor("suave"))
    elif len(texto) < tamanho:
        faltam = maximo - sum(c.isdigit() for c in texto)
        rotulo.configure(text=f"Faltam {faltam} dígito(s)", fg=cor("suave"))
    else:
        valida = (converter_data(texto) if com_hora
                  else converter_data_simples(texto)) is not None
        if valida:
            rotulo.configure(text="Data válida" if not com_hora else "Data/hora válida",
                             fg=cor("verde"))
        else:
            rotulo.configure(text="Data inexistente" if not com_hora
                             else "Data/hora inexistente", fg=cor("vermelho"))
