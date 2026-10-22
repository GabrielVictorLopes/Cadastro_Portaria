"""Validações dos dados digitados (formato e regras semânticas)."""

from datetime import datetime

from nucleo.constantes import (
    ANO_MINIMO, CHAVES_TEXTO, FORMATO_DATA_HORA, MAX_COR, MAX_EMPRESA, MAX_MODELO,
    MAX_NOME, MAX_OBSERVACOES, MOTIVOS, PADRAO_NOME, PADRAO_PLACA, ROTULOS, TIPOS)
from nucleo.estado import registros
from nucleo.utilitarios import converter_data, limpar_espacos


# ======================================================================
# VALIDAÇÕES
# ======================================================================
def validar_nome(nome, rotulo="O nome"):
    """Retorna (True, "") se o nome for válido, ou (False, mensagem)."""
    if nome == "":
        return False, f"{rotulo} não pode ficar vazio."
    if len(nome) < 2:
        return False, f"{rotulo} é muito curto. Digite o nome completo."
    if len(nome) > MAX_NOME:
        return False, f"{rotulo} deve ter no máximo {MAX_NOME} caracteres."
    if not PADRAO_NOME.match(nome):
        return False, (f"{rotulo} não pode conter números ou símbolos.\n"
                       "Exemplos válidos: João Silva, Ana Vitória.")
    return True, ""


def validar_datas(texto_entrada, texto_saida, agora_dt=None):
    """
    Valida a entrada e a saída. Retorna (ok, campo, título, mensagem).
    A entrada é obrigatória; a saída é opcional (vazia = pessoa ainda dentro).
    """
    # --- Verificação de FORMATO (estrutura do texto digitado) ---
    if texto_entrada == "":
        return False, "entrada", "Campo obrigatório", \
            "Informe a data e hora da entrada."

    data_entrada = converter_data(texto_entrada)
    if data_entrada is None:
        return False, "entrada", "Formato inválido", (
            "Entrada em formato inválido.\n"
            "Use dd/mm/aaaa hh:mm  (exemplo: 06/10/2026 09:30)")

    data_saida = None
    if texto_saida != "":
        data_saida = converter_data(texto_saida)
        if data_saida is None:
            return False, "saida", "Formato inválido", (
                "Saída em formato inválido.\n"
                "Use dd/mm/aaaa hh:mm  (exemplo: 06/10/2026 11:20)")

    # ==================================================================
    # ANÁLISE SEMÂNTICA: o formato está correto, mas o SIGNIFICADO das
    # datas também precisa fazer sentido para uma portaria.
    # As comparações abaixo são feitas entre objetos datetime.
    # ==================================================================
    momento_atual = agora_dt or datetime.now()

    # Regra 1: a entrada não pode estar no futuro.
    if data_entrada > momento_atual:
        return False, "entrada", "Erro semântico", (
            "Erro semântico:\nA entrada não pode ser uma data/hora futura.")

    # Regra 2: a data precisa ser plausível (ex.: ano 0001 não faz sentido).
    if data_entrada.year < ANO_MINIMO:
        return False, "entrada", "Erro semântico", (
            f"Erro semântico:\nA entrada não pode ser anterior ao ano {ANO_MINIMO}.")

    if data_saida is not None:
        # Regra 3: a saída (se preenchida) não pode estar no futuro.
        if data_saida > momento_atual:
            return False, "saida", "Erro semântico", (
                "Erro semântico:\nA saída não pode ser uma data/hora futura.")

        # Regra 4: a saída não pode ser anterior à entrada.
        # Observação: entrada IGUAL à saída é permitida (permanência de
        # duração zero, por exemplo alguém que só entregou algo e saiu).
        if data_saida < data_entrada:
            return False, "saida", "Erro semântico", (
                "Erro semântico:\nA saída não pode ser anterior à entrada.")

    return True, "", "", ""


def validar_telefone(texto):
    """Retorna (True, telefone formatado) ou (False, mensagem). Vazio é aceito."""
    digitos = "".join(c for c in texto if c.isdigit())
    if digitos == "":
        return True, ""
    if len(digitos) not in (10, 11):
        return False, "O telefone deve ter 10 ou 11 dígitos, com DDD."
    if "0" in digitos[:2]:                       # não existe DDD 0X nem X0
        return False, "O DDD do telefone é inválido."
    if len(digitos) == 11 and digitos[2] != "9":
        return False, "Telefone com 11 dígitos deve começar com 9 depois do DDD."
    return True, formatar_telefone(digitos)


def formatar_telefone(digitos):
    """'31987654321' -> '(31) 98765-4321'."""
    if len(digitos) <= 2:
        return digitos
    if len(digitos) <= 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}".rstrip("-")
    return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"


def validar_dados(dados, agora_dt=None):
    """
    Valida e normaliza os dados do formulário.
    Retorna (dados_normalizados, None) se estiver tudo certo, ou
    (None, (campo, título, mensagem)) indicando QUAL campo precisa ser corrigido.
    """
    d = {chave: limpar_espacos(dados.get(chave, "")) for chave in CHAVES_TEXTO}

    # Nome obrigatório e válido
    ok, mensagem = validar_nome(d["nome"])
    if not ok:
        return None, ("nome", "Nome inválido", mensagem)

    # Semântica: o tipo precisa pertencer às categorias permitidas
    if d["tipo"] not in TIPOS:
        return None, ("tipo", "Tipo inválido",
                      "Selecione um tipo de acesso válido: " + ", ".join(TIPOS) + ".")

    # Motivo é opcional, mas se vier preenchido precisa ser uma das opções
    if d["motivo"] != "" and d["motivo"] not in MOTIVOS:
        return None, ("motivo", "Motivo inválido",
                      "Selecione um motivo da lista ou deixe em branco.")

    # Datas: formato + regras semânticas
    ok, campo, titulo, mensagem = validar_datas(d["entrada"], d["saida"], agora_dt)
    if not ok:
        return None, (campo, titulo, mensagem)
    d["entrada"] = converter_data(d["entrada"]).strftime(FORMATO_DATA_HORA)
    if d["saida"] != "":
        d["saida"] = converter_data(d["saida"]).strftime(FORMATO_DATA_HORA)

    # Telefone (opcional)
    ok, resultado = validar_telefone(d["telefone"])
    if not ok:
        return None, ("telefone", "Telefone inválido", resultado)
    d["telefone"] = resultado

    # Pessoa visitada (opcional): mesmas regras de um nome
    if d["visitado"] != "":
        ok, mensagem = validar_nome(d["visitado"], "O nome da pessoa visitada")
        if not ok:
            return None, ("visitado", "Pessoa visitada inválida", mensagem)

    # Placa (opcional)
    d["placa"] = d["placa"].upper().replace("-", "")
    if d["placa"] != "" and not PADRAO_PLACA.match(d["placa"]):
        return None, ("placa", "Placa inválida",
                      "Use o formato ABC1234 ou ABC1D23 (3 letras, 1 número, "
                      "1 letra ou número, 2 números).")

    # Cor do veículo (opcional): só letras
    if d["cor"] != "" and not PADRAO_NOME.match(d["cor"]):
        return None, ("cor", "Cor inválida", "A cor deve conter apenas letras.")

    # Tamanhos máximos
    limites = {"empresa": MAX_EMPRESA, "modelo": MAX_MODELO, "cor": MAX_COR,
               "observacoes": MAX_OBSERVACOES}
    for campo, maximo in limites.items():
        if len(d[campo]) > maximo:
            return None, (campo, "Texto muito longo",
                          f"{ROTULOS[campo]}: máximo de {maximo} caracteres.")

    return d, None


def existe_duplicado(dados, ignorar_id=None):
    """
    Possível duplicidade = mesmo nome + mesmo tipo + mesma entrada.
    (Não bloqueia só pelo nome: a mesma pessoa pode entrar várias vezes.)
    """
    for r in registros:
        if r["id"] == ignorar_id:
            continue
        if (r["nome"].casefold() == dados["nome"].casefold()
                and r["tipo"] == dados["tipo"]
                and r["entrada"] == dados["entrada"]):
            return True
    return False
