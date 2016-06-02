# coding=utf-8
from unirio.sie.base import SIE
from unirio.sie.utils import remover_acentos_query


class SIEAlunos(SIE):
    def __init__(self):
        super(SIEAlunos, self).__init__()
        self.path = "ALUNOS"

    def getCRA(self, ID_ALUNO):
        """
        O cálculo do coeficiente de rendimento acumulado é calculado pela expressão S (Di × Ci) / S Ci onde Di é a nota
        final da disciplina “i”; Ci é o crédito atribuído à disciplina “i”. Assim, o CRa do aluno é a somatório dos
        produtos das notas da disciplina pelo seu respectivo crédito, dividido pelo somatório dos créditos acumulados
        até o período em curso. O CRa é critério indispensável e fundamental nos concursos de bolsas.

        Referência: Manual do Aluno - UNIRIO

        :type ID_ALUNO: int
        :param ID_ALUNO: Idenficador único de um aluno na tabela ALUNOS
        :return: O coeficiente de rendimento acumulado deste aluno
        :rtype : dict
        """
        return self.api.get("V_COEF_REND_ACAD_ALL", {"ID_ALUNO": ID_ALUNO}).content[0]

    def getCRAAlunos(self, alunos):
        try:
            params = {
                "ID_ALUNO_SET": alunos,
                "LMIN": 0,
                "LMAX": 99999
            }
            cras = self.api.get("V_COEF_REND_ACAD_ALL", params).content
            return {a['ID_ALUNO']: a for a in cras}
        except ValueError:
            return {}

    def getAlunoAtivoFromCPF(self, cpf):
        """
        :type cpf: str
        :rtype : dict
        """
        return self.api.get("V_ALUNOS_ATIVOS", {"CPF_SEM_MASCARA": cpf}).content[0]

    def get_alunos_ativos_graduacao(self,nome_ou_nomes):
        return self.get_alunos_ativos(nome_ou_nomes,"graduacao")

    def get_alunos_ativos(self,nome_ou_nomes,tipo=None):
        """

        :param nome_ou_nomes: string usada em uma query de like no bd
        :return: lista de alunos que dão match na string passada em query
        """

        nome_ou_nomes = remover_acentos_query(nome_ou_nomes)

        params = {"LMIN": 0,
                  "LMAX": 999,
                  "NOME":nome_ou_nomes,
                  "ORDERBY":"NOME",
                  "SORT":"ASC"
                  }

        if tipo:
            params.update({"TIPO_DE_ALUNO":tipo})
        #fields = ["ID_ALUNO", "NOME", "MATRICULA"]
        try:
            res = self.api.get("V_ALUNOS_ATIVOS",params)
            return res.content if res is not None else []
        except ValueError:
            return []

