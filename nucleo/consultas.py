"""Pesquisa, filtros, ordenação e indicadores dos registros."""

from datetime import date, datetime, timedelta

from nucleo.utilitarios import (
    converter_data, formatar_id, formatar_placa, remover_acentos)
from nucleo.calculos import calcular_duracao, calcular_situacao, situacao_confere


# ======================================================================
# PESQUISA E FILTROS
# ======================================================================
def intervalo_periodo(periodo, hoje=None, data_ini=None, data_fim=None):
    """
    Converte o nome do período em (data inicial, data final).
    Retorna None para 'Todos'. No período personalizado, qualquer ponta pode
    ficar em aberto (None).
    """
    hoje = hoje or date.today()
    if periodo == "Hoje":
        return hoje, hoje
    if periodo == "Ontem":
        ontem = hoje - timedelta(days=1)
        return ontem, ontem
    if periodo == "Últimos 7 dias":
        return hoje - timedelta(days=6), hoje      # hoje e os 6 dias anteriores
    if periodo == "Últimos 30 dias":
        return hoje - timedelta(days=29), hoje
    if periodo == "Período personalizado":
        return data_ini, data_fim
    return None


def registro_no_intervalo(registro, intervalo):
    """True se a data da ENTRADA do registro está dentro do intervalo."""
    if intervalo is None or intervalo == (None, None):
        return True
    data = converter_data(registro["entrada"])
    if data is None:
        return False
    inicio, fim = intervalo
    if inicio is not None and data.date() < inicio:
        return False
    if fim is not None and data.date() > fim:
        return False
    return True


def criterios_padrao():
    """Critérios que mostram todos os registros."""
    return {"texto": "", "tipo": "Todos", "situacao": "Todos", "periodo": "Todos",
            "data_ini": None, "data_fim": None, "motivo": "Todos", "empresa": ""}


def filtrar_registros(lista, criterios, hoje=None):
    """
    Retorna só os registros que atendem a TODOS os critérios ao mesmo tempo.
    A pesquisa procura (sem diferenciar maiúsculas/acentos) em: ID, nome,
    tipo, telefone, empresa, placa, pessoa visitada e motivo.
    """
    texto = remover_acentos(criterios["texto"].strip())
    empresa = remover_acentos(criterios["empresa"].strip())
    intervalo = intervalo_periodo(criterios["periodo"], hoje,
                                  criterios["data_ini"], criterios["data_fim"])

    resultado = []
    for r in lista:
        if texto != "":
            campos = [formatar_id(r["id"]), str(r["id"]),
                      remover_acentos(r["nome"]), remover_acentos(r["tipo"]),
                      remover_acentos(r["telefone"]),
                      "".join(c for c in r["telefone"] if c.isdigit()),
                      remover_acentos(r["empresa"]), remover_acentos(r["placa"]),
                      remover_acentos(formatar_placa(r["placa"])),
                      remover_acentos(r["visitado"]), remover_acentos(r["motivo"])]
            if not any(texto in campo for campo in campos):
                continue
        if criterios["tipo"] != "Todos" and r["tipo"] != criterios["tipo"]:
            continue
        if criterios["situacao"] != "Todos" \
                and not situacao_confere(r, criterios["situacao"]):
            continue
        if criterios["motivo"] != "Todos" and r["motivo"] != criterios["motivo"]:
            continue
        if empresa != "" and empresa not in remover_acentos(r["empresa"]):
            continue
        if not registro_no_intervalo(r, intervalo):
            continue
        resultado.append(r)
    return resultado


# ======================================================================
# ORDENAÇÃO
# ======================================================================
def chave_ordenacao(registro, coluna, agora_dt=None):
    """Valor usado para comparar dois registros na coluna escolhida."""
    if coluna == "ID":
        return registro["id"]
    if coluna == "Nome":
        return remover_acentos(registro["nome"])
    if coluna == "Tipo":
        return remover_acentos(registro["tipo"])
    if coluna == "Entrada":
        # Ordena como datetime (calendário), não como texto
        return converter_data(registro["entrada"]) or datetime.min
    if coluna == "Saida":
        return converter_data(registro["saida"]) or datetime.max
    if coluna == "Permanencia":
        duracao = calcular_duracao(registro, agora_dt)
        return duracao.total_seconds() if duracao is not None else -1
    if coluna == "Situacao":
        return calcular_situacao(registro)
    if coluna == "Motivo":
        return remover_acentos(registro["motivo"])
    return registro["placa"]                      # coluna Veículo


# ======================================================================
# INDICADORES (calculados a partir dos registros, nunca digitados)
# ======================================================================
def calcular_indicadores(lista, hoje=None):
    """
    Indicadores do painel.
    - Sobre TODOS os registros: total, dentro, saíram.
    - Sobre HOJE: entradas e entregadores (pela data de entrada).
    - Sobre quem está NO LOCAL AGORA: visitantes, funcionários, moradores.
    """
    hoje = hoje or date.today()
    ind = {"total": len(lista), "dentro": 0, "saiu": 0, "entradas_hoje": 0,
           "entregadores_hoje": 0, "visitantes": 0, "funcionarios": 0,
           "moradores": 0}
    for r in lista:
        dentro = r["saida"] == ""
        ind["dentro" if dentro else "saiu"] += 1
        entrada = converter_data(r["entrada"])
        if entrada is not None and entrada.date() == hoje:
            ind["entradas_hoje"] += 1
            if r["tipo"] == "Entregador":
                ind["entregadores_hoje"] += 1
        if dentro:
            if r["tipo"] == "Visitante":
                ind["visitantes"] += 1
            elif r["tipo"] == "Funcionário":
                ind["funcionarios"] += 1
            elif r["tipo"] == "Morador":
                ind["moradores"] += 1
    return ind
