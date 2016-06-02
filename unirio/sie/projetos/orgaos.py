# coding=utf-8
from unirio.sie import SIE, SIEException

__author__ = 'diogomartins'


class SIEOrgaosProjetos(SIE):
    def __init__(self):
        super(SIEOrgaosProjetos, self).__init__()
        self.path = "ORGAOS_PROJETOS"

    def criarOrgaosProjetos(self, projeto, ID_UNIDADE):
        """
        FUNCAO_ORG_TAB => 6006 - Função dos órgãos nos projetos
        FUNCAO_ITEM_TAB => 6 - Curso beneficiado

        :param projeto: Um dicionário contendo a entrada uma entrada da tabela PROJETOS
        :param ID_UNIDADE:
        :return:
        """
        orgaoProj = {
            "ID_PROJETO": projeto["ID_PROJETO"],
            "ID_UNIDADE": ID_UNIDADE,
            "FUNCAO_ORG_TAB": 6006,
            "FUNCAO_ORG_ITEM": 6,
            "DT_INICIAL": projeto["DT_INICIAL"],
            "SITUACAO": "A"
        }
        try:
            return self.api.post(self.path, orgaoProj)
        except Exception as e:
            raise SIEException("Não foi possível associar um órgão ao projeto.", e)

    def removerOrgaosProjetos(self, ID_ORGAO_PROJETO):
        self.api.delete(self.path, {"ID_ORGAO_PROJETO": ID_ORGAO_PROJETO})

    def removerOrgaosProjetosDeProjeto(self, ID_PROJETO):
        """
        Dada uma entrada na tabela PROJETOS, a função busca e remove todas as entradas de ORGAOES_PROJETOS referentes a
        esse projeto.

        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        :type ID_PROJETO: int
        """
        try:
            orgaos = self.api.get(self.path,
                                  {"ID_PROJETO": ID_PROJETO},
                                  ['ID_ORGAO_PROJETO'])
            for orgao in orgaos.content:
                self.removerOrgaosProjetos(orgao['ID_ORGAO_PROJETO'])
        except ValueError as e:
            raise SIEException("Nenhuma entrada encontrada em ORGAOS_PROJETOS", e)