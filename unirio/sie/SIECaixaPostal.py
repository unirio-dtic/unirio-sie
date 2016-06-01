# coding=utf-8
"""
Módulo que cuida das caixas postais que aparecerão no sistema.
"""
from datetime import date
from unirio.sie.base import SIE
from unirio.sie.SIEDocumento import SIEDocumentoDAO
from unirio.sie.SIEFuncionarios import SIEFuncionarios
from unirio.sie.SIEProjetos import SIEArquivosProj
from unirio.sie.SIEProjetosPesquisa import SIEProjetosPesquisa, SIECandidatosBolsistasProjsPesquisa, \
    SIEAvaliacaoProjsPesquisaDAO
from unirio.sie.utils import sie_str_to_date


class SIECaixaPostal(SIE):
    """
    Classe base que cuida dos acessos ao banco/API das 'caixas postais' relativas a Projeto de Pesquisa.
    Seguem o comportamento básico de
    Entrada - Enviados - Deferidos/Em andamento - Câmara
    """

    path = ""

    COD_SITUACAO_LIMBO = 999
    COD_SITUACAO_DEFERIDO = 777
    COD_COM_A_DPQ = 10
    COD_COM_A_CAMARA = 500
    COD_TIPO_DESTINO_PROFESSOR_COORDENADOR = 20  # TODO Verificar se será mesmo assim!
    COD_TIPO_DESTINO_PROFESSOR_CAMARA = 20  # TODO Verificar se será mesmo assim!
    COD_COM_PROFESSOR = 1
    TIPO_ARQUIVO_PARECER = 9999999

    def get_camara(self, id_usuario, adm=False):
        """
        Pega projetos de  um id_usuario de uma câmara
        :return:
        """

        where = {
            "SITUACAO_ATUAL": self.COD_COM_A_CAMARA,
            "ULTIMA_SITUACAO": 'S',
            "LMIN": 0,
            "LMAX": 999999
        }

        if not adm:
            # Se usuário não é adm, restringe os dados para a caixa postal do usuário, senão (Dpq) pega tudo.
            where.update({
                "ID_DESTINO": id_usuario,  # TODO Resolver como será isso
                "TIPO_DESTINO": self.COD_TIPO_DESTINO_PROFESSOR_CAMARA  # TODO Resolver como será isso
            })

        return self.api.get(self.path, where, bypass_no_content_exception=True)

    def get_entrada(self):
        """
        Pega projetos na caixa entrada
        :return:
        """

        where = {
            "SITUACAO_ATUAL": self.COD_COM_A_DPQ,
            "ULTIMA_SITUACAO": 'S',
            "LMIN": 0,
            "LMAX": 999999
        }

        return self.api.get(self.path, where, bypass_no_content_exception=True)

    def get_deferidos(self):
        """
        Pega projetos em andamento
        :return:
        """

        where = {
            "SITUACAO_ATUAL": self.COD_SITUACAO_DEFERIDO,
            "ULTIMA_SITUACAO": 'S',
            "LMIN": 0,
            "LMAX": 999999
        }

        return self.api.get(self.path, where, bypass_no_content_exception=True)

    def get_enviados(self):
        """
        Pega a caixa de enviados
        :return:
        """

        where = {
            "SITUACAO_ANTERIOR": self.COD_COM_A_DPQ,
            "SITUACAO_ATUAL_SET": [self.COD_COM_A_CAMARA, self.COD_COM_PROFESSOR],
            # Filtra, pois pode ser 999 ou 777 e ter sido deferido pela dpq. =]
            "ULTIMA_SITUACAO": 'S',
            "LMIN": 0,
            "LMAX": 999999
        }

        return self.api.get(self.path, where, bypass_no_content_exception=True)

    def get_linha_tramit(self, id_documento):
        """
        Pega uma linha da tramitação com o id_documento passado.
        :param id_documento:
        :return:
        """

        where = {
            "ID_DOCUMENTO": id_documento,
            "ORDERBY": 'SEQUENCIA',
            'SORT': 'DESC'
        }

        return self.api.get_single_result(self.path, where)

    def get_linha_tramit_por_id_projeto(self, id_projeto):
        """
        Pega uma linha da tramitação com o id_projeto passado.

        :param id_projeto:
        :return:
        """

        where = {
            "ID_PROJETO": id_projeto,
            "ORDERBY": 'SEQUENCIA',
            'SORT': 'DESC'
        }

        return self.api.get_single_result(self.path, where)

    def get_tramitacoes(self, id_documento):  # TODO Será id_projeto mesmo ou id_documento para ser mais genérico?
        """
        Pega as tramitações referentes a um projeto/id_documento
        :param id_projeto:
        :return:
        """
        where = {
            "ID_DOCUMENTO": id_documento,
            "LMIN": 0,
            "LMAX": 999999,
            'ORDERBY': 'SEQUENCIA',
            'SORT': 'DESC'
        }

        return self.api.get(self.path, where, bypass_no_content_exception=True)

    @classmethod
    def _monta_destino_professor_camara(self, fluxo, professor_camara):
        # TODO FLUXO ESTA ERRADO NO TESTE!
        # return fluxo["TIPO_DESTINO"], professor_camara
        return 20, professor_camara

    def get_professor_origem(self, fluxo, id_documento):
        """

        :param fluxo:
        :param documento:
        :return:
        """

        # Em tese, acho que deveria ser a primeira pessoa que mandou a tramitação
        # Mas pode ser que a origem seja mudada, então fica o id_usuario do coordenador do projeto.

        linha_tramit = self.get_linha_tramit(id_documento)
        coordenador = SIEFuncionarios().get_funcionario(linha_tramit["CPF_COORDENADOR"])
        tipo_destino = self.COD_TIPO_DESTINO_PROFESSOR_COORDENADOR  # professor é uma pessoa (tipo destino em tese é 20)
        id_destino = coordenador["ID_USUARIO"]

        return tipo_destino, id_destino

    def tramitar_dpq(self, id_documento, despacho):
        SIEDocumentoDAO().receber_e_tramitar(id_documento, despacho, proxima_situacao=self.COD_COM_A_DPQ)

    def retornar_para_origem(self, id_documento, despacho):
        SIEDocumentoDAO().receber_e_tramitar(id_documento, despacho,
                                             self.COD_COM_PROFESSOR,
                                             lambda _fluxo: self.get_professor_origem(_fluxo, id_documento)
                                             )

    def tramitar_camara(self, id_documento, despacho, professor_camara):
        proxima_situacao = self.COD_COM_A_CAMARA
        SIEDocumentoDAO().receber_e_tramitar(id_documento, despacho, proxima_situacao,
                                             lambda _fluxo: self._monta_destino_professor_camara(_fluxo,
                                                                                                 professor_camara))

    def tramitar_indeferimento(self, id_documento, despacho, aplicar_acao=None):
        """
        TODO Separar para "Camara"?

        :return:
        """
        SIEDocumentoDAO().receber_e_tramitar(id_documento, despacho, proxima_situacao=self.COD_COM_A_DPQ,
                                             aplicar_acao=aplicar_acao)

    def tramitar_deferimento(self, id_documento, despacho, aplicar_acao=None):
        """
        TODO Separar para 'Câmara'?
        :param id_documento:
        :param despacho:
        :param aplicar_acao:
        :return:
        """
        proxima_situacao = self.COD_SITUACAO_DEFERIDO
        SIEDocumentoDAO().receber_e_tramitar(id_documento, despacho, proxima_situacao, aplicar_acao=aplicar_acao)

    def registrar_arquivo_avaliacao(self, arquivo, id_documento):
        """
        Registra arquivo de parecer. No caso padrão, não registra, mas avaliação de relatorio docente e plano de estudos registrarão.
        :param arquivo:
        :return:
        """
        # TODO Não me parece no lugar certo enquanto classe.
        pass


class SIECaixaPostalCadastroProjetosPesquisa(SIECaixaPostal):
    """
    Classe que cuida dos acessos ao banco/API das 'caixas postais' da parte de Cadastro de Projetos.
    """

    path = "V_TRAMIT_CAD_PESQUISA"

    COD_SITUACAO_DEFERIDO = 777
    COD_COM_A_DPQ = 10
    COD_COM_A_CAMARA = 500
    COD_TIPO_DESTINO_PROFESSOR_CAMARA = 20  # TODO Verificar se será mesmo assim!
    COD_COM_PROFESSOR = 1
    TIPO_ARQUIVO_PARECER = SIEArquivosProj.ITEM_TIPO_ARQUIVO_PARECER_CAMARA_CADASTRO_PROJETO
    ID_TIPO_DOC = 217  # TODO Fazer referencia ao tipo na tabela que cria o documento.

    def cancela_projeto(self, id_documento):
        despacho = "**PROJETO CANCELADO PELA DPq**"

        if self.projeto_legado_esta_tramitado_corretamente(id_documento):
            # fluxo correto
            SIEDocumentoDAO().receber_e_tramitar(id_documento,
                                                 despacho,
                                                 proxima_situacao=self.COD_SITUACAO_LIMBO,
                                                 aplicar_acao=self._acao_pos_cancelamento_projeto)
        else:
            # cancela de forma gambiarrada
            self._muda_situacao_projeto(id_documento, SIEProjetosPesquisa.ITEM_SITUACAO_CANCELADO)
            SIEDocumentoDAO().atualizar_situacao_documento(
                documento={"ID_DOCUMENTO": id_documento},
                fluxo={"SITUACAO_FUTURA": self.COD_SITUACAO_LIMBO}
            )

    def projeto_legado_esta_tramitado_corretamente(self, id_documento):
        """
        Gambiarra para lidar com projetos antigos. Como na página de deferidos estamos pegando os projetos pela situação
        atual, muitos projetos não estão com a tramitação no ponto correto.

        Assim, é preciso identificar se na etapa de cancelamento esse projeto está com a tramitação correta ou não.
        Tramitação correta seria no estado 777, único estado que seria possível cancelar projetos. (Não confundir com indeferimento).

        :param id_documento:
        :return:
        """
        linha_tramitacao = self.get_linha_tramit(id_documento)
        projeto_esta_correto = int(linha_tramitacao['SITUACAO_ATUAL']) == self.COD_SITUACAO_DEFERIDO
        return projeto_esta_correto

    def _acao_pos_cancelamento_projeto(self, id_documento):
        self._acoes_comuns_arquivamento_projeto(id_documento, SIEProjetosPesquisa.ITEM_SITUACAO_CANCELADO)

    def _acao_pos_indeferimento_projeto(self, id_documento):
        self._acoes_comuns_arquivamento_projeto(id_documento, SIEProjetosPesquisa.ITEM_SITUACAO_INDEFERIDO)

    def _acoes_comuns_arquivamento_projeto(self, id_documento, situacao):
        self._muda_situacao_projeto(id_documento, situacao)
        SIEDocumentoDAO().arquivar_documento(id_documento)

    def indefere_projeto(self, id_documento):
        despacho = "**PROJETO INDEFERIDO PELA DPq**"
        SIEDocumentoDAO().receber_e_tramitar(id_documento,
                                             despacho,
                                             proxima_situacao=self.COD_SITUACAO_LIMBO,
                                             resolvedor_destino=lambda _fluxo: self.get_professor_origem(_fluxo,
                                                                                                         id_documento),
                                             # volta para o professor.
                                             aplicar_acao=self._acao_pos_indeferimento_projeto)

    def coloca_projeto_em_andamento(self, id_documento):
        projeto = SIEProjetosPesquisa().get_projeto_by_doc(id_documento)
        if projeto["SITUACAO_ITEM"] == SIEProjetosPesquisa.ITEM_SITUACAO_TRAMITE_REGISTRO:
            self._muda_situacao_projeto(id_documento, SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO)
        else:
            # TODO Em tese, não deve ser possível colocar um projeto em andamento que não está em trâmite para registro.
            pass

    def coloca_projeto_concluido(self, id_documento):
        self._muda_situacao_projeto(id_documento, SIEProjetosPesquisa.ITEM_SITUACAO_CONCLUIDO)

    def _muda_situacao_projeto(self, id_documento, nova_situacao):
        """
        Muda a situacao de um projeto.

        :param id_documento:
        :param nova_situacao:
        :return:
        """

        projeto = SIEProjetosPesquisa().get_projeto_by_doc(id_documento)
        projeto_update = {
            "SITUACAO_ITEM": nova_situacao,
            "ID_PROJETO": projeto["ID_PROJETO"]
        }

        SIEProjetosPesquisa().atualizar_projeto(projeto_update)

    def tramitar_deferimento(self, id_documento, despacho, aplicar_acao=None):
        """
        Ação de 'câmara'.
        :param id_documento:
        :param despacho:
        :param aplicar_acao:
        :return:
        """
        aplicar_acao = aplicar_acao or self.coloca_projeto_em_andamento
        super(SIECaixaPostalCadastroProjetosPesquisa, self).tramitar_deferimento(id_documento, despacho, aplicar_acao)

    def get_deferidos(self):
        """
        Em teoria, get_deferidos deveria apenas pegar os projetos cujo documento encontra-se na situacao 777.
        Por conta do legado, é melhor pegar de acordo com a situação do projeto.

        :return:
        """
        where = {
            "SITUACAO_ITEM_PROJETO_SET": [
                SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO,
                SIEProjetosPesquisa.ITEM_SITUACAO_RENOVADO,
                SIEProjetosPesquisa.ITEM_SITUACAO_SUSPENSO,
            ],
            "ULTIMA_SITUACAO": 'S',
            "LMIN": 0,
            "LMAX": 999999
        }
        return self.api.get(self.path, where, bypass_no_content_exception=True)


        # def get_deferidos(self):
        # deferidos = super(SIECaixaPostalCadastroProjetosPesquisa,self).get_deferidos()
        # valores_proibidos = [SIEProjetosPesquisa.ITEM_SITUACAO_INDEFERIDO,
        #                      SIEProjetosPesquisa.ITEM_SITUACAO_CONCLUIDO,
        #                      SIEProjetosPesquisa.ITEM_SITUACAO_CANCELADO,
        #                      ]
        #
        # return [x for x in deferidos if x["SITUACAO_ITEM_PROJETO"] not in valores_proibidos]

    def get_entrada(self):
        """
        Em tese, a entrada deveria ser apenas os projetos que estão com a DPq.
        Por conta de legado, existem muuuitos projetos com status diferente de "Em trâmite pra registro" com a DPq, por
        isso, filtramos por status aqui também.

        :return:
        """

        where = {
            "SITUACAO_ITEM_PROJETO": SIEProjetosPesquisa.ITEM_SITUACAO_TRAMITE_REGISTRO,
            "SITUACAO_ATUAL": self.COD_COM_A_DPQ,
            "ULTIMA_SITUACAO": 'S',
            "LMIN": 0,
            "LMAX": 999999
        }
        return self.api.get(self.path, where, bypass_no_content_exception=True)

    def _filtra_ate_ano(self, dados, ano):
        """
        Filtra os dados retirando os que tiverem sido alterados até o ano passado (inclusive). Itens com alterações posteriores permanecem.
        :param dados:
        :param ano:
        :return:
        """

        filtrados = [enviado for enviado in dados if
                     sie_str_to_date(enviado['DT_ALTERACAO']) > date(ano, 12, 31)]  # Até dia 31/12/ano.
        return filtrados

    def get_enviados(self):
        """
        Pega a caixa de enviados
        :return:
        """

        enviados = super(SIECaixaPostalCadastroProjetosPesquisa, self).get_enviados()
        return self._filtra_ate_ano(enviados, 2015)


class SIECaixaPostalAvalRelatorioDocenteProjetosPesquisa(SIECaixaPostal):
    """
    Classe que cuida dos acessos ao banco/API das 'caixas postais' da parte de Avaliação de Projetos.
    """

    path = "V_TRAMIT_AVA_PESQUISA"

    COD_SITUACAO_DEFERIDO = 777
    COD_COM_A_DPQ = 10
    COD_COM_A_CAMARA = 20
    COD_TIPO_DESTINO_PROFESSOR_CAMARA = 20
    COD_COM_PROFESSOR = 1
    TIPO_ARQUIVO_PARECER = SIEArquivosProj.ITEM_TIPO_ARQUIVO_PARECER_CAMARA_AVAL_REL_DOCENTE
    ID_TIPO_DOC = 223  # TODO Fazer referencia ao tipo na tabela que cria o documento.

    def registrar_arquivo_avaliacao(self, arquivo, id_documento):
        """
        Registrao um arquivo de parecer com uma avaliacao/candidato/projeto.
        No caso, registra como um arquivo da avaliação do id_documento passado como argumento
        :param arquivo:
        :param id_documento:
        """
        avaliacao = SIEAvaliacaoProjsPesquisaDAO().get_avaliacao_by_doc(id_documento)

        SIEArquivosProj().atualizar_arquivo(id_arquivo=arquivo["ID_ARQUIVO_PROJ"], params=
        {"ID_AVALIACAO_PROJ": avaliacao["ID_AVALIACAO_PROJ"]})

    def _atualiza_projeto_avaliado(self, id_projeto, avaliado=False, situacao=None, dt_renovacao=None):
        """
        Atualizações referentes à tabela PROJETOS após a tramitação de (in)deferimento.

        # talvez setar avaliacao_item como avaliado(3) ?
        # Situação do projeto (dependente de lógica)
        # dt_ultima_avaliacao
        # setar nova dt_conclusao se for o caso

        :param id_documento:
        :param situacao:
        :param dt_renovacao:
        :return:
        """

        proj_update = {
            "ID_PROJETO": id_projeto,
            "DT_ULTIMA_AVAL": date.today()
        }

        if avaliado:
            proj_update.update({
                "AVALIACAO_ITEM": SIEProjetosPesquisa.ITEM_AVALIACAO_PROJETOS_AVALIADO
            })

        # se situacao for mencionada
        if situacao:
            proj_update.update({
                "SITUACAO_ITEM": situacao
            })

        # se renovacao for mencionada.
        if dt_renovacao:
            proj_update.update({
                "DT_CONCLUSAO": dt_renovacao
            })

        SIEProjetosPesquisa().atualizar_projeto(proj_update)

    def _atualiza_avaliacao(self, id_avaliacao, situacao=None):
        """
        atualizações referentes a tabela de avaliacoes_proj

        # AVALIACOES_PROJ
        # setar id_contrato_rh (professor avaliador)
        # setar id_unidade (professor avaliador)
        # copiar nova situação do projeto ou deixar a quando da avaliacao? TODO ???

        :param id_documento:
        :return:
        """

        aval_update = {
            "ID_AVALIACAO_PROJ": id_avaliacao,
            "ID_CONTRATO_RH": self.usuario["ID_CONTRATO_RH"],
            "ID_UNIDADE": self.usuario["ID_LOT_OFICIAL"],
        }

        if situacao:
            aval_update.update({
                "SITUACAO_ITEM": situacao
            })

        SIEAvaliacaoProjsPesquisaDAO().atualizar_avaliacao(aval_update)

    def _is_renovacao_projeto(self, avaliacao, projeto):
        """
        Nome autossuficiente?

        :param avaliacao:
        :param projeto:
        :return:
        """
        data_conclusao_nova = sie_str_to_date(avaliacao["DT_CONCLUSAO"])
        data_conclusao_atual = sie_str_to_date(projeto["DT_CONCLUSAO"])

        return data_conclusao_nova > data_conclusao_atual

    def _is_concluinte(self, projeto):
        """
        Retorna se o projeto deverá estar concluído antes da abertura do proximo período de avaliação.

        :param projeto:
        :return:
        """
        # TODO TEMOS QUE IMPLEMENTAR.

        return False

    def _projeto_tem_mais_pendencias(self, projeto):
        """
        Retorna se projeto tem mais pendencias do que a atual.
        Por exemplo, podem existir mais avaliações a serem enviadas.
        :param projeto:
        :return:
        """

        # TODO

        return False

    def callback_deferimento(self, id_documento):
        """
        O que acontece após as tramitações. Paralelo ao "aplicar ação/aplicação" do SIE. Caso de deferimento/aprovação relatório.
        :param id_documento: ID_DOCUMENTO de uma AVALIACAO_PROJ
        :return:
        """

        avaliacao = SIEAvaliacaoProjsPesquisaDAO().get_avaliacao_by_doc(id_documento)
        projeto = SIEProjetosPesquisa().get_projeto(avaliacao["ID_PROJETO"])

        if self._projeto_tem_mais_pendencias(projeto):
            raise NotImplementedError
        if self._is_renovacao_projeto(avaliacao, projeto):
            self._atualiza_projeto_avaliado(projeto['ID_PROJETO'], avaliado=True,
                                            situacao=SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO,
                                            dt_renovacao=avaliacao["DT_CONCLUSAO"])
            self._atualiza_avaliacao(avaliacao["ID_AVALIACAO_PROJ"], SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO)
        elif self._is_concluinte(projeto):
            self._atualiza_projeto_avaliado(projeto['ID_PROJETO'], avaliado=True,
                                            situacao=SIEProjetosPesquisa.ITEM_SITUACAO_CONCLUIDO, dt_renovacao=False)
            self._atualiza_avaliacao(avaliacao["ID_AVALIACAO_PROJ"], SIEProjetosPesquisa.ITEM_SITUACAO_CONCLUIDO)
        else:
            self._atualiza_projeto_avaliado(projeto['ID_PROJETO'], avaliado=True,
                                            situacao=SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO, dt_renovacao=False)
            self._atualiza_avaliacao(avaliacao["ID_AVALIACAO_PROJ"], SIEProjetosPesquisa.ITEM_SITUACAO_ANDAMENTO)

    def callback_indeferimento(self, id_documento):
        """
        O que acontece após as tramitações. Paralelo ao "aplicar ação/aplicação" do SIE. Caso de indeferimento do relatório.
        :param id_documento:
        :return:
        """

        # avaliacao = SIEAvaliacaoProjsPesquisaDAO().get_avaliacao_by_doc(id_documento)
        # projeto = SIEProjetosPesquisa().get_projeto(avaliacao["ID_PROJETO"])
        #
        # self._atualiza_projeto(projeto['ID_PROJETO'])
        # self._atualiza_avaliacao(avaliacao["ID_AVALIACAO_PROJ"])
        pass  # De acordo com o que combinamos, nada será feito no indeferimento. Mantendo método por questões de lógica.

    def _atualiza_projeto_nao_avaliado(self, id_projeto):
        """
        Atualizações referentes à tabela PROJETOS após a tramitação de (in)deferimento.

        # talvez setar avaliacao_item como avaliado(3) ?
        # Situação do projeto (dependente de lógica)
        # dt_ultima_avaliacao
        # setar nova dt_conclusao se for o caso

        :param id_documento:
        :param situacao:
        :param dt_renovacao:
        :return:
        """

        proj_update = {
            "ID_PROJETO": id_projeto,
            "AVALIACAO_ITEM": SIEProjetosPesquisa.ITEM_AVALIACAO_PROJETOS_INSTITUICAO_NAO_AVALIADO
        }

        SIEProjetosPesquisa().atualizar_projeto(proj_update)

    def _mudar_avaliacao_nao_avaliado(self, id_documento):
        """
        Atualiza projeto para não avaliado.
        :return:
        """
        # atualiza projeto

        linha_tramit = self.get_linha_tramit(id_documento)
        self._atualiza_projeto_nao_avaliado(linha_tramit["ID_PROJETO"])

    def retornar_para_origem(self, id_documento, despacho):
        SIEDocumentoDAO().receber_e_tramitar(id_documento, despacho,
                                             self.COD_COM_PROFESSOR,
                                             lambda _fluxo: self.get_professor_origem(_fluxo, id_documento),
                                             aplicar_acao=self._mudar_avaliacao_nao_avaliado
                                             )

    def tramitar_deferimento(self, id_documento, despacho, aplicar_acao=None):
        aplicar_acao = aplicar_acao or self.callback_deferimento
        super(SIECaixaPostalAvalRelatorioDocenteProjetosPesquisa, self).tramitar_deferimento(id_documento, despacho,
                                                                                             aplicar_acao)

    def tramitar_indeferimento(self, id_documento, despacho, aplicar_acao=None):
        aplicar_acao = aplicar_acao or self.callback_indeferimento
        super(SIECaixaPostalAvalRelatorioDocenteProjetosPesquisa, self).tramitar_indeferimento(id_documento, despacho,
                                                                                               aplicar_acao)


class SIECaixaPostalAvalCandidatosBolsistasProjetosPesquisa(SIECaixaPostal):
    """
    Classe que cuida dos acessos ao banco/API das 'caixas postais' da parte de Avaliação de Projetos.
    """

    path = "V_TRAMIT_PLANO_ESTUDOS"

    COD_SITUACAO_DEFERIDO = 777
    COD_COM_A_DPQ = 10
    COD_COM_A_CAMARA = 20
    COD_TIPO_DESTINO_PROFESSOR_CAMARA = 20
    COD_COM_PROFESSOR = 1
    TIPO_ARQUIVO_PARECER = SIEArquivosProj.ITEM_TIPO_ARQUIVO_PARECER_CAMARA_AVAL_PLANO_ESTUDOS
    ID_TIPO_DOC = 289

    ID_DOCUMENTO_DUMMY = 1

    def callback_deferimento(self, id_documento):
        """
        O que fazer depois da tramitação se coordenador seleciona "aprovar"
        :param id_documento:
        :return:
        """
        self._mudar_status_candidato(id_documento, SIECandidatosBolsistasProjsPesquisa.STATUS_DEFERIDO)

    def _mudar_status_candidato(self, id_documento, novo_status):
        """
        Muda o status do candidato a bolsista referenciado pelo documento de id_documento para o novo_status.


        :param id_documento:
        :param novo_status:
        :return:
        """

        candidato = SIECandidatosBolsistasProjsPesquisa().get_candidato_bolsista(id_documento=id_documento)
        candidato_novo = {
            "ID_CANDIDATOS_BOLSISTA": candidato['ID_CANDIDATOS_BOLSISTA'],
            "STATUS": novo_status
        }
        SIECandidatosBolsistasProjsPesquisa().atualizar_candidato(candidato_novo)

    def callback_indeferimento(self, id_documento):
        """
        O que fazer depois da tramitação se seleciona "reprovar"
        :param id_documento:
        :return:
        """
        self._mudar_status_candidato(id_documento, SIECandidatosBolsistasProjsPesquisa.STATUS_INDEFERIDO)

    def registrar_arquivo_avaliacao(self, arquivo, id_documento):
        """
        Registra arquivo com parecer (em arquivo) sobre um candidato referenciado por id_documento

        :param arquivo:
        :param id_documento:
        :return:
        """
        candidato = SIECandidatosBolsistasProjsPesquisa().get_candidato_bolsista(id_documento=id_documento)

        candidato_novo = {
            "ID_CANDIDATOS_BOLSISTA": candidato['ID_CANDIDATOS_BOLSISTA'],
            "ID_PARECER": arquivo['ID_ARQUIVO_PROJ']
        }

        SIECandidatosBolsistasProjsPesquisa().atualizar_candidato(candidato_novo)

    def tramitar_deferimento(self, id_documento, despacho, aplicar_acao=None):
        aplicar_acao = aplicar_acao or self.callback_deferimento
        super(SIECaixaPostalAvalCandidatosBolsistasProjetosPesquisa, self).tramitar_deferimento(id_documento, despacho,
                                                                                                aplicar_acao)

    def tramitar_indeferimento(self, id_documento, despacho, aplicar_acao=None):
        aplicar_acao = aplicar_acao or self.callback_indeferimento
        super(SIECaixaPostalAvalCandidatosBolsistasProjetosPesquisa, self).tramitar_indeferimento(id_documento,
                                                                                                  despacho,
                                                                                                  aplicar_acao)

    def tramitar_camara(self, id_documento, despacho, professor_camara):
        super(SIECaixaPostalAvalCandidatosBolsistasProjetosPesquisa, self).tramitar_camara(id_documento, despacho,
                                                                                           professor_camara)

    def cancela_pedido(self, id_documento):
        despacho = "**CANDIDATO CANCELADO PELA DPq**"

        # TODO: Qual a melhor abordagem para este problema?


        # fluxo correto
        # SIEDocumentoDAO().receber_e_tramitar(id_documento,
        #                                          despacho,
        #                                          proxima_situacao=self.COD_SITUACAO_LIMBO
        #                                      # TODO existe resolvedor_destino?
        #                                      # TODO existe acao após?
        #                                          )
        # cancela de forma gambiarrada
        SIEDocumentoDAO().atualizar_situacao_documento(
            documento={"ID_DOCUMENTO": id_documento},
            fluxo={"SITUACAO_FUTURA": self.COD_SITUACAO_LIMBO}
        )
