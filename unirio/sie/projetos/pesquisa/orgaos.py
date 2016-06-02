# coding=utf-8
from datetime import date
from unirio.api import NoContentException, APIException
from unirio.sie.exceptions import SIEException
from unirio.sie.projetos.orgaos import SIEOrgaosProjetos
from unirio.sie.projetos.pesquisa import SIEProjetosPesquisa
from unirio.sie.utils import datas_colidem, sie_str_to_date

__author__ = 'diogomartins'


class SIEOrgaosProjsPesquisa(SIEOrgaosProjetos):
    COD_SITUACAO_ATIVO = "A"
    COD_SITUACAO_INATIVO = "I"

    def __init__(self):
        super(SIEOrgaosProjsPesquisa, self).__init__()

    def get_orgao_as_row(self, id_orgao_projeto):
        # todo Gera dependencia de pydal. Isso realmente deveria estar aqui?
        if id_orgao_projeto:
            orgao_bd = self.get_orgao(id_orgao_projeto)
            if orgao_bd:
                orgao_dict = {
                    'nome': orgao_bd[u'NOME_UNIDADE'].encode('utf-8'),
                    'descricao_origem': "UNIRIO" if orgao_bd[u"ORIGEM"] == "ID_UNIDADE" else "Externo",
                    'funcao_orgao': orgao_bd[u"FUNCAO_ORG_ITEM"],
                    "valor": orgao_bd[u'VL_CONTRIBUICAO'],
                    'participacao_inicio': sie_str_to_date(orgao_bd[u'DT_INICIAL']) if orgao_bd[
                        u'DT_INICIAL'] else None,
                    'participacao_fim': sie_str_to_date(orgao_bd[u'DT_FINAL']) if orgao_bd[
                        u'DT_FINAL'] else None,
                    'observacao': orgao_bd[u'OBS_ORG_PROJETO'].encode('utf-8'),
                    'id': orgao_bd[u"ID_ORGAO_PROJETO"],
                    'id_projeto': orgao_bd[u"ID_PROJETO"],
                    'origem': orgao_bd["ORIGEM"],
                    'id_origem': orgao_bd["ID_ORIGEM"]
                }
                orgao_row = Storage(orgao_dict)
                return orgao_row
        return None

    def get_orgao(self, id_orgao_projeto):
        params = {"LMIN": 0,
                  "LMAX": 1,
                  "ID_ORGAO_PROJETO": id_orgao_projeto,
                  }
        try:
            return self.api.get("V_PROJETOS_ORGAOS", params).first()
        except NoContentException:
            return {}

    def cadastra_orgao(self, orgao):
        """

        :param orgao: Um órgão é composto dos seguintes campos:
            'ID_PROJETO',
            ID_UNIDADE ou ID_ENT_EXTERNA,
            "FUNCAO_ORG_ITEM",
            "DT_INICIAL",
            "DT_FINAL",
            "VL_CONTRIBUICAO",
            "OBS_ORG_PROJETO"
        :return: APIPostResponse em caso de sucesso, None c.c.
        :raises: unirio.api.exceptions.APIException
        """
        orgao.update({
            'FUNCAO_ORG_TAB': SIEProjetosPesquisa.COD_TABELA_FUNCOES_ORGAOS,
            'SITUACAO': self.COD_SITUACAO_ATIVO,
        })
        try:
            return self.api.post(self.path, orgao)
        except APIException as e:
            raise SIEException("Falha ao cadastrar órgão", e)

    def get_orgaos(self, id_projeto, situacao=None):
        """
        Retorna dicionário com todos os orgaos do projeto
        :return: dict com informações dos orgaos
        """

        if situacao is None:
            situacao = self.COD_SITUACAO_ATIVO

        params = {"LMIN": 0,
                  "LMAX": 999,
                  "ID_PROJETO": id_projeto,
                  "SITUACAO": situacao
                  }

        try:
            res = self.api.get("V_PROJETOS_ORGAOS", params)
            return res.content if res is not None else []
        except NoContentException:
            return []

    def get_orgaos_inativos(self, id_projeto):
        """
        Retorna dicionário com todos os orgaos inativos do projeto
        :return: dict com informações dos orgaos
        """

        return self.get_orgaos(id_projeto,self.COD_SITUACAO_INATIVO)

    def atualizar_orgao(self, orgao):
        """
        :rtype : APIPUTResponse
        :raises: APIException
        """
        try:
            retorno = self.api.put(self.path, orgao)
            if retorno.affectedRows == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao atualizar órgão", e)

    def inativar_orgao(self, id_orgao_projeto):
        """
        Inativa um órgão.
        :rtype : APIPUTResponse
        :raises: APIException
        """

        orgao = {
            "ID_ORGAO_PROJETO": id_orgao_projeto,
            "SITUACAO": self.COD_SITUACAO_INATIVO,
            "DT_FINAL": date.today()
        }

        try:
            return self.atualizar_orgao(orgao)
        except SIEException as e:
            raise SIEException("Falha ao inativar órgão", e)

    def deletar_orgao(self, id_orgao_projeto):

        params = {"ID_ORGAO_PROJETO": id_orgao_projeto}
        try:
            retorno = self.api.delete(self.path, params)
            if retorno and retorno.affectedRows == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao remover órgão", e)

    def orgao_ja_presente(self, orgao, id_origem, origem, alteracao=False):
        """
        Verifica se já existe órgão cadastrado com mesma id_origem e origem num mesmo período neste projeto.

        :param orgao:
        :param id_origem:
        :param origem:
        :return:
        """

        orgaos = self.get_orgaos(orgao["ID_PROJETO"])  # TODO orgao_as_row não tem esse projeto.

        for orgao_bd in orgaos:

            if int(id_origem) == int(orgao_bd['ID_ORIGEM']) and origem == orgao_bd['ORIGEM']:
                # Se mesmo órgão, verifica datas 'encavaladas'
                data_inicial_orgao = sie_str_to_date(orgao_bd[u'DT_INICIAL']) if orgao_bd[
                    u'DT_INICIAL'] else None
                data_final_orgao = sie_str_to_date(orgao_bd[u'DT_FINAL']) if orgao_bd[
                    u'DT_FINAL'] else None

                if datas_colidem(orgao['DT_INICIAL'], orgao['DT_FINAL'], data_inicial_orgao, data_final_orgao):
                    if not alteracao or int(orgao_bd['ID_ORGAO_PROJETO']) != int(orgao["ID_ORGAO_PROJETO"]):
                        # É colisão se não for alteração ou se colidir com outro que não seja ele mesmo.
                        return True
        return False