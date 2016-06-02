from datetime import date, datetime, timedelta
from unirio.api import APIException
from unirio.sie import SIE, SIEException, SIETiposDocumentosDAO, SIEAssuntosDAO

__author__ = 'diogomartins'


class SIEAvaliacaoProjDAO(SIE):
    path = "AVALIACOES_PROJ"

    def __init__(self):
        super(SIEAvaliacaoProjDAO, self).__init__()

    def atualizar_avaliacao(self, avaliacao):
        """
        :param avaliacao:
        :rtype : bool
        :raises SIEException
        """
        try:
            retorno = self.api.put(self.path, avaliacao)
            if retorno.affectedRows == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao atualizar avaliação", e)

    def get_avaliacao(self, ano_ref, id_projeto, periodo_ref_tab=None, periodo_ref_item=None):
        """
        Retorna uma row da tabela AVALIACOES_PROJ -> indica que já foi criada uma avaliação para aquele projeto no ano de referencia.
        Tal row só é criada quando o docente envia um relatório de pesquisa.

        :param ano_ref: ano de referencia
        :param periodo_ref_tab: tab do periodo
        :param periodo_ref_item: ano de referencia
        :param id_projeto: id do projeto
        :return: dicionário contendo informações da linha respectiva no bd

        """
        params = {
            "ID_PROJETO": id_projeto,
            "ANO_REF": ano_ref
        }

        if periodo_ref_item:
            params.update({
                "PERIODO_REF_ITEM": periodo_ref_item
            })

        if periodo_ref_tab:
            params.update({
                "PERIODO_REF_TAB": periodo_ref_tab
            })

        return self.api.get_single_result(self.path, params, bypass_no_content_exception=True)

    def documento_inicial_padrao(self):
        # TODO Checar com o ALEX!
        # todo Property ?


        infos_tipo_documento = SIETiposDocumentosDAO().obter_parametros_tipo_documento(223)
        assunto_relacionado = SIEAssuntosDAO().get_by_id(infos_tipo_documento['ID_ASSUNTO_PADRAO'])

        return {
            "ID_TIPO_DOC": 223,
            "ID_PROCEDENCIA": self.usuario["ID_CONTRATO_RH"],
            "ID_PROPRIETARIO": self.usuario["ID_USUARIO"],
            "ID_CRIADOR": self.usuario["ID_USUARIO"],
            "TIPO_PROCEDENCIA": "S",
            "TIPO_INTERESSADO": "S",
            "ID_INTERESSADO": self.usuario["ID_CONTRATO_RH"],
            "SITUACAO_ATUAL": 1,
            "TIPO_PROPRIETARIO": 20,  # Indica a restrição de usuário
            # "TIPO_ORIGEM": 20,  # atualizacao do sie Out/2015
            "DT_CRIACAO": date.today(),
            "HR_CRIACAO": datetime.now().time().strftime("%H:%M:%S"),
            "IND_ELIMINADO": "N",
            "IND_AGENDAMENTO": "N",
            "IND_RESERVADO": "N",
            "IND_EXTRAVIADO": "N",
            "TEMPO_ESTIMADO": 1,
            "ID_ASSUNTO": assunto_relacionado['ID_ASSUNTO'],
            # assunto_relacionado['DESCR_ASSUNTO'],
            "DT_LIMITE_ARQ": date.today() + timedelta(days=int(assunto_relacionado['TEMPO_ARQUIVAMENTO']))
        # TODO Se for None, qual o comportamento esperado?
            # "OBSERVACOES": ?? Não estamos usando.
            # "SEQUENCIA": 1  # atualizacao do sie Out/2015
        }