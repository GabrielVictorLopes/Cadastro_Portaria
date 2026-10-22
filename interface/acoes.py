"""Ações sobre os registros: registrar saída, excluir e exportar."""

import os
from datetime import datetime
from tkinter import filedialog, messagebox

from nucleo.constantes import PASTA_DADOS
from nucleo.estado import T, registros
from nucleo.utilitarios import agora_texto, buscar_registro
from nucleo.calculos import calcular_permanencia
from nucleo.persistencia import registrar_historico
from nucleo.operacoes import operacao_excluir, operacao_registrar_saida
from nucleo.consultas import filtrar_registros
from nucleo.exportacao import (
    eh_arquivo_do_sistema, exportar_csv, linhas_exportacao_historico,
    linhas_exportacao_registros)
from interface.base import ir_para_aba, mostrar_status
from interface.formulario import (
    avisar_falha_ao_salvar, depois_de_alterar_dados, pai_mensagens)
from interface.atualizacao import (
    atualizar_historico, criterios_atuais, eventos_do_historico, selecionar_registro)


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
