"""Normalizacao explicita; as marcas intermediarias nunca entram no banco."""
import csv
import datetime as dt
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BRUTOS = RAIZ / 'dados' / 'brutos'
MESES = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}

def carregar_csv(caminho, encoding='utf-8', separador=','):
    with open(caminho, newline='', encoding=encoding) as f:
        return list(csv.DictReader(f, delimiter=separador))

def normalizar_texto(valor):
    return ' '.join(str(valor or '').split()).upper()

def chave_texto(valor):
    return ''.join(c for c in unicodedata.normalize('NFKD', normalizar_texto(valor)) if not unicodedata.combining(c))

def normalizar_data(valor):
    if isinstance(valor, dt.datetime): return valor.date()
    if isinstance(valor, dt.date): return valor
    s = str(valor or '').strip().lower()
    m = re.fullmatch(r'(\d{1,2}) de ([a-zç]{3}) de (\d{4})', s)
    if m:
        return dt.date(int(m[3]), MESES[m[2]], int(m[1]))
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s): return dt.date.fromisoformat(s)
    m = re.fullmatch(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2}|\d{4})', s)
    if not m: raise ValueError('DATA_INVALIDA: ' + s)
    ano = int(m[3])
    if len(m[3]) == 2: ano += 2000 if ano <= 26 else 1900
    return dt.date(ano, int(m[2]), int(m[1]))

def normalizar_presenca(valor):
    s = chave_texto(valor)
    if s in {'P','X','1','PRESENTE'}: return 'presente'
    if s in {'F','0','FALTA','FALTOU'}: return 'falta'
    if s in {'J','JUSTIFICADA','FALTA JUSTIFICADA'}: return 'justificada'
    if s in {'','-'}: return 'indefinido'
    raise ValueError('RN-01_MARCA_DESCONHECIDA: ' + s)

def presenca_oficial(valor):
    p = normalizar_presenca(valor)
    if p == 'indefinido': raise ValueError('RN-01_INDEFINIDA')
    return 'falta justificada' if p == 'justificada' else p

def carregar_modelo(raiz=RAIZ):
    nomes=['familia','participante','colaborador','oficina','encontro','frequencia','doacao','orgao','encaminhamento','lacuna_frequencia']
    dados={}
    for nome in nomes:
        rows=carregar_csv(Path(raiz)/'dados/tratados'/(nome+'.csv'))
        for r in rows:
            for k,v in r.items():
                if v=='':r[k]=None
                elif k in {'n_dependentes','vagas','id_lacuna','linha_origem'}:r[k]=int(v)
        dados[nome]=rows
    return dados
