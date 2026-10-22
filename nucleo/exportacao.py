"""Preparação e gravação das exportações em CSV."""

import csv
import os

from nucleo.constantes import (
    ARQ_BACKUP, ARQ_CONFIG, ARQ_HISTORICO, ARQ_REGISTROS, CABECALHO_HISTORICO,
    PASTA_DADOS)
from nucleo.utilitarios import formatar_placa
from nucleo.calculos import calcular_permanencia, calcular_situacao


# ======================================================================
# EXPORTAÇÃO
# ======================================================================
def proteger_excel(valor):
    """Evita que o Excel interprete um texto como fórmula (=, +, -, @)."""
    texto = str(valor)
    if texto[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + texto
    return texto


def eh_arquivo_do_sistema(destino):
    """
    True se o destino é um arquivo de dados do sistema (registros, backup,
    histórico, configurações ou cópia original). No Windows a comparação
    ignora maiúsculas/minúsculas ('REGISTROS.CSV' é o mesmo arquivo).
    """
    pasta, nome = os.path.split(os.path.normcase(os.path.abspath(destino)))
    if pasta != os.path.normcase(os.path.abspath(PASTA_DADOS)):
        return False
    protegidos = {os.path.normcase(n) for n in
                  (ARQ_REGISTROS, ARQ_BACKUP, ARQ_HISTORICO, ARQ_CONFIG)}
    return nome in protegidos or nome.startswith(os.path.normcase("registros_original_"))


def exportar_csv(arquivo, cabecalho, linhas):
    """
    Grava um CSV compatível com Excel (separador ';' e acentos preservados).
    Nunca mexe no arquivo principal. Retorna (ok, mensagem_de_erro).
    """
    try:
        with open(arquivo, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.writer(f, delimiter=";")
            escritor.writerow(cabecalho)
            for linha in linhas:
                escritor.writerow([proteger_excel(c) for c in linha])
        return True, ""
    except OSError as erro:
        return False, str(erro)


def linhas_exportacao_registros(lista, agora_dt=None):
    """Cabeçalho e linhas para exportar registros (inclui situação e permanência)."""
    cabecalho = ["ID", "Nome", "Tipo de acesso", "Entrada", "Saída", "Permanência",
                 "Situação", "Motivo", "Telefone", "Empresa", "Pessoa visitada",
                 "Placa", "Modelo", "Cor", "Observações"]
    linhas = [[r["id"], r["nome"], r["tipo"], r["entrada"], r["saida"],
               calcular_permanencia(r, agora_dt), calcular_situacao(r),
               r["motivo"], r["telefone"], r["empresa"], r["visitado"],
               formatar_placa(r["placa"]), r["modelo"], r["cor"],
               r["observacoes"]] for r in lista]
    return cabecalho, linhas


def linhas_exportacao_historico(eventos):
    """Histórico de atividades."""
    linhas = [[e["data"], e["acao"], e["id"], e["nome"], e["descricao"]]
              for e in eventos]
    return list(CABECALHO_HISTORICO), linhas
