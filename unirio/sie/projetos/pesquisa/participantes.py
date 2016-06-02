# coding=utf-8
from datetime import date
from unirio.api import APIException, NoContentException
from unirio.sie.exceptions import SIEException
from unirio.sie.projetos.participantes import SIEParticipantesProjs
from unirio.sie.utils import campos_sie_lower, datas_colidem, sie_str_to_date
from unirio.sie.projetos.pesquisa import SIEProjetosPesquisa


__author__ = 'diogomartins'


class SIEParticipantesProjsPesquisa(SIEParticipantesProjs):
    COD_SITUACAO_ATIVO = "A"
    COD_SITUACAO_INATIVO = "I"

    path = "PARTICIPANTES_PROJ"

    def __init__(self):
        super(SIEParticipantesProjsPesquisa, self).__init__()

    def cadastra_participante(self, participante):
        """

        :param participante: Um participante é composto dos seguintes campos:
            'id_projeto','id_curso_aluno','id_contrato_rh','id_ent_externa','id_pessoa','id_unidade',
                              'funcao_participante','data_ini','data_final','carga_horaria','carga_horaria_sugerida',
                              'titulacao_item','situacao/a-i','desc_mail','link_lattes'
        :return: APIPostResponse em caso de sucesso, None c.c.
        :raises APIException:
        """
        participante.update({
            'FUNCAO_TAB': SIEProjetosPesquisa.COD_TABELA_FUNCOES_PROJ,
            'TITULACAO_TAB': SIEProjetosPesquisa.COD_TABELA_TITULACAO,
            'SITUACAO': self.COD_SITUACAO_ATIVO,
            'TITULACAO_ITEM': SIEProjetosPesquisa.ITEM_TITULACAO_INDEFINIDA
        })

        try:
            return self.api.post(self.path, participante)
        except APIException as e:
            raise SIEException("Falha ao cadastrar participante", e)

    def get_participantes(self, id_projeto, situacao=None):
        """
        Retorna dicionário com todos os participantes do projeto
        :return: dict com informações dos participantes
        """

        if situacao is None:
            situacao = self.COD_SITUACAO_ATIVO

        params = {
            "LMIN": 0,
            "LMAX": 999,
            "ID_PROJETO": id_projeto,
            "SITUACAO": situacao
        }
        try:
            res = self.api.get("V_PROJETOS_PARTICIPANTES", params, cache_time=0)
            return res.content if res is not None else []
        except NoContentException:
            return []

    def get_participantes_inativos(self, id_projeto):
        """
        Retorna dicionário com todos os participantes inativos do projeto
        :return: dict com informações dos participantes
        """
        return self.get_participantes(id_projeto, self.COD_SITUACAO_INATIVO)

    def get_participante_as_row(self, id_participante):
        """
        Este método retorna um dicionário contendo os dados referentes ao participante convertidos para o formato compatível
        com o modelo no web2py.
        :param id_participante: integer,
        :return: gluon.pydal.objects.Row contendo as informações, None caso não exista participante com a id informada/erro.
        """
        if id_participante:
            participante = self.get_participante(id_participante)
            if participante:
                participante_to_row = campos_sie_lower([participante])[0]
                participante_to_row['id'] = participante_to_row['id_participante']
                # participante_to_row['carga_horaria'] = '20'; #dummy
                # participante_to_row['link_lattes'] = '???'; #dummy
                participante_to_row['descr_mail'] = participante_to_row['descr_mail'].strip()
                participante_to_row['funcao'] = participante_to_row['funcao_item']
                participante_to_row['participacao_fim'] = sie_str_to_date(participante_to_row['dt_final']) if \
                participante_to_row[
                    'dt_final'] else None
                participante_to_row['participacao_inicio'] = sie_str_to_date(participante_to_row['dt_inicial']) if \
                participante_to_row[
                    'dt_inicial'] else None

                participante_row = Storage(participante_to_row)
            else:
                participante_row = None
        else:
            participante_row = None
        return participante_row

    def get_participante(self, id_participante):
        """
        Retorna dicionário com o participantes de id_participante
        :return: dict com informações dos participantes, None caso contrário.
        """
        params = {
            "LMIN": 0,
            "LMAX": 1,
            "ID_PARTICIPANTE": id_participante,
        }
        try:
            res = self.api.get("V_PROJETOS_PARTICIPANTES", params)
            return res.content[0] if res is not None else None
        except NoContentException:
            return None

    def atualizar_participante(self, participante):
        """
        :rtype : bool
        :raises APIException
        """
        try:
            retorno = self.api.put(self.path, participante)
            if retorno.affectedRows == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao atualizar participante", e)

    def inativar_participante(self, id_participante):
        """
        :rtype : bool
        :raises APIException
        """

        participante = {
            "ID_PARTICIPANTE": id_participante,
            "SITUACAO": self.COD_SITUACAO_INATIVO,
            "DT_FINAL": date.today()  # TODO É isso mesmo???
        }

        try:
            return self.atualizar_participante(participante)
        except SIEException as e:
            raise SIEException("Falha ao inativar participante", e)


    def deletar_participante(self, id_participante):

        params = {"ID_PARTICIPANTE": id_participante}
        try:
            retorno = self.api.delete(self.path, params)
            if retorno and int(retorno.affectedRows) == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao atualizar participante", e)

    def participante_ja_presente(self, participante, id_origem, origem, alteracao=False):
        """
        Verifica se já existe participante cadastrado com mesma id_origem e origem num mesmo período neste projeto e mesma função

        :param participante:
        :param id_origem:
        :param origem:
        :return:
        """

        participantes = self.get_participantes(participante["ID_PROJETO"])

        for participante_bd in participantes:

            if int(id_origem) == int(participante_bd['ID_ORIGEM']) and origem == participante_bd['ORIGEM'] and int(
                    participante['FUNCAO_ITEM']) == int(participante_bd['FUNCAO_ITEM']):
                # Se mesmo participante - mesma origem e mesma função, verifica datas 'encavaladas'
                data_inicial_participante = sie_str_to_date(participante_bd[u'DT_INICIAL']) if participante_bd[
                    u'DT_INICIAL'] else None
                data_final_participante = sie_str_to_date(participante_bd[u'DT_FINAL']) if participante_bd[
                    u'DT_FINAL'] else None

                if datas_colidem(participante['DT_INICIAL'], participante['DT_FINAL'], data_inicial_participante,
                                 data_final_participante):
                    if not alteracao or int(participante_bd['ID_PARTICIPANTE']) != int(participante["ID_PARTICIPANTE"]):
                        # É colisão se não for alteração ou se colidir com outro que não seja ele mesmo.
                        return True
        return False