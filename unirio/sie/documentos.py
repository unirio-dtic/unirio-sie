# coding=utf-8

from datetime import date, timedelta
from time import strftime
from deprecate import deprecated

from unirio.sie import SIEException
from unirio.sie.base import SIE
from unirio.api.exceptions import APIException, NoContentException

__all__ = [
    "SIEDocumentoDAO",
    "_NumeroProcessoTipoDocumentoDAO"
]


class SIEDocumentoDAO(SIE):
    # Valores de prioridade de documento

    TRAMITACAO_PRIORIDADE_NORMAL = 2

    # Valores validos para SITUACAO_TRAMIT

    TRAMITACAO_SITUACAO_AGUARDANDO = "T"
    TRAMITACAO_SITUACAO_ENTREGUE = "E"
    TRAMITACAO_SITUACAO_RECEBIDO = "R"

    # Valores validos para IND_RETORNO_OBRIG

    TRAMITACAO_IND_RETORNO_OBRIG_SIM = "S"
    TRAMITACAO_IND_RETORNO_OBRIG_NAO = "N"
    TRAMITACAO_IND_RETORNO_OBRIG_CONFORME_FLUXO = "F"

    # codigos restricao de tramitacao (usados para TIPO_DESTINO)
    COD_RESTRICAO_TRAMIT_USUARIO = 20

    # Paths para busca na api

    path = "DOCUMENTOS"
    tramite_path = "TRAMITACOES"
    fluxo_path = "FLUXOS"

    def criar_documento(self, novo_documento_params):
        """
        Inclui um novo documento eletronico do SIE e retorna ele. Uma tramitacao inicial ja eh iniciada (exceto se for especificado sem_tramite=True).

        Notas:
        SITUACAO_ATUAL = 1      => Um novo documento sempre se inicia com 1
        TIPO_PROPRIETARIO = 20  => Indica restricao de usuarios
        TIPO_ORIGEM = 20        => Recebe mesmo valor de TIPO_PROPRIETARIO
        SEQUENCIA = 1           => Indica que eh o primeiro passo de tramitacao
        TIPO_PROCEDENCIA = S    => Indica servidor
        TIPO_INTERESSADO = S    => Indica servidor

        IND_ELIMINADO, IND_AGENDAMENTO, IND_RESERVADO,
        IND_EXTRAVIADO, TEMPO_ESTIMADO => Valores fixos (Seguimos documento com recomendacoes da sintese)

        :param novo_documento_params: Um dicionario contendo parametros para criar o documento.
        :type novo_documento_params: dict

        :return: Um dicionario contendo a entrada da tabela DOCUMENTOS correspondente ao documento criado.
        :rtype: dict
        """

        num_processo_handler = _NumeroProcessoTipoDocumentoDAO(novo_documento_params["ID_TIPO_DOC"])

        # determinando ultimo numero
        num_processo = num_processo_handler.gerar_numero_processo()

        if not novo_documento_params.get("NUM_PROCESSO", None):
            novo_documento_params.update({"NUM_PROCESSO": num_processo})

        try:
            id_documento = self.api.post(self.path, novo_documento_params).insertId
            novo_documento = self.api.get_single_result(self.path, {"ID_DOCUMENTO": id_documento})

        except APIException as e:
            num_processo_handler.reverter_ultimo_numero_processo()
            raise SIEException("Falha ao criar documento de avaliação", e)

        # criando entrada na tabela de tramitacoes (pre-etapa)
        try:
            self.__adiciona_registro_inicial_tramitacao(novo_documento)
        except APIException as e:
            # TODO REVERTER CRIACAO DO DOCUMENTO e ULTIMO NÚMERO PROCESSO.
            raise e
        try:
            _EstadosDocumentosDAO().ativar_documento(id_documento)
        except APIException as e:
            # TODO REVERTER CRIACAO DO ULTIMO NÚMERO PROCESSO DOCUMENTO e DA TRAMITACAO.
            raise e

        return novo_documento

    def obter_documento(self, id_documento):
        """
        Retorna o documento com o id especificado. Caso nao exista, retorna None

        :param id_documento: Identificador unico de uma entrada na tabela DOCUMENTOS
        :type id_documento: int
        :return: Uma dicionario correspondente a uma entrada da tabela DOCUMENTOS
        :rtype: dict
        """
        params = {"ID_DOCUMENTO": id_documento}
        return self.api.get_single_result(self.path, params)

    def remover_documento(self, documento):
        """
        Dada uma entrada na tabela de DOCUMENTOS, a funcao remove suas tramitacoes e o documento em si

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        """
        self.remover_tramitacoes(documento)
        response = self.api.delete(self.path, {'ID_DOCUMENTO': documento['ID_DOCUMENTO']})
        if response.affectedRows > 0:
            del documento

    def receber_e_tramitar(self, id_documento, despacho, proxima_situacao, resolvedor_destino=None, aplicar_acao=None):

        documento = self.obter_documento(id_documento)
        if documento["DT_ARQUIVAMENTO"]:
            raise SIEException("Documento já encontra-se arquivado.")
        self.receber_documento(documento)
        fluxo = self.obter_proximo_fluxo_dado_destino(documento, proxima_situacao)

        if fluxo is None:
            raise SIEException("Documento em estado de tramitação corrompido.")

        fluxo["TEXTO_DESPACHO"] = despacho

        self.tramitar_documento(documento, fluxo, resolvedor_destino=resolvedor_destino)

        if callable(aplicar_acao):
            aplicar_acao(id_documento)

    def tramitar_documento(self, documento, fluxo, resolvedor_destino=None):
        """
        Envia o documento seguindo o fluxo especificado.
        Caso o fluxo especificado tenha a flag IND_QUERY='S', ou seja, o tipo_destino e id_destino devem
        ser obtidos atraves de uma query adicional, eh necessario o especificar o parametro resolvedor_destino
        com um callable que retorna o TIPO_DESTINO e ID_DESTINO corretos.

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :param fluxo: Um dicionario referente a uma entrada na tabela FLUXOS
        :type fluxo: dict
        :param resolvedor_destino: Um callable que recebe um parametro "fluxo" e retorna uma tupla (tipo_destino, id_destino)
        :type resolvedor_destino: callable
        """
        # No SIE, tramitar documento eh atualizar a situacao da tramitacao (e outros campos) e definir o fluxo dela
        self._marcar_tramitacao_atual_entregue(documento, fluxo, resolvedor_destino)

    def receber_documento(self, documento):
        """
        Marca o documento como recebido pela instituicao destinataria da tramitacao atual do documento.
        Normalmente esse metodo deve ser usado para emular a abertura da tramitacao atraves da caixa postal do SIE.

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        """
        precisa_criar_registro = self._marcar_tramitacao_atual_recebida(documento)
        if precisa_criar_registro:
            # cria linha com 'T'
            self._criar_registro_tramitacao(documento)

    def atualizar_situacao_documento(self, documento, fluxo):
        """
        Atualiza o documento na tabela com os dados do fluxo especificado.
        Normalmente chamado apos uma tramitacao for concluida.

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :param fluxo: Um dicionario referente a uma entrada na tabela FLUXOS
        :type fluxo: dict
         """
        documento_atualizado = {
            "ID_DOCUMENTO": documento["ID_DOCUMENTO"],
            "SITUACAO_ATUAL": fluxo["SITUACAO_FUTURA"],
            "DT_ALTERACAO": date.today(),
            "HR_ALTERACAO": strftime("%H:%M:%S"),
        }
        self.api.put(self.path, documento_atualizado)

    # ========================= Tramitacao ===================================

    def __adiciona_registro_inicial_tramitacao(self, documento):
        """
        Cria um registro na tabela de tramitacoes para esse documento recem-criado.

        Deve ser feito antes de fazer a primeira tramitacao do documento (de preferencia ao criar o documento)

        :rtype: dict
        :return: Um dicionario equivalente a uma entrada da tabela TRAMITACOES
        """

        tramitacao_params = {
            "SEQUENCIA": 1,  # Primeiro passo da tramitacao
            "ID_DOCUMENTO": documento["ID_DOCUMENTO"],
            "TIPO_ORIGEM": documento["TIPO_PROPRIETARIO"],
            "ID_ORIGEM": documento["ID_PROPRIETARIO"],
            "TIPO_DESTINO": documento["TIPO_PROPRIETARIO"],
            "ID_DESTINO": documento["ID_PROPRIETARIO"],
            "DT_ENVIO": date.today(),
            "SITUACAO_TRAMIT": SIEDocumentoDAO.TRAMITACAO_SITUACAO_AGUARDANDO,
            "IND_RETORNO_OBRIG": SIEDocumentoDAO.TRAMITACAO_IND_RETORNO_OBRIG_NAO,
            "DT_ALTERACAO": date.today(),
            "HR_ALTERACAO": strftime("%H:%M:%S"),
            "PRIORIDADE_TAB": 5101,  # Tabela estruturada utilizada para indicar o nivel de prioridade
            "PRIORIDADE_ITEM": SIEDocumentoDAO.TRAMITACAO_PRIORIDADE_NORMAL
        }

        id_tramitacao = self.api.post(self.tramite_path, tramitacao_params).insertId
        tramitacao = self.api.get_single_result(self.tramite_path, {"ID_TRAMITACAO": id_tramitacao})

        return tramitacao

    def _criar_registro_tramitacao(self, documento):
        """
        Cria um registro novo na tabela de tramitacoes para esse documento.

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :return: Retorna a linha de tramitacao recem criada
        :rtype: dict
        :raises: SIEException
        """

        # pegar a mais recente do documento
        tramitacao_anterior = self.obter_tramitacao_atual(documento)

        # so deveriamos criar um registro novo caso a tramitacao anterior estiver no estado SIEDocumentoDAO.TRAMITACAO_SITUACAO_RECEBIDO
        # essa restricao pode conflitar com dados antigos e incosistentes
        if tramitacao_anterior["SITUACAO_TRAMIT"] != SIEDocumentoDAO.TRAMITACAO_SITUACAO_RECEBIDO:
            raise SIEException("Tramitacao anterior ainda nao foi processada")

        tramitacao_params = {
            "SEQUENCIA": tramitacao_anterior["SEQUENCIA"] + 1,
            "ID_DOCUMENTO": documento["ID_DOCUMENTO"],
            "TIPO_ORIGEM": documento["TIPO_PROPRIETARIO"],
            "ID_ORIGEM": documento["ID_PROPRIETARIO"],
            "TIPO_DESTINO": documento["TIPO_PROPRIETARIO"],
            "ID_DESTINO": documento["ID_PROPRIETARIO"],
            "DT_ENVIO": date.today(),
            "SITUACAO_TRAMIT": SIEDocumentoDAO.TRAMITACAO_SITUACAO_AGUARDANDO,
            "IND_RETORNO_OBRIG": SIEDocumentoDAO.TRAMITACAO_IND_RETORNO_OBRIG_NAO,
            "DT_ALTERACAO": date.today(),
            "HR_ALTERACAO": strftime("%H:%M:%S"),
            "PRIORIDADE_TAB": 5101,
            "PRIORIDADE_ITEM": SIEDocumentoDAO.TRAMITACAO_PRIORIDADE_NORMAL
        }

        id_tramitacao = self.api.post(self.tramite_path, tramitacao_params).insertId
        tramitacao = self.api.get_single_result(self.tramite_path, {
            "ID_TRAMITACAO": id_tramitacao})  # pega uma instancia nova do banco (por seguranca)

        return tramitacao

    def _marcar_tramitacao_atual_entregue(self, documento, fluxo, resolvedor_destino=None):
        """
        Marca a tramitacao atual como entregue, atualiza os campos necessarios e define o fluxo especificado na tramitacao.

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :param fluxo: Um dicionario referente a uma entrada na tabela FLUXOS
        :type fluxo: dict
        :param resolvedor_destino: eh um callable que resolve o destino dado um fluxo que tenha a flag IND_QUERY='S',
                                    ou seja, o tipo_destino e id_destino devem ser obtidos atraves de uma query adicional.
                                    O retorno deve ser uma tupla (tipo_destino, id_destino).
        :type resolvedor_destino: callable
        :raises: SIEException
        """

        try:
            # Pega a tramitacao atual
            tramitacao = self.obter_tramitacao_atual(documento)

            if tramitacao["SITUACAO_TRAMIT"] != SIEDocumentoDAO.TRAMITACAO_SITUACAO_AGUARDANDO:
                # Espera uma linha de tramitação com status 'T'
                raise SIEException("Documento em estado de tramitação corrompido.")

            if self.__is_destino_fluxo_definido_externamente(fluxo):
                if not resolvedor_destino:
                    raise SIEException("Nao eh possivel tramitar um documento atraves de um fluxo "
                                       "que possui a flag IND_QUERY='S' sem ter especificado uma "
                                       "callable para resolver o destino (id/tipo)")

                tipo_destino, id_destino = resolvedor_destino(fluxo)
                fluxo.update({'TIPO_DESTINO': tipo_destino, 'ID_DESTINO': id_destino})

            # atualizando a tramitacao
            tramitacao.update({
                "TIPO_DESTINO": fluxo["TIPO_DESTINO"],
                "ID_DESTINO": fluxo["ID_DESTINO"],
                "DT_ENVIO": date.today(),
                "DT_VALIDADE": self.__calcular_data_validade(date.today(), fluxo["NUM_DIAS"]),
                "DESPACHO": fluxo["TEXTO_DESPACHO"],
                "DESPACHO_RTF": fluxo["TEXTO_DESPACHO"],
                "SITUACAO_TRAMIT": SIEDocumentoDAO.TRAMITACAO_SITUACAO_ENTREGUE,
                "IND_RETORNO_OBRIG": SIEDocumentoDAO.TRAMITACAO_IND_RETORNO_OBRIG_CONFORME_FLUXO,
                "ID_FLUXO": fluxo["ID_FLUXO"],
                "DT_ALTERACAO": date.today(),
                "HR_ALTERACAO": strftime("%H:%M:%S"),
                "CONCORRENCIA": tramitacao["CONCORRENCIA"] + 1,
                "ID_USUARIO_INFO": self.usuario["ID_USUARIO"],
                "DT_DESPACHO": date.today(),
                "HR_DESPACHO": strftime("%H:%M:%S"),
                "ID_APLIC_ACAO": fluxo["ID_APLIC_ACAO"]
            })

            self.api.put(self.tramite_path, tramitacao)

            try:
                self.atualizar_situacao_documento(documento, fluxo)
            except APIException as e:
                raise SIEException("Nao foi possivel atualizar o documento", e)

        except (APIException, SIEException) as e:
            raise SIEException("Nao foi possivel tramitar o documento", e)

    def arquivar_documento(self, id_documento):
        """
        Método que resume a ação de arquivar documento aplicada em comum a todos os arquivamentos.

        :param id_documento: id_documento do documento a ser arquivado.
        :return:
        """
        # Pega a tramitacao atual
        documento = {"ID_DOCUMENTO": id_documento}
        tramitacao = self.obter_tramitacao_atual(documento)

        tramitacao.update({
            "SITUACAO_TRAMIT": SIEDocumentoDAO.TRAMITACAO_SITUACAO_RECEBIDO
        })

        self.api.put(self.tramite_path, tramitacao)

        # atualiza documento
        documento.update({
            "DT_ARQUIVAMENTO": date.today()
        })
        self.api.put(self.path, documento)

    def _marcar_tramitacao_atual_recebida(self, documento):
        """
        Marca o documento como recebido na tramitacao atual do documento
        Muda o id_proprietario e o tipo_proprietario do documento atual.
        Esse metodo deve ser usado para emular a abertura da tramitacao atraves da caixa postal do SIE.

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :return Boolean indicando se comportamento foi de receber o documento ou ignorar.
        :raises: SIEException
        """
        try:
            # Pega a tramitacao atual
            tramitacao = self.obter_tramitacao_atual(documento)

            if tramitacao["SITUACAO_TRAMIT"] == SIEDocumentoDAO.TRAMITACAO_SITUACAO_ENTREGUE:
                # atualiza tramitacao
                tramitacao.update({
                    "SITUACAO_TRAMIT": SIEDocumentoDAO.TRAMITACAO_SITUACAO_RECEBIDO,
                    "DT_RECEBIMENTO": date.today(),
                    "HR_RECEBIMENTO": strftime("%H:%M:%S")
                    # "DT_ALTERACAO": date.today(), # são alterados pelo servidor
                    # "HR_ALTERACAO": strftime("%H:%M:%S"), # são alterados pelo servidor
                })
                self.api.put(self.tramite_path, tramitacao)

                # atualiza documento
                documento.update({
                    "TIPO_PROPRIETARIO": tramitacao["TIPO_DESTINO"],
                    "ID_PROPRIETARIO": tramitacao['ID_DESTINO']
                })
                self.api.put(self.path, documento)

                return True

            elif tramitacao["SITUACAO_TRAMIT"] == SIEDocumentoDAO.TRAMITACAO_SITUACAO_AGUARDANDO:
                # raise? Em tese, posso abrir pelo SIE e não precisaria desse passo.
                return False
            else:
                # Shouldn't fall here.
                raise NotImplementedError

        except (APIException, SIEException) as e:
            raise SIEException("Nao foi possivel tramitar o documento", e)

    def obter_primeira_tramitacao(self, documento):
        """

        Retorna a primeira tramitacao do documento passado como parametro.

        :param documento: dict contendo ID_DOCUMENTO
        :return:
        """
        try:
            params = {
                "ID_DOCUMENTO": documento['ID_DOCUMENTO'],
                "ORDERBY": "SEQUENCIA",
                "SORT": "ASC"
            }
            # Pega a tramitacao atual
            tramitacao = self.api.get_single_result(self.tramite_path, params)
        except APIException as e:
            raise SIEException("Nao foi possivel obter tramitacao", e)

        return tramitacao

    def obter_tramitacoes(self, documento):
        """
        Retorna as tramitacoes de um documento.
        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :return: Uma dicionario correspondente a uma entrada da tabela TRAMITACOES
        :rtype : dict
        :raises: SIEException
        """
        try:
            params = {
                "ID_DOCUMENTO": documento['ID_DOCUMENTO'],
                "ORDERBY": "SEQUENCIA",
                "SORT": "ASC"
            }
            # Pega a tramitacao atual
            tramitacao = self.api.get(self.tramite_path, params)
        except APIException as e:
            raise SIEException("Nao foi possivel obter tramitacao", e)

        return tramitacao

    def obter_tramitacao_atual(self, documento):
        """
        Retorna a tramitacao atual (mais recente) do documento.
        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :return: Uma dicionario correspondente a uma entrada da tabela TRAMITACOES
        :rtype : dict
        :raises: SIEException
        """
        try:
            params = {
                "ID_DOCUMENTO": documento['ID_DOCUMENTO'],
                "ORDERBY": "SEQUENCIA",
                "SORT": "DESC"
            }
            # Pega a tramitacao atual
            tramitacao = self.api.get_single_result(self.tramite_path, params)
        except APIException as e:
            raise SIEException("Nao foi possivel obter tramitacao", e)

        return tramitacao

    def remover_tramitacoes(self, documento):
        """
        Dado um documento, a funcao busca e remove suas tramitacoes. Use com cautela.
        
        :type documento: dict
        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :raises: SIEException
        """
        try:
            tramitacoes = self.api.get(self.tramite_path, {"ID_DOCUMENTO": documento['ID_DOCUMENTO']},
                                       ['ID_TRAMITACAO'])
            for tramitacao in tramitacoes.content:
                self.api.delete(self.tramite_path, {'ID_TRAMITACAO': tramitacao['ID_TRAMITACAO']})
        except APIException as e:
            print "Nenhuma tramitacao encontrada para o documento %d" % documento['ID_DOCUMENTO']
            raise e

    @staticmethod
    def __is_destino_fluxo_definido_externamente(fluxo):
        return fluxo['IND_QUERY'].strip() == 'S'

    # MARK: Fluxos

    def obter_fluxo_tramitacao_atual(self, documento):
        """
        Retorna o fluxo de tramitacao atual do documento especificado:

        SELECT F.*
        FROM FLUXOS F
        WHERE ID_FLUXO = (  SELECT T.*
                            FROM TRAMITACOES
                            WHERE ID_DOCUMENTO = :ID_DOCUMENTO
                            ORDER BY :ID_TRAMITACAO DESC
                            LIMIT 1)

        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :rtype : dict
        :return: Uma dicionario correspondente a uma entrada da tabela FLUXOS
        """

        # obter da tabela de tramitacoes pois o fluxo pode ter sido modificado ao longo do tempo
        # isso eh de contraste com obter da tabela de fluxos para termos as opcoes de fluxo mais atualizadas
        tramitacao_atual = self.obter_tramitacao_atual(documento)
        params = {"ID_FLUXO": tramitacao_atual["ID_FLUXO"]}
        return self.api.get_single_result(self.fluxo_path, params)

    def obter_proximos_fluxos_tramitacao_validos(self, documento):
        """
        Retorna os proximos fluxos de tramitacoes validos atualmente para o documento especificado
        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :return: dicionarios com os fluxos
        :rtype: APIResultObject
        """

        params = {
            "ID_TIPO_DOC": documento["ID_TIPO_DOC"],
            "SITUACAO_ATUAL": documento["SITUACAO_ATUAL"],
            "IND_ATIVO": "S",
            "LMIN": 0,
            "LMAX": 99999999
        }
        return self.api.get(self.fluxo_path, params, bypass_no_content_exception=True)

    def obter_proximo_fluxo_dado_destino(self, documento, destino):
        """
        Retorna os proximos fluxos de tramitacoes validos atualmente para o documento especificado
        :param documento: Um dicionario contendo uma entrada da tabela DOCUMENTOS
        :type documento: dict
        :param destino: Um int contendo o cod da situacao futura pretendida
        :type destino: int
        :return: dicionarios com os fluxos
        :rtype: APIResultObject
        """

        params = {
            "ID_TIPO_DOC": documento["ID_TIPO_DOC"],
            "SITUACAO_ATUAL": documento["SITUACAO_ATUAL"],
            "SITUACAO_FUTURA": destino,
            "IND_ATIVO": "S",
            "LMIN": 0,
            "LMAX": 99999999
        }
        return self.api.get_single_result(self.fluxo_path, params, bypass_no_content_exception=True)

    def obter_fluxo_inicial(self, documento):
        """
        Retorna o fluxo de acordo com a query para pegar o fluxo inicial de uma tramitacao:

        “SELECT F.* FROM FLUXOS F WHERE F.SITUACAO_ATUAL = 1 AND F.IND_ATIVO = ‘S’ AND F.ID_TIPO_DOC =
        :ID_TIPO_DOC”

        :param documento:
        :return:
        """
        params = {
            "ID_TIPO_DOC": documento["ID_TIPO_DOC"],
            "SITUACAO_ATUAL": 1,
            "IND_ATIVO": "S",
        }

        fluxos = self.api.get(self.fluxo_path, params, bypass_no_content_exception=True)

        if len(fluxos) == 0:
            raise SIEException("Nao foi possivel obter o fluxo inical para o tipo de documento especificado.")

        if len(fluxos) > 2:
            raise SIEException("Tipo de documento possui mais de um fluxo inicial definido. Escolha um manualmente.")

        return fluxos.first()

    @staticmethod
    def __calcular_data_validade(data, dias):
        """
        Autodocumentada.

        :type data: date
        :type dias: int
        :rtype: date
        :param data: Data incial
        :param dias: Quantidade de dias
        :return: Retorna a data enviada, acrescida da quantidade de dias
        """
        return data + timedelta(days=dias)

    def obter_documentos(self, tipo_doc, params):
        """
        Obtem documento de um tipo de documento especifico, onde mais parâmetros podem ser especificados.

        :param tipo_doc:
        :return:
        """

        params.update({
            "ID_TIPO_DOC": tipo_doc,
            "LMIN": 0,
            "LMAX": 99999
        })

        return self.api.get(self.path, params, bypass_no_content_exception=True)


class _EstadosDocumentosDAO(SIE):
    path = "ESTADOS_DOCUMENTOS"

    COD_TABELA_SITUACAO_DOCUMENTO = 2001
    ITEM_SITUACAO_DOCUMENTO_ATIVO = 1

    def __init__(self):
        super(_EstadosDocumentosDAO, self).__init__()

    def ativar_documento(self, id_documento):
        """
        Insere uma linha em 'ESTADOS_DOCUMENTOS' com a situacao 'ativa'.
        Com isso ele supostamente aparece na caixa postal dos usuários.

        :param id_documento:
        :return:
        """
        documento_ativo = {
            "ID_DOCUMENTO": id_documento,
            "COD_SITUACAO_TAB": self.COD_TABELA_SITUACAO_DOCUMENTO,
            "COD_SITUACAO_ITEM": self.ITEM_SITUACAO_DOCUMENTO_ATIVO
        }

        self.api.post(self.path, documento_ativo)


class SIEAssuntosDAO(SIE):
    path = "ASSUNTOS"
    primary_key = "ID_ASSUNTO"  # TODO Começo a achar que isso resolve metade de alguns problemas.

    def __init__(self):
        super(SIEAssuntosDAO, self).__init__()

    def get_by_id(self, identifier):
        """
        Retorna a única linha da tabela que tem o id passado, se o mesmo existir, None c.c.
        :param identifier:
        :return:
        """

        # TODO Acho que esse método está genérico suficiente para representar esse tipo de comportamento comum.
        where = {
            self.primary_key: identifier
        }

        return self.api.get_single_result(self.path, where, bypass_no_content_exception=True)


class SIETiposDocumentosDAO(SIE):
    path = "TIPOS_DOCUMENTOS"

    COD_IND_NUMERACAO_SUPERIOR = "S"

    def __init__(self):
        super(SIETiposDocumentosDAO, self).__init__()

    def obter_parametros_tipo_documento(self, id_tipo_doc):
        where = {
            "ID_TIPO_DOC": id_tipo_doc
        }

        return self.api.get_single_result(self.path, where)

    def get_tipo_doc_a_incrementar(self, id_tipo_doc):
        params = self.obter_parametros_tipo_documento(id_tipo_doc)

        while params['IND_NUMERACAO_SUP'] == self.COD_IND_NUMERACAO_SUPERIOR:
            # TODO Existe maneira mais esperta de fazer isso aqui?
            params = self.obter_parametros_tipo_documento(params['ID_TIPO_DOC_SUP'])

        return params['ID_TIPO_DOC']

    def obter_mascara(self, id_tipo_doc):
        # todo: strip eh necessario pois mascara vem com whitespaces no final(pq???). ']
        return self.obter_parametros_tipo_documento(id_tipo_doc)["MASCARA_TIPO_DOC"].strip()


class _NumeroProcessoTipoDocumentoDAO(SIE):
    """ Classe helper para gerar os numeros de processo de documentos. """
    path = "NUMEROS_TIPO_DOC"

    def __init__(self, id_tipo_documento, ano=date.today().year):
        """
        :param id_tipo_documento: ID do tipo de documento que esta se lidando
        :type id_tipo_documento: int
        :param ano:
        """
        super(_NumeroProcessoTipoDocumentoDAO, self).__init__()
        self.id_tipo_doc = id_tipo_documento
        self.ano = ano

    def gerar_numero_processo(self):
        """
        Gera o proximo numero de processo a ser usado, formado de acordo com a mascara do tipo de documento.

        :rtype: str
        :return: Retorna o NUM_PROCESSO gerado a partir da logica de negocio
        :raise: SIEException
        """
        try:
            try:
                mascara = SIETiposDocumentosDAO().obter_mascara(self.id_tipo_doc)
                prox_numero = self.__proximo_numero_tipo_documento()
            except APIException as e:
                raise SIEException("Erro obter mascara do tipo documento " + str(self.id_tipo_doc), e)

            if mascara == "pNNNN/AAAA":  # TODO usar o parser de mascara ao inves dessa gambi
                numero = self.__gera_numero_processo_projeto(prox_numero, "P")

            elif mascara == "eNNNN/AAAA":  # TODO usar o parser de mascara ao inves dessa gambi
                numero = self.__gera_numero_processo_projeto(prox_numero, "e")

            elif mascara == "xNNNN/AAAA":  # TODO usar o parser de mascara ao inves dessa gambi
                numero = self.__gera_numero_processo_projeto(prox_numero, "x")

            elif mascara == "dNNNN/AAAA":  # TODO usar o parser de mascara ao inves dessa gambi
                numero = self.__gera_numero_processo_projeto(prox_numero, "d")

            elif mascara == "peNNNN/AAAA":  # TODO usar o parser de mascara ao inves dessa gambi
                numero = self.__gera_numero_processo_projeto(prox_numero, "pe")

            elif mascara == "NNNNNN/AAAA":  # TODO usar um parser de mascar em vez dessa gambi
                numero = self.__gera_numero_processo_avaliacao_projeto(prox_numero)
            else:  # interpretar a mascara
                # TODO Criar parser para mascara para entender como gerar o numero do processo de modo generico

                raise NotImplementedError
            return numero
        except Exception as e:
            raise e  # raise SIEException("Erro ao gerar numero de processo.", e)

    def reverter_ultimo_numero_processo(self):
        """ Reverte a geracao do ultimo numero de processo. """
        params = {"ID_TIPO_DOC": SIETiposDocumentosDAO().get_tipo_doc_a_incrementar(self.id_tipo_doc),
                  "ANO_TIPO_DOC": self.ano}
        fields = ["NUM_ULTIMO_DOC"]

        try:
            valor_anterior = self.api.get_single_result(self.path, params, fields)[
                                 "NUM_ULTIMO_DOC"] - 1  # TODO resolver problema de concorrencia
            try:
                self.__atualizar_ultimo_numero_tipo_documento(valor_anterior)
            except Exception as e:
                raise SIEException("Erro ao reverter geracao de numero de processo.", e)
        except ValueError as e:
            raise SIEException(
                "Nao existem registros de numeros de processo para o tipo de documento " + str(self.id_tipo_doc), e)

    def atualizar_indicadores_default(self):
        """
        O método atualiza todos os IND_DEFAULT para N para ID_TIPO_DOC da instãncia

        """

        try:

            numerosDocumentos = self.api.get(
                self.path,
                {"ID_TIPO_DOC": SIETiposDocumentosDAO().get_tipo_doc_a_incrementar(self.id_tipo_doc)},
                ["ID_NUMERO_TIPO_DOC"]
            )

            for numero in numerosDocumentos.content:
                self.api.put(
                    self.path,
                    {
                        "ID_NUMERO_TIPO_DOC": numero["ID_NUMERO_TIPO_DOC"],
                        "IND_DEFAULT": "N"
                    }
                )
        except NoContentException as e:
            pass

    def criar_novo_numero_tipo_documento(self):
        """

        NUM_ULTIMO_DOC retorna 1 para que não seja necessário chamar novo método para atualizar
        :rtype : int
        :return: NUM_ULTIMO_DOC da inserção
        """
        NUM_ULTIMO_DOC = 1
        params = {
            "ID_TIPO_DOC": SIETiposDocumentosDAO().get_tipo_doc_a_incrementar(self.id_tipo_doc),
            "ANO_TIPO_DOC": self.ano,
            "IND_DEFAULT": "S",
            "NUM_ULTIMO_DOC": NUM_ULTIMO_DOC
        }
        self.api.post(self.path, params)
        return NUM_ULTIMO_DOC

    def __proximo_numero_tipo_documento(self):
        """
        O metodo retorna qual sera o proximo NUM_TIPO_DOC que sera utilizado. Caso ja exista
        uma entrada nesta tabela para o ANO_TIPO_DOC e ID_TIPO_DOC, retornara o ultimo numero,
        caso contrario, uma nova entrada sera criada.

        :rtype: int
        :raises: SIEException
        """
        params = {"ID_TIPO_DOC": SIETiposDocumentosDAO().get_tipo_doc_a_incrementar(self.id_tipo_doc),
                  "ANO_TIPO_DOC": self.ano}
        fields = ["NUM_ULTIMO_DOC"]

        try:
            numero_novo = self.api.get_single_result(self.path, params, fields)[
                              "NUM_ULTIMO_DOC"] + 1  # TODO resolver problema de concorrencia
            try:
                self.__atualizar_ultimo_numero_tipo_documento(numero_novo)
            except Exception as e:
                raise SIEException(
                    "Erro ao atualizar contador numero de processo para o tipo de documento %d" % self.id_tipo_doc, e)
        except ValueError as e:
            # caso nao exista uma entrada na tabela, criar uma para comecar a
            # gerir a sequencia de numeros de processo para esse tipo de documento/ano
            # SIEException("Não existe entrada na tabela de numeros de processo
            # para o tipo de documento %d" % self.id_tipo_doc, e)
            self.atualizar_indicadores_default()
            numero_novo = self.criar_novo_numero_tipo_documento()

        return numero_novo

    def __atualizar_ultimo_numero_tipo_documento(self, valor):
        """
        Atualiza o contador/sequence do numero de processo do tipo de documento especificado com o valor passado.

        :param valor: valor a ser assinalado como ultimo numero de processo do tipo de documento
        :type valor: int
        :rtype: None
        """
        params = {"ID_TIPO_DOC": SIETiposDocumentosDAO().get_tipo_doc_a_incrementar(self.id_tipo_doc),
                  "ANO_TIPO_DOC": self.ano}
        fields = ["ID_NUMERO_TIPO_DOC"]
        numero_tipo_documento_row = self.api.get_single_result(self.path, params, fields)
        params = {
            "ID_NUMERO_TIPO_DOC": numero_tipo_documento_row["ID_NUMERO_TIPO_DOC"],
            "NUM_ULTIMO_DOC": valor,
            "DT_ALTERACAO": date.today(),
            "HR_ALTERACAO": strftime("%H:%M:%S"),
        }
        self.api.put(self.path, params)

    @deprecated
    def __gera_numero_processo_projeto(self, prox_numero, tipo):
        """
        Codigo especifico para gerar numero de processo de projetos
        OBS: esse metodo eh temporario. Deve-se usar o parser generico.
        """

        num_ultimo_doc = str(prox_numero).zfill(4)  # NNNN
        num_processo = tipo + ("%s/%d" % (num_ultimo_doc, self.ano))  # _NNNN/AAAA
        return num_processo

    @deprecated
    def __gera_numero_processo_avaliacao_projeto(self, prox_numero):
        """
        Codigo especifico para gerar numero de processo de avaliacoes de projeto
        OBS: esse metodo eh temporario. Deve-se usar o parser generico.
        """

        num_ultimo_doc = str(prox_numero).zfill(6)  # NNNNNN
        num_processo = "%s/%d" % (num_ultimo_doc, self.ano)  # NNNNNN/AAAA
        return num_processo
