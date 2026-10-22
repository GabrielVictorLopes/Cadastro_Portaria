"""
Sistema de Controle de Portaria
UC - Teoria da Computação e Compiladores
"""

# ======================================================================
# IMPORTAÇÕES
# ======================================================================
import copy                                   # cópia segura dos dados (desfazer)
import csv                                    # arquivos CSV
import json                                   # configurações
import os                                     # arquivos e pastas
import re                                     # expressões regulares
import unicodedata                            # remover acentos
from datetime import date, datetime, timedelta
from types import SimpleNamespace             # "caixas" para agrupar variáveis
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# ======================================================================
# CONSTANTES
# ======================================================================
VERSAO = "3.0"

# Arquivos
PASTA_DADOS = os.path.dirname(os.path.abspath(__file__))
ARQ_REGISTROS = "registros.csv"
ARQ_BACKUP = "registros_backup.csv"
ARQ_HISTORICO = "historico.csv"
ARQ_CONFIG = "configuracoes.json"

FORMATO_DATA_HORA = "%d/%m/%Y %H:%M"          # 06/10/2026 09:30
FORMATO_DATA = "%d/%m/%Y"                     # 06/10/2026
FORMATO_EVENTO = "%d/%m/%Y %H:%M:%S"          # usado no histórico
ANO_MINIMO = 2000

# Listas permitidas
TIPOS = ["Visitante", "Morador", "Entregador", "Funcionário"]
MOTIVOS = ["Visita", "Entrega", "Serviço", "Reunião", "Manutenção",
           "Moradia", "Outro"]
FILTRO_TIPOS = ["Todos"] + TIPOS
# Opções do filtro "Situação": com o alerta de tempo máximo ativo, quem está
# no local é separado em "No prazo" e "Excedido".
FILTRO_SITUACOES = ["Todos", "No local", "Saiu"]
FILTRO_SITUACOES_ALERTA = ["Todos", "No local", "No prazo", "Excedido", "Saiu"]
FILTRO_MOTIVOS = ["Todos"] + MOTIVOS
PERIODOS = ["Todos", "Hoje", "Ontem", "Últimos 7 dias", "Últimos 30 dias",
            "Período personalizado"]
ACOES_HISTORICO = ["Cadastro", "Edição", "Saída", "Exclusão", "Exportação",
                   "Configuração"]

# Campos do cadastro (chave interna -> rótulo mostrado ao usuário)
CHAVES_TEXTO = ["nome", "tipo", "motivo", "entrada", "saida", "telefone",
                "empresa", "visitado", "observacoes", "placa", "modelo", "cor"]
ROTULOS = {
    "id": "ID", "nome": "Nome", "tipo": "Tipo de acesso", "motivo": "Motivo",
    "entrada": "Entrada", "saida": "Saída", "telefone": "Telefone",
    "empresa": "Empresa", "visitado": "Pessoa visitada",
    "observacoes": "Observações", "placa": "Placa", "modelo": "Modelo",
    "cor": "Cor",
}

# Ordem das colunas no registros.csv (a situação e a permanência NÃO são salvas)
COLUNAS_CSV = [("ID", "id"), ("Nome", "nome"), ("Tipo de acesso", "tipo"),
               ("Entrada", "entrada"), ("Saída", "saida"),
               ("Telefone", "telefone"), ("Empresa", "empresa"),
               ("Pessoa visitada", "visitado"), ("Motivo", "motivo"),
               ("Observações", "observacoes"), ("Placa", "placa"),
               ("Modelo", "modelo"), ("Cor", "cor")]
CABECALHO_CSV = [rotulo for rotulo, _ in COLUNAS_CSV]
CHAVES_CSV = [chave for _, chave in COLUNAS_CSV]
CABECALHO_HISTORICO = ["Data/Hora", "Ação", "ID", "Nome", "Descrição"]

# Limites de tamanho
MAX_NOME = 60
MAX_EMPRESA = 60
MAX_MODELO = 30
MAX_COR = 20
MAX_OBSERVACOES = 200

# Expressões regulares
# Nome: só letras (com acentos) separadas por espaço, hífen ou apóstrofo.
PADRAO_NOME = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$")
CARACTERES_INVALIDOS_NOME = re.compile(r"[^A-Za-zÀ-ÖØ-öø-ÿ '\-]")
# Placa: antiga (ABC1234) ou Mercosul (ABC1D23), sem hífen.
PADRAO_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

# Máscaras de digitação ('#' = um número; os outros símbolos são colocados sozinhos)
MASCARA_DATA_HORA = ("##/##/#### ##:##", 12)
MASCARA_DATA = ("##/##/####", 8)

# Configurações padrão (salvas em configuracoes.json)
CONFIG_PADRAO = {
    "tema": "claro",
    "tempo_max_horas": 4,
    "alerta_ativo": True,
    "mostrar_motivo": True,
    "mostrar_veiculo": False,
    "proximo_id": 1,
}

TEXTO_SITUACAO = {"No local": "● No local", "Saiu": "○ Saiu"}
TEXTO_ALERTA = "⚠ Excedido"

# Colunas da tabela principal:
# (identificador, título, largura, largura mínima, alinhamento, estica?)
COLUNAS_TABELA = [
    ("ID",          "ID",             48,  44, "center", False),
    ("Nome",        "Nome",          190, 140, "w",      True),
    ("Tipo",        "Tipo",           95,  85, "center", False),
    ("Entrada",     "Entrada",       118, 112, "center", False),
    ("Saida",       "Saída",         118, 112, "center", False),
    ("Permanencia", "Permanência",   175, 120, "w",      False),
    ("Situacao",    "Situação",      100,  95, "center", False),
    ("Motivo",      "Motivo",         95,  80, "center", False),
    ("Veiculo",     "Veículo",        85,  75, "center", False),
]

# ---------------------------------------------------------------------
# Temas de cores (claro e escuro)
# ---------------------------------------------------------------------
PALETAS = {
    # Base grafite/pedra com laranja como cor principal
    # (as chaves "azul"/"azul_h" guardam a cor principal do tema)
    "claro": {
        "fundo": "#F5F5F4", "card": "#FFFFFF", "borda": "#E7E5E4",
        "texto": "#1C1917", "suave": "#78716C", "campo": "#FAFAF9",
        "titulo": "#C2410C", "cabecalho": "#1F2328",
        "cabecalho_escuro": "#111317", "cabecalho_texto": "#D6D3D1",
        "selecao": "#FFEDD5", "aba": "#E7E5E4",
        "azul": "#C2410C", "azul_h": "#9A3412",
        "verde": "#15803D", "verde_h": "#166534",
        "vermelho": "#DC2626", "vermelho_h": "#B91C1C",
        "amarelo": "#EAB308", "amarelo_h": "#CA8A04",
        "cinza": "#E7E5E4", "cinza_h": "#D6D3D1",
        "branco": "#FFFFFF", "escuro": "#1C1917",
        "dentro_bg": "#F0FDF4", "dentro_fg": "#166534",
        "saiu_bg": "#FAFAF9", "saiu_fg": "#57534E",
        "alerta_bg": "#FEF2F2", "alerta_fg": "#B91C1C",
    },
    "escuro": {
        "fundo": "#0F1012", "card": "#1A1C1F", "borda": "#2C2F33",
        "texto": "#ECEAE8", "suave": "#A8A29E", "campo": "#222428",
        "titulo": "#FB923C", "cabecalho": "#08090A",
        "cabecalho_escuro": "#1F2226", "cabecalho_texto": "#D6D3D1",
        "selecao": "#7C2D12", "aba": "#222428",
        "azul": "#EA580C", "azul_h": "#C2410C",
        "verde": "#16A34A", "verde_h": "#15803D",
        "vermelho": "#E11D48", "vermelho_h": "#BE123C",
        "amarelo": "#EAB308", "amarelo_h": "#CA8A04",
        "cinza": "#2C2F33", "cinza_h": "#3A3E44",
        "branco": "#FFFFFF", "escuro": "#1C1917",
        "dentro_bg": "#0F2A1A", "dentro_fg": "#86EFAC",
        "saiu_bg": "#1A1C1F", "saiu_fg": "#A8A29E",
        "alerta_bg": "#3B1219", "alerta_fg": "#FDA4AF",
    },
}

# Estilos de botão: (cor de fundo, cor ao passar o mouse, cor do texto)
ESTILOS_BOTAO = {
    "azul": ("azul", "azul_h", "branco"),
    "verde": ("verde", "verde_h", "branco"),
    "vermelho": ("vermelho", "vermelho_h", "branco"),
    "amarelo": ("amarelo", "amarelo_h", "escuro"),
    "cinza": ("cinza", "cinza_h", "texto"),
}

FONTE = "Segoe UI"


# ======================================================================
# ESTADO DO PROGRAMA
# ======================================================================
registros = []                    # lista de dicionários (um por pessoa)
config = dict(CONFIG_PADRAO)      # configurações carregadas do arquivo

# Estado geral (em vez de várias variáveis globais soltas)
S = SimpleNamespace(
    proximo_id=1,                 # só aumenta: IDs excluídos não são reaproveitados
    id_em_edicao=None,            # None = cadastrando | número = editando
    coluna_ordenada="ID",
    ordem_decrescente=False,
    tema="claro",
    suspender_filtros=False,      # evita atualizar a tabela várias vezes seguidas
    extras_abertos=False,
    formulario_aberto=False,      # janela de cadastro/edição está aberta?
    avancados_abertos=False,
    id_status=None,               # temporizador da mensagem da barra de status
    ticks=0,
    dia_tabela=None,              # dia em que a tabela foi filtrada ("Hoje" muda à meia-noite)
)

# Widgets da interface (criados em criar_interface)
T = SimpleNamespace(tematizaveis=[], textos=[])


# ======================================================================
# FUNÇÕES AUXILIARES
# ======================================================================
def caminho(nome_arquivo):
    """Caminho completo de um arquivo de dados do sistema."""
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
    S.proximo_id = max(1, config["proximo_id"])
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


def aplicar_tema():
    """Aplica o tema escolhido (config['tema']) em TODOS os componentes."""
    S.tema = config["tema"]
    configurar_estilo()
    T.janela.configure(bg=cor("fundo"))
    for widget, opcoes in T.tematizaveis:
        aplicar_opcoes(widget, opcoes)
    for texto in T.textos:
        configurar_tags_texto(texto)
    configurar_tags_tabela()
    T.botao_tema.configure(text="Tema claro" if S.tema == "escuro" else "Tema escuro")
    atualizar_modo_formulario()        # reaplica o destaque de edição (amarelo) sobre o novo tema


def alternar_tema():
    """Botão do cabeçalho: alterna entre tema claro e escuro."""
    anterior = config["tema"]
    config["tema"] = "escuro" if anterior == "claro" else "claro"
    aplicar_tema()
    T.var_config_tema.set(config["tema"].capitalize())
    salvar_configuracoes()
    registrar_historico("Configuração", "", "",
                        f"Tema alterado de {anterior} para {config['tema']}")
    mostrar_status(f"Tema {config['tema']} ativado.", "info")


# ======================================================================
# INTERFACE: JANELA, CABEÇALHO E BARRA DE STATUS
# ======================================================================
def criar_janela():
    janela = tk.Tk()
    T.janela = janela
    janela.title("Cadastro de Portaria - Controle de entrada e saída")
    largura = min(1280, janela.winfo_screenwidth() - 40)
    altura = min(860, janela.winfo_screenheight() - 90)
    janela.geometry(f"{largura}x{altura}+20+10")
    janela.minsize(min(1000, largura), min(640, altura))
    S.tema = config["tema"]
    janela.configure(bg=cor("fundo"))
    configurar_estilo()
    janela.protocol("WM_DELETE_WINDOW", ao_fechar)


def criar_cabecalho():
    """Faixa do cabeçalho: nome do sistema à esquerda; identificação, tema e relógio à direita."""
    faixa = criar_quadro(T.janela, "cabecalho")
    faixa.pack(fill="x")
    interno = criar_quadro(faixa, "cabecalho")
    interno.pack(fill="x", padx=20, pady=10)

    esquerda = criar_quadro(interno, "cabecalho")
    esquerda.pack(side="left")
    criar_rotulo(esquerda, "Cadastro de Portaria", "cabecalho", "branco",
                 (FONTE, 20, "bold")).pack(anchor="w")
    criar_rotulo(esquerda, "Controle de entrada e saída", "cabecalho",
                 "cabecalho_texto", (FONTE, 11)).pack(anchor="w")

    direita = criar_quadro(interno, "cabecalho")
    direita.pack(side="right")
    linha = criar_quadro(direita, "cabecalho")
    linha.pack(anchor="e")
    criar_rotulo(linha, "CONTROLE DE ACESSO", "cabecalho_escuro", "branco",
                 (FONTE, 9, "bold"), padx=12, pady=4).pack(side="left")
    T.botao_tema = tk.Button(linha, text="Tema escuro", command=alternar_tema,
                             font=(FONTE, 9, "bold"), relief="flat", bd=0,
                             cursor="hand2", padx=10, pady=4)
    registrar(T.botao_tema, bg="cabecalho_escuro", fg="branco",
              activebackground="azul_h", activeforeground="branco")
    T.botao_tema.pack(side="left", padx=(8, 0))
    T.rotulo_relogio = criar_rotulo(direita, "", "cabecalho", "cabecalho_texto",
                                    (FONTE, 10))
    T.rotulo_relogio.pack(anchor="e", pady=(6, 0))

    criar_quadro(T.janela, "azul", height=4).pack(fill="x")     # faixa de destaque


def criar_barra_status():
    """Barra inferior: mensagens discretas à esquerda e contagem à direita."""
    barra = criar_quadro(T.janela, "card")
    barra.pack(side="bottom", fill="x")
    T.rotulo_status = criar_rotulo(barra, "Pronto.", "card", "suave", (FONTE, 9))
    T.rotulo_status.pack(side="left", padx=14, pady=4)
    T.rotulo_contagem = criar_rotulo(barra, "", "card", "suave", (FONTE, 9))
    T.rotulo_contagem.pack(side="right", padx=14)


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


def atualizar_relogio():
    """Atualiza data e hora a cada segundo; a cada minuto atualiza os tempos."""
    T.rotulo_relogio.configure(text=datetime.now().strftime("%d/%m/%Y   %H:%M:%S"))
    S.ticks += 1
    if S.ticks % 60 == 0:
        atualizar_tempos()
    T.janela.after(1000, atualizar_relogio)


# ======================================================================
# INTERFACE: DASHBOARD (indicadores)
# ======================================================================
# (título do grupo, cor do título, [(indicador, rótulo, cor do número)])
GRUPOS_INDICADORES = [
    ("TODOS OS REGISTROS", "suave",
     [("total", "TOTAL", "azul"), ("dentro", "NO LOCAL AGORA", "verde"),
      ("saiu", "SAÍRAM", "suave")]),
    ("SOMENTE HOJE", "amarelo_h",
     [("entradas_hoje", "ENTRADAS", "azul"),
      ("entregadores_hoje", "ENTREGADORES", "azul")]),
    ("NO LOCAL AGORA, POR TIPO", "verde",
     [("visitantes", "VISITANTES", "verde"),
      ("funcionarios", "FUNCIONÁRIOS", "verde"),
      ("moradores", "MORADORES", "verde")]),
]


def criar_dashboard(pai):
    """Indicadores no topo. Os três grupos deixam claro o que cada número mede."""
    T.var_ind = {chave: tk.StringVar(value="0")
                 for _, _, itens in GRUPOS_INDICADORES for chave, _, _ in itens}
    faixa = criar_quadro(pai, "fundo")
    faixa.pack(fill="x", pady=(0, 8))

    for coluna, (titulo, cor_titulo, itens) in enumerate(GRUPOS_INDICADORES):
        caixa = tk.Frame(faixa, highlightthickness=1)
        registrar(caixa, bg="card", highlightbackground="borda")
        caixa.grid(row=0, column=coluna, sticky="nsew",
                   padx=(0 if coluna == 0 else 8, 0))
        faixa.columnconfigure(coluna, weight=len(itens))
        criar_rotulo(caixa, titulo, "card", cor_titulo,
                     (FONTE, 8, "bold")).pack(anchor="w", padx=10, pady=(6, 0))
        interno = criar_quadro(caixa)
        interno.pack(fill="x", padx=10, pady=(0, 6))
        for posicao, (chave, rotulo, cor_numero) in enumerate(itens):
            interno.columnconfigure(posicao, weight=1, uniform=f"grupo{coluna}")
            mini = criar_quadro(interno)
            mini.grid(row=0, column=posicao, sticky="w")
            criar_rotulo(mini, rotulo, "card", "suave",
                         (FONTE, 8, "bold")).pack(anchor="w")
            criar_rotulo(mini, "", "card", cor_numero, (FONTE, 18, "bold"),
                         textvariable=T.var_ind[chave]).pack(anchor="w")


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
# INTERFACE: PESQUISA E FILTROS
# ======================================================================
def criar_filtros(pai):
    """Pesquisa e filtros (os filtros avançados ficam recolhidos)."""
    cartao, conteudo, _ = criar_cartao(pai, "Pesquisa e filtros")
    cartao.pack(fill="x", pady=(0, 8))

    T.var_pesquisa = tk.StringVar()
    T.var_empresa = tk.StringVar()
    T.var_data_ini = tk.StringVar()
    T.var_data_fim = tk.StringVar()
    T.var_filtro_tipo = tk.StringVar(value="Todos")
    T.var_filtro_situacao = tk.StringVar(value="Todos")
    T.var_filtro_periodo = tk.StringVar(value="Todos")
    T.var_filtro_motivo = tk.StringVar(value="Todos")

    linha1 = criar_quadro(conteudo)
    linha1.pack(fill="x")
    linha1.columnconfigure(1, weight=1)
    criar_rotulo(linha1, "Pesquisar:").grid(row=0, column=0, sticky="w")
    T.campo_pesquisa = criar_campo_texto(linha1, T.var_pesquisa)
    T.campo_pesquisa.grid(row=0, column=1, sticky="ew", ipady=4, padx=(8, 12))

    def lista(coluna, texto, variavel, valores, largura, ao_selecionar=ao_filtro_mudou):
        criar_rotulo(linha1, texto).grid(row=0, column=coluna, sticky="w")
        caixa = criar_lista(linha1, variavel, valores, largura)
        caixa.grid(row=0, column=coluna + 1, padx=(6, 12))
        caixa.bind("<<ComboboxSelected>>", lambda e: ao_selecionar())
        return caixa

    lista(2, "Tipo:", T.var_filtro_tipo, FILTRO_TIPOS, 11)
    T.lista_situacao = lista(4, "Situação:", T.var_filtro_situacao,
                             opcoes_filtro_situacao(), 10)
    T.lista_periodo = lista(6, "Período:", T.var_filtro_periodo, PERIODOS, 19,
                            ao_mudar_periodo)

    T.botao_avancado = criar_botao(linha1, "Filtros avançados ▸", alternar_avancados,
                                   "cinza", 18)
    T.botao_avancado.grid(row=0, column=8, padx=(0, 6))
    criar_botao(linha1, "Aplicar", aplicar_filtros, "azul", 9).grid(row=0, column=9,
                                                                    padx=(0, 6))
    criar_botao(linha1, "Limpar filtros", limpar_filtros, "cinza", 13)\
        .grid(row=0, column=10)

    # --- Filtros avançados (recolhidos) ---
    T.frame_avancado = criar_quadro(conteudo)
    T.frame_avancado.pack(fill="x", pady=(8, 0))
    T.frame_avancado.columnconfigure(7, weight=1)
    criar_rotulo(T.frame_avancado, "De:").grid(row=0, column=0, sticky="w")
    T.campo_data_ini = criar_campo_texto(T.frame_avancado, T.var_data_ini)
    T.campo_data_ini.configure(width=11)
    T.campo_data_ini.grid(row=0, column=1, ipady=3, padx=(6, 12))
    criar_rotulo(T.frame_avancado, "Até:").grid(row=0, column=2, sticky="w")
    T.campo_data_fim = criar_campo_texto(T.frame_avancado, T.var_data_fim)
    T.campo_data_fim.configure(width=11)
    T.campo_data_fim.grid(row=0, column=3, ipady=3, padx=(6, 12))
    criar_rotulo(T.frame_avancado, "Motivo:").grid(row=0, column=4, sticky="w")
    caixa = criar_lista(T.frame_avancado, T.var_filtro_motivo, FILTRO_MOTIVOS, 12)
    caixa.grid(row=0, column=5, padx=(6, 12))
    caixa.bind("<<ComboboxSelected>>", lambda e: ao_filtro_mudou())
    criar_rotulo(T.frame_avancado, "Empresa:").grid(row=0, column=6, sticky="w")
    criar_campo_texto(T.frame_avancado, T.var_empresa)\
        .grid(row=0, column=7, sticky="ew", ipady=3, padx=(6, 0))
    T.frame_avancado.pack_forget()
    S.avancados_abertos = False

    T.var_pesquisa.trace_add("write", lambda *a: ao_filtro_mudou())
    T.var_empresa.trace_add("write", lambda *a: ao_filtro_mudou())
    for variavel, campo in ((T.var_data_ini, T.campo_data_ini),
                            (T.var_data_fim, T.campo_data_fim)):
        variavel.trace_add("write", lambda *a, var=variavel, cp=campo:
                           ao_digitar_data_filtro(var, cp))


def alternar_avancados(abrir=None):
    """Mostra ou esconde os filtros avançados."""
    S.avancados_abertos = (not S.avancados_abertos) if abrir is None else abrir
    if S.avancados_abertos:
        T.frame_avancado.pack(fill="x", pady=(8, 0))
        T.botao_avancado.configure(text="Filtros avançados ▾")
    else:
        T.frame_avancado.pack_forget()
        T.botao_avancado.configure(text="Filtros avançados ▸")


def criterios_atuais():
    """Lê os filtros da tela."""
    return {"texto": T.var_pesquisa.get(), "tipo": T.var_filtro_tipo.get(),
            "situacao": T.var_filtro_situacao.get(),
            "periodo": T.var_filtro_periodo.get(),
            "data_ini": converter_data_simples(T.var_data_ini.get()),
            "data_fim": converter_data_simples(T.var_data_fim.get()),
            "motivo": T.var_filtro_motivo.get(), "empresa": T.var_empresa.get()}


def ao_filtro_mudou():
    """Qualquer filtro mudou: atualiza a tabela (a menos que seja uma mudança em lote)."""
    if not S.suspender_filtros:
        atualizar_tabela()


def ao_mudar_periodo():
    """Escolheu um período pronto: apaga as datas. Personalizado: abre os campos de data."""
    if T.var_filtro_periodo.get() == "Período personalizado":
        alternar_avancados(True)
    else:
        S.suspender_filtros = True
        T.var_data_ini.set("")
        T.var_data_fim.set("")
        S.suspender_filtros = False
    atualizar_tabela()


def ao_digitar_data_filtro(variavel, campo):
    """Máscara (só números) nas datas do filtro; digitar uma data ativa o período personalizado."""
    aplicar_mascara(variavel, campo, MASCARA_DATA[0], MASCARA_DATA[1])
    if S.suspender_filtros:
        return
    if variavel.get() != "" and T.var_filtro_periodo.get() != "Período personalizado":
        T.var_filtro_periodo.set("Período personalizado")
    atualizar_tabela()


def aplicar_filtros():
    """Botão Aplicar: confere o período personalizado e atualiza a tabela."""
    c = criterios_atuais()
    if c["data_ini"] and c["data_fim"] and c["data_ini"] > c["data_fim"]:
        messagebox.showwarning("Período inválido",
                               "A data inicial não pode ser posterior à data final.")
        return
    for texto, campo in ((T.var_data_ini.get(), "inicial"),
                         (T.var_data_fim.get(), "final")):
        if texto != "" and converter_data_simples(texto) is None:
            messagebox.showwarning("Data inválida",
                                   f"A data {campo} do filtro é inválida (use dd/mm/aaaa).")
            return
    atualizar_tabela()
    mostrar_status("Filtros aplicados.", "info")


def limpar_filtros(evento=None):
    """Volta todos os filtros ao padrão e mostra todos os registros."""
    S.suspender_filtros = True
    T.var_pesquisa.set("")
    T.var_empresa.set("")
    T.var_data_ini.set("")
    T.var_data_fim.set("")
    T.var_filtro_tipo.set("Todos")
    T.var_filtro_situacao.set("Todos")
    T.var_filtro_periodo.set("Todos")
    T.var_filtro_motivo.set("Todos")
    S.suspender_filtros = False
    atualizar_tabela()
    mostrar_status("Filtros limpos.", "info")


# ======================================================================
# INTERFACE: TABELA PRINCIPAL, PAINEL DE DETALHES E AÇÕES
# ======================================================================
def criar_tabela(pai):
    """Tabela de registros (ttk.Treeview) com rolagem vertical e horizontal."""
    cartao = tk.Frame(pai, highlightthickness=1)
    registrar(cartao, bg="card", highlightbackground="borda")
    cartao.grid(row=0, column=0, sticky="nsew")
    cartao.rowconfigure(0, weight=1)
    cartao.columnconfigure(0, weight=1)

    nomes = [coluna[0] for coluna in COLUNAS_TABELA]
    T.tabela = ttk.Treeview(cartao, columns=nomes, show="headings",
                            selectmode="extended")
    for nome, titulo, largura, minimo, alinhamento, estica in COLUNAS_TABELA:
        # Clicar no cabeçalho ordena a tabela por essa coluna
        T.tabela.heading(nome, text=titulo, command=lambda c=nome: ordenar_por(c))
        T.tabela.column(nome, width=largura, minwidth=minimo, anchor=alinhamento,
                        stretch=estica)

    barra_v = ttk.Scrollbar(cartao, orient="vertical", command=T.tabela.yview)
    barra_h = ttk.Scrollbar(cartao, orient="horizontal", command=T.tabela.xview)
    T.tabela.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
    T.tabela.grid(row=0, column=0, sticky="nsew")
    barra_v.grid(row=0, column=1, sticky="ns")
    barra_h.grid(row=1, column=0, sticky="ew")

    # Mensagem mostrada por cima da tabela quando não há linhas
    T.rotulo_vazio = criar_rotulo(T.tabela, "", "card", "suave", (FONTE, 11),
                                  justify="center")

    T.tabela.bind("<Double-1>", duplo_clique)                       # editar
    T.tabela.bind("<<TreeviewSelect>>", lambda e: atualizar_detalhes())
    T.tabela.bind("<Button-3>", abrir_menu_contexto)                # botão direito
    aplicar_colunas_visiveis()


def aplicar_colunas_visiveis():
    """Mostra ou esconde as colunas opcionais (Motivo e Veículo)."""
    visiveis = [c[0] for c in COLUNAS_TABELA
                if not (c[0] == "Motivo" and not config["mostrar_motivo"])
                and not (c[0] == "Veiculo" and not config["mostrar_veiculo"])]
    T.tabela.configure(displaycolumns=visiveis)


def criar_detalhes(pai):
    """Painel lateral com todos os dados do registro selecionado."""
    cartao, conteudo, _ = criar_cartao(pai, "Registro selecionado")
    cartao.grid(row=0, column=1, sticky="ns", padx=(10, 0))
    T.detalhes = criar_texto(conteudo, altura=10, largura=34)
    barra = ttk.Scrollbar(conteudo, orient="vertical", command=T.detalhes.yview)
    T.detalhes.configure(yscrollcommand=barra.set)
    T.detalhes.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")


def criar_barra_acoes(pai):
    """Barra de ações no topo da aba: o cadastro é aberto por aqui."""
    faixa = criar_quadro(pai, "fundo")
    faixa.pack(fill="x", pady=(0, 8))
    criar_botao(faixa, "+ Nova entrada", nova_entrada, "verde", 18).pack(side="left")
    criar_botao(faixa, "Registrar saída", registrar_saida, "azul", 16)\
        .pack(side="left", padx=8)
    criar_botao(faixa, "Editar selecionado", editar, "amarelo", 18).pack(side="left")
    criar_botao(faixa, "Excluir selecionado", excluir, "vermelho", 18)\
        .pack(side="left", padx=8)
    criar_botao(faixa, "Exportar filtrados", lambda: exportar("filtrados"), "cinza", 16)\
        .pack(side="left")
    criar_rotulo(faixa, "Ctrl+N nova • Ctrl+R saída • Ctrl+E editar • Del excluir • "
                        "Ctrl+F pesquisar", "fundo", "suave", (FONTE, 9)).pack(side="right")


def criar_aba_portaria(aba):
    """Aba principal: dashboard, ações, filtros e a tabela (que ocupa o espaço restante)."""
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    criar_dashboard(corpo)
    criar_barra_acoes(corpo)
    criar_filtros(corpo)
    area = criar_quadro(corpo, "fundo")
    area.pack(fill="both", expand=True)
    area.rowconfigure(0, weight=1)
    area.columnconfigure(0, weight=1)
    criar_tabela(area)
    criar_detalhes(area)


# ======================================================================
# ATUALIZAÇÃO DA TABELA, INDICADORES E DETALHES
# ======================================================================
def valores_linha(r, agora_dt):
    """Valores de um registro, na ordem das colunas da tabela."""
    return (formatar_id(r["id"]), r["nome"], r["tipo"], r["entrada"], r["saida"],
            calcular_permanencia(r, agora_dt), texto_situacao(r, agora_dt),
            r["motivo"], formatar_placa(r["placa"]))


def tag_linha(r, agora_dt):
    """Cor da linha: alerta (tempo excedido), dentro ou saiu."""
    if excedeu_limite(r, agora_dt):
        return "alerta"
    return "dentro" if r["saida"] == "" else "saiu"


def atualizar_tabela():
    """Redesenha a tabela (filtrada e ordenada) e atualiza tudo que depende dela."""
    selecionados = T.tabela.selection()
    for item in T.tabela.get_children():
        T.tabela.delete(item)

    agora_dt = datetime.now()
    S.dia_tabela = agora_dt.date()
    visiveis = filtrar_registros(registros, criterios_atuais(), S.dia_tabela)
    visiveis.sort(key=lambda r: chave_ordenacao(r, S.coluna_ordenada, agora_dt),
                  reverse=S.ordem_decrescente)
    for r in visiveis:
        T.tabela.insert("", tk.END, iid=str(r["id"]), values=valores_linha(r, agora_dt),
                        tags=(tag_linha(r, agora_dt),))

    # Mantém selecionados os registros que continuam visíveis
    for item in selecionados:
        if T.tabela.exists(item):
            T.tabela.selection_add(item)

    atualizar_mensagem_vazia(len(visiveis))
    atualizar_indicadores()
    atualizar_contagem(len(visiveis))
    atualizar_detalhes()


def atualizar_tempos():
    """A cada minuto: atualiza permanência e alertas SEM redesenhar a tabela inteira."""
    agora_dt = datetime.now()
    if S.dia_tabela != agora_dt.date():   # virou o dia: "Hoje"/"Ontem" mudaram
        atualizar_tabela()
        return
    for item in T.tabela.get_children():
        r = buscar_registro(int(item))
        if r is None:
            continue
        T.tabela.set(item, "Permanencia", calcular_permanencia(r, agora_dt))
        T.tabela.set(item, "Situacao", texto_situacao(r, agora_dt))
        T.tabela.item(item, tags=(tag_linha(r, agora_dt),))
    atualizar_indicadores()
    atualizar_contagem(len(T.tabela.get_children()))
    atualizar_detalhes()


def atualizar_mensagem_vazia(quantidade_visivel):
    """Mensagem amigável quando a tabela não tem linhas."""
    if quantidade_visivel > 0:
        T.rotulo_vazio.place_forget()
        return
    if registros:
        texto = ("Nenhum registro corresponde à pesquisa ou aos filtros.\n"
                 "Use \"Limpar filtros\" para ver todos os registros.")
    else:
        texto = "Nenhum registro cadastrado ainda.\nClique em \"+ Nova entrada\" para começar."
    T.rotulo_vazio.configure(text=texto)
    T.rotulo_vazio.place(relx=0.5, rely=0.5, anchor="center")


def atualizar_indicadores():
    """Recalcula os indicadores a partir dos registros."""
    indicadores = calcular_indicadores(registros)
    for chave, variavel in T.var_ind.items():
        variavel.set(str(indicadores[chave]))


def atualizar_contagem(quantidade_visivel):
    """Texto da barra de status: 'Exibindo X de Y' e quantidade de alertas."""
    agora_dt = datetime.now()
    alertas = sum(1 for r in registros if excedeu_limite(r, agora_dt))
    texto = f"Exibindo {quantidade_visivel} de {len(registros)} registros"
    if alertas:
        texto += f"   •   ⚠ {alertas} acima do tempo máximo ({config['tempo_max_horas']}h)"
    T.rotulo_contagem.configure(text=texto)


def atualizar_detalhes():
    """Mostra no painel lateral os dados do registro selecionado."""
    selecionados = T.tabela.selection()
    if len(selecionados) == 0:
        escrever_texto(T.detalhes, [("Nenhum registro selecionado.\n\n", "valor"),
                                    ("Clique em uma linha da tabela para ver os "
                                     "detalhes da pessoa.", "suave")])
        return
    if len(selecionados) > 1:
        escrever_texto(T.detalhes, [(f"{len(selecionados)} registros selecionados.\n\n",
                                     "valor"),
                                    ("Selecione apenas um para ver os detalhes.", "suave")])
        return

    r = buscar_registro(int(selecionados[0]))
    if r is None:
        return
    agora_dt = datetime.now()
    pares = [("ID", formatar_id(r["id"])), ("Nome", r["nome"]),
             ("Tipo de acesso", r["tipo"]), ("Entrada", r["entrada"]),
             ("Saída", r["saida"]), ("Permanência", calcular_permanencia(r, agora_dt)),
             ("Situação", calcular_situacao(r).upper()), ("Motivo", r["motivo"]),
             ("Telefone", r["telefone"]), ("Empresa", r["empresa"]),
             ("Pessoa visitada", r["visitado"]), ("Placa", formatar_placa(r["placa"])),
             ("Modelo", r["modelo"]), ("Cor", r["cor"]),
             ("Observações", r["observacoes"])]
    partes = []
    if excedeu_limite(r, agora_dt):
        partes.append((f"⚠ Tempo máximo ({config['tempo_max_horas']}h) excedido\n\n",
                       "alerta"))
    for rotulo, valor in pares:
        partes.append((rotulo + ":  ", "chave"))
        partes.append(((valor or "—") + "\n", "valor"))
    escrever_texto(T.detalhes, partes)


def selecionar_registro(numero_id):
    """Seleciona e mostra um registro na tabela (se ele estiver visível)."""
    item = str(numero_id)
    if T.tabela.exists(item):
        T.tabela.selection_set(item)
        T.tabela.see(item)


def ordenar_por(coluna):
    """Clique no cabeçalho: ordena; clicar de novo inverte a ordem."""
    if coluna == S.coluna_ordenada:
        S.ordem_decrescente = not S.ordem_decrescente
    else:
        S.coluna_ordenada = coluna
        S.ordem_decrescente = False
    atualizar_cabecalhos()
    atualizar_tabela()


def atualizar_cabecalhos():
    """Mostra a seta ▲ (crescente) ou ▼ (decrescente) na coluna ordenada."""
    for nome, titulo, *_ in COLUNAS_TABELA:
        seta = ""
        if nome == S.coluna_ordenada:
            seta = " ▼" if S.ordem_decrescente else " ▲"
        T.tabela.heading(nome, text=titulo + seta)


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


# ======================================================================
# FLUXO: REGISTRO DE SAÍDA E EXCLUSÃO
# ======================================================================
def registrar_saida(evento=None):
    """Coloca a data/hora atual como saída do registro selecionado."""
    ir_para_aba("portaria")
    selecionados = T.tabela.selection()
    if len(selecionados) == 0:
        messagebox.showwarning("Atenção", "Selecione uma pessoa que esteja dentro.")
        return
    if len(selecionados) > 1:
        messagebox.showwarning(
            "Atenção", "Selecione apenas uma pessoa para registrar a saída.")
        return

    numero_id = int(selecionados[0])
    ok, resultado = operacao_registrar_saida(numero_id, agora_texto())
    if not ok:
        if resultado == "JA_TEM_SAIDA":
            messagebox.showinfo("Registrar saída",
                                "Este registro já possui uma saída.\n"
                                "Para corrigir o horário, use \"Editar selecionado\".",
                                parent=pai_mensagens())
        elif "Erro semântico" in str(resultado) or "não existe" in str(resultado):
            messagebox.showerror("Registrar saída", resultado, parent=pai_mensagens())
        else:
            avisar_falha_ao_salvar(resultado)
        return

    depois_de_alterar_dados()
    selecionar_registro(numero_id)
    mostrar_status(f"Saída de {resultado['nome']} registrada às "
                   f"{resultado['saida'][-5:]} (permanência "
                   f"{calcular_permanencia(resultado)}).")


def excluir(evento=None):
    """Exclui um ou mais registros selecionados, após confirmação."""
    ir_para_aba("portaria")
    selecionados = T.tabela.selection()
    if len(selecionados) == 0:
        messagebox.showwarning("Atenção", "Selecione um registro para excluir.")
        return

    ids = [int(item) for item in selecionados]
    nomes = [r["nome"] for r in (buscar_registro(i) for i in ids) if r is not None]
    lista = ", ".join(nomes[:5]) + (f" e mais {len(nomes) - 5}" if len(nomes) > 5 else "")
    if not messagebox.askyesno(
            "Confirmar exclusão",
            "Deseja realmente excluir o(s) registro(s) selecionado(s)?\n\n"
            f"{lista}\n\nEsta ação não pode ser desfeita "
            "(o histórico de atividades é mantido)."):
        return

    ok, resultado = operacao_excluir(ids)
    if not ok:
        avisar_falha_ao_salvar(resultado)
        return
    depois_de_alterar_dados()
    mostrar_status("Registro(s) excluído(s) com sucesso.")


# ======================================================================
# FLUXO: EXPORTAÇÃO
# ======================================================================
def preparar_exportacao(tipo):
    """Retorna (cabeçalho, linhas, nome sugerido, descrição) da exportação pedida."""
    carimbo = datetime.now().strftime("%Y%m%d_%H%M")
    if tipo == "filtrados":
        lista = filtrar_registros(registros, criterios_atuais())
        cabecalho, linhas = linhas_exportacao_registros(lista)
        return cabecalho, linhas, f"registros_filtrados_{carimbo}.csv", \
            "Registros filtrados"
    cabecalho, linhas = linhas_exportacao_historico(eventos_do_historico())
    return cabecalho, linhas, f"historico_{carimbo}.csv", "Histórico de atividades"


def exportar(tipo):
    """Pede o local do arquivo e exporta. Não modifica o arquivo principal."""
    cabecalho, linhas, sugestao, descricao = preparar_exportacao(tipo)
    if not linhas:
        messagebox.showinfo("Exportar", f"{descricao}: não há dados para exportar.")
        return
    destino = filedialog.asksaveasfilename(
        title=f"Exportar: {descricao}", defaultextension=".csv",
        initialfile=sugestao, initialdir=PASTA_DADOS,
        filetypes=[("CSV (abre no Excel)", "*.csv")])
    if not destino:
        return
    if eh_arquivo_do_sistema(destino):
        messagebox.showerror("Exportar", "Escolha outro nome: este arquivo é usado "
                                         "pelo próprio sistema e não pode ser substituído.")
        return
    ok, erro = exportar_csv(destino, cabecalho, linhas)
    if not ok:
        messagebox.showerror("Erro na exportação",
                             f"Não foi possível gravar o arquivo.\n\nDetalhe: {erro}")
        return
    registrar_historico("Exportação", "", "",
                        f"{descricao}: {len(linhas)} linha(s) → {os.path.basename(destino)}")
    atualizar_historico()
    mostrar_status(f"{descricao}: {len(linhas)} linha(s) exportada(s) para "
                   f"{os.path.basename(destino)}.")


# ======================================================================
# MENU DE CONTEXTO (botão direito na tabela)
# ======================================================================
def criar_menu_contexto():
    """Menu com as ações principais sobre o registro."""
    T.menu_contexto = tk.Menu(T.janela, tearoff=0)
    registrar(T.menu_contexto, bg="card", fg="texto", activebackground="selecao",
              activeforeground="texto")
    T.menu_contexto.add_command(label="Editar", command=editar)
    T.menu_contexto.add_command(label="Registrar saída", command=registrar_saida)
    T.menu_contexto.add_separator()
    T.menu_contexto.add_command(label="Excluir", command=excluir)


def abrir_menu_contexto(evento):
    """Seleciona a linha clicada (se necessário) e abre o menu."""
    item = T.tabela.identify_row(evento.y)
    if not item:
        return
    if item not in T.tabela.selection():
        T.tabela.selection_set(item)
    try:
        T.menu_contexto.tk_popup(evento.x_root, evento.y_root)
    finally:
        T.menu_contexto.grab_release()


def preencher_tabela(tabela, linhas):
    """Substitui todas as linhas de uma tabela simples."""
    for item in tabela.get_children():
        tabela.delete(item)
    for linha in linhas:
        tabela.insert("", tk.END, values=linha)


# ======================================================================
# INTERFACE: ABA HISTÓRICO
# ======================================================================
def eventos_do_historico():
    """Eventos do histórico que atendem aos filtros da aba Histórico."""
    return filtrar_historico(ler_historico(), T.var_hist_texto.get(),
                            T.var_hist_acao.get(),
                            converter_data_simples(T.var_hist_ini.get()),
                            converter_data_simples(T.var_hist_fim.get()))


def criar_aba_historico(aba):
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    T.var_hist_texto = tk.StringVar()
    T.var_hist_acao = tk.StringVar(value="Todas")
    T.var_hist_ini = tk.StringVar()
    T.var_hist_fim = tk.StringVar()

    cartao, conteudo, _ = criar_cartao(corpo, "Histórico de atividades")
    cartao.pack(fill="x", pady=(0, 8))
    linha = criar_quadro(conteudo)
    linha.pack(fill="x")
    linha.columnconfigure(1, weight=1)
    criar_rotulo(linha, "Pesquisar:").grid(row=0, column=0, sticky="w")
    campo = criar_campo_texto(linha, T.var_hist_texto)
    campo.grid(row=0, column=1, sticky="ew", ipady=4, padx=(8, 12))
    criar_rotulo(linha, "Ação:").grid(row=0, column=2, sticky="w")
    lista = criar_lista(linha, T.var_hist_acao, ["Todas"] + ACOES_HISTORICO, 12)
    lista.grid(row=0, column=3, padx=(6, 12))
    lista.bind("<<ComboboxSelected>>", lambda e: atualizar_historico())
    criar_rotulo(linha, "De:").grid(row=0, column=4, sticky="w")
    campo_ini = criar_campo_texto(linha, T.var_hist_ini)
    campo_ini.configure(width=11)
    campo_ini.grid(row=0, column=5, ipady=3, padx=(6, 10))
    criar_rotulo(linha, "Até:").grid(row=0, column=6, sticky="w")
    campo_fim = criar_campo_texto(linha, T.var_hist_fim)
    campo_fim.configure(width=11)
    campo_fim.grid(row=0, column=7, ipady=3, padx=(6, 12))
    criar_botao(linha, "Limpar", limpar_filtros_historico, "cinza", 9)\
        .grid(row=0, column=8, padx=(0, 6))
    criar_botao(linha, "Exportar", lambda: exportar("historico"), "azul", 10)\
        .grid(row=0, column=9)

    T.var_hist_texto.trace_add("write", lambda *a: atualizar_historico())
    for variavel, campo_data in ((T.var_hist_ini, campo_ini), (T.var_hist_fim, campo_fim)):
        variavel.trace_add("write", lambda *a, var=variavel, cp=campo_data:
                           (aplicar_mascara(var, cp, MASCARA_DATA[0], MASCARA_DATA[1]),
                            atualizar_historico()))

    criar_rotulo(corpo, "O histórico é um registro local: quem tem acesso à pasta do "
                        "programa pode editar o arquivo historico.csv. Não é uma "
                        "auditoria inviolável. Excluir um registro não apaga o seu histórico.",
                 "fundo", "suave", (FONTE, 9), wraplength=1000, justify="left")\
        .pack(side="bottom", anchor="w", pady=(6, 0))

    quadro, T.tabela_historico = criar_tabela_simples(
        corpo, [("data", "Data/Hora", 140, "center"), ("acao", "Ação", 90, "center"),
                ("id", "ID", 50, "center"), ("nome", "Nome", 180, "w"),
                ("descricao", "Descrição", 520, "w")], 12)
    quadro.pack(fill="both", expand=True)
    T.rotulo_hist = criar_rotulo(corpo, "", "fundo", "suave", (FONTE, 9))
    T.rotulo_hist.pack(side="bottom", anchor="e")


def atualizar_historico():
    """Recarrega o histórico respeitando os filtros da aba."""
    if not hasattr(T, "tabela_historico"):
        return
    eventos = eventos_do_historico()
    preencher_tabela(T.tabela_historico, [(e["data"], e["acao"], e["id"], e["nome"],
                                           e["descricao"]) for e in eventos])
    T.rotulo_hist.configure(text=f"{len(eventos)} evento(s) exibido(s)")


def limpar_filtros_historico():
    T.var_hist_texto.set("")
    T.var_hist_acao.set("Todas")
    T.var_hist_ini.set("")
    T.var_hist_fim.set("")
    atualizar_historico()


# ======================================================================
# INTERFACE: ABAS CONFIGURAÇÕES E SOBRE
# ======================================================================
def criar_aba_configuracoes(aba):
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    cartao, conteudo, _ = criar_cartao(corpo, "Configurações")
    cartao.pack(fill="x")

    T.var_config_tema = tk.StringVar(value=config["tema"].capitalize())
    T.var_config_tempo = tk.StringVar(value=str(config["tempo_max_horas"]))
    T.var_config_alerta = tk.BooleanVar(value=config["alerta_ativo"])
    T.var_config_motivo = tk.BooleanVar(value=config["mostrar_motivo"])
    T.var_config_veiculo = tk.BooleanVar(value=config["mostrar_veiculo"])

    criar_rotulo(conteudo, "Tema:").grid(row=0, column=0, sticky="w", pady=6)
    criar_lista(conteudo, T.var_config_tema, ["Claro", "Escuro"], 12)\
        .grid(row=0, column=1, sticky="w", padx=10)
    criar_rotulo(conteudo, "Tempo máximo de permanência (horas):")\
        .grid(row=1, column=0, sticky="w", pady=6)
    ttk.Spinbox(conteudo, from_=1, to=72, width=6, textvariable=T.var_config_tempo)\
        .grid(row=1, column=1, sticky="w", padx=10)
    ttk.Checkbutton(conteudo, text="Alertar quando a permanência passar do tempo máximo",
                    variable=T.var_config_alerta).grid(row=2, column=0, columnspan=3,
                                                       sticky="w", pady=6)
    criar_rotulo(conteudo, "Colunas opcionais da tabela:")\
        .grid(row=3, column=0, sticky="w", pady=(10, 0))
    ttk.Checkbutton(conteudo, text="Mostrar a coluna Motivo",
                    variable=T.var_config_motivo).grid(row=4, column=0, columnspan=3,
                                                       sticky="w")
    ttk.Checkbutton(conteudo, text="Mostrar a coluna Veículo (placa)",
                    variable=T.var_config_veiculo).grid(row=5, column=0, columnspan=3,
                                                        sticky="w")
    criar_botao(conteudo, "Salvar configurações", salvar_configuracoes_da_tela,
                "verde", 22).grid(row=6, column=0, sticky="w", pady=(14, 0))
    criar_rotulo(conteudo, f"As configurações ficam em {ARQ_CONFIG}, na pasta:\n"
                           f"{PASTA_DADOS}", "card", "suave", (FONTE, 9), justify="left")\
        .grid(row=7, column=0, columnspan=3, sticky="w", pady=(12, 0))


def salvar_configuracoes_da_tela():
    """Valida e aplica as configurações escolhidas."""
    try:
        horas = int(T.var_config_tempo.get())
    except ValueError:
        horas = 0
    if not 1 <= horas <= 72:
        messagebox.showwarning("Tempo máximo inválido",
                               "Informe um número inteiro de horas entre 1 e 72.")
        return

    novas = {"tema": T.var_config_tema.get().lower(), "tempo_max_horas": horas,
             "alerta_ativo": bool(T.var_config_alerta.get()),
             "mostrar_motivo": bool(T.var_config_motivo.get()),
             "mostrar_veiculo": bool(T.var_config_veiculo.get())}
    alteracoes = [f"{chave}: {config[chave]} → {valor}"
                  for chave, valor in novas.items() if config[chave] != valor]
    config.update(novas)
    atualizar_opcoes_situacao()

    if not salvar_configuracoes():
        messagebox.showerror("Erro ao salvar",
                             "Não foi possível gravar o arquivo de configurações. "
                             "As mudanças valem apenas até fechar o programa.")
    else:
        mostrar_status("Configurações salvas.")
    if alteracoes:
        registrar_historico("Configuração", "", "", "; ".join(alteracoes))
    aplicar_tema()
    aplicar_colunas_visiveis()
    atualizar_tabela()
    atualizar_historico()


def atualizar_opcoes_situacao():
    """Troca as opções do filtro de situação quando o alerta é ligado/desligado."""
    opcoes = opcoes_filtro_situacao()
    T.lista_situacao.configure(values=opcoes)
    if T.var_filtro_situacao.get() not in opcoes:
        T.var_filtro_situacao.set("Todos")


def criar_aba_sobre(aba):
    corpo = criar_quadro(aba, "fundo")
    corpo.pack(fill="both", expand=True, padx=2, pady=8)
    cartao, conteudo, _ = criar_cartao(corpo, "Sobre o sistema e ajuda")
    cartao.pack(fill="both", expand=True)
    texto = criar_texto(conteudo, altura=20, largura=80)
    texto.pack(fill="both", expand=True)
    escrever_texto(texto, [
        (f"Cadastro de Portaria - Controle de entrada e saída (versão {VERSAO})\n", "titulo"),
        ("Trabalho da UC Teoria da Computação e Compiladores - Faculdade UNA.\n"
         "Sistema local feito apenas com bibliotecas do Python (Tkinter, csv, json...).\n\n",
         "normal"),
        ("Atalhos de teclado\n", "titulo"),
        ("Ctrl+N  nova entrada (abre a janela)   Ctrl+F  pesquisar   Ctrl+L  limpar filtros\n"
         "Ctrl+E  editar selecionado     Ctrl+R  registrar saída\n"
         "Delete  excluir (com a tabela em foco)   Enter  confirmar/editar\n"
         "Na janela de cadastro: Ctrl+S ou Enter salvam; Esc cancela.\n\n",
         "codigo"),
        ("Arquivos criados (na pasta do programa)\n", "titulo"),
        (f"{ARQ_REGISTROS}: registros principais (ID, nome, tipo, entrada, saída e dados extras).\n"
         f"{ARQ_BACKUP}: cópia do arquivo anterior, atualizada a cada salvamento.\n"
         "registros_original_*.csv: cópia do arquivo original guardada antes de migração ou correção.\n"
         f"{ARQ_HISTORICO}: histórico de atividades (cadastro, edição, saída, exclusão...).\n"
         f"{ARQ_CONFIG}: tema, tempo máximo, alertas, colunas e último ID usado.\n"
         "Arquivos exportados: no local e com o nome que você escolher.\n\n", "normal"),
        ("Observações\n", "titulo"),
        ("• Situação e permanência são calculadas na hora; não são salvas no CSV.\n"
         "• O histórico é um registro local e pode ser editado por quem acessa a pasta.\n"
         "• O backup guarda sempre a versão imediatamente anterior do arquivo.\n"
         "• O controle de vagas de estacionamento não foi implementado.\n", "normal"),
    ])
    criar_botao(conteudo, "Abrir pasta dos arquivos", abrir_pasta_dados, "cinza", 24)\
        .pack(anchor="w", pady=(8, 0))


def abrir_pasta_dados():
    """Abre a pasta dos arquivos no Explorador do Windows."""
    try:
        os.startfile(PASTA_DADOS)                 # só existe no Windows
    except (AttributeError, OSError):
        messagebox.showinfo("Pasta dos arquivos", PASTA_DADOS)


# ======================================================================
# NAVEGAÇÃO (abas)
# ======================================================================
ABAS = [("portaria", "  Portaria  ", criar_aba_portaria),
        ("historico", "  Histórico  ", criar_aba_historico),
        ("configuracoes", "  Configurações  ", criar_aba_configuracoes),
        ("sobre", "  Sobre / Ajuda  ", criar_aba_sobre)]


def criar_abas():
    T.abas = ttk.Notebook(T.janela)
    T.abas.pack(fill="both", expand=True, padx=14, pady=(10, 4))
    T.quadros_abas = {}
    for chave, titulo, construtor in ABAS:
        quadro = criar_quadro(T.abas, "fundo")
        T.abas.add(quadro, text=titulo)
        T.quadros_abas[chave] = quadro
        construtor(quadro)
    T.abas.bind("<<NotebookTabChanged>>", lambda e: ao_mudar_aba())


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


def ao_mudar_aba():
    chave = aba_atual()
    if chave == "historico":
        atualizar_historico()


# ======================================================================
# ATALHOS DE TECLADO
# ======================================================================
def focar_pesquisa(evento=None):
    """Ctrl+F: leva o cursor para o campo de pesquisa."""
    ir_para_aba("portaria")
    T.campo_pesquisa.focus_set()
    T.campo_pesquisa.select_range(0, tk.END)


def atalho_salvar(evento=None):
    """Ctrl+S na janela principal: salva as configurações (o cadastro tem o seu próprio Ctrl+S)."""
    if aba_atual() == "configuracoes":
        salvar_configuracoes_da_tela()


def atalho_limpar_filtros(evento=None):
    ir_para_aba("portaria")
    limpar_filtros()


def configurar_atalhos():
    """
    Liga as teclas às funções. Delete só funciona com a tabela em foco, para
    não apagar letras de quem está digitando em um campo de texto.
    """
    atalhos = {"n": nova_entrada, "f": focar_pesquisa, "s": atalho_salvar,
               "e": editar, "r": registrar_saida, "l": atalho_limpar_filtros}
    for letra, funcao in atalhos.items():
        T.janela.bind(f"<Control-{letra}>", funcao)
        T.janela.bind(f"<Control-{letra.upper()}>", funcao)

    T.tabela.bind("<Delete>", excluir)
    T.tabela.bind("<Return>", editar)
    for campo in T.campos.values():
        campo.bind("<Return>", salvar_formulario)       # Enter confirma o formulário
    T.campo_pesquisa.bind("<Return>", lambda e: T.tabela.focus_set())


# ======================================================================
# FECHAMENTO E INICIALIZAÇÃO
# ======================================================================
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


def ao_fechar():
    """Pede confirmação se a janela de cadastro estiver aberta com dados não salvos."""
    if S.formulario_aberto and formulario_tem_alteracoes() and not messagebox.askyesno(
            "Sair do sistema",
            "Há dados no formulário que ainda não foram salvos.\n"
            "Deseja sair mesmo assim?", parent=pai_mensagens()):
        return
    T.janela.destroy()


def mostrar_avisos_carregamento(avisos):
    """Mostra, de forma amigável, os avisos encontrados ao abrir o CSV."""
    detalhes = avisos[:8]
    if len(avisos) > 8:
        detalhes.append(f"... e mais {len(avisos) - 8} aviso(s).")
    messagebox.showwarning("Atenção ao carregar os registros",
                           "\n\n".join(detalhes))


def criar_interface():
    """Monta a tela inteira."""
    criar_janela()
    criar_cabecalho()
    criar_barra_status()
    criar_abas()
    criar_janela_formulario()
    criar_menu_contexto()
    aplicar_tema()


def iniciar():
    carregar_configuracoes()
    criar_interface()
    avisos = carregar_registros()
    limpar_formulario()
    atualizar_cabecalhos()
    atualizar_tabela()
    atualizar_historico()
    configurar_atalhos()
    atualizar_relogio()
    if avisos:
        mostrar_avisos_carregamento(avisos)
    T.janela.mainloop()


if __name__ == "__main__":
    iniciar()