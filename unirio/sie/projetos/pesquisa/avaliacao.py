# coding=utf-8
from unirio.api import APIException
from unirio.sie import SIEException, SIEDocumentoDAO
from unirio.sie.projetos.pesquisa import SIEProjetosPesquisa
from unirio.sie.projetos.avaliacao import SIEAvaliacaoProjDAO

__author__ = 'diogomartins'


class SIEAvaliacaoProjsPesquisaDAO(SIEAvaliacaoProjDAO):
    COD_TABELA_TIPO_AVALIACAO = 6016
    ITEM_TIPO_AVALIACAO_PROJETO = 1

    COD_SITUACAO_COM_COORDENADOR = 1

    def __init__(self):
        super(SIEAvaliacaoProjDAO, self).__init__()

    def get_avaliacao_by_id(self, id_avaliacao_proj):
        """
        Retorna uma row da view V_AVALIACOES_PROJ
        Tal row só é criada quando o docente envia um relatório de pesquisa.

        :param id_avaliacao_proj: id da avaliação
        :return: dicionário contendo informações da linha respectiva no bd

        """
        params = {
            "ID_AVALIACAO_PROJ": id_avaliacao_proj
        }
        return self.api.get_single_result("V_AVALIACOES_PROJ", params, bypass_no_content_exception=True)

    def get_avaliacao_by_doc(self, id_doc):
        """
        Retorna uma row da tabela AVALIACOES_PROJ
        Tal row só é criada quando o docente envia um relatório de pesquisa.

        :param id_documento: id do documento da avaliação
        :return: dicionário contendo informações da linha respectiva no bd

        """

        params = {
            "ID_DOCUMENTO": id_doc
        }
        return self.api.get_single_result("AVALIACOES_PROJ", params, bypass_no_content_exception=True)


    def _resolve_situacao_avaliacao(self, situacao_projeto, prorrogacao):
        """Resolve o valor da coluna 'SITUACAO_ITEM' da avaliação a ser criada.
        TODO Existem casos não previstos?
        :param situacao_projeto: conteudo da coluna 'SITUACAO_ITEM' da tabela PROJETOS
        :type situacao_projeto: int
        :param prorrogacao: booleano que indica se o usuário pediu ou não prorrogação da vigencia do projeto.
        :type prorrogacao: bool
        :returns: A situação que deve ser utilizada.
        :rtype: int
        """
        # TODO O que fazer com esse método. Não sabemos se isso será usado ou não!

        if situacao_projeto == SIEProjetosPesquisa.ITEM_SITUACAO_SUSPENSO:
            return SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO
        elif prorrogacao:
            return SIEProjetosPesquisa.ITEM_SITUACAO_RENOVADO
        else:
            return situacao_projeto

    def criar_avaliacao(self, projeto, documento, params_projeto_pesquisa, data_prorrogacao=False, obs=''):
        """
        :param id_projeto:
        :param documento:
        :param params_projeto_pesquisa:
        :param prorrogacao:
        :return:
        """
        # projeto = SIEProjetosPesquisa().get_projeto(id_projeto)

        avaliacao_default = {
            "PERIODO_REF_TAB": params_projeto_pesquisa["PERIODO_REF_TAB"],
            "PERIODO_REF_ITEM": params_projeto_pesquisa["PERIODO_REF_ITEM"],
            "TIPO_AVAL_TAB": self.COD_TABELA_TIPO_AVALIACAO,
            "TIPO_AVAL_ITEM": self.ITEM_TIPO_AVALIACAO_PROJETO,
            "SITUACAO_TAB": SIEProjetosPesquisa.COD_TABELA_SITUACAO,
            "SITUACAO_ITEM": projeto['SITUACAO_ITEM'], # Atualizado conforme e-mail de 9 de dezembro de 2015 23:33 da Síntese.
            "ANO_REF": params_projeto_pesquisa["ANO_REF_AVAL"],
        # TODO  em tese, o ano de referencia é o ano atual de avaliação, pois nenhum projeto pode pedir bolsas sem estar 'em andamento' e para estar 'em andamento' os relatórios não podem estar atrasados -> só falta o relatório atual
            "DT_CONCLUSAO": data_prorrogacao if data_prorrogacao else projeto['DT_CONCLUSAO'],
            "ID_CONTRATO_RH": self.usuario['ID_CONTRATO_RH'],
            "ID_UNIDADE": self.usuario['ID_LOT_OFICIAL']
        }

        avaliacao_default.update({
            "ID_PROJETO": projeto['ID_PROJETO'],
            "ID_DOCUMENTO": documento['ID_DOCUMENTO'],
            "NUM_PROCESSO": documento["NUM_PROCESSO"]
        })

        if obs:
            avaliacao_default.update({
                'OBS_PRORROGACAO': obs
            })

        try:
            resultado = self.api.post(self.path, avaliacao_default)
            avaliacao_default.update({"ID_AVALIACAO_PROJ": resultado.insertId})  # ????
            return avaliacao_default
        except APIException as e:
            raise SIEException("Falha ao criar avaliação.", e)

    def is_avaliacao_com_professor(self, avaliacao):
        """
        Método retorna se a avaliação passada como parâmetro está com o professor ( e o mesmo pode reenviar relatório) ou não.

        :param avaliacao: avaliação contendo ID_DOCUMENTO obrigatoriamente.
        :type avaliacao: dict
        """

        id_documento_avaliacao = avaliacao["ID_DOCUMENTO"]

        documento_avaliacao = SIEDocumentoDAO().obter_documento(id_documento_avaliacao)

        return int(documento_avaliacao['SITUACAO_ATUAL']) == self.COD_SITUACAO_COM_COORDENADOR