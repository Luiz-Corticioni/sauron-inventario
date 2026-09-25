"""Testes das partes que não dependem da digitação do usuário."""

import tempfile
import unittest
from pathlib import Path

import ativos
import dados
import vulnerabilidades
from utilitarios import (
    Severidade,
    StatusVulnerabilidade,
    TipoAtivo,
    calcular_painel,
)


def criar_base_exemplo():
    """Monta uma base pequena e previsível para os testes."""

    return {
        101: {
            "id": 101,
            "nome": "SW-CORE-01",
            "tipo": TipoAtivo.SWITCH,
            "responsavel": "Equipe de Redes",
            "setor": "TI",
            "localizacao": "Sala de Servidores",
            "descricao": "Switch principal",
            "vulnerabilidades": {
                "VUL-001": {
                    "categoria": "Software desatualizado",
                    "descricao": "Firmware antigo",
                    "severidade": Severidade.ALTA,
                    "status": StatusVulnerabilidade.EM_TRATAMENTO,
                    "tratamento_sugerido": "Atualizar o firmware.",
                }
            },
        },
        202: {
            "id": 202,
            "nome": "NOTE-FIN-01",
            "tipo": TipoAtivo.NOTEBOOK,
            "responsavel": "Ana",
            "setor": "Financeiro",
            "localizacao": "Financeiro",
            "descricao": "Notebook corporativo",
            "vulnerabilidades": {},
        },
    }


class TestesSentinela(unittest.TestCase):
    def test_busca_direta_por_id(self):
        base = criar_base_exemplo()
        self.assertEqual(ativos.buscar_por_id(base, 101)["nome"], "SW-CORE-01")
        self.assertIsNone(ativos.buscar_por_id(base, 999))

    def test_busca_parcial_por_nome_ignora_maiusculas(self):
        encontrados = ativos.buscar_por_nome(criar_base_exemplo(), "fin")
        self.assertEqual([item["id"] for item in encontrados], [202])

    def test_id_da_vulnerabilidade_avanca(self):
        self.assertEqual(vulnerabilidades.gerar_id(criar_base_exemplo()), "VUL-002")

    def test_painel_contabiliza_ativos_e_riscos(self):
        resumo = calcular_painel(criar_base_exemplo())
        self.assertEqual(resumo["total_ativos"], 2)
        self.assertEqual(resumo["total_vulnerabilidades"], 1)
        self.assertEqual(resumo["ativos_sem_vulnerabilidades"], 1)
        self.assertEqual(resumo["severidades_abertas"][Severidade.ALTA], 1)

    def test_persistencia_preserva_enums_e_chaves_inteiras(self):
        base = criar_base_exemplo()
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "inventario.json"
            dados.salvar(base, caminho)
            recarregada = dados.carregar(caminho)

        self.assertEqual(set(recarregada), {101, 202})
        self.assertIs(recarregada[101]["tipo"], TipoAtivo.SWITCH)
        vulnerabilidade = recarregada[101]["vulnerabilidades"]["VUL-001"]
        self.assertIs(vulnerabilidade["severidade"], Severidade.ALTA)
        self.assertIs(
            vulnerabilidade["status"], StatusVulnerabilidade.EM_TRATAMENTO
        )


if __name__ == "__main__":
    unittest.main()

