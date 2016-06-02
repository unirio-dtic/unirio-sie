# coding=utf-8
import base64
from datetime import date
import re
from deprecate import deprecated
from unirio.api import APIException
from unirio.sie import SIE, remover_acentos_query, SIEException

__author__ = 'diogomartins'


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