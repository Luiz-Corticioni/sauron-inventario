"""Testes automatizados das regras centrais do Sauron."""

import math
import tempfile
import unittest
from pathlib import Path

import ativos
import autenticacao
import dados
import estrutura
import identificacao
import modo_euler
import vulnerabilidades
from utilitarios import Severidade, StatusVulnerabilidade, TipoAtivo, calcular_painel


def criar_base_exemplo():
    base = dados.criar_base_vazia()
    base["setores"][5] = {
        "id": 5, "nome": "Redes", "setor_pai_id": 3,
        "descricao": "Subsetor de redes",
    }
    base["salas"]["SAL-007"] = {
        "id": "SAL-007", "nome": "Laboratório de Redes", "setor_id": 5,
        "categoria": "LABORATORIO", "descricao": "",
    }
    base["ativos"] = {
        "4H21444": {
            "id": "4H21444", "hostname": "SW-EQUIPE-21444", "nome": "SW-EQUIPE-21444",
            "tipo": TipoAtivo.SWITCH, "fabricante": "Huawei",
            "codigo_fabricante": "H", "numero_serie": "21444",
            "usuario": "Equipe", "responsavel": "Equipe de Redes",
            "setor_id": 5, "sala_id": "SAL-007", "descricao": "Switch principal",
            "vulnerabilidades": {
                "VUL-02-001": {
                    "codigo_categoria": 2, "categoria": "Software desatualizado",
                    "descricao": "Firmware antigo", "severidade": Severidade.ALTA,
                    "status": StatusVulnerabilidade.EM_TRATAMENTO,
                    "tratamento_sugerido": "Atualizar o firmware.",
                }
            },
        },
        "2D20200": {
            "id": "2D20200", "hostname": "NB-ANA-20200", "nome": "NB-ANA-20200",
            "tipo": TipoAtivo.NOTEBOOK, "fabricante": "Dell",
            "codigo_fabricante": "D", "numero_serie": "20200",
            "usuario": "Ana", "responsavel": "Suporte",
            "setor_id": 2, "sala_id": "SAL-004", "descricao": "Notebook corporativo",
            "vulnerabilidades": {},
        },
    }
    return base


class TestesSauron(unittest.TestCase):
    def test_id_e_hostname_automaticos(self):
        self.assertEqual(identificacao.gerar_id_ativo(TipoAtivo.SWITCH, "H", "21444"), "4H21444")
        self.assertEqual(identificacao.gerar_hostname(TipoAtivo.SWITCH, "Luiz Fabiano", "21444"), "SW-LUIZFABIANO-21444")
        self.assertTrue(identificacao.validar_id_ativo("4H21444"))
        self.assertFalse(identificacao.validar_id_ativo("qualquer-numero"))

    def test_busca_por_id_estruturado(self):
        registros = criar_base_exemplo()["ativos"]
        self.assertEqual(ativos.buscar_por_id(registros, "4h21444")["hostname"], "SW-EQUIPE-21444")
        self.assertIsNone(ativos.buscar_por_id(registros, "4H99999"))

    def test_busca_textual_ignora_maiusculas(self):
        encontrados = ativos.buscar_por_nome(criar_base_exemplo()["ativos"], "ana")
        self.assertEqual([item["id"] for item in encontrados], ["2D20200"])

    def test_id_da_vulnerabilidade_por_categoria(self):
        self.assertEqual(vulnerabilidades.gerar_id(criar_base_exemplo()["ativos"], 2), "VUL-02-002")
        self.assertEqual(vulnerabilidades.gerar_id(criar_base_exemplo()["ativos"], 3), "VUL-03-001")

    def test_pin_e_hash(self):
        credencial = autenticacao.criar_credencial("123456", salt="00" * 16, iteracoes=1000)
        self.assertTrue(autenticacao.verificar_pin("123456", credencial))
        self.assertFalse(autenticacao.verificar_pin("654321", credencial))
        self.assertNotIn("123456", credencial.values())

    def test_painel_contabiliza_ativos_e_riscos(self):
        resumo = calcular_painel(criar_base_exemplo()["ativos"])
        self.assertEqual(resumo["total_ativos"], 2)
        self.assertEqual(resumo["total_vulnerabilidades"], 1)
        self.assertEqual(resumo["severidades_abertas"][Severidade.ALTA], 1)

    def test_hierarquia_e_salas_tabeladas(self):
        base = criar_base_exemplo()
        self.assertEqual(estrutura.caminho_setor(base, 5), "TI > Redes")
        self.assertEqual(estrutura.proximo_id_sala(base["salas"]), "SAL-008")
        self.assertTrue(estrutura.sala_adequada(TipoAtivo.SWITCH, base["salas"]["SAL-007"]))
        self.assertFalse(estrutura.sala_adequada(TipoAtivo.SERVIDOR, base["salas"]["SAL-004"]))

    def test_persistencia_em_seis_tabelas_txt(self):
        base = criar_base_exemplo()
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            dados.salvar(base, pasta)
            self.assertEqual(
                {item.name for item in pasta.glob("*.txt")},
                {"ativos.txt", "vulnerabilidades.txt", "setores.txt", "salas.txt", "seguranca.txt", "auditoria.txt"},
            )
            recarregada = dados.carregar(pasta)
        self.assertEqual(set(recarregada["ativos"]), {"4H21444", "2D20200"})
        self.assertIs(recarregada["ativos"]["4H21444"]["tipo"], TipoAtivo.SWITCH)
        vulnerabilidade = recarregada["ativos"]["4H21444"]["vulnerabilidades"]["VUL-02-001"]
        self.assertIs(vulnerabilidade["severidade"], Severidade.ALTA)

    def test_modo_euler_classifica_deriva_e_integra(self):
        funcao, arvore, _ = modo_euler.compilar_funcao("x^2 + 2*x - 3")
        self.assertEqual(modo_euler.identificar_tipo(arvore), "Quadrática")
        derivada = modo_euler.derivar_polinomio(modo_euler.extrair_polinomio(arvore))
        self.assertEqual(modo_euler.formatar_polinomio(derivada), "2*x + 2")
        self.assertAlmostEqual(funcao(2), 5.0)
        quadrado, _, _ = modo_euler.compilar_funcao("x^2")
        self.assertAlmostEqual(modo_euler.integrar_simpson(quadrado, 0, 1, 100), 1 / 3, places=8)

    def test_modo_euler_encontra_raizes_e_bloqueia_codigo(self):
        quadratica, _, _ = modo_euler.compilar_funcao("x^2 - 4")
        raizes = modo_euler.encontrar_raizes(quadratica, -3, 3)
        self.assertTrue(any(math.isclose(raiz, -2, abs_tol=1e-6) for raiz in raizes))
        with self.assertRaises(modo_euler.ErroExpressao):
            modo_euler.compilar_funcao("__import__('os').system('echo perigo')")


if __name__ == "__main__":
    unittest.main()
