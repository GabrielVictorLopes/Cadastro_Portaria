"""Atualização da tabela, dos indicadores, dos detalhes e do histórico."""

from datetime import datetime
import tkinter as tk

from nucleo.constantes import COLUNAS_TABELA
from nucleo.estado import S, T, config, registros
from nucleo.utilitarios import (
    buscar_registro, converter_data_simples, formatar_id, formatar_placa)
from nucleo.calculos import (
    calcular_permanencia, calcular_situacao, excedeu_limite, texto_situacao)
from nucleo.persistencia import filtrar_historico, ler_historico
from nucleo.consultas import calcular_indicadores, chave_ordenacao, filtrar_registros
from interface.base import escrever_texto, mostrar_status, preencher_tabela


def criterios_atuais():
    """Lê os filtros da tela."""
    return {"texto": T.var_pesquisa.get(), "tipo": T.var_filtro_tipo.get(),
            "situacao": T.var_filtro_situacao.get(),
            "periodo": T.var_filtro_periodo.get(),
            "data_ini": converter_data_simples(T.var_data_ini.get()),
            "data_fim": converter_data_simples(T.var_data_fim.get()),
            "motivo": T.var_filtro_motivo.get(), "empresa": T.var_empresa.get()}


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
    if T.var_filtro_situacao.get() in ("No prazo", "Excedido"):
        # Com o tempo, quem estava "No prazo" passa a "Excedido": refiltra
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


def eventos_do_historico():
    """Eventos do histórico que atendem aos filtros da aba Histórico."""
    return filtrar_historico(ler_historico(), T.var_hist_texto.get(),
                            T.var_hist_acao.get(),
                            converter_data_simples(T.var_hist_ini.get()),
                            converter_data_simples(T.var_hist_fim.get()))


def atualizar_historico():
    """Recarrega o histórico respeitando os filtros da aba."""
    if not hasattr(T, "tabela_historico"):
        return
    eventos = eventos_do_historico()
    preencher_tabela(T.tabela_historico, [(e["data"], e["acao"], e["id"], e["nome"],
                                           e["descricao"]) for e in eventos])
    T.rotulo_hist.configure(text=f"{len(eventos)} evento(s) exibido(s)")
    if S.falha_historico:
        S.falha_historico = False
        mostrar_status("Atenção: a última atividade não pôde ser gravada no histórico "
                       "(historico.csv pode estar aberto em outro programa).", "erro")
