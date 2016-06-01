# -*- coding: utf-8 -*-
from datetime import datetime
from deprecate import deprecated
from unicodedata import normalize
from functools import wraps

__author__ = 'raulbarbosa'


def sie_strip_unicode_string(encoding='utf-8'):
    """
    Decorator que faz um tratamento de strings que vem do BD (SIE) - usar para exibição primordialmente.
    :param encoding: um encoding para 'encodar' a string
    :return: parâmetro passado 'encodado e stripado' se existir ou string vazia.
    """

    def actual_decorator(fn):

        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            lista = fn(self, *args, **kwargs)
            return strip_encode(lista, encoding)
        return wrapper
    return actual_decorator


def strip_encode(string, encoding='utf-8'):
    """
    Usado nos muitos casos de encoda string se tem string, senão exibe vazio.
    :param string:
    :param encoding:
    :return:
    """

    if string:
        return encode_if_unicode(string, encoding).strip()
    else:
        return ""


def encoded_tab_estruturada(encoding):
    """

    :param encoding: um encoding para 'encodar' a string
    :return: uma lista onde cada elemento é uma tupla (item,descricao) e descricao será o parâmetro a ser encodado
    """

    def actual_decorator(fn):

        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            lista = fn(self, *args, **kwargs)
            if lista:
                lista = [(item, descricao.encode(encoding)) for (item, descricao) in
                         lista]  # encoda segundo item (texto do banco)
            return lista
        return wrapper
    return actual_decorator


def encode_if_unicode(x, encoding='utf-8'):
    return x.encode(encoding) if type(x) == unicode else x


@deprecated
def dict_encode_if_unicode(dicionario):
    return {campo: encode_if_unicode(dicionario[campo]) for campo in dicionario} if type(dicionario) == dict else {}


def campos_sie_lower(lista):
    """
    Refaz uma lista de Rows vinda da API com os nomes dos campos em letra minuscula
    :param lista:
    :return: lista_final com os campos em minuscula.
    """
    lista_final = []
    for item in lista:
        novo_item = {}
        for k, v in item.iteritems():
            novo_item[encode_if_unicode(k).lower()] = encode_if_unicode(v)
        lista_final.append(novo_item)
    return lista_final


def remover_acentos_query(query):
    if isinstance(query, list):
        query = map(remover_acentos, query)
    else:
        query = remover_acentos(query)
    return query


def sie_date_to_str():
    raise NotImplementedError


def force_int(lista_strings):
    """
    Força uma lista de string a ser uma só de inteiros.

    >>> a = force_int(['1','2'])
    >>> assert a == [1,2]

    :type lista_strings: List[str]
    :return:
    """

    a = map(lambda x: int(x), lista_strings)
    return a


def sie_str_to_date(campo, format='%Y-%m-%d'):
    """
    Dado um campo que é 'date' no SIE, transforma em instância para ser utilizada no python.
    :rtype: object
    """
    assert campo  # Asserção só para ele não criar com uma data vazia e causar silent error.

    return datetime.strptime(campo.strip(), format).date()


def datas_colidem(d1_ini, d1_fim, d2_ini, d2_fim):
    """
    Verifica de dois intervalos de data colidem.
    Lógica usada é a seguinte (baseada numa resposta do stack overflow bem sagaz):
    Duas datas não colidem se:

    | A |                   |A |
           |B |    ou  |B |

    :param d1_ini:
    :param d1_fim:
    :param d2_ini:
    :param d2_fim:
    :return:
    """

    caso_1 = d2_ini >= d1_fim and d2_ini > d1_ini
    caso_2 = d1_ini >= d2_fim and d1_ini > d2_ini

    return not (caso_1 or caso_2)


def remover_acentos(txt, encoding='utf-8'):
    """
    Devolve cópia de uma str substituindo os caracteres
    acentuados pelos seus equivalentes não acentuados.

    ATENÇÃO: carateres gráficos não ASCII e não alfa-numéricos,
    tais como bullets, travessões, aspas assimétricas, etc.
    são simplesmente removidos!

    >>> remover_acentos('[ACENTUAÇÃO] ç: áàãâä! éèêë? íì&#297;îï, óòõôö; úù&#361;ûü.')
    '[ACENTUACAO] c: aaaaa! eeee? iiiii, ooooo; uuuuu.'

    """
    if isinstance(txt, unicode):
        txt = txt.encode('utf-8')
    return normalize('NFKD', txt.decode(encoding)).encode('ASCII', 'ignore')
