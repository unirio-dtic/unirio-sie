# coding=utf-8

import re
import base64
from datetime import date, datetime, timedelta
from deprecate import deprecated

from unirio.sie.base import SIE
from unirio.sie.exceptions import SIEException
from unirio.sie.SIEBolsistas import SIEBolsas, SIEBolsistas
from unirio.sie.SIEDocumento import SIEDocumentoDAO, SIETiposDocumentosDAO, SIEAssuntosDAO
from unirio.sie.SIEFuncionarios import SIEFuncionarios
from unirio.sie.SIETabEstruturada import SIETabEstruturada
from unirio.sie.utils import remover_acentos_query
from unirio.api.exceptions import NoContentException, APIException


__all__ = [
    "SIEProjetos",
    "SIEArquivosProj",
    "SIEClassificacoesPrj",
    "SIEParticipantesProjs",
    "SIECursosDisciplinas",
    "SIEClassifProjetos",
    "SIEOrgaosProjetos"
]


class SIEProjetos(SIE):
    TIPO_DOCUMENTO = -1

    def __init__(self):
        super(SIEProjetos, self).__init__()
        self.path = "PROJETOS"

    def getProjeto(self, ID_PROJETO):
        """
        Dado o identificador único de um projeto na tabela PROJETOS, a função retorna um dicionáio
        correspondente. A requisição é cacheada.

        :param ID_PROJETO: Identificador único de um projeto
        :type ID_PROJETO: int
        :return: Uma entrada na tabela PROJETOS
        :rtype : dict
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO
        }

        return self.api.get_single_result(self.path, params)

    def getProjetoDados(self, ID_PROJETO):
        """
        Dado o identificador único de um projeto na tabela PROJETOS, a função retorna um dicionáio
        correspondente a uma entrada na view V_PROJETOS_DADOS, que é uma juncão das tabelas PROJETOS,
        PARTICIPANTES_PRJ, DOCUMENTOS, CLASSIFICACAO_PRJ

        :param ID_PROJETO: Identificador único de um projeto
        :type ID_PROJETO: int
        :return: Uma entrada na view V_PROJETOS_DADOS
        :rtype: dict
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO
        }

        try:
            return self.api.get("V_PROJETOS_DADOS", params).first()
        except NoContentException:
            return None

    def getCoordenador(self, ID_PROJETO):
        """
        Dado um ID_PROJETO, a função retorna o seu coordenador, na forma de um dicionário representativo de uma entrada
        na tabela PESSOAS.

        :param ID_PROJETO: Identificador único de um projeto na tabela PROJETOS
        :return: Uma entrada na tabela PESSOAS
        :rtype : dict
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO,
            'FUNCAO_ITEM': 1
        }

        try:
            c = self.api.get("PARTICIPANTES_PROJ", params).first()
            return self.api.get("PESSOAS", {"ID_PESSOA": c['ID_PESSOA']}).first()
        except NoContentException:
            return None

    def getDisciplina(self, ID_PROJETO):
        """
        Dado um identificador único na tabela de PROJETOS, a função retornará uma string correspondente ao nome da
        disciplina, de acordo com a classificaçao do projeto

        :rtype : str
        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        :return: Nome de uma disciplina
        """
        params = {
            'LMIN': 0,
            'LMAX': 1,
            'ID_PROJETO': ID_PROJETO
        }

        try:
            return self.api.get("V_PROJETOS_DADOS", params).first()['NOME_DISCIPLINA']
        except NoContentException:
            return None

    def projetosDeEnsino(self, edicao, params=None):
        """

        :type edicao: gluon.storage.Storage
        :param edicao: Uma entrada da tabela `edicao`
        :type params: dict
        :param params: Um dicionário de parâmetros a serem usados na busca
        :rtype : list
        :return: Uma lista de projetos de ensino
        """
        if not params:
            params = {}

        params.update({
            "ID_CLASSIFICACAO": 40161,
            "DT_INICIAL": edicao.dt_inicial_projeto,
            "LMIN": 0,
            "LMAX": 99999
        })

        return self.api.get(self.path, params).content

    def projetosDadosEnsino(self, edicao, params=None):
        """

        :type edicao: gluon.storage.Storage
        :param edicao: Uma entrada da tabela `edicao`
        :type params: dict
        :param params: Um dicionário de parâmetros a serem usados na busca
        :rtype : list
        :return: Uma lista de projetos de ensino
        """
        if not params:
            params = {}

        params.update({
            "ID_CLASSIFICACAO": 40161,
            "DT_INICIAL": edicao.dt_inicial_projeto,
            "LMIN": 0,
            "LMAX": 99999
        })

        return self.api.get('V_PROJETOS_DADOS', params).content

    @staticmethod
    def isAvaliado(projeto):
        """
        0 => Situação do projeto da Instituição
        1 => Concluído/Publicado
        2 => Em andamento
        4 => Suspenso
        5 => Cancelado
        6 => Renovado
        7 => Cancelado - Res. Interna
        8 => Em tramite para registro
        9 => Indeferido

        :type projeto: dict
        :param projeto: Dicionário correspondente a uma entrada na tabela PROJETOS
        :rtype bool
        """
        # TODO discituir se usar uma lista estática é uma solução aceitável ou se deveria ser realizada uma consulta na TAB_ESTRUTURADA
        if projeto["SITUACAO_ITEM"] in range(1, 10):
            return True

    @deprecated
    def salvarProjeto(self, projeto, funcionario, edicao):
        """
        EVENTO_TAB              => Tipos de Eventos
        EVENTO_ITEM = 1         => Não se aplica
        TIPO_PUBLICO_TAB        => Público alvo
        TIPO_PUBLICO_ITEM = 8   => 3o grau
        AVALIACAO_TAB           => Avaliação dos projetos da Instituição
        AVALIACAO_ITEM = 2      => Pendente de avaliacao

        :type projeto: dict
        :param projeto: Um projeto a ser inserido no banco
        :type funcionario: dict
        :param funcionario: Dicionário de IDS de um funcionário
        :type edicao: gluon.storage.Storage
        :param edicao: Uma entrada da tabela `edicao`
        :return: Um dicionário contendo a entrada uma nova entrada da tabela PROJETOS
        """
        novoDocumento = SIEDocumentoDAO().criar_documento(215, funcionario)
        projeto.update({
            "ID_DOCUMENTO": novoDocumento["ID_DOCUMENTO"],
            "ID_UNIDADE": SIECursosDisciplinas().getIdUnidade(projeto['ID_CURSO']),
            "NUM_PROCESSO": novoDocumento["NUM_PROCESSO"],
            "EVENTO_TAB": 6028,
            "EVENTO_ITEM": 1,
            "TIPO_PUBLICO_TAB": 6002,
            "TIPO_PUBLICO_ITEM": 8,
            "ACESSO_PARTICIP": "S",
            "PAGA_BOLSA": "S",
            "DT_INICIAL": edicao.dt_inicial_projeto,
            "DT_REGISTRO": date.today(),
            "AVALIACAO_TAB": 6010,
            "AVALIACAO_ITEM": 2
        })

        novoProjeto = self.api.post(self.path, projeto)
        projeto.update({"ID_PROJETO": novoProjeto.insertId})

        return projeto

    def avaliarProjeto(self, ID_PROJETO, avaliacao):
        """
        Método utilizado para avaliar um projeto

        avaliacao = 9           => indeferido (Indeferido)
        avaliacao = 2           => deferido (Em andamento)
        AVALIACAO_ITEM = 3      => Avaliado
        AVALIACAO_ITEM = 4      => Avaliado fora do prazo

        :type ID_PROJETO: int
        :type avaliacao: int
        :param ID_PROJETO: Identificador único de um PROJETO
        :param avaliacao: Um inteiro correspondente a uma avaliação
        """
        try:
            self.api.put(
                self.path,
                {
                    "ID_PROJETO": ID_PROJETO,
                    "AVALIACAO_ITEM": 3,
                    "SITUACAO_ITEM": avaliacao,
                    "DT_ULTIMA_AVAL": date.today()
                }
            )
            self.tramitarDocumentoProjeto(ID_PROJETO, avaliacao)
        except APIException:
            raise APIException("Não foi possível atualizar o estado da avaliação de um projeto.")

    @deprecated
    def removerProjeto(self, ID_PROJETO):
        """
        Dada uma entrada na tabela PROJETOS, a função busca e remove essa entrada após buscar e remover o DOCUMENTO
        relacionado, os partifipantes deste projeto, seu orgão e classificação

        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        """
        projeto = self.getProjeto(ID_PROJETO)
        SIEParticipantesProjs().removerParticipantesFromProjeto(projeto['ID_PROJETO'])
        SIEOrgaosProjetos().removerOrgaosProjetosDeProjeto(projeto['ID_PROJETO'])
        SIEClassifProjetos().removerClassifProjetosDeProjeto(projeto['ID_PROJETO'])

        if projeto["ID_DOCUMENTO"]:
            # Se existe documento relacionado a este documento.
            documento = SIEDocumentoDAO().obter_documento(projeto['ID_DOCUMENTO'])
            SIEDocumentoDAO().remover_documento(documento)
        else:
            # print "Nenhum documento relacionado ao projeto %d" % ID_PROJETO # TODO Colocar logging?
            pass

        self.api.delete(self.path, {"ID_PROJETO": ID_PROJETO})

    def situacoes(self):
        """
        A função retorna uma lista de dicionários com as possíveis situações (SITUACAO_ITEM) de um projeto

        :rtype : list
        :return: Lista de dicionários contendo as chaves `ITEM_TABELA` e `DESCRICAO`
        """
        return SIETabEstruturada().itemsDeCodigo(6011)

    def documento_inicial_padrao(self):
        # todo Property ?

        infos_tipo_documento = SIETiposDocumentosDAO().obter_parametros_tipo_documento(self.TIPO_DOCUMENTO)
        assunto_relacionado = SIEAssuntosDAO().get_by_id(infos_tipo_documento['ID_ASSUNTO_PADRAO'])

        return {
            "ID_TIPO_DOC": self.TIPO_DOCUMENTO,
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
            "RESUMO_ASSUNTO": assunto_relacionado['DESCR_ASSUNTO'],
            "DT_LIMITE_ARQ": date.today() + timedelta(days=int(assunto_relacionado['TEMPO_ARQUIVAMENTO']))
        # TODO Se for None, qual o comportamento esperado?
            # "OBSERVACOES": ?? Não estamos usando.
            # "SEQUENCIA": 1  # atualizacao do sie Out/2015
        }


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


class SIEArquivosProj(SIE):
    COD_TABELA_TIPO_ARQUIVO = 6005
    ITEM_TIPO_ARQUIVO_TERMO_OUTORGA = 19
    ITEM_TIPO_ARQUIVO_PROJETO = 1
    ITEM_TIPO_ARQUIVO_ATA_DEPARTAMENTO = 5
    ITEM_TIPO_ARQUIVO_PARECER_CEUA = 18
    ITEM_TIPO_ARQUIVO_PLANO_DE_ESTUDOS = 15
    ITEM_TIPO_ARQUIVO_RELATORIO_DOCENTE = 14
    ITEM_TIPO_ARQUIVO_PONTUACAO_LATTES = 10
    ITEM_TIPO_ARQUIVO_CURRICULO_LATTES = 12
    ITEM_TIPO_ARQUIVO_PARECER_CAMARA_GENERICO = 8
    ITEM_TIPO_ARQUIVO_PARECER_CAMARA_CADASTRO_PROJETO = 22
    ITEM_TIPO_ARQUIVO_PARECER_CAMARA_AVAL_REL_DOCENTE = 23
    ITEM_TIPO_ARQUIVO_PARECER_CAMARA_AVAL_PLANO_ESTUDOS = 24
    ITEM_TIPO_ARQUIVO_JUSTIFICATIVA_CONCLUSAO_PROJETO = 25

    def __init__(self):
        super(SIEArquivosProj, self).__init__()
        self.path = "ARQUIVOS_PROJ"

    def __conteudoDoArquivo(self, arquivo):
        """
        O campo CONTEUDO_ARQUIVO é BLOB, tendo em vista que a API espera uma string base64, o método é responsável por
        encodar o conteúdo e fornecer uma string válida

        :type arquivo: FieldStorage
        :rtype : str
        :param arquivo: Um arquivo a ser convertido
        :return: Uma string correspondente ao conteúdo de um arquivo binário, na forma de base64
        """
        return base64.b64encode(arquivo.file.read())

    def get_arquivo_projeto(self, id_projeto):
        """
        Retorna um dicionário contendo a ata de departamento que satisfaça o id_projeto ou None, caso tal arquivo não exista
        :param id_projeto:
        :return:
        """
        return self.get_arquivo(id_projeto, self.ITEM_TIPO_ARQUIVO_PROJETO)

    def get_ata_departamento(self, id_projeto):
        """
        Retorna um dicionário contendo o arquivo de projeto que satisfaça o id_projeto ou None, caso tal arquivo não exista
        :param id_projeto:
        :return:
        """
        return self.get_arquivo(id_projeto, self.ITEM_TIPO_ARQUIVO_ATA_DEPARTAMENTO)

    def get_parecer_comite_etica(self, id_projeto):
        """
        Retorna um dicionário contendo o arquivo de parecer de comite de ética que satisfaça o id_projeto ou None, caso tal arquivo não exista
        :param id_projeto:
        :return:
        """
        return self.get_arquivo(id_projeto, self.ITEM_TIPO_ARQUIVO_PARECER_CEUA)

    def get_termo_outorga(self, id_projeto):
        """
        Retorna um dicionário contendo o termo de outorga que satisfaça o id_projeto ou None, caso tal arquivo não exista
        :param id_projeto:
        :return:
        """
        return self.get_arquivo(id_projeto, self.ITEM_TIPO_ARQUIVO_TERMO_OUTORGA)

    def get_arquivos_for_bug(self):

        params = {
            'LMIN': 0,
            'LMAX': 99999,
            'ORDERBY': 'ID_ARQUIVO_PROJ',
            'SORT': 'DESC',
            'DT_INCLUSAO_MIN': date(2015, 12, 31),
            "ID_CLASSIFICACAO_PROJETO": 39718
        }

        fields = ["ID_PROJETO", "DT_INCLUSAO", "TIPO_ARQUIVO", "ID_ARQUIVO_PROJ", "NOME_ARQUIVO", "TITULO_PROJETO",
                  "COORDENADOR"]
        arquivos = self.api.get("V_ARQUIVOS_PROJ", params, fields, bypass_no_content_exception=True)

        return arquivos

    def get_arquivos_for_bug_check_b64(self):

        def is_valid_base64(s):
            return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,3}$', s)

        def duplo_64(b64string):
            string_correta = base64.b64decode(b64string)

            if is_valid_base64(string_correta):
                return True
            return False

        def arquivo_estranho(s):

            fora_ascii = [c for c in s if ord(c) < 32 or ord(c) == 127]
            if len(fora_ascii):
                return True
            return False

        params = {
            'LMIN': 0,
            'LMAX': 99999,
            'ORDERBY': 'ID_ARQUIVO_PROJ',
            'SORT': 'DESC',
            'DT_INCLUSAO_MIN': date(2015, 12, 31),
            "ID_CLASSIFICACAO_PROJETO": 39718
        }

        fields = ["ID_PROJETO", "DT_INCLUSAO", "TIPO_ARQUIVO", "ID_ARQUIVO_PROJ", "NOME_ARQUIVO", "CONTEUDO_ARQUIVO",
                  "TITULO_PROJETO", "COORDENADOR"]
        arquivos = self.api.get("V_ARQUIVOS_PROJ", params, fields, bypass_no_content_exception=True)

        arquivos2 = []
        for arquivo in list(arquivos):
            if duplo_64(arquivo[u'CONTEUDO_ARQUIVO'].strip()) or arquivo_estranho(arquivo['NOME_ARQUIVO']):
                arquivos2.append({
                    "ID_PROJETO": arquivo['ID_PROJETO'],
                    "DT_INCLUSAO": arquivo['DT_INCLUSAO'],
                    "TIPO_ARQUIVO": arquivo['TIPO_ARQUIVO'],
                    "ID_ARQUIVO_PROJ": arquivo['ID_ARQUIVO_PROJ'],
                    "NOME_ARQUIVO": arquivo['NOME_ARQUIVO'],
                    "TITULO_PROJETO": arquivo['TITULO_PROJETO'],
                    "COORDENADOR": arquivo['COORDENADOR']
                })

        return arquivos2

    def get_arquivos_projeto(self, id_projeto):
        """
        Retorna um APIRequestObject contendo os arquivos que satisfaçam o id_projeto passado como parâmetro
        :param id_projeto: id_projeto relacionado ao arquivo
        :return: dicionário contendo {NOME_ARQUIVO:, file:, CONTEUDO_ARQUIVO.
        """
        params = {
            'ID_PROJETO': id_projeto,
            'LMIN': 0,
            'LMAX': 999,
            'ORDERBY': 'ID_ARQUIVO_PROJ',
            'SORT': 'DESC'
        }

        arquivo = self.api.get("V_ARQUIVOS_PROJ", params, bypass_no_content_exception=True)
        return arquivo

    def get_arquivo_by_id(self, id_arquivo_proj):
        """
        Retorna uma row da view V_ARQUIVOS_PROJ
        Row representa um arquivo do projeto

        :param id_arquivo_proj: id do arquivo
        :return: dicionário contendo informações da linha respectiva no bd

        """
        params = {
            "ID_ARQUIVO_PROJ": id_arquivo_proj
        }
        return self.api.get_single_result("V_ARQUIVOS_PROJ", params, bypass_no_content_exception=True)

    def get_arquivo_by_column_e_tipo(self, tipo, valor_coluna, coluna="ID_PROJETO"):
        """
        Pega o id de um arquivo com base em uma coluna e o valor passado com um tipo.
        :param coluna: coluna para filtrar
        :param valor_coluna: valor da coluna para filtrar
        :param tipo: tipo do arquivo
        :return:
        """

        where = {
            coluna: valor_coluna,
            "TIPO_ARQUIVO_ITEM": tipo,
            "ORDERBY": "ID_ARQUIVO_PROJ",
            "SORT": "DESC",
        }

        fields = ["ID_ARQUIVO_PROJ"]

        return self.api.get_single_result(self.path, where, fields, bypass_no_content_exception=True)

    def get_arquivo(self, id_projeto, tipo_arquivo):
        """
        Retorna um dicionário contendo o arquivo que satisfaça o id_projeto e tipo_arquivo e ou None, caso tal arquivo não exista
        :param id_projeto: id_projeto relacionado ao arquivo
        :param tipo_arquivo: tipo do arquivo
        :return: dicionário contendo {NOME_ARQUIVO:, file:, CONTEUDO_ARQUIVO.
        """
        params = {
            'ID_PROJETO': id_projeto,
            'TIPO_ARQUIVO_ITEM': tipo_arquivo,
            'LMIN': 0,
            'LMAX': 1,
            'ORDERBY': 'ID_ARQUIVO_PROJ',
            'SORT': 'DESC'
        }

        fields = ["NOME_ARQUIVO", "CONTEUDO_ARQUIVO"]
        try:
            arquivo = self.api.get(self.path, params, fields, 0).content  # TODO Esse cara vem em base64?
        except (ValueError, AttributeError):
            arquivo = None
        return arquivo

    def get_arquivo_by_id(self, id_arquivo_proj):
        """
        Retorna uma row da view V_ARQUIVOS_PROJ
        Row representa um arquivo do projeto

        :param id_arquivo_proj: id do arquivo
        :return: dicionário contendo informações da linha respectiva no bd

        """
        params = {
            "ID_ARQUIVO_PROJ": id_arquivo_proj
        }
        return self.api.get_single_result("V_ARQUIVOS_PROJ", params, bypass_no_content_exception=True)

    def salvar_arquivo(self, nome_arquivo, arquivo, id_projeto, tipo_arquivo):
        """
        :type arquivo: FieldStorage
        :param arquivo: Um arquivo correspondente a um projeto que foi enviado para um formulário
        :type id_projeto: int/string
        :param id_projeto: Um id de projeto
        :rtype : dict
        """
        arquivo_proj = {
            "ID_PROJETO": id_projeto,
            "DT_INCLUSAO": date.today(),
            "TIPO_ARQUIVO_TAB": self.COD_TABELA_TIPO_ARQUIVO,
            "TIPO_ARQUIVO_ITEM": tipo_arquivo,
            "NOME_ARQUIVO": remover_acentos_query(nome_arquivo),
            "CONTEUDO_ARQUIVO": self.handle_blob(arquivo)
        }

        try:
            novo_arquivo_proj = self.api.post(self.path, arquivo_proj)
            arquivo_proj.update({"ID_ARQUIVO_PROJ": novo_arquivo_proj.insertId})  # ????
            return arquivo_proj
        except APIException as e:
            raise SIEException("Falha ao salvar arquivo.", e)

    def atualizar_arquivo(self, id_arquivo, params):
        if params is None:
            raise RuntimeError  # TODO SIEError?

        assert isinstance(params, dict)

        params.update({
            "ID_ARQUIVO_PROJ": id_arquivo
        })

        try:
            self.api.put(self.path, params)
        except APIException as e:
            raise SIEException("Falha ao atualizar arquivo", e)

    def deletar_arquivo(self, id_arquivo):
        self.api.delete(self.path, {"ID_ARQUIVO_PROJ": id_arquivo})

    @deprecated
    def salvarArquivo(self, arquivo, projeto, funcionario, TIPO_ARQUIVO_ITEM, callback=None):
        """

        TIPO_ARQUIVO_ITEM = 1       => Projeto

        :type arquivo: FieldStorage
        :param arquivo: Um arquivo correspondente a um projeto que foi enviado para um formulário
        :type projeto: dict
        :param projeto: Um dicionário contendo uma entrada da tabela PROJETOS
        :type funcionario: dict
        :param funcionario: Dicionário de IDS de um funcionário
        :rtype : dict
        """
        arquivoProj = {
            "ID_PROJETO": projeto["ID_PROJETO"],
            "DT_INCLUSAO": date.today(),
            "TIPO_ARQUIVO_TAB": 6005,
            "TIPO_ARQUIVO_ITEM": TIPO_ARQUIVO_ITEM,
            "NOME_ARQUIVO": arquivo.filename,
            "CONTEUDO_ARQUIVO": self.__conteudoDoArquivo(arquivo)
        }
        # TODO remover comentários quando BLOB estiver sendo salvo no DB2
        # novoArquivoProj = self.api.post(self.path, arquivoProj)
        # arquivoProj.update({"ID_ARQUIVO_PROJ": novoArquivoProj.insertId})
        # self.salvarDB2BLOB(arquivoProj) # não era para estar aqui!
        if callback:
            callback(arquivo, arquivoProj, funcionario)

        return arquivoProj

        # def salvarCopiaLocal(self, arquivo, arquivo_proj, funcionario, edicao):
        #     """
        #
        #     :type arquivo: FieldStorage
        #     :param arquivo: Um arquivo correspondente a um projeto que foi enviado para um formulário
        #     :type arquivo_proj: dict
        #     :param arquivo_proj: Um dicionário contendo uma entrada da tabela ARQUIVO_PROJS
        #     :type funcionario: dict
        #     :param funcionario: Dicionário de IDS de um funcionário
        #     :type edicao: gluon.storage.Storage
        #     :param edicao: Uma entrada da tabela `edicao`
        #     """
        #     # TODO id_arquivo_proj não está com o comportamente desejado, mas é necessário até que BLOBS sejam inseridos corretamente. Remover o mesmo após resolver problema
        #     # noinspection PyExceptClausesOrder,PyBroadException
        #     try:
        #         with open(arquivo.fp.name, 'rb') as stream:
        #             i = current.db.projetos.insert(
        #                 anexo_tipo=arquivo.type,
        #                 anexo_nome=arquivo.filename,
        #                 id_arquivo_proj=None,
        #                 id_funcionario=funcionario["ID_FUNCIONARIO"],
        #                 id_projeto=arquivo_proj["ID_PROJETO"],
        #                 edicao=edicao.id,
        #                 arquivo=current.db.projetos.arquivo.store(stream, arquivo.filename),      # upload
        #                 tipo_arquivo_item=arquivo_proj["TIPO_ARQUIVO_ITEM"],
        #                 dt_envio=datetime.now()
        #             )
        #             print "Gravou localmente [%s] com ID [%d]" % (arquivo.filename, i)
        #     except IOError as e:
        #         if e.errno == 63:
        #             current.session.flash += "Impossivel salvar o arquivo %s. Nome muito grande" % arquivo.filename
        #     except IntegrityError:
        #         current.db.rollback()
        #         current.session.flash += "Não é possível enviar mais de um arquivo por etapa"
        #     except Exception as e:
        #         current.db.rollback()
        #         raise e
        #     finally:
        #         current.db.commit()


class SIEClassificacoesPrj(SIE):
    COD_CLASSIFICACAO_PRJ_CAMARA_PESQUISA = 33
    COD_CLASSIFICACAO_PRJ_CLASSIFICACAO_CNPQ = 3
    COD_CLASSIFICACAO_PRJ_COMITE_ETICA = 32
    COD_CLASSIFICACAO_PRJ_GRUPO_CNPQ = 4
    ITEM_PARECER_COMITE_ETICA_NAO_SE_APLICA = 40172

    def __init__(self):
        super(SIEClassificacoesPrj, self).__init__()
        self.path = "CLASSIFICACOES_PRJ"

    def getClassificacoesPrj(self, classificacaoItem, codigo):
        """
        Talvez devesse se chamar get_classificacao_projeto


        CLASSIFICACAO_ITEM  => 1 - Tipos de Projetos, 41 - Disciplina vinculada
        CODIGO PARA CLASSIFICACAO_ITEM = 1 => 1 - Ensino, 2 - Pesquisa, 3 - Extensão, 4 - Desenvolvimento institucional

        :type classificacaoItem: int
        :type codigo: int
        :param classificacaoItem:
        :param codigo: COD_DISCIPLINA de uma disciplina do SIE
        :rtype : list
        :return: Uma lista de dicionários com os tipos de projetos
        """
        params = {
            'CLASSIFICACAO_ITEM': classificacaoItem,
            'CODIGO': codigo
        }
        fields = [
            'ID_CLASSIFICACAO',
            'DESCRICAO'
        ]
        return self.api.get(self.path, params, fields).content

    def get_descricao_classificacoes_by_ids(self,lista_ids_classificacao):
        """
        Passada uma lista de id_classificacao, retorna a descricao para cada uma.
        :param lista_ids_classificacao:
        :return:
        """
        params = {
            'LMIN': 0,
            'LMAX': 9999,
            "ID_CLASSIFICACAO_SET": lista_ids_classificacao
        }

        fields = ['ID_CLASSIFICACAO', "DESCRICAO"]

        return self.api.get(self.path, params, fields)

    def get_classificacoes_proj(self, classificacao_item):
        """
        CLASSIFICACAO_ITEM  => 1 - Tipos de Projetos, 41 - Disciplina vinculada
        CODIGO PARA CLASSIFICACAO_ITEM = 1 => 1 - Ensino, 2 - Pesquisa, 3 - Extensão, 4 - Desenvolvimento institucional

        :type classificacao_item: int
        :param classificacao_item:
        :rtype : list
        :return: Uma lista de dicionários com os tipos de projetos
        """
        params = {
            'CLASSIFICACAO_ITEM': classificacao_item,
            "ORDERBY": "DESCRICAO",
            "SORT": 'ASC'
        }
        params.update({
            'LMIN': 0,
            'LMAX': 9999
        })
        fields = ["ID_CLASSIFICACAO", "DESCRICAO", "CODIGO", "ID_CLASSIF_SUP"]
        return self.api.get(self.path, params, fields).content

    def get_camaras_pesquisa(self):
        try:
            camaras_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_CAMARA_PESQUISA)
            camaras = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8')) for d in camaras_dict]
        except AttributeError:
            camaras = None

        return camaras

    def get_classificacoes_cnpq(self):
        try:
            classif_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_CLASSIFICACAO_CNPQ)
            classif = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8'), d[u'ID_CLASSIF_SUP']) for d in
                       classif_dict]
        except AttributeError:
            classif = None

        return classif

    def get_grupos_cnpq(self):
        try:
            grupo_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_GRUPO_CNPQ)
            grupos = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8'), d[u'ID_CLASSIF_SUP']) for d in
                      grupo_dict]
        except AttributeError:
            grupos = None

        return grupos

    def get_comites_etica(self):
        try:
            comites_dict = self.get_classificacoes_proj(self.COD_CLASSIFICACAO_PRJ_COMITE_ETICA)
            comites = [(d[u'ID_CLASSIFICACAO'], d[u'DESCRICAO'].encode('utf-8')) for d in comites_dict]
        except AttributeError:
            comites = None

        return comites


class SIEParticipantesProjs(SIE):
    def __init__(self):
        super(SIEParticipantesProjs, self).__init__()
        self.path = "PARTICIPANTES_PROJ"

    def criarParticipanteCoordenador(self, ID_PROJETO, funcionario):
        """
        FUNCAO_TAB = 6003       => Papel do participante de um projeto
        FUNCAO_ITEM = 1         => Coordenador
        SITUACAO = A            => Ao adicionar um participante, ele estará ativo(A)

        :param ID_PROJETO: Identificador único de uma entrada na tabela PROJETOS
        :param funcionario: Dicionário de IDS de um funcionário
        :rtype : unirio.api.apiresult.APIPostResponse
        """
        escolaridade = SIEFuncionarios().getEscolaridade(funcionario["ID_FUNCIONARIO"])
        participante = {
            "TITULACAO_ITEM": escolaridade["ESCOLARIDADE_ITEM"],
            "ID_PESSOA": funcionario["ID_PESSOA"],
            "ID_CONTRATO_RH": funcionario["ID_CONTRATO_RH"]
            # "DESCR_MAIL": funcionario["DESCR_MAIL"],   # TODO deveria constar na session.funcionario
        }

        return self._criarParticipante(ID_PROJETO, 1, participante)

    def criarParticipanteBolsista(self, projeto, aluno, edicao):
        """
        TITULACAO_ITEM = 9      => Superior Incompleto
        FUNCAO_ITEM = 3         => Bolsista

        :param aluno: Dicionário de atributos de um aluno
        :rtype : unirio.api.apiresult.APIPostResponse
        """
        ID_BOLSISTA = SIEBolsistas().criarBolsista(SIEBolsas().getBolsa(6), edicao, aluno, projeto).insertId

        participante = {
            "ID_PESSOA": aluno["ID_PESSOA"],
            "ID_CURSO_ALUNO": aluno["ID_CURSO_ALUNO"],
            "TITULACAO_ITEM": 9,
            "DESCR_MAIL": aluno["DESCR_MAIL"],
            "ID_BOLSISTA": ID_BOLSISTA
        }

        return self._criarParticipante(projeto['ID_PROJETO'], 3, participante)

    def _criarParticipante(self, ID_PROJETO, FUNCAO_ITEM, participante={}):
        """
        FUNCAO_TAB = 6003       => Papel do participante de um projeto

        FUNCAO_ITEM previstas na TAB_ESTRUTURADA:

        1 => Coordenador
        2 => Orientador
        3 => Bolsista
        4 => Participante Voluntário
        5 => Pesquisador Colaborador
        6 => Co-orientador
        10 => Apresentador
        11 => Autor
        12 => Co-autor
        13 => Executor
        14 => Estagiário
        15 => Acompanhante
        16 => Monitoria não subsidiada
        20 => Não definida
        17 => Orientador de aluno
        50 => Candidato a bolsista

        :type ID_PROJETO: int
        :param ID_PROJETO: Identificador único de uma projeto na tabela PROJETOS
        :type FUNCAO_ITEM: int
        :param FUNCAO_ITEM: Identificador úncio de uma descrição de função. Identificadores possíveis podem ser
                            encontrados na TAB_ESTRUTURADA, COD_TABELA 6003
        :rtype : unirio.api.apiresult.APIPostResponse
        """
        participante.update({
            "CARGA_HORARIA": 20,
            "CH_SUGERIDA": 20,
            "DT_INICIAL": date.today(),
            "ID_PROJETO": ID_PROJETO,
            "FUNCAO_ITEM": FUNCAO_ITEM,
            "FUNCAO_TAB": 6003,
            "ID_PESSOA": participante["ID_PESSOA"],
            "SITUACAO": "A",
            "TITULACAO_TAB": 168,
        })

        return self.api.post(self.path, participante)

    def descricaoDeFuncaoDeParticipante(self, participante):
        """
        Dado um parcipante, o método retorna a descrição textual de sua função no projeto

        :type participante: dict
        :rtype : str
        :param participante: Um dicionário correspondente a uma entrada da tabela PARTICIPANTES_PROJ que contenha pelo
        menos a chave FUNCAO_ITEM
        """
        try:
            return SIETabEstruturada().descricaoDeItem(participante["FUNCAO_ITEM"], 6003)
        except AttributeError:
            return "Não foi possível recuperar"

    def getParticipantes(self, params):
        """

        :rtype : list
        """
        params.update({
            'LMIN': 0,
            'LMAX': 9999
        })

        try:
            return self.api.get(self.path, params).content
        except (ValueError, AttributeError):
            return None

    def getBolsistas(self, ID_PROJETO):
        params = {
            'ID_PROJETO': ID_PROJETO,
            'FUNCAO_ITEM': 3
        }
        return self.getParticipantes(params)

    def getParticipacoes(self, pessoa, params={}):
        """

        :param pessoa: Um dicionário da view V_FUNCIONARIO_IDS
        :param params: Um dicionários de parâmetros a serem utilizados na busca
        :return: Uma lista de participações em projetos
        :rtype: list
        """
        params.update({
            "ID_PESSOA": pessoa["ID_PESSOA"],
            "LMIN": 0,
            "LMAX": 9999
        })

        try:
            return self.api.get(self.path, params).content
        except ValueError:
            return []

    def getParticipante(self, ID_PARTICIPANTE):
        params = {
            'ID_PARTICIPANTE': ID_PARTICIPANTE,
            'LMIN': 0,
            'LMAX': 1
        }
        return self.api.get(self.path, params).first()

    def removerParticipante(self, ID_PARTICIPANTE):
        self.api.delete(self.path, {"ID_PARTICIPANTE": ID_PARTICIPANTE})

    def removerParticipantesFromProjeto(self, ID_PROJETO):
        params = {
            "ID_PROJETO": ID_PROJETO,
            "LMIN": 0,
            "LMAX": 99999
        }
        try:
            participantes = self.api.get(self.path, params, ['ID_PARTICIPANTE'])
            for p in participantes.content:
                self.removerParticipante(p['ID_PARTICIPANTE'])
        except ValueError:
            print "Nenhum participante para remover do projeto %d" % ID_PROJETO

    def inativarParticipante(self, participante):
        """
        Dado um participante, o método inativa o mesmo e a bolsa referente.

        :type participante: dict
        :param participante: Uma entrada da tabela PARTICIPANTES_PROJ, contendo as keys ID_PARTICIPANTE e ID_BOLSISTA
        """
        params = {
            'ID_PARTICIPANTE': participante['ID_PARTICIPANTE'],
            'SITUACAO': 'I',
            'DT_FINAL': date.today()
        }
        self.api.put(self.path, params)
        SIEBolsistas().inativarBolsista(participante['ID_BOLSISTA'])


class SIECursosDisciplinas(SIE):
    def __init__(self):
        super(SIECursosDisciplinas, self).__init__()
        self.path = "V_CURSOS_DISCIPLINAS"

    def getCursos(self, params=None):
        if not params:
            params = {}

        params.update({
            "LMIN": 0,
            "LMAX": 99999,
            "ORDERBY": "NOME_CURSO",
            "DISTINCT": "T"
        })
        fields = [
            "NOME_CURSO",
            "ID_CURSO"
        ]
        return self.api.get(self.path, params, fields).content

    def getCursosGraduacao(self):
        """
        NIVEL_CURSO_ITEM = 3    => Graduação

        :rtype : list
        :return: Returna uma lista de cursos de graduação
        """
        params = {"NIVEL_CURSO_ITEM": 3}
        return self.getCursos(params)

    def getDisciplinas(self, ID_CURSO, filtroObrigatorias=False):
        params = {
            "LMIN": 0,
            "LMAX": 9999,
            "ID_CURSO": ID_CURSO,
            "ORDERBY": "NOME_DISCIPLINA"
        }
        if filtroObrigatorias:
            params["OBRIGATORIA"] = "S"
        fields = [
            "NOME_DISCIPLINA",
            "COD_DISCIPLINA"
        ]
        return self.api.get(self.path, params, fields).content

    def getIdUnidade(self, ID_CURSO):
        """
        :type ID_CURSO: int
        :rtype : int
        """
        params = {
            "ID_CURSO": ID_CURSO
        }
        fields = ["ID_UNIDADE"]
        return self.api.get(self.path, params, fields).first()["ID_UNIDADE"]


class SIEClassifProjetos(SIE):
    def __init__(self):
        super(SIEClassifProjetos, self).__init__()
        self.path = "CLASSIF_PROJETOS"

    @deprecated
    def criarClassifProjetos(self, ID_PROJETO, ID_CLASSIFICACAO):
        """

        :type ID_PROJETO: int
        :param ID_PROJETO: Identificador único de um projeto
        :type ID_CLASSIFICACAO: int
        :param ID_CLASSIFICACAO: Identificador único da classificação de um projeto
        :rtype: unirio.api.result.APIPOSTResponse
        """
        classifProj = {
            "ID_PROJETO": ID_PROJETO,
            "ID_CLASSIFICACAO": ID_CLASSIFICACAO
        }

        try:
            return self.api.post(self.path, classifProj)
        except APIException as e:
            raise SIEException("Não foi possível criar uma nova classificação para o projeto.", e)

    @deprecated
    def removerClassifProjetos(self, ID_CLASSIF_PROJETO):
        self.api.delete(self.path, {"ID_CLASSIF_PROJETO": ID_CLASSIF_PROJETO})

    @deprecated
    def removerClassifProjetosDeProjeto(self, ID_PROJETO):
        params = {
            "ID_PROJETO": ID_PROJETO,
            "LMIN": 0,
            "LMAX": 9999
        }
        try:
            classifs = self.api.get(self.path, params, ["ID_CLASSIF_PROJETO"], bypass_no_content_exception=True)
            for classif in classifs:
                self.removerClassifProjetos(classif['ID_CLASSIF_PROJETO'])
        except APIException as e:
            raise SIEException("Falha ao remover classificações", e)

    @deprecated
    def getClassifProjetos(self, ID_PROJETO):
        params = {
            "ID_PROJETO": ID_PROJETO,
            "LMIN": 0,
            "LMAX": 9999
        }
        try:
            return self.api.get(self.path, params)
        except ValueError:
            return None

    @deprecated
    def getClassifProjetosEnsino(self, ID_PROJETO):
        try:
            return self.getClassifProjetos(ID_PROJETO).content[0]
        except ValueError:
            return None

    @deprecated
    def atualizar(self, ID_CLASSIF_PROJETO, ID_CLASSIFICACAO):
        raise NotImplementedError
        # self.db.log_admin.insert(
        #             acao='update',
        #             valores=ID_CLASSIFICACAO,
        #             tablename='CLASSIF_PROJETOS',
        #             colname='ID_CLASSIFICACAO',
        #             uid=ID_CLASSIF_PROJETO,
        #             user_id=current.auth.user_id,
        #             dt_alteracao=datetime.now()
        #     )
        # return self.api.put(self.path, {
        #     'ID_CLASSIF_PROJETO': ID_CLASSIF_PROJETO,
        #     'ID_CLASSIFICACAO': ID_CLASSIFICACAO
        # })

    def atualizar_classificacoes(self, id_projeto, classificacoes_cnpq, grupos, comite, camara):
        """

        :param id_projeto:
        :param classificacoes_cnpq:
        :param grupos:
        :param comite:
        :param camara:
        :return:
        """

        # pior maneira de se fazer isso: deletar o que tem, criar de novo.
        self.removerClassifProjetosDeProjeto(id_projeto)  # TRY???

        todas_classificacoes = camara + classificacoes_cnpq + comite + grupos

        for classificacao in todas_classificacoes:
            self.criarClassifProjetos(id_projeto, classificacao)

    def get_classif_projeto(self, params):

        params.update({
            "LMIN": 0,
            "LMAX": 9999,
        })
        try:
            res = self.api.get("V_PROJETOS_CLASSIFICACOES", params)
            return res.content if res is not None else []
        except (AttributeError, ValueError, NoContentException):
            return []

    def get_classificacoes_cnpq(self, id_projeto):

        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_CLASSIFICACAO_CNPQ
        }
        classificacoes_cnpq = self.get_classif_projeto(params)
        if classificacoes_cnpq:
            ids_classificacoes_cnpq = [row[u'ID_CLASSIFICACAO'] for row in classificacoes_cnpq]
            return ids_classificacoes_cnpq
        return []

    def get_grupos_cnpq(self, id_projeto):

        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_GRUPO_CNPQ
        }
        grupos_cnpq = self.get_classif_projeto(params)
        if grupos_cnpq:
            ids_grupos_cnpq = [row[u'ID_CLASSIFICACAO'] for row in grupos_cnpq]
            return ids_grupos_cnpq
        return []

    def get_camara_pesquisa(self, id_projeto):
        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_CAMARA_PESQUISA
        }
        camara_pesquisa = self.get_classif_projeto(params)
        if camara_pesquisa:
            return camara_pesquisa[0][u"ID_CLASSIFICACAO"]
        return None

    def get_comite_etica(self, id_projeto):
        params = {
            "ID_PROJETO": id_projeto,
            "CLASSIFICACAO_ITEM": SIEClassificacoesPrj.COD_CLASSIFICACAO_PRJ_COMITE_ETICA
        }
        comite_etica = self.get_classif_projeto(params)
        if comite_etica:
            return comite_etica[0][u"ID_CLASSIFICACAO"]
        return None


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
