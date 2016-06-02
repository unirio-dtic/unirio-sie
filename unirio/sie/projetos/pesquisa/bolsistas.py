# coding=utf-8
from datetime import date, datetime, timedelta
from unirio.api import APIException
from unirio.sie import SIE, SIEException, SIEParametrosDAO, SIEFuncionarioID, SIEDocumentoDAO
from unirio.sie.projetos import SIEArquivosProj
from unirio.sie.documentos import SIETiposDocumentosDAO, SIEAssuntosDAO

__author__ = 'diogomartins'


class SIECandidatosBolsistasProjsPesquisa(SIE):
    """
    Classe DAO que faz a interação com a tabela de candidatos a bolsistas
    """

    STATUS_DEFERIDO = "D"
    STATUS_INDEFERIDO = "I"
    path = "CANDIDATOS_BOLSISTA"

    def __init__(self):
        super(SIECandidatosBolsistasProjsPesquisa, self).__init__()

    def from_candidato_item(self, candidato, id_plano_de_estudos):
        """
        Monta candidato a ser inserido no banco de dados a partir da instancia guardada dos formulários anteriores na session
        :param candidato:
        :return:
        """

        candidato_bolsista = {
            "ID_PROJETO": candidato['projeto_pesquisa'],
            "ID_CURSO_ALUNO": candidato['id_curso_aluno'],
            "ID_PLANO_ESTUDO": id_plano_de_estudos,
            "RENOVACAO": "S" if candidato['renovacao'] else "N",
            "INOVACAO": candidato['inovacao']
        }

        if candidato['link_lattes']:
            candidato_bolsista.update({"LINK_LATTES": candidato['link_lattes']})
        if candidato['descr_mail']:
            candidato_bolsista.update({"DESCR_MAIL": candidato['descr_mail']})

        # ESSE ERA O ANTIGO. DEIXAR AQUI POIS NUNCA SE SABE.
        # candidato_bolsista = {
        #     "ID_PROJETO": candidato['projeto_pesquisa'],
        #     "FUNCAO_ITEM": SIEProjetosPesquisa.ITEM_FUNCOES_PROJ_CANDIDATO_BOLSISTA,
        #     "CARGA_HORARIA": 20,
        #     "TITULACAO_ITEM": SIEProjetosPesquisa.ITEM_TITULACAO_SUPERIOR_INCOMPLETO, # TODO Deve ser mesmo hard-coded? E se for uma segunda graduação?
        #     "CH_SUGERIDA": 20,
        #     "ID_CURSO_ALUNO": candidato['id_curso_aluno'],
        #     "ID_PESSOA": candidato['id_pessoa'],
        #     "ID_UNIDADE": candidato['id_unidade'],
        #     "DT_INICIAL": date.today(),
        #     "DESCR_MAIL": candidato['descr_mail'],
        #     # "ID_BOLSISTA": "..." # TODO??
        #     "LINK_LATTES": candidato['link_lattes'],
        # }
        return candidato_bolsista

    def deletar_candidatos(self, candidatos):
        try:
            for candidato in candidatos:
                params = {"ID_CANDIDATOS_BOLSISTA": candidato["ID_CANDIDATOS_BOLSISTA"]}

                # Deletar linha do candidato
                self.api.delete(self.path, params)
                # plano de estudo relacionado.
                SIEArquivosProj().deletar_arquivo(candidato["ID_PLANO_ESTUDO"])

            return True
        except APIException as e:
            raise SIEException("Não foi possível deletar candidato a bolsista", e)

    def get_candidato_bolsista(self, **kwargs):
        """
        Retorna o candidato a bolsista, dependendo dos kwargs passados. Existem duas formas de se pegar um candidato a bolsista:
        Uma é via o id_candidatos_bolsista, ou é via id_projeto + id_curso_aluno
        :param kwargs: idealmente, ou é { id_candidatos_bolsista: } ou {id_projeto: "", id_curso_aluno: ""}
        :return: candidato a bolsista ou None
        :rtype dict
        """

        params = {}
        if 'id_candidatos_bolsista' in kwargs:
            params.update({
                "ID_CANDIDATOS_BOLSISTA": kwargs['id_candidatos_bolsista']
            })
        elif 'id_projeto' in kwargs and 'id_curso_aluno' in kwargs and 'ano_ref' in kwargs:
            params.update({
                "ID_PROJETO": kwargs['id_projeto'],
                "ID_CURSO_ALUNO": kwargs['id_curso_aluno'],
                "ANO_REF_AVAL": kwargs['ano_ref']  # TODO Seria mesmo ano ref aval? ou ano candidatura?
            })
        elif 'id_documento' in kwargs:
            params.update({
                "ID_DOCUMENTO": kwargs['id_documento'],
            })
        else:
            raise RuntimeError("Parâmetros inválidos.")

        return self.api.get_single_result(self.path, params, cache_time=0)

    def get_candidatos_bolsistas(self, cpf_coordenador):
        """
        Retorna os candidatos a bolsista atuais de um coordenador.
        :param cpf_coordenador:
        :return:
        """

        params = {
            "CPF_COORDENADOR": cpf_coordenador,
            "ANO_REF_AVAL": SIEParametrosDAO().parametros_prod_inst()["ANO_REF_AVAL"]
        }

        return self.api.get("V_CANDIDATOS_BOLSISTA_DADOS", params, bypass_no_content_exception=True)

    def documento_inicial_padrao(self, id_candidato):
        #TODO Checar com o ALEX e com VINICIUS
        #todo Property ?

        infos_tipo_documento = SIETiposDocumentosDAO().obter_parametros_tipo_documento(289)
        assunto_relacionado = SIEAssuntosDAO().get_by_id(infos_tipo_documento['ID_ASSUNTO_PADRAO'])

        # TODO Criar view específica para fazer isso ou criar outra classe que não faça dependencia cíclica.
        cpf = self.api.get_single_result("V_TRAMIT_PLANO_ESTUDOS",{"ID_CANDIDATOS_BOLSISTA":id_candidato})["CPF_COORDENADOR"]
        professor = SIEFuncionarioID().getFuncionarioIDs(cpf)


        return {
            "ID_TIPO_DOC": 289,
            "ID_PROCEDENCIA": professor["ID_CONTRATO_RH"],
            "ID_PROPRIETARIO": professor["ID_USUARIO"],
            "ID_CRIADOR": self.usuario["ID_USUARIO"],
            "TIPO_PROCEDENCIA": "S",
            "TIPO_INTERESSADO": "S",
            "ID_INTERESSADO": professor["ID_CONTRATO_RH"],
            "SITUACAO_ATUAL": 1,
            "TIPO_PROPRIETARIO": 20, # Indica a restrição de usuário
            "DT_CRIACAO": date.today(),
            "HR_CRIACAO":datetime.now().time().strftime("%H:%M:%S"),
            "IND_ELIMINADO": "N",
            "IND_AGENDAMENTO": "N",
            "IND_RESERVADO": "N",
            "IND_EXTRAVIADO": "N",
            "TEMPO_ESTIMADO": 1,
            "ID_ASSUNTO": assunto_relacionado['ID_ASSUNTO'],
            "DT_LIMITE_ARQ": date.today()+timedelta(days=int(assunto_relacionado['TEMPO_ARQUIVAMENTO'])) # TODO Se for None, qual o comportamento esperado?
        }

    def registra_candidato_documento(self,id_candidato):

        documento_candidato = self.documento_inicial_padrao(id_candidato)
        documentoDAO = SIEDocumentoDAO()

        documento = documentoDAO.criar_documento(documento_candidato)  # PASSO 1

        # faz a primeira tramitação
        fluxo = documentoDAO.obter_fluxo_inicial(documento)

        try:
            documentoDAO.tramitar_documento(documento, fluxo)
        except:
            # TODO Rollback da criação de documento.
            raise

        candidato_bolsista = {
            "ID_CANDIDATOS_BOLSISTA": id_candidato,
            "ID_DOCUMENTO": documento['ID_DOCUMENTO'],
            #"NUM_PROCESSO": documento['NUM_PROCESSO'] # TODO DEVERIA TER?
        }

        self.atualizar_candidato(candidato_bolsista)

        return candidato_bolsista["ID_DOCUMENTO"]

    def atualizar_candidato(self, candidato):
        """
        :rtype : bool
        :raises SIEException
        """
        try:
            retorno = self.api.put(self.path, candidato)
            if retorno.affectedRows == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao atualizar participante", e)


    def cadastra_candidato(self, candidato, ano_ref):
        """
        Cadastra candidato a bolsista no banco pela API.

        :param candidato:
        :return:
        """

        candidato.update({
            "ANO_REF_AVAL": ano_ref
        })

        try:
            return self.api.post(self.path, candidato)
        except APIException as e:
            raise SIEException("Falha ao cadastrar candidato", e)

    def inserir_candidato_bolsista(self, candidato, id_plano_estudos, coordenador):

        candidato_bolsista = SIECandidatosBolsistasProjsPesquisa().from_candidato_item(candidato, id_plano_estudos)

        # Adiciona infos gambiarradas de coordenador
        candidato_bolsista.update({
            "TITULACAO_MAX": coordenador['titulacao'],
            "REGIME": coordenador['regime']
        })

        ano_ref = SIEParametrosDAO().parametros_prod_inst()[
            "ANO_REF_AVAL"]  # TODO em tese, o ano de referencia é o ano atual??

        # TODO candidato_bolsista_no_banco = SIECandidatosBolsistasProjsPesquisa().get_candidato_bolsista(id_projeto=candidato['projeto_pesquisa'],id_curso_aluno=candidato['id_curso_aluno'],ano_ref=ano_ref) # TODO seria essa uma boa maneira de verificar? podia ter uma exception quando inserisse? id_projeto + id_curso_aluno?
        # TODO if not candidato_bolsista_no_banco:
        return SIECandidatosBolsistasProjsPesquisa().cadastra_candidato(candidato_bolsista, ano_ref)