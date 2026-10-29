"""Constantes do sistema: arquivos, listas permitidas, limites, cores e colunas."""

import os
import re


# ======================================================================
# CONSTANTES
# ======================================================================
VERSAO = "3.1"

# Arquivos
# Pasta dos arquivos de dados: dados/, na pasta do projeto (um nível acima de nucleo/)
PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(PASTA_PROJETO, "dados")
ARQ_REGISTROS = "registros.csv"
ARQ_BACKUP = "registros_backup.csv"
ARQ_HISTORICO = "historico.csv"
ARQ_CONFIG = "configuracoes.json"
ARQ_TRAVA = "portaria.lock"     # impede duas cópias do programa abertas ao mesmo tempo

FORMATO_DATA_HORA = "%d/%m/%Y %H:%M"          # 06/10/2026 09:30
FORMATO_DATA = "%d/%m/%Y"                     # 06/10/2026
FORMATO_EVENTO = "%d/%m/%Y %H:%M:%S"          # usado no histórico
ANO_MINIMO = 2000

# Listas permitidas
TIPOS = ["Visitante", "Morador", "Entregador", "Funcionário"]
MOTIVOS = ["Visita", "Entrega", "Serviço", "Reunião", "Manutenção",
           "Moradia", "Outro"]
FILTRO_TIPOS = ["Todos"] + TIPOS
# DDDs existentes no Brasil (plano de numeração da Anatel)
DDDS_VALIDOS = {
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "22", "24", "27",
    "28", "31", "32", "33", "34", "35", "37", "38", "41", "42", "43", "44", "45",
    "46", "47", "48", "49", "51", "53", "54", "55", "61", "62", "63", "64", "65",
    "66", "67", "68", "69", "71", "73", "74", "75", "77", "79", "81", "82", "83",
    "84", "85", "86", "87", "88", "89", "91", "92", "93", "94", "95", "96", "97",
    "98", "99"}
# Um texto que começa com um destes caracteres vira fórmula ao abrir o CSV no Excel
INICIO_FORMULA = ("=", "+", "-", "@", "\t", "\r")
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
