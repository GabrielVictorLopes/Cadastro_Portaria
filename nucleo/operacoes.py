"""Cadastro, edição, saída e exclusão de registros (lógica, sem interface)."""

import copy

from nucleo.constantes import CHAVES_TEXTO, ROTULOS
from nucleo.estado import S, config, registros
from nucleo.utilitarios import buscar_registro
from nucleo.calculos import calcular_permanencia
from nucleo.persistencia import (
    gravar_registros, registrar_historico, salvar_configuracoes)
from nucleo.validacoes import validar_datas


# ======================================================================
# CADASTRO, EDIÇÃO, SAÍDA E EXCLUSÃO (lógica, sem interface)
# Todas retornam (ok, resultado). Se o salvamento falhar, a alteração é
# DESFEITA na memória, para o programa nunca mostrar dados que não foram salvos.
# ======================================================================
def aplicar_e_salvar(alteracao):
    """Executa alteracao() e salva. Se não conseguir salvar, desfaz tudo."""
    copia = copy.deepcopy(registros)
    id_antes = S.proximo_id
    alteracao()
    ok, erro = gravar_registros()
    if not ok:
        registros[:] = copia
        S.proximo_id = id_antes
        return False, erro
    return True, ""


def operacao_cadastrar(dados):
    """Cria um novo registro com ID único e crescente (nunca reutiliza IDs)."""
    novo = {"id": S.proximo_id}
    novo.update(dados)

    def alterar():
        registros.append(novo)
        S.proximo_id += 1

    ok, erro = aplicar_e_salvar(alterar)
    if not ok:
        return False, erro
    config["proximo_id"] = S.proximo_id          # lembra o contador entre execuções
    salvar_configuracoes()
    registrar_historico("Cadastro", novo["id"], novo["nome"],
                        f"Entrada registrada ({novo['tipo']}) em {novo['entrada']}")
    return True, novo


def operacao_editar(numero_id, dados):
    """Atualiza um registro existente (o ID não muda)."""
    registro = buscar_registro(numero_id)
    if registro is None:
        return False, "Este registro não existe mais."
    alterados = [ROTULOS[k] for k in CHAVES_TEXTO if registro[k] != dados[k]]

    def alterar():
        registro.update(dados)

    ok, erro = aplicar_e_salvar(alterar)
    if not ok:
        return False, erro
    descricao = ("Campos alterados: " + ", ".join(alterados)) if alterados \
        else "Nenhum campo foi alterado"
    registrar_historico("Edição", numero_id, dados["nome"], descricao)
    return True, registro


def operacao_registrar_saida(numero_id, texto_saida):
    """
    Coloca a data/hora da saída em um registro que ainda está dentro.
    Retorna (False, "JA_TEM_SAIDA") se a saída já existir.
    """
    registro = buscar_registro(numero_id)
    if registro is None:
        return False, "Este registro não existe mais."
    if registro["saida"] != "":
        return False, "JA_TEM_SAIDA"

    ok, _campo, _titulo, mensagem = validar_datas(registro["entrada"], texto_saida)
    if not ok:
        return False, mensagem

    def alterar():
        registro["saida"] = texto_saida

    ok, erro = aplicar_e_salvar(alterar)
    if not ok:
        return False, erro
    registrar_historico("Saída", numero_id, registro["nome"],
                        f"Saída registrada em {texto_saida} "
                        f"(permanência {calcular_permanencia(registro)})")
    return True, registro


def operacao_excluir(ids):
    """Exclui um ou mais registros pelo ID."""
    ids = set(ids)
    removidos = [copy.copy(r) for r in registros if r["id"] in ids]

    def alterar():
        registros[:] = [r for r in registros if r["id"] not in ids]

    ok, erro = aplicar_e_salvar(alterar)
    if not ok:
        return False, erro
    for r in removidos:     # o histórico NÃO é apagado junto com o registro
        registrar_historico("Exclusão", r["id"], r["nome"],
                            f"Registro excluído ({r['tipo']}, entrada {r['entrada']})")
    return True, removidos
