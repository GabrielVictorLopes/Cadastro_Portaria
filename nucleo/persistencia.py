"""Leitura e gravação dos arquivos: configurações, registros e histórico."""

import csv
import json
import os
from datetime import datetime

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from nucleo.constantes import (
    ARQ_BACKUP, ARQ_CONFIG, ARQ_HISTORICO, ARQ_REGISTROS, ARQ_TRAVA, CABECALHO_CSV,
    CABECALHO_HISTORICO, CHAVES_CSV, CONFIG_PADRAO, FORMATO_DATA_HORA,
    FORMATO_EVENTO, PALETAS, TIPOS)
from nucleo.estado import S, config, registros
from nucleo.utilitarios import (
    CHAVES_CABECALHO, TIPOS_NORMALIZADOS, caminho, converter_data, remover_acentos)


# ======================================================================
# TRAVA: UMA CÓPIA DO PROGRAMA POR VEZ
# Duas cópias abertas gravariam o arquivo inteiro uma por cima da outra.
# A trava é do sistema operacional: some sozinha se o programa fechar
# ou travar, então nunca fica "presa".
# ======================================================================
def obter_trava():
    """Trava dados/portaria.lock. Retorna False se outra cópia já está aberta."""
    try:
        arquivo = open(caminho(ARQ_TRAVA), "a+")
    except OSError:
        return True             # sem como criar a trava: não impede o uso
    try:
        if os.name == "nt":
            arquivo.seek(0)
            msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        arquivo.close()
        return False
    S.trava = arquivo           # mantido aberto até o programa fechar
    return True


# ======================================================================
# PERSISTÊNCIA: CONFIGURAÇÕES
# ======================================================================
def carregar_configuracoes():
    """Lê configuracoes.json. Se não existir ou estiver inválido, usa o padrão."""
    config.clear()
    config.update(CONFIG_PADRAO)
    try:
        with open(caminho(ARQ_CONFIG), encoding="utf-8") as f:
            lido = json.load(f)
    except (OSError, ValueError):
        return
    if not isinstance(lido, dict):
        return
    for chave, padrao in CONFIG_PADRAO.items():
        if chave not in lido:
            continue
        valor = lido[chave]
        # bool é subclasse de int: true/false não podem valer como número (e vice-versa)
        if isinstance(valor, type(padrao)) and \
                isinstance(valor, bool) == isinstance(padrao, bool):
            config[chave] = valor
    if config["tema"] not in PALETAS:
        config["tema"] = "claro"
    if not 1 <= config["tempo_max_horas"] <= 72:
        config["tempo_max_horas"] = CONFIG_PADRAO["tempo_max_horas"]


def salvar_configuracoes():
    """Grava configuracoes.json (arquivo temporário + substituição). True se ok."""
    arquivo = caminho(ARQ_CONFIG)
    temporario = arquivo + ".tmp"
    try:
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.replace(temporario, arquivo)
        return True
    except OSError:
        return False


# ======================================================================
# PERSISTÊNCIA: REGISTROS (CSV, backup, migração)
# ======================================================================
def copiar_arquivo(origem, destino):
    """Copia um arquivo byte a byte."""
    with open(origem, "rb") as arquivo_origem, open(destino, "wb") as arquivo_destino:
        arquivo_destino.write(arquivo_origem.read())


def preservar_original():
    """
    Guarda uma cópia do registros.csv atual em registros_original_AAAAMMDD_HHMMSS.csv.
    Usada antes de migrar ou corrigir o arquivo. Nunca sobrescreve outra cópia.
    """
    origem = caminho(ARQ_REGISTROS)
    base = "registros_original_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = caminho(base + ".csv")
    numero = 2
    while os.path.exists(destino):
        destino = caminho(f"{base}_{numero}.csv")
        numero += 1
    copiar_arquivo(origem, destino)
    return os.path.basename(destino)


def gravar_registros():
    """
    Grava registros.csv de forma segura. Retorna (ok, mensagem_de_erro).

    1) escreve tudo em um arquivo temporário;
    2) copia o arquivo atual para registros_backup.csv;
    3) só então substitui o arquivo principal.
    Se algo falhar, o arquivo principal continua intacto.
    """
    arquivo = caminho(ARQ_REGISTROS)
    temporario = arquivo + ".tmp"
    try:
        with open(temporario, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.writer(f, delimiter=";")
            escritor.writerow(CABECALHO_CSV)
            for r in registros:
                escritor.writerow([r[chave] for chave in CHAVES_CSV])
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(arquivo):
            copiar_arquivo(arquivo, caminho(ARQ_BACKUP))
        os.replace(temporario, arquivo)
        return True, ""
    except OSError as erro:
        try:
            os.remove(temporario)
        except OSError:
            pass
        return False, str(erro)


def ler_linhas_csv(arquivo):
    """Lê um CSV e devolve [(número da linha, [células])], ignorando linhas vazias."""
    for codificacao in ("utf-8-sig", "cp1252"):
        try:
            with open(arquivo, newline="", encoding=codificacao) as f:
                leitor = csv.reader(f, delimiter=";")
                linhas = []
                for linha in leitor:
                    if any(c.strip() for c in linha):
                        linhas.append((leitor.line_num, [c.strip() for c in linha]))
                return linhas
        except UnicodeDecodeError:
            continue
    raise ValueError("codificação do arquivo não reconhecida")


def montar_dados_da_linha(chaves, valores):
    """Cria o dicionário de um registro a partir de uma linha do CSV."""
    dados = {chave: "" for chave in CHAVES_CSV}
    for chave, valor in zip(chaves, valores):
        if chave is not None:
            dados[chave] = valor
    return dados


def validar_dados_csv(dados):
    """Confere uma linha do CSV. Retorna o motivo do erro ou '' se estiver ok."""
    if dados["nome"] == "":
        return "nome vazio"
    if dados["tipo"] not in TIPOS:
        return f"tipo de acesso inválido ({dados['tipo']})"
    entrada = converter_data(dados["entrada"])
    if entrada is None:
        return f"data de entrada inválida ({dados['entrada']})"
    if dados["saida"] != "":
        saida = converter_data(dados["saida"])
        if saida is None:
            return f"data de saída inválida ({dados['saida']})"
        if saida < entrada:
            return "saída anterior à entrada"
    return ""


def carregar_registros():
    """
    Carrega registros.csv para a lista 'registros'.

    - Preserva os IDs do arquivo (IDs repetidos ou inválidos recebem novo ID).
    - Migra formatos antigos (sem cabeçalho / sem ID / sem os novos campos).
    - Linhas inválidas NÃO são apagadas do disco: antes de qualquer correção
      ou migração, uma cópia do arquivo original é guardada.
    - Nunca fecha o programa: problemas viram avisos.

    Retorna uma lista de avisos (textos) para mostrar ao usuário.
    """
    registros.clear()
    avisos = []
    arquivo = caminho(ARQ_REGISTROS)
    # O histórico também guarda os IDs já usados: mesmo que configuracoes.json
    # se perca, um ID de registro excluído não volta a ser usado.
    S.proximo_id = max(1, config["proximo_id"], maior_id_historico() + 1)
    if not os.path.exists(arquivo):
        return avisos

    try:
        linhas = ler_linhas_csv(arquivo)
    except (OSError, csv.Error, ValueError):
        try:
            copia = preservar_original()
            avisos.append("Não foi possível ler o arquivo registros.csv. O sistema "
                          f"iniciará vazio; o arquivo original foi guardado em {copia}.")
        except OSError:
            avisos.append("Não foi possível ler o arquivo registros.csv e nem "
                          "guardar uma cópia dele. Salvar novos dados pode "
                          "sobrescrevê-lo: faça uma cópia manual antes de continuar.")
        return avisos

    precisa_regravar = False
    chaves_cabecalho = None
    if linhas and linhas[0][1][0].casefold() == "id":
        chaves_cabecalho = [CHAVES_CABECALHO.get(remover_acentos(c))
                            for c in linhas[0][1]]
        if chaves_cabecalho != CHAVES_CSV:
            precisa_regravar = True                 # formato antigo: migrar
        # Colunas de cabeçalho vazias (ex.: ';' extras deixados pelo Excel) não contam
        if any(chave is None and celula != ""
               for chave, celula in zip(chaves_cabecalho, linhas[0][1])):
            avisos.append("O arquivo tem colunas desconhecidas, que não serão "
                          "mantidas no novo arquivo (o original será guardado).")
        linhas = linhas[1:]
    elif linhas:
        precisa_regravar = True                     # sem cabeçalho: migrar

    sem_id = []                 # registros que receberão um ID novo
    ids_usados = set()

    for numero_linha, l in linhas:
        if chaves_cabecalho is not None:
            dados = montar_dados_da_linha(chaves_cabecalho, l)
        elif len(l) >= 5 and l[0].isdigit():
            dados = montar_dados_da_linha(CHAVES_CSV, l)          # com ID
        elif len(l) == 4 and l[2] in TIPOS:
            dados = montar_dados_da_linha(CHAVES_CSV[:4], l)      # ID sem saída
        elif len(l) == 4:
            dados = montar_dados_da_linha(CHAVES_CSV[1:5], l)     # formato antigo
        else:
            avisos.append(f"Linha {numero_linha}: dados incompletos (ignorada).")
            continue

        # Tipo digitado sem acento ou com outras maiúsculas ('funcionario') é corrigido
        tipo = TIPOS_NORMALIZADOS.get(remover_acentos(dados["tipo"]))
        if tipo is not None and tipo != dados["tipo"]:
            dados["tipo"] = tipo
            precisa_regravar = True

        erro = validar_dados_csv(dados)
        if erro != "":
            avisos.append(f"Linha {numero_linha}: {erro} (ignorada).")
            continue

        # Padroniza as datas (ex.: '6/1/2026 9:30' -> '06/01/2026 09:30')
        for chave in ("entrada", "saida"):
            if dados[chave] != "":
                padronizada = converter_data(dados[chave]).strftime(FORMATO_DATA_HORA)
                if padronizada != dados[chave]:
                    dados[chave] = padronizada
                    precisa_regravar = True

        texto_id = dados.get("id", "")
        if texto_id.isdigit() and int(texto_id) > 0 and int(texto_id) not in ids_usados:
            dados["id"] = int(texto_id)
            ids_usados.add(dados["id"])
            registros.append(dados)
        else:
            if texto_id != "":
                avisos.append(f"Linha {numero_linha}: ID inválido ou repetido "
                              "(um novo ID foi gerado).")
            sem_id.append(dados)

    S.proximo_id = max(max(ids_usados, default=0) + 1, S.proximo_id)
    for dados in sem_id:
        dados["id"] = S.proximo_id
        S.proximo_id += 1
        registros.append(dados)
    registros.sort(key=lambda r: r["id"])
    config["proximo_id"] = S.proximo_id

    if sem_id or any(a.startswith("Linha") for a in avisos):
        precisa_regravar = True
    if precisa_regravar:
        try:
            copia = preservar_original()
        except OSError:
            avisos.append("Não foi possível guardar uma cópia do arquivo original; "
                          "por segurança, ele NÃO foi alterado agora. Porém, o próximo "
                          "salvamento vai regravá-lo sem as linhas com problema: faça "
                          "uma cópia manual de registros.csv antes de continuar.")
            return avisos
        ok, erro = gravar_registros()
        if ok:
            avisos.append(f"Arquivo atualizado para o formato atual. Cópia do "
                          f"original guardada em {copia}.")
        else:
            avisos.append(f"Não foi possível regravar o arquivo ({erro}). "
                          f"O original continua intacto.")
    return avisos


# ======================================================================
# PERSISTÊNCIA: HISTÓRICO DE ATIVIDADES
# ======================================================================
def registrar_historico(acao, numero_id, nome, descricao):
    """
    Acrescenta uma linha em historico.csv. Retorna True se gravou.
    Observação: é um registro LOCAL e comum; quem tem acesso à pasta pode
    editar o arquivo. Não é uma auditoria inviolável.
    """
    arquivo = caminho(ARQ_HISTORICO)
    try:
        if not os.path.exists(arquivo):
            with open(arquivo, "w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f, delimiter=";").writerow(CABECALHO_HISTORICO)
        with open(arquivo, "a", newline="", encoding="utf-8") as f:
            csv.writer(f, delimiter=";").writerow(
                [datetime.now().strftime(FORMATO_EVENTO), acao, numero_id,
                 nome, descricao])
        return True
    except OSError:
        S.falha_historico = True        # a interface avisa o usuário
        return False


def ler_historico():
    """Lê historico.csv. Retorna lista de dicionários, do evento mais novo ao mais antigo."""
    arquivo = caminho(ARQ_HISTORICO)
    if not os.path.exists(arquivo):
        return []
    try:
        linhas = ler_linhas_csv(arquivo)
    except (OSError, csv.Error, ValueError):
        return []
    eventos = []
    for _, l in linhas:
        if l[0] == CABECALHO_HISTORICO[0] or len(l) < 5:
            continue
        eventos.append({"data": l[0], "acao": l[1], "id": l[2], "nome": l[3],
                        "descricao": l[4]})
    eventos.reverse()
    return eventos


def maior_id_historico():
    """Maior ID de registro citado no histórico (0 se não houver)."""
    ids = [int(e["id"]) for e in ler_historico() if e["id"].isdigit()]
    return max(ids, default=0)


def filtrar_historico(eventos, texto="", acao="Todas", data_ini=None, data_fim=None):
    """Filtra eventos do histórico por texto, tipo de ação e período."""
    texto = remover_acentos(texto.strip())
    resultado = []
    for e in eventos:
        if acao != "Todas" and e["acao"] != acao:
            continue
        if texto != "":
            campos = (e["nome"], e["descricao"], e["id"], e["acao"])
            if not any(texto in remover_acentos(c) for c in campos):
                continue
        if data_ini is not None or data_fim is not None:
            try:
                dia = datetime.strptime(e["data"], FORMATO_EVENTO).date()
            except ValueError:
                continue
            if data_ini is not None and dia < data_ini:
                continue
            if data_fim is not None and dia > data_fim:
                continue
        resultado.append(e)
    return resultado
