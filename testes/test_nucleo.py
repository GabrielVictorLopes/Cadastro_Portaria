"""
Testes automatizados do núcleo (sem interface gráfica).

Execute na pasta do projeto:
    python -m unittest discover -s testes -t . -v

Os testes de arquivos usam uma pasta temporária: a pasta dados/ real
nunca é lida nem alterada.
"""

import os
import shutil
import tempfile
import unittest
from datetime import date, datetime
from unittest import mock

from nucleo.constantes import CONFIG_PADRAO
from nucleo.estado import S, config, registros
from nucleo import calculos, consultas, exportacao, operacoes, persistencia, validacoes

AGORA = datetime(2026, 10, 29, 18, 0)
HOJE = AGORA.date()


def registro(**campos):
    """Registro completo com valores padrão (sobrescritos por 'campos')."""
    base = {"id": 1, "nome": "Ana Lima", "tipo": "Visitante", "motivo": "",
            "entrada": "29/10/2026 10:00", "saida": "", "telefone": "",
            "empresa": "", "visitado": "", "observacoes": "", "placa": "",
            "modelo": "", "cor": ""}
    base.update(campos)
    return base


def dados_formulario(**campos):
    dados = registro(**campos)
    del dados["id"]
    return dados


class BaseTeste(unittest.TestCase):
    """Zera o estado compartilhado antes de cada teste."""

    def setUp(self):
        registros.clear()
        config.clear()
        config.update(CONFIG_PADRAO)
        S.proximo_id = 1
        S.falha_historico = False


class BaseArquivos(BaseTeste):
    """Redireciona a pasta de dados para uma pasta temporária."""

    def setUp(self):
        super().setUp()
        self.pasta = tempfile.mkdtemp()
        for alvo in ("nucleo.utilitarios.PASTA_DADOS", "nucleo.exportacao.PASTA_DADOS"):
            patch = mock.patch(alvo, self.pasta)
            patch.start()
            self.addCleanup(patch.stop)
        self.addCleanup(shutil.rmtree, self.pasta, ignore_errors=True)

    def arquivo(self, nome):
        return os.path.join(self.pasta, nome)

    def escrever(self, nome, texto, codificacao="utf-8-sig"):
        with open(self.arquivo(nome), "w", encoding=codificacao, newline="") as f:
            f.write(texto)

    def ler(self, nome):
        with open(self.arquivo(nome), encoding="utf-8-sig") as f:
            return f.read()


# ======================================================================
# VALIDAÇÕES
# ======================================================================
class TesteValidacaoDatas(BaseTeste):
    def test_entrada_futura_recusada(self):
        self.assertFalse(validacoes.validar_datas("30/10/2026 08:00", "", AGORA)[0])

    def test_entrada_antes_de_2000_recusada(self):
        self.assertFalse(validacoes.validar_datas("31/12/1999 10:00", "", AGORA)[0])

    def test_saida_futura_recusada(self):
        ok, campo, _, _ = validacoes.validar_datas("29/10/2026 08:00", "30/10/2026 08:00", AGORA)
        self.assertEqual((ok, campo), (False, "saida"))

    def test_saida_antes_da_entrada_recusada(self):
        ok, campo, _, _ = validacoes.validar_datas("29/10/2026 10:00", "29/10/2026 09:59", AGORA)
        self.assertEqual((ok, campo), (False, "saida"))

    def test_saida_igual_a_entrada_aceita(self):
        self.assertTrue(validacoes.validar_datas("29/10/2026 10:00", "29/10/2026 10:00", AGORA)[0])

    def test_data_inexistente_recusada(self):
        self.assertFalse(validacoes.validar_datas("30/02/2026 10:00", "", AGORA)[0])

    def test_entrada_obrigatoria(self):
        self.assertEqual(validacoes.validar_datas("", "", AGORA)[1], "entrada")


class TesteValidacaoCampos(BaseTeste):
    def validar(self, **campos):
        return validacoes.validar_dados(dados_formulario(**campos), AGORA)

    def test_normalizacao(self):
        dados, erro = self.validar(nome=" Ana   Souza ", entrada="1/10/2026 9:05",
                                   placa="abc-1234", telefone="31987654321")
        self.assertIsNone(erro)
        self.assertEqual(dados["nome"], "Ana Souza")
        self.assertEqual(dados["entrada"], "01/10/2026 09:05")
        self.assertEqual(dados["placa"], "ABC1234")
        self.assertEqual(dados["telefone"], "(31) 98765-4321")

    def test_nomes(self):
        self.assertEqual(self.validar(nome="")[1][0], "nome")
        self.assertEqual(self.validar(nome="A")[1][0], "nome")
        self.assertEqual(self.validar(nome="Ana2")[1][0], "nome")
        self.assertEqual(self.validar(nome="A" * 61)[1][0], "nome")
        self.assertIsNone(self.validar(nome="Ana D'Ávila-Souza")[1])

    def test_tipo_e_motivo(self):
        self.assertEqual(self.validar(tipo="Gerente")[1][0], "tipo")
        self.assertEqual(self.validar(motivo="Passeio")[1][0], "motivo")
        self.assertIsNone(self.validar(motivo="")[1])

    def test_telefone(self):
        self.assertEqual(validacoes.validar_telefone("3133334444"), (True, "(31) 3333-4444"))
        self.assertEqual(validacoes.validar_telefone(""), (True, ""))
        self.assertFalse(validacoes.validar_telefone("319876543")[0])      # 9 dígitos
        self.assertFalse(validacoes.validar_telefone("31887654321")[0])    # celular sem 9
        self.assertFalse(validacoes.validar_telefone("0198765432")[0])     # DDD 01
        self.assertFalse(validacoes.validar_telefone("23987654321")[0])    # DDD 23 não existe

    def test_placa_e_cor(self):
        self.assertIsNone(self.validar(placa="ABC1D23")[1])
        self.assertEqual(self.validar(placa="AB12345")[1][0], "placa")
        self.assertEqual(self.validar(cor="Azul2")[1][0], "cor")

    def test_limites_de_tamanho(self):
        self.assertEqual(self.validar(empresa="x" * 61)[1][0], "empresa")
        self.assertEqual(self.validar(observacoes="x" * 201)[1][0], "observacoes")

    def test_texto_que_vira_formula_recusado(self):
        for valor in ("=HYPERLINK(\"http://x\")", "+1", "-2", "@SOMA(A1)"):
            with self.subTest(valor=valor):
                self.assertEqual(self.validar(observacoes=valor)[1][0], "observacoes")
        self.assertEqual(self.validar(empresa="=1+1")[1][0], "empresa")
        self.assertIsNone(self.validar(observacoes="Entrega - caixa grande")[1])

    def test_duplicidade(self):
        registros.append(registro(id=1, nome="Ana Lima"))
        self.assertTrue(validacoes.existe_duplicado(registro(nome="ANA LIMA")))
        self.assertFalse(validacoes.existe_duplicado(registro(nome="Ana Lima"), ignorar_id=1))
        self.assertFalse(validacoes.existe_duplicado(registro(entrada="29/10/2026 10:01")))


# ======================================================================
# CÁLCULOS
# ======================================================================
class TesteCalculos(BaseTeste):
    def test_permanencia(self):
        self.assertEqual(calculos.calcular_permanencia(
            registro(entrada="29/10/2026 09:30", saida="29/10/2026 11:05")), "01h 35min")
        self.assertEqual(calculos.calcular_permanencia(registro(entrada="29/10/2026 14:00"),
                                                       AGORA), "Em andamento — 04h 00min")
        self.assertEqual(calculos.calcular_permanencia(registro(entrada="29/10/2026 19:00"),
                                                       AGORA), "Em andamento")

    def test_alerta_compara_minutos_inteiros(self):
        dentro = registro(entrada="29/10/2026 14:00")
        self.assertFalse(calculos.excedeu_limite(dentro, AGORA))
        self.assertFalse(calculos.excedeu_limite(dentro, AGORA.replace(second=59)))
        self.assertTrue(calculos.excedeu_limite(registro(entrada="29/10/2026 13:59"), AGORA))

    def test_alerta_desligado_e_quem_saiu(self):
        antigo = registro(entrada="29/10/2026 08:00")
        config["alerta_ativo"] = False
        self.assertFalse(calculos.excedeu_limite(antigo, AGORA))
        config["alerta_ativo"] = True
        self.assertTrue(calculos.excedeu_limite(antigo, AGORA))
        self.assertFalse(calculos.excedeu_limite(registro(entrada="29/10/2026 08:00",
                                                          saida="29/10/2026 17:00"), AGORA))

    def test_filtro_de_situacao(self):
        excedido = registro(entrada="29/10/2026 08:00")
        no_prazo = registro(entrada="29/10/2026 17:00")
        self.assertTrue(calculos.situacao_confere(excedido, "No local", AGORA))
        self.assertTrue(calculos.situacao_confere(excedido, "Excedido", AGORA))
        self.assertFalse(calculos.situacao_confere(excedido, "No prazo", AGORA))
        self.assertTrue(calculos.situacao_confere(no_prazo, "No prazo", AGORA))


# ======================================================================
# CONSULTAS
# ======================================================================
class TesteConsultas(BaseTeste):
    def setUp(self):
        super().setUp()
        self.lista = [
            registro(id=7, nome="João Silva", telefone="(31) 98765-4321", placa="ABC1234",
                     observacoes="segredo"),
            registro(id=8, nome="Maria", tipo="Entregador", empresa="Rápido Express",
                     motivo="Entrega", entrada="28/10/2026 10:00", saida="28/10/2026 11:00"),
            registro(id=9, nome="Paulo", entrada="19/10/2026 10:00", saida="19/10/2026 11:00"),
        ]

    def ids(self, **criterios):
        c = consultas.criterios_padrao()
        c.update(criterios)
        return [r["id"] for r in consultas.filtrar_registros(self.lista, c, HOJE)]

    def test_pesquisa(self):
        self.assertEqual(self.ids(texto="joao"), [7])
        self.assertEqual(self.ids(texto="007"), [7])
        self.assertEqual(self.ids(texto="98765"), [7])
        self.assertEqual(self.ids(texto="abc-1234"), [7])
        self.assertEqual(self.ids(texto="segredo"), [])        # observações não entram

    def test_filtros_combinados(self):
        self.assertEqual(self.ids(tipo="Entregador", situacao="Saiu"), [8])
        self.assertEqual(self.ids(motivo="Entrega", empresa="rapido"), [8])

    def test_periodos(self):
        self.assertEqual(self.ids(periodo="Hoje"), [7])
        self.assertEqual(self.ids(periodo="Ontem"), [8])
        self.assertEqual(self.ids(periodo="Últimos 7 dias"), [7, 8])
        self.assertEqual(self.ids(periodo="Período personalizado",
                                  data_ini=date(2026, 10, 19), data_fim=None), [7, 8, 9])
        self.assertEqual(consultas.intervalo_periodo("Últimos 7 dias", HOJE),
                         (date(2026, 10, 23), HOJE))

    def test_indicadores(self):
        self.lista.append(registro(id=10, tipo="Funcionário"))
        ind = consultas.calcular_indicadores(self.lista, HOJE)
        self.assertEqual((ind["total"], ind["dentro"], ind["saiu"]), (4, 2, 2))
        self.assertEqual((ind["entradas_hoje"], ind["visitantes"], ind["funcionarios"]),
                         (2, 1, 1))

    def test_ordenacao_por_entrada_e_cronologica(self):
        ordem = sorted(self.lista, key=lambda r: consultas.chave_ordenacao(r, "Entrada"))
        self.assertEqual([r["id"] for r in ordem], [9, 8, 7])


# ======================================================================
# EXPORTAÇÃO
# ======================================================================
class TesteExportacao(BaseArquivos):
    def test_protecao_de_formula(self):
        self.assertEqual(exportacao.proteger_excel("=1+1"), "'=1+1")
        self.assertEqual(exportacao.proteger_excel("Texto"), "Texto")
        self.assertEqual(exportacao.proteger_excel(5), "5")

    def test_arquivos_do_sistema_protegidos(self):
        for nome in ("registros.csv", "REGISTROS.CSV", "historico.csv", "configuracoes.json",
                     "registros_backup.csv", "registros_original_1.csv",
                     "registros.csv.tmp", "portaria.lock"):
            with self.subTest(nome=nome):
                self.assertTrue(exportacao.eh_arquivo_do_sistema(self.arquivo(nome)))
        self.assertFalse(exportacao.eh_arquivo_do_sistema(self.arquivo("relatorio.csv")))

    def test_situacao_exportada_igual_a_tela(self):
        _, linhas = exportacao.linhas_exportacao_registros(
            [registro(entrada="29/10/2026 08:00"), registro(entrada="29/10/2026 17:00"),
             registro(saida="29/10/2026 11:00")], AGORA)
        self.assertEqual([l[6] for l in linhas], ["Excedido", "No local", "Saiu"])

    def test_gravacao_do_csv(self):
        destino = self.arquivo("saida.csv")
        ok, _ = exportacao.exportar_csv(destino, ["A", "B"], [["=x", "ção"]])
        self.assertTrue(ok)
        self.assertEqual(self.ler("saida.csv").splitlines(), ["A;B", "'=x;ção"])


# ======================================================================
# PERSISTÊNCIA E OPERAÇÕES
# ======================================================================
class TestePersistencia(BaseArquivos):
    CABECALHO = ("ID;Nome;Tipo de acesso;Entrada;Saída;Telefone;Empresa;"
                 "Pessoa visitada;Motivo;Observações;Placa;Modelo;Cor\n")

    def cadastrar(self, **campos):
        ok, novo = operacoes.operacao_cadastrar(dados_formulario(**campos))
        self.assertTrue(ok)
        return novo

    def test_cadastro_grava_e_recarrega(self):
        novo = self.cadastrar(nome="Ana Lima")
        self.assertEqual(novo["id"], 1)
        registros.clear()
        self.assertEqual(persistencia.carregar_registros(), [])
        self.assertEqual(registros[0]["nome"], "Ana Lima")
        self.assertIn("Cadastro", self.ler("historico.csv"))

    def test_backup_guarda_versao_anterior(self):
        self.cadastrar(nome="Primeira Pessoa")
        self.cadastrar(nome="Segunda Pessoa")
        self.assertNotIn("Segunda", self.ler("registros_backup.csv"))
        self.assertIn("Segunda", self.ler("registros.csv"))

    def test_falha_ao_gravar_desfaz_na_memoria(self):
        self.cadastrar(nome="Ana Lima")
        with mock.patch("nucleo.persistencia.os.replace", side_effect=OSError("bloqueado")):
            ok, erro = operacoes.operacao_cadastrar(dados_formulario(nome="Outra Pessoa"))
        self.assertFalse(ok)
        self.assertEqual(len(registros), 1)
        self.assertEqual(S.proximo_id, 2)
        self.assertFalse(os.path.exists(self.arquivo("registros.csv.tmp")))

    def test_registrar_saida(self):
        novo = self.cadastrar(entrada="29/10/2026 10:00")
        ok, _ = operacoes.operacao_registrar_saida(novo["id"], "29/10/2026 09:00")
        self.assertFalse(ok)                                  # antes da entrada
        self.assertTrue(operacoes.operacao_registrar_saida(novo["id"], "29/10/2026 11:00")[0])
        self.assertEqual(operacoes.operacao_registrar_saida(novo["id"], "29/10/2026 12:00"),
                         (False, "JA_TEM_SAIDA"))

    def test_edicao_registra_campos_alterados(self):
        novo = self.cadastrar()
        ok, _ = operacoes.operacao_editar(novo["id"], dados_formulario(empresa="Loja X"))
        self.assertTrue(ok)
        self.assertIn("Campos alterados: Empresa", self.ler("historico.csv"))

    def test_id_nao_reaproveitado_mesmo_sem_configuracoes(self):
        self.cadastrar()
        segundo = self.cadastrar()
        operacoes.operacao_excluir([segundo["id"]])
        os.remove(self.arquivo("configuracoes.json"))
        persistencia.carregar_configuracoes()
        persistencia.carregar_registros()
        self.assertEqual(self.cadastrar()["id"], 3)

    def test_tipo_sem_acento_e_corrigido(self):
        self.escrever("registros.csv", self.CABECALHO +
                      "1;Ana Lima;funcionario;01/10/2026 09:00;;;;;;;;;\n")
        persistencia.carregar_registros()
        self.assertEqual(registros[0]["tipo"], "Funcionário")

    def test_linha_invalida_ignorada_e_original_preservado(self):
        self.escrever("registros.csv", self.CABECALHO +
                      "1;Ana Lima;Gerente;01/10/2026 09:00;;;;;;;;;\n"
                      "2;Bia Souza;Visitante;01/10/2026 09:00;;;;;;;;;\n")
        avisos = persistencia.carregar_registros()
        self.assertEqual([r["id"] for r in registros], [2])
        self.assertTrue(any("Linha 2" in a for a in avisos))
        copias = [n for n in os.listdir(self.pasta) if n.startswith("registros_original_")]
        self.assertEqual(len(copias), 1)

    def test_migracao_de_formato_antigo(self):
        self.escrever("registros.csv", "Ana Lima;Visitante;1/10/2026 9:00;01/10/2026 10:00\n",
                      "cp1252")
        persistencia.carregar_registros()
        self.assertEqual(registros[0]["id"], 1)
        self.assertEqual(registros[0]["entrada"], "01/10/2026 09:00")
        self.assertTrue(self.ler("registros.csv").startswith("ID;Nome"))

    def test_ids_repetidos_recebem_novo_id(self):
        linha = "5;Ana Lima;Visitante;01/10/2026 09:00;;;;;;;;;\n"
        self.escrever("registros.csv", self.CABECALHO + linha + linha)
        persistencia.carregar_registros()
        self.assertEqual(sorted(r["id"] for r in registros), [5, 6])

    def test_configuracao_invalida_usa_padrao(self):
        self.escrever("configuracoes.json",
                      '{"tema": "roxo", "tempo_max_horas": 500, "alerta_ativo": "sim"}')
        persistencia.carregar_configuracoes()
        self.assertEqual(config, CONFIG_PADRAO)

    def test_falha_no_historico_e_sinalizada(self):
        with mock.patch("builtins.open", side_effect=OSError("bloqueado")):
            self.assertFalse(persistencia.registrar_historico("Cadastro", 1, "Ana", "x"))
        self.assertTrue(S.falha_historico)

    def test_trava_impede_segunda_copia(self):
        self.assertTrue(persistencia.obter_trava())
        primeira = S.trava
        self.addCleanup(primeira.close)
        self.assertFalse(persistencia.obter_trava())
        self.assertIs(S.trava, primeira)


if __name__ == "__main__":
    unittest.main()
