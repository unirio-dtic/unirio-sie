from datetime import date

from unirio.sie.tests.base import SIETestCase

__author__ = 'carlosfaruolo'


class TestDocumento(SIETestCase):
    DUMMY_INVALID_ID = 857893245934

    def __init__(self, *args, **kwargs):
        super(TestDocumento, self).__init__(*args, **kwargs)

        from unirio.sie.documentos import SIEDocumentoDAO
        from unirio.sie.funcionarios import SIEFuncionarioID

        self.documento_valido = self.api.get(SIEDocumentoDAO.path).first()
        self.funcionario_dummy = self.api.get(SIEFuncionarioID.path).first()

    def setUp(self):
        from unirio.sie.documentos import SIEDocumentoDAO
        self.dao = SIEDocumentoDAO()

    def test_criar_documento_projeto_pesquisa(self):
        from unirio.sie.projetos import pesquisa

        dao_projetos = pesquisa()
        documento = self.dao.criar_documento(self.funcionario_dummy, dao_projetos.documento_inicial_padrao(self.funcionario_dummy))
        self.assertIsInstance(documento, dict)
        self.dao.remover_documento(documento)  # clean poopie

    def test_criar_documento_params_vazios(self):
        with self.assertRaises(KeyError):
            from unirio.sie.projetos import projetos

            dao_projetos = projetos()
            documento = self.dao.criar_documento(self.funcionario_dummy, dict())
            # devo tentar apagar o documento?

    def test_obter_documento(self):
        documento = self.dao.obter_documento(2654)
        self.assertIsInstance(documento, dict)

    def test_obter_documento_id_errado(self):
        with self.assertRaises(Exception):
            documento = self.dao.obter_documento(self.DUMMY_INVALID_ID)

    def test_remover_documento(self):
        from unirio.sie.projetos import pesquisa

        dao_projetos = pesquisa()
        documento = self.dao.criar_documento(self.funcionario_dummy, dao_projetos.documento_inicial_padrao(self.funcionario_dummy))
        self.dao.remover_documento(documento)
        # test passed

    def test_atualizar_situacao_documento(self):
        self.fail("Test not implemented")  # TODO implement this!

# === Tramitacao =======================================================================================================

    def test_tramitar_documento(self):
        self.fail("Test not implemented")  # TODO implement this!

    def test_tramitar_documento_algum_param_nulo(self):
        self.fail("Test not implemented")  # TODO implement this!

    def test_obter_tramitacao_atual(self):
        self.assertIsInstance(self.dao.obter_tramitacao_atual(self.documento_valido), dict)

    def test_remover_tramitacoes(self):
        self.fail("Test not implemented")  # TODO implement this!

# === Fluxo ============================================================================================================

    def test_obter_fluxo_tramitacao_atual(self):
        self.assertIsInstance(self.dao.obter_fluxo_tramitacao_atual(self.documento_valido), dict)

    def test_obter_fluxo_tramitacao_atual_doc_vazio(self):
        with self.assertRaises(KeyError):
            self.dao.obter_fluxo_tramitacao_atual(dict())

    def test_obter_proximos_fluxos_tramitacoes_atual(self):
        fluxos = self.dao.obter_proximos_fluxos_tramitacao_validos(self.documento_valido)
        self.assertIsInstance(fluxos, list)
        for obj in fluxos:
            self.assertIsInstance(obj, dict)

# === _NumProcessoHandler ==============================================================================================

    def __get_ultimo_numero_processo(self):
            return self.dao.api.get_single_result("NUMEROS_TIPO_DOC", {"ID_TIPO_DOC": self.documento_valido["ID_TIPO_DOC"], "ANO_TIPO_DOC": date.today().year}, ["NUM_ULTIMO_DOC"])["NUM_ULTIMO_DOC"]

    def test_gerar_numero_processo(self):

        previous_value = self.__get_ultimo_numero_processo()

        from unirio.sie.documentos import _NumeroProcessoTipoDocumentoDAO
        handler = _NumeroProcessoTipoDocumentoDAO(self.documento_valido["ID_TIPO_DOC"], self.funcionario_dummy)
        handler.gerar_numero_processo()

        new_value = self.__get_ultimo_numero_processo()
        self.assertEqual(previous_value + 1, new_value)
        try:
            handler.reverter_ultimo_numero_processo()
        except Exception:
            pass

    def test_reverter_ultimo_numero_processo(self):
        from unirio.sie.documentos import _NumeroProcessoTipoDocumentoDAO
        handler = _NumeroProcessoTipoDocumentoDAO(self.documento_valido["ID_TIPO_DOC"], self.funcionario_dummy)
        try:
            handler.gerar_numero_processo()
        except Exception:
            pass
        previous_value = self.__get_ultimo_numero_processo()
        handler.reverter_ultimo_numero_processo()
        new_value = self.__get_ultimo_numero_processo()
        self.assertEqual(previous_value - 1, new_value)

# ======================================================================================================================
# more TODO: implement remaining tests
# remember to implement wrong parameters tests as well
