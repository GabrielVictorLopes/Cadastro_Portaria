"""Funções auxiliares: datas, textos, IDs e busca de registros."""

import os
import unicodedata
from datetime import datetime

from nucleo.constantes import (
    CHAVES_TEXTO, COLUNAS_CSV, FORMATO_DATA, FORMATO_DATA_HORA, PASTA_DADOS, TIPOS)
from nucleo.estado import registros


# ======================================================================
# FUNÇÕES AUXILIARES
# ======================================================================
def caminho(nome_arquivo):
    """Caminho completo de um arquivo de dados do sistema (cria a pasta se faltar)."""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    return os.path.join(PASTA_DADOS, nome_arquivo)


def agora_texto():
    """Data/hora atual no formato dd/mm/aaaa hh:mm."""
    return datetime.now().strftime(FORMATO_DATA_HORA)


def remover_acentos(texto):
    """'João' -> 'joao' (também ignora maiúsculas). Usado em pesquisa e ordenação."""
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acentos = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acentos.casefold()


def converter_data(texto):
    """Texto 'dd/mm/aaaa hh:mm' -> datetime. Retorna None se for inválido."""
    try:
        return datetime.strptime(texto, FORMATO_DATA_HORA)
    except (ValueError, TypeError):
        return None


def converter_data_simples(texto):
    """Texto 'dd/mm/aaaa' -> date. Retorna None se for inválido."""
    try:
        return datetime.strptime(texto, FORMATO_DATA).date()
    except (ValueError, TypeError):
        return None


def formatar_id(numero):
    """Mostra o ID com 3 dígitos: 1 -> '001'."""
    return f"{numero:03d}"


def formatar_duracao(duracao):
    """timedelta -> '01h 35min'."""
    minutos_totais = int(duracao.total_seconds() // 60)
    horas, minutos = divmod(minutos_totais, 60)
    return f"{horas:02d}h {minutos:02d}min"


def formatar_placa(placa):
    """'ABC1234' -> 'ABC-1234'. Placas Mercosul ficam como estão."""
    if len(placa) == 7 and placa[:3].isalpha() and placa[3:].isdigit():
        return placa[:3] + "-" + placa[3:]
    return placa


def limpar_espacos(texto):
    """'João    Silva ' -> 'João Silva'."""
    return " ".join(str(texto).split())


def buscar_registro(numero_id):
    """Procura um registro pelo ID. Retorna None se não existir."""
    for registro in registros:
        if registro["id"] == numero_id:
            return registro
    return None


def registro_vazio():
    """Dicionário com todos os campos em branco."""
    dados = {chave: "" for chave in CHAVES_TEXTO}
    dados["id"] = 0
    return dados


# Tabelas derivadas das constantes (precisam de remover_acentos)
TIPOS_NORMALIZADOS = {remover_acentos(t): t for t in TIPOS}
CHAVES_CABECALHO = {remover_acentos(rotulo): chave for rotulo, chave in COLUNAS_CSV}
CHAVES_CABECALHO.update({"tipo": "tipo", "pessoa a visitar": "visitado",
                         "observacao": "observacoes"})
