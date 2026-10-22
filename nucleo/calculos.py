"""Cálculos de situação, permanência e alerta (nunca são salvos no CSV)."""

from datetime import datetime, timedelta

from nucleo.constantes import (
    FILTRO_SITUACOES, FILTRO_SITUACOES_ALERTA, TEXTO_ALERTA, TEXTO_SITUACAO)
from nucleo.estado import config
from nucleo.utilitarios import converter_data, formatar_duracao


# ======================================================================
# CÁLCULOS (situação, permanência e alerta: nunca são salvos no CSV)
# ======================================================================
def calcular_situacao(registro):
    """Sem saída -> 'No local'.  Com saída -> 'Saiu'."""
    return "No local" if registro["saida"] == "" else "Saiu"


def calcular_duracao(registro, agora_dt=None):
    """
    Saída - entrada. Se a pessoa ainda está dentro, usa o momento atual
    (tempo transcorrido). NÃO altera nem inventa nenhum horário de saída.
    """
    entrada = converter_data(registro["entrada"])
    if entrada is None:
        return None
    if registro["saida"] == "":
        fim = agora_dt or datetime.now()
    else:
        fim = converter_data(registro["saida"])
        if fim is None:
            return None
    return fim - entrada


def calcular_permanencia(registro, agora_dt=None):
    """'01h 35min' (quem saiu) ou 'Em andamento — 01h 42min' (quem está dentro)."""
    duracao = calcular_duracao(registro, agora_dt)
    valida = duracao is not None and duracao >= timedelta(0)
    texto = formatar_duracao(duracao) if valida else "—"
    if registro["saida"] == "":
        return f"Em andamento — {texto}" if valida else "Em andamento"
    return texto


def limite_permanencia():
    """Tempo máximo de permanência configurado (timedelta)."""
    return timedelta(hours=config["tempo_max_horas"])


def excedeu_limite(registro, agora_dt=None):
    """True se a pessoa está dentro há mais tempo que o limite (e o alerta está ativo)."""
    if not config["alerta_ativo"] or registro["saida"] != "":
        return False
    duracao = calcular_duracao(registro, agora_dt)
    return duracao is not None and duracao > limite_permanencia()


def texto_situacao(registro, agora_dt=None):
    """Texto mostrado na coluna Situação (inclui o alerta de tempo excedido)."""
    if excedeu_limite(registro, agora_dt):
        return TEXTO_ALERTA
    return TEXTO_SITUACAO[calcular_situacao(registro)]


def opcoes_filtro_situacao():
    """Opções do filtro de situação conforme o alerta de tempo máximo."""
    return FILTRO_SITUACOES_ALERTA if config["alerta_ativo"] else FILTRO_SITUACOES


def situacao_confere(registro, filtro, agora_dt=None):
    """True se o registro se encaixa na opção escolhida no filtro de situação."""
    if filtro == "Excedido":
        return excedeu_limite(registro, agora_dt)
    if filtro == "No prazo":
        return registro["saida"] == "" and not excedeu_limite(registro, agora_dt)
    return calcular_situacao(registro) == filtro
