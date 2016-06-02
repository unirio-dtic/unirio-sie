# coding=utf-8
import collections
from datetime import date
from deprecate import deprecated

from .avaliacao import SIEAvaliacaoProjsPesquisaDAO
from unirio.api import NoContentException, APIException
from unirio.sie.documentos import SIEDocumentoDAO
from unirio.sie.exceptions import SIEException
from unirio.sie.projetos.base import SIEProjetos
from unirio.sie.projetos.classificacoes import SIEClassifProjetos
from unirio.sie.projetos.arquivos import SIEArquivosProj
from unirio.sie.tab_estruturada import SIETabEstruturada
from unirio.sie.utils import sie_str_to_date, remover_acentos_query

__author__ = 'diogomartins'


class SIEProjetosPesquisa(SIEProjetos):
    """
    Classe que representa os projetos de pesquisa
    """

    COD_TABELA_FUNDACOES = 6025  # Fundações
    COD_TABELA_FUNCOES_PROJ = 6003  # Funções Projeto
    COD_TABELA_FUNCOES_ORGAOS = 6006
    COD_TABELA_TITULACAO = 168  # Titulação
    COD_TABELA_TIPO_EVENTO = 6028  # => Tipos de Eventos
    COD_TABELA_TIPO_PUBLICO_ALVO = 6002  # => Público alvo
    COD_TABELA_AVALIACAO_PROJETOS_INSTITUICAO = 6010  # => Avaliação dos projetos da Instituição
    COD_TABELA_SITUACAO = 6011

    ITEM_TAB_ESTRUTURADA_DESCRICAO_CAMPO = 0
    ITEM_TITULACAO_INDEFINIDA = 99
    ITEM_FUNDACOES_NAO_SE_APLICA = 1  # => Não se aplica
    ITEM_TIPO_EVENTO_NAO_SE_APLICA = 1  # => Não se aplica
    ITEM_TIPO_PUBLICO_3_GRAU = 8  # => 3o grau
    ITEM_AVALIACAO_PROJETOS_INSTITUICAO_NAO_AVALIADO = 1  # => Não-avaliado
    ITEM_AVALIACAO_PROJETOS_INSTITUICAO_PENDENTE_AVALIACAO = 2
    ITEM_AVALIACAO_PROJETOS_AVALIADO = 3

    ITEM_CLASSIFICACAO_PROJETO_PESQUISA = 39718

    ITEM_SITUACAO_SUSPENSO = 4
    ITEM_SITUACAO_RENOVADO = 6
    ITEM_SITUACAO_TRAMITE_REGISTRO = 8
    ITEM_SITUACAO_INDEFERIDO = 9
    ITEM_SITUACAO_ANDAMENTO = 2
    ITEM_SITUACAO_CONCLUIDO = 1
    ITEM_SITUACAO_CANCELADO = 5

    # TODO Ter estes parâmetros HARD-CODED é uma limitação.
    ITEM_FUNCOES_PROJ_CANDIDATO_BOLSISTA = 50
    ITEM_FUNCOES_PROJ_DESCR = 0
    ITEM_FUNCOES_PROJ_COORDENADOR = 1
    ITEM_FUNCOES_PROJ_BOLSISTA = 3
    ITEM_FUNCOES_PROJ_NAO_DEFINIDA = 20

    ITEM_FUNCOES_ORGAOS_RESPONSAVEL = 5
    ITEM_FUNCOES_ORGAOS_AGENCIA_FOMENTO = 4
    ITEM_FUNCOES_ORGAOS_PARTICIPANTE = 3
    ITEM_ESTADO_REGULAR = 1

    TIPO_DOCUMENTO = 217

    SITUACAO_ATIVO = 'A'
    ACESSO_PARTICIPANTES_APENAS_COORDENADOR = 'N'
    NAO_PAGA_BOLSA = 'N'

    def __init__(self):
        super(SIEProjetosPesquisa, self).__init__()

    def get_agencia_fomento(self, id_projeto):
        """

        :param id_projeto: int/string representando a id de um projeto do qual se quer a agência de fomento
        :return: None se não existe agencia de fomento para o projeto ou a "row" vinda do banco.
        """
        params = {
            'ID_PROJETO': id_projeto,
            'FUNCAO_ORG_ITEM': self.ITEM_FUNCOES_ORGAOS_AGENCIA_FOMENTO,
            'LMIN': 0,
            'LMAX': 1,
            'ORDERBY': 'ID_ORGAO_PROJETO',
            "SORT": 'ASC'
        }

        try:
            agencias = self.api.get("V_PROJETOS_ORGAOS", params, cache_time=0)
            return agencias.first()
        except (NoContentException, ValueError):
            return None

    def enviar_relatorio_docente(self, relatorio, params_projeto):

        documento_dao = SIEDocumentoDAO()

        avaliacao = SIEAvaliacaoProjsPesquisaDAO().get_avaliacao(params_projeto['ANO_REF_AVAL'], relatorio.id_projeto,
                                                                 params_projeto["PERIODO_REF_TAB"],
                                                                 params_projeto["PERIODO_REF_ITEM"])
        if avaliacao:
            avaliacao_com_professor = SIEAvaliacaoProjsPesquisaDAO().is_avaliacao_com_professor(avaliacao)
            if not avaliacao_com_professor:
                raise SIEException(
                    "Já há avaliação cadastrada para este projeto neste período de avaliação. Caso queira enviar outra avaliação, entre em contato com a DPq.")
            else:

                # Salva relatorio
                arquivo_salvo = SIEArquivosProj().salvar_arquivo(nome_arquivo=relatorio.filename,
                                                                 arquivo=relatorio.arquivo,
                                                                 id_projeto=relatorio.id_projeto,
                                                                 tipo_arquivo=SIEArquivosProj.ITEM_TIPO_ARQUIVO_RELATORIO_DOCENTE)

                try:
                    # atualizar ref tabela de arquivos com id da avaliacao
                    SIEArquivosProj().atualizar_arquivo(arquivo_salvo["ID_ARQUIVO_PROJ"],
                                                        {"ID_AVALIACAO_PROJ": avaliacao["ID_AVALIACAO_PROJ"]})
                except:
                    # TODO Rollback do upload de arquivo
                    raise

                #

                # obtem estado atual
                documento = documento_dao.obter_documento(avaliacao["ID_DOCUMENTO"])
                tramitacao_atual = documento_dao.obter_tramitacao_atual(documento)

                # recebe documento se necessario
                try:
                    documento_dao.receber_documento(documento)
                except:
                    # TODO Rollback do atualizar arquivo e do salvar.
                    raise


                # tramita para DPq de novo.
                fluxo = documento_dao.obter_fluxo_inicial(
                    documento)  # TODO É o fluxo inicial? Me parece ser! Senão seria o último.

                try:
                    documento_dao.tramitar_documento(documento, fluxo)
                except:
                    # TODO Rollback do receber do documento (ou n), do atualizar e do salvar
                    raise
        else:

            # TODO Isso deve ser atômico de alguma forma, ou ter vários try,except.

            # Salva relatorio
            arquivo_salvo = SIEArquivosProj().salvar_arquivo(nome_arquivo=relatorio.filename,
                                                             arquivo=relatorio.arquivo,
                                                             id_projeto=relatorio.id_projeto,
                                                             tipo_arquivo=SIEArquivosProj.ITEM_TIPO_ARQUIVO_RELATORIO_DOCENTE)

            # cria documento avaliacao
            documento_avaliacao = SIEAvaliacaoProjsPesquisaDAO().documento_inicial_padrao()
            projeto = self.get_projeto(relatorio.id_projeto)

            documento_avaliacao.update({
                "RESUMO_ASSUNTO": "Projeto n" + u"\u00BA " + projeto['NUM_PROCESSO'].strip()  # Parece ser.
            })

            try:
                documento = documento_dao.criar_documento(documento_avaliacao)  # PASSO 1
            except SIEException:
                # TODO rollback do salvar arquivo.
                raise

            # cria avaliacao para o arquivo
            try:
                avaliacao = SIEAvaliacaoProjsPesquisaDAO().criar_avaliacao(projeto, documento, params_projeto,
                                                                           data_prorrogacao=relatorio.nova_data_conclusao,
                                                                           obs=relatorio.obs)

            except SIEException:
                # TODO Rollback do upload do arquivo e da criação de documento
                raise

            try:
                # atualizar ref tabela de arquivos com id da avaliacao
                SIEArquivosProj().atualizar_arquivo(arquivo_salvo["ID_ARQUIVO_PROJ"],
                                                    {"ID_AVALIACAO_PROJ": avaliacao["ID_AVALIACAO_PROJ"]})
            except SIEException:
                # TODO Rollback da criação da avaliação, da criação do documento e do upload do arquivo.
                raise

            # tramita para a câmara
            fluxo = documento_dao.obter_fluxo_inicial(documento)

            try:
                documento_dao.tramitar_documento(documento, fluxo)
            except:
                # TODO Rollback da atualização do arquivo, criação da avaliação, da criação do documento e do upload do arquivo.
                raise

            try:
                # atualizar projeto com avaliacao_item pendente.
                self.atualizar_projeto({
                    "ID_PROJETO": relatorio.id_projeto,
                    "AVALIACAO_ITEM": SIEProjetosPesquisa.ITEM_AVALIACAO_PROJETOS_INSTITUICAO_PENDENTE_AVALIACAO
                })
            except:
                # TODO Rollback da tramitação, da atualização do arquivo, criação da avaliação, da criação do documento e do upload do arquivo.
                raise

    def retramitar_projeto(self,id_projeto , id_documento):
        """
        Retramita um projeto que estava em ajustes com o professor.

        :param id_documento: id_documento do projeto em questão
        :type id_documento: int
        :param id_projeto: id_projeto do projeto em questão
        :type id_projeto: int
        :return:
        """

        self._valida_classificacoes_projetos(id_projeto)

        documento = SIEDocumentoDAO().obter_documento(id_documento)
        SIEDocumentoDAO().receber_documento(documento)
        self._tramita_professor_dpq(documento)

        # TODO Precisa atualizar projeto??

    def registrar_projeto(self, id_projeto):
        """
        Cria o documento e tramita para DPQ. Muda status do projeto tb.
        :param id_projeto:
        :return:
        :rtype: bool
        """

        self._valida_classificacoes_projetos(id_projeto)

        documento = self._cria_documento_projeto()

        # marcando a maneira de lidar com o fluxo caso o destino esteja em uma query (IND_QUERY='S')
        # resolvedor_destino = lambda fluxo: self.resolve_destino_tramitacao(fluxo, id_projeto) # Era usado anteriormente. Deixando aqui pois pode server para depois.

        self._tramita_professor_dpq(documento)

        projeto = {
            "ID_PROJETO": id_projeto,
            "ID_DOCUMENTO": documento['ID_DOCUMENTO'],
            "NUM_PROCESSO": documento['NUM_PROCESSO']
        }

        self.atualizar_projeto(projeto)

    def _tramita_professor_dpq(self, documento):
        """
        Faz uma tramitação correspondente ao passo inicial do cadastro de projeto (pega fluxo inicial).

        :param documento:
        :return:
        """

        documentoDAO = SIEDocumentoDAO()
        fluxo = documentoDAO.obter_fluxo_inicial(documento)
        try:
            documentoDAO.tramitar_documento(documento, fluxo)
        except:
            # TODO Rollback da criação de documento.
            raise

    def _cria_documento_projeto(self):

        documento_projeto = self.documento_inicial_padrao()
        documento = SIEDocumentoDAO().criar_documento(documento_projeto)  # PASSO 1
        return documento

    def _valida_classificacoes_projetos(self, id_projeto):
        # verificar se tem classificações
        classificacoes_projeto = SIEClassifProjetos().get_classificacoes_cnpq(id_projeto)
        grupos_projeto = SIEClassifProjetos().get_grupos_cnpq(id_projeto)
        camara_pesquisa = SIEClassifProjetos().get_camara_pesquisa(id_projeto)
        if not camara_pesquisa or not classificacoes_projeto or not grupos_projeto:
            raise SIEException("Projeto não cadastrado. Favor informar as classificações na aba anterior.")

    def resolve_destino_tramitacao(self, fluxo, id_projeto):
        """
        Resolve o destino do fluxo. No caso de projetos, faz uma query específica no banco.
        Ideal seria que este método fosse uma espécie de delegate, com parâmetros variáveis. pq todo o método primeira tramitacao iria para dentro de um DAO de documento.
        """
        params = {
            "FUNCAO_ORG_ITEM": SIEProjetosPesquisa.ITEM_FUNCOES_ORGAOS_RESPONSAVEL,  # TODO ??? Não seria a câmara??
            "ID_PROJETO": id_projeto
        }
        id_destino = self.api.get("ORGAOS_PROJETOS", params).first()
        return fluxo['TIPO_DESTINO'], id_destino

    @deprecated
    def get_projeto_as_row(self, id_projeto):
        # todo: NECESSITA de refactor ou deve deixar de existir
        """
        Este método retorna um dicionário contendo os dados referentes ao projeto convertidos para o formato compatível
        com o web2py.
        :param id_projeto: integer, id do projeto
        :return: gluon.pydal.objects.Row contendo as informações, None caso não exista projeto com a id informada/erro.
        """
        if id_projeto:
            projeto_bd = self.get_projeto(id_projeto)
            if projeto_bd:
                arquivosDAO = SIEArquivosProj()
                termo = arquivosDAO.get_termo_outorga(id_projeto)
                ata = arquivosDAO.get_ata_departamento(id_projeto)
                arquivo_proj = arquivosDAO.get_arquivo_projeto(id_projeto)
                agencia_fomento = self.get_agencia_fomento(id_projeto)

                projeto = {
                    'id_documento': projeto_bd['ID_DOCUMENTO'],
                    'num_processo': projeto_bd['NUM_PROCESSO'],
                    'titulo': projeto_bd[u'TITULO'].encode('utf-8') if projeto_bd[
                                                                                       u'TITULO'] is not None else "",
                    'resumo': projeto_bd[u'RESUMO'].encode('utf-8') if projeto_bd[
                                                                                       u'RESUMO'] is not None else "",
                    'keyword_1': projeto_bd[u'PALAVRA_CHAVE01'].encode('utf-8') if projeto_bd[
                                                                                       u'PALAVRA_CHAVE01'] is not None else "",
                    'keyword_2': projeto_bd[u'PALAVRA_CHAVE02'].encode('utf-8') if projeto_bd[
                                                                                       u'PALAVRA_CHAVE02'] is not None else "",
                    'keyword_3': projeto_bd[u'PALAVRA_CHAVE03'].encode('utf-8') if projeto_bd[
                                                                                       u'PALAVRA_CHAVE03'] is not None else "",
                    'keyword_4': projeto_bd[u'PALAVRA_CHAVE04'].encode('utf-8') if projeto_bd[
                                                                                       u'PALAVRA_CHAVE04'] is not None else "",
                    "financeiro_apoio_financeiro": int(bool(agencia_fomento)),
                # agencia de fomento é uma linha de orgaos do projeto. a representacao na pagina espera um int (0 ou 1).
                    # TODO Lógica cheia de gambiarra de lidar com fundações.
                    "carga_horaria": projeto_bd[u'CARGA_HORARIA'],
                    "financeiro_termo_outorga": termo,  # TODO
                    "financeiro_valor_previsto": CurrencyWidget.as_string(
                        agencia_fomento["VL_CONTRIBUICAO"]) if agencia_fomento else "",
                    "financeiro_agencia_fomento": agencia_fomento["NOME_UNIDADE"].encode(
                        'utf-8').strip() if agencia_fomento else "",
                    "financeiro_id_orgao_projeto": agencia_fomento["ID_ORGAO_PROJETO"] if agencia_fomento else "",
                    "financeiro_id_origem": agencia_fomento["ID_ORIGEM"] if agencia_fomento else "",
                    "financeiro_origem": agencia_fomento["ORIGEM"] if agencia_fomento else "",
                    "ata_departamento": ata,  # TODO
                    "arquivo_projeto": arquivo_proj,  # TODO
                    'vigencia_inicio': sie_str_to_date(projeto_bd[u'DT_INICIAL']) if projeto_bd[
                        u'DT_INICIAL'] else None,
                    'vigencia_final': sie_str_to_date(projeto_bd[u'DT_CONCLUSAO']) if projeto_bd[
                        u'DT_CONCLUSAO'] else None,
                    'id': projeto_bd[u"ID_PROJETO"]
                }
                return Storage(projeto)
            else:
                return None
        return None

    def get_projeto_by_doc(self,id_documento):
        """
        Este método retorna um dicionário contendo os dados referentes ao projeto no banco de dados.
        :param id_documento: integer, id do documento do projeto.
        :return: dicionário contendo as informações, None caso não exista projeto com a id informada/erro.
        """

        where = {
            "ID_DOCUMENTO": id_documento
        }
        return self.api.get_single_result(self.path,where,bypass_no_content_exception=True)


    def get_projeto(self, id_projeto):
        """
        Este método retorna um dicionário contendo os dados referentes ao projeto no banco de dados.
        :param id_projeto: integer, id do projeto
        :return: dicionário contendo as informações, None caso não exista projeto com a id informada/erro.
        """
        return super(SIEProjetosPesquisa, self).getProjeto(id_projeto)

    def criar_projeto(self, projeto):
        """
        :type projeto: dict
        :param projeto: Um projeto a ser inserido no banco
        :return: Um dicionário contendo a entrada uma nova entrada da tabela PROJETOS
        """

        projeto_padrao = {
            "EVENTO_TAB": self.COD_TABELA_TIPO_EVENTO,
            "EVENTO_ITEM": self.ITEM_TIPO_EVENTO_NAO_SE_APLICA,
            "TIPO_PUBLICO_TAB": self.COD_TABELA_TIPO_PUBLICO_ALVO,
            "TIPO_PUBLICO_ITEM": self.ITEM_TIPO_PUBLICO_3_GRAU,
            "ACESSO_PARTICIP": self.ACESSO_PARTICIPANTES_APENAS_COORDENADOR,
            "PAGA_BOLSA": self.NAO_PAGA_BOLSA,
            "AVALIACAO_TAB": self.COD_TABELA_AVALIACAO_PROJETOS_INSTITUICAO,
            "AVALIACAO_ITEM": self.ITEM_AVALIACAO_PROJETOS_INSTITUICAO_NAO_AVALIADO,
            'ID_CLASSIFICACAO': self.ITEM_CLASSIFICACAO_PROJETO_PESQUISA,
            'SITUACAO_TAB': self.COD_TABELA_SITUACAO,
            'SITUACAO_ITEM': self.ITEM_SITUACAO_TRAMITE_REGISTRO,
            'FUNDACAO_TAB': self.COD_TABELA_FUNDACOES, "DT_REGISTRO": date.today()
        }

        projeto.update(projeto_padrao)
        try:
            novo_projeto = self.api.post(self.path, projeto)
            projeto.update({'id_projeto': novo_projeto.insertId})
            return projeto
        except APIException as e:
            raise SIEException("Falha ao cadastrar projeto.", e)

    def atualizar_projeto(self, projeto):
        try:
            retorno = self.api.put(self.path, projeto)
            if retorno and retorno.affectedRows == 1:
                return True
            return False
        except APIException as e:
            raise SIEException("Falha ao atualizar projeto", e)

    def get_lista_opcoes_titulacao(self):
        """
        :return: lista contendo listas ("CodOpcao","NomeOpcao")
        """
        return SIETabEstruturada().get_drop_down_options(self.COD_TABELA_TITULACAO)

    def get_lista_fundacoes(self):
        """
        :return: lista contendo listas ("CodOpcao","NomeOpcao")
        """
        return SIETabEstruturada().get_drop_down_options(codigo_tabela=self.COD_TABELA_FUNDACOES,
                                                         valores_proibidos=(self.ITEM_TAB_ESTRUTURADA_DESCRICAO_CAMPO,
                                                                            self.ITEM_FUNDACOES_NAO_SE_APLICA,))

    def get_lista_status_projeto(self):
        return SIETabEstruturada().get_drop_down_options(self.COD_TABELA_SITUACAO)

    def get_lista_funcoes_orgaos(self):
        """
        :return: lista contendo listas ("CodOpcao","NomeOpcao")
        """
        funcoes_proibidas = (
            0,
            self.ITEM_FUNCOES_ORGAOS_RESPONSAVEL
        )

        return SIETabEstruturada().get_drop_down_options(self.COD_TABELA_FUNCOES_ORGAOS, funcoes_proibidas)

    def get_lista_funcoes_projeto_pesquisa(self):
        """
        :return: lista contendo listas ("CodOpcao","NomeOpcao")
        """
        funcoes_proibidas = (
            self.ITEM_FUNCOES_PROJ_BOLSISTA,
            self.ITEM_FUNCOES_PROJ_CANDIDATO_BOLSISTA,
            self.ITEM_FUNCOES_PROJ_COORDENADOR,
            self.ITEM_FUNCOES_PROJ_DESCR,
            self.ITEM_FUNCOES_PROJ_NAO_DEFINIDA
        )

        return SIETabEstruturada().get_drop_down_options(self.COD_TABELA_FUNCOES_PROJ, funcoes_proibidas)

    def get_membros_camara(self,id_camara):
        """
        Pega os membros de uma câmara de pesquisa, dado um id_classificacao (que consta em classificacoes_prj).
        :param id_camara:
        :return:
        """

        where = {
            "ID_CLASSIFICACAO": id_camara,
            "LMIN":0,
            "LMAX":100
        }

        return self.api.get("V_MEMBROS_CAMARA",where,bypass_no_content_exception=True)

    def get_membros_comunidade_like(self, query):

        query = remover_acentos_query(query)

        params = {"LMIN": 0,
                  "LMAX": 99999,
                  "NOME": query,
                  "ORDERBY": "NOME",
                  "SORT": "ASC"
                  }

        # fields = ['NOME','ID_PESSOA','MATRICULA','DESCRICAO_VINCULO']
        try:
            res = self.api.get("V_PROJETOS_PESSOAS", params, cache_time=0)
            return res.content if res is not None else []
        except ValueError:
            return []

    def get_orgaos_like(self, query):

        query = remover_acentos_query(query)

        params = {"LMIN": 0,
                  "LMAX": 99999,
                  "NOME_UNIDADE": query,
                  "ORDERBY": "NOME_UNIDADE",
                  "SORT": "ASC"
                  }

        # fields = ['NOME_UNIDADE','ID_ORIGEM','ORIGEM']
        try:
            res = self.api.get("V_ORGAOS_PROJ", params, cache_time=0)
            return res.content if res is not None else []
        except ValueError:
            return []

    def get_orgao(self, id_origem, origem):

        params = {"LMIN": 0,
                  "LMAX": 1,
                  "ID_ORIGEM": id_origem,
                  "ORIGEM": origem
                  }

        try:
            res = self.api.get("V_ORGAOS_PROJ", params, cache_time=self.cacheTime)
            return res.content[0] if res is not None else {}
        except ValueError:
            return {}

    def get_membro_comunidade(self, id_pessoa, matricula):

        params = {"LMIN": 0,
                  "LMAX": 1,
                  "ID_PESSOA": id_pessoa,
                  }
        if matricula:
            # Entidade externa só tem ID_PESSOA
            params.update({
                "MATRICULA": matricula
            })

        try:
            res = self.api.get("V_PROJETOS_PESSOAS", params, cache_time=0)
            return res.content[0] if res is not None else {}
        except ValueError:
            return {}

    def get_projetos_pode_pedir_bolsista(self,
                                         cpf_coordenador):  # TODO possivelmente atrelado a uma instancia de algum modelo de coordenador
        projetos_possiveis = self.get_projetos(cpf_coordenador=cpf_coordenador, situacoes=[self.ITEM_SITUACAO_ANDAMENTO,
                                                                                           self.ITEM_SITUACAO_TRAMITE_REGISTRO])

        # Filtra os que tão sem id_documento (ainda não tramitados)
        return filter(lambda projeto: projeto["ID_DOCUMENTO"] is not None,
                      projetos_possiveis)  # TODO tem como fazer sem ser por aqui? checar is not null pela API?

    def get_projetos_em_andamento(self, cpf_coordenador):
        return self.get_projetos(cpf_coordenador, self.ITEM_SITUACAO_ANDAMENTO)

    def get_projetos(self, cpf_coordenador=None, situacoes=None, **_attributes):

        params = {
            "LMIN": 0,
            "LMAX": 9999,
        }

        if cpf_coordenador:
            params.update({
                "CPF_COORDENADOR": cpf_coordenador
            })
        if situacoes:
            if isinstance(situacoes, collections.Iterable) and len(situacoes) > 1:
                params.update({"SITUACAO_ITEM_SET": situacoes})
            elif isinstance(situacoes, collections.Iterable):
                params.update({"SITUACAO_ITEM": situacoes[0]})  # TODO AttributeError?
            else:
                params.update({"SITUACAO_ITEM": situacoes})

        params.update(_attributes)

        return self.api.get("V_PROJETOS_PESQUISA", params, cache_time=0, bypass_no_content_exception=True)

    def get_coordenador(self, id_projeto):
        """
        Retorna dicionário com o participantes de id_participante
        :return: dict com informações dos participantes, None caso contrário.
        """
        params = {"LMIN": 0,
                  "LMAX": 1,
                  "ID_PROJETO": id_projeto,
                  "FUNCAO_ITEM": SIEProjetosPesquisa.ITEM_FUNCOES_PROJ_COORDENADOR
                  }
        try:
            res = self.api.get("V_PROJETOS_PARTICIPANTES", params, cache_time=0)
            return res.content[0] if res is not None else None
        except ValueError:
            return None

    def get_relatorios_docente(self, cpf):
        """
        Retorna os relatorios docentes de um projeto
        :param cpf: cpf do coordenador
        :return:
        """
        pass