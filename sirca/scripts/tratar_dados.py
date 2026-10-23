"""ETL deterministica. Brutos imutaveis; uma decisao por linha fisica.
Reexecute da raiz: python scripts/tratar_dados.py
"""
import sys, csv, re, json, hashlib, datetime as dt
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook
R = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'componente/src'))
from carregador import normalizar_texto, chave_texto, normalizar_data, presenca_oficial
BR=R/'dados/brutos'; OUT=R/'dados/tratados'; EV=R/'evidencias'
REF=dt.date(2026,10,22)
ARQ='Instituto_Semear_planilhas_operacionais_2024-2026.xlsx'
NULLS={'','-','N/I','NAO INFORMADO','??'}

def texto(v):
    s=' '.join(str(v or '').split())
    return None if chave_texto(s) in NULLS else s

def valor(v):
    if v is None or chave_texto(v) in NULLS or chave_texto(v)=='NAO INFORMADO': return None
    s=str(v).replace('R$','').replace(' ','')
    if ',' in s:s=s.replace('.','').replace(',','.')
    try:n=Decimal(s)
    except InvalidOperation:raise ValueError('VALOR_INVALIDO')
    if not n.is_finite() or n<0:raise ValueError('VALOR_INVALIDO')
    return str(n.quantize(Decimal('.01')))

def data(v,opcional=False,negocio=False):
    if texto(v) is None:
        if opcional:return None
        raise ValueError('DATA_AUSENTE')
    d=normalizar_data(v)
    if d>REF:raise ValueError('DATA_FUTURA')
    if negocio and d<dt.date(2024,1,1):raise ValueError('DATA_ANTERIOR_2024')
    return d.isoformat()

def inteiro(v,opcional=False):
    if texto(v) is None:
        if opcional:return None
        raise ValueError('INTEIRO_AUSENTE')
    try:n=Decimal(str(v))
    except InvalidOperation:raise ValueError('INTEIRO_INVALIDO')
    if n<0 or n != int(n):raise ValueError('INTEIRO_INVALIDO')
    return int(n)

def gravar_csv(p,rows,fields=None):
    rows=list(rows)
    if fields is None:fields=list(rows[0]) if rows else []
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True);EV.mkdir(parents=True,exist_ok=True)
    w=load_workbook(BR/ARQ,read_only=True,data_only=True)
    ledger={}; transformations=[]; tables=defaultdict(list); presence=Counter(); encounters={}
    def register(src,sheet,line,row):
        k=(src,sheet,line)
        ledger[k]={'arquivo':src,'aba':sheet,'linha':line,'decisao':None,'regra':None,'detalhe':'','tratado':'','bruto':json.dumps(list(row),ensure_ascii=False,default=str)}
        return k
    def decide(k,decision,rule,detail='',tratado=None):
        assert ledger[k]['decisao'] is None,(k,ledger[k])
        ledger[k].update(decisao=decision,regra=rule,detalhe=detail,tratado=json.dumps(tratado,ensure_ascii=False) if tratado else '')
    def reject(k,e):decide(k,'rejeitado',str(e).split(':')[0],str(e))
    def transform(k,field,a,b,rule):
        if str(a or '') != str(b or ''):
            transformations.append({'arquivo':k[0],'aba':k[1],'linha':k[2],'campo':field,'antes':str(a or ''),'depois':str(b or ''),'criterio':rule})
    def sheet(name):
        for line,row in enumerate(list(w[name].values)[1:],2):
            k=register(ARQ,name,line,row)
            if not any(x is not None and str(x).strip() for x in row):reject(k,'LINHA_VAZIA');continue
            yield k,row
    # Familias: nenhum codigo novo e inventado.
    familias={}
    for k,r in sheet('CadastroFamilias'):
        try:
            cod=normalizar_texto(r[0])
            if not re.fullmatch(r'F\d{3}',cod):raise ValueError('LINHA_NAO_CADASTRAL')
            if cod in familias:raise ValueError('CHAVE_DUPLICADA')
            situ=chave_texto(r[10]).lower()
            if situ not in {'ativo','inativo','desligado'}:raise ValueError('SITUACAO_INVALIDA')
            nome=texto(r[1])
            if not nome:raise ValueError('NOME_AUSENTE')
            row=dict(id_familia=cod,nome_responsavel=nome,cpf_mascarado=texto(r[2]),nascimento_responsavel=data(r[3],True),endereco=texto(r[4]),bairro=texto(r[5]),telefone=texto(r[6]),n_dependentes=inteiro(r[7],True),renda_familiar=valor(r[8]),data_cadastro=data(r[9]),situacao=situ,observacao=texto(r[11]))
            familias[cod]=row;tables['familia'].append(row);decide(k,'aceito','CADASTRO_VALIDO',cod,row)
            for field,old in [('nome_responsavel',r[1]),('bairro',r[5]),('renda_familiar',r[8]),('situacao',r[10]),('data_cadastro',r[9])]:transform(k,field,old,row[field],'normalizacao deterministica')
        except (ValueError,KeyError) as e:reject(k,e)
    # Participantes: duplicatas semanticamente iguais sao uma unica pessoa; nomes abreviados nao sao deduplicados por aproximacao.
    participantes={}; names=defaultdict(list)
    for k,r in sheet('Participantes'):
        try:
            cod=normalizar_texto(r[0]);fam=normalizar_texto(r[2]);nome=texto(r[1])
            if not re.fullmatch(r'P\d{3}',cod):raise ValueError('CODIGO_PARTICIPANTE_AUSENTE_OU_INVALIDO')
            if fam not in familias:raise ValueError('RN-02_FAMILIA_INEXISTENTE')
            if not nome:raise ValueError('NOME_AUSENTE')
            situ=chave_texto(r[7]).lower()
            if situ not in {'ativo','desligado','transferido'}:raise ValueError('SITUACAO_INVALIDA')
            row=dict(id_participante=cod,nome=nome,id_familia=fam,nascimento=data(r[3]),escola=texto(r[4]),turma_ano=texto(r[5]),data_entrada=data(r[6]),situacao=situ,data_desligamento=None)
            if row['nascimento']>row['data_entrada']:raise ValueError('NASCIMENTO_APOS_ENTRADA')
            if cod in participantes:
                old=participantes[cod]
                if all(chave_texto(old[x])==chave_texto(row[x]) for x in row):raise ValueError('CADASTRO_DUPLICADO_EQUIVALENTE')
                raise ValueError('CADASTRO_DUPLICADO_CONFLITANTE')
            participantes[cod]=row;names[chave_texto(nome)].append(cod);tables['participante'].append(row);decide(k,'aceito','CADASTRO_VALIDO',cod,row)
            for field,old in [('nome',r[1]),('nascimento',r[3]),('data_entrada',r[6]),('situacao',r[7])]:transform(k,field,old,row[field],'normalizacao deterministica')
        except (ValueError,KeyError) as e:reject(k,e)
    cols={};colseq=0
    def colaborador(nome,tipo):
        nonlocal colseq
        nk=(chave_texto(nome),tipo)
        if nk not in cols:
            colseq+=1;cols[nk]=f'C{colseq:03d}'
            tables['colaborador'].append(dict(id_colaborador=cols[nk],nome=texto(nome),tipo_identificador=tipo))
        return cols[nk]
    oficinas={};ofnames={}
    for k,r in sheet('Oficinas'):
        try:
            cod=normalizar_texto(r[0]);nome=texto(r[1])
            if not re.fullmatch(r'OF\d{2}',cod) or cod in oficinas:raise ValueError('CODIGO_OFICINA_INVALIDO')
            h=re.fullmatch(r'(\d\d:\d\d) às (\d\d:\d\d)',str(r[4]).strip())
            if not h:raise ValueError('HORARIO_INVALIDO')
            for t in h.groups():dt.time.fromisoformat(t)
            if h[1]>=h[2]:raise ValueError('HORARIO_INVALIDO')
            def mes(v):
                if not texto(v) or chave_texto(v)=='EM ANDAMENTO':return None
                m=re.fullmatch(r'(\d{2})/(\d{4})',str(v))
                if not m:raise ValueError('MES_INVALIDO')
                dt.date(int(m[2]),int(m[1]),1)
                return f'{m[2]}-{m[1]}'
            row=dict(id_oficina=cod,nome=nome,id_oficineiro=colaborador(r[2],'nome_fornecido'),dia_semana=chave_texto(r[3]).lower(),hora_inicio=h[1],hora_fim=h[2],sala=texto(r[5]),vagas=inteiro(r[6]),mes_inicio=mes(r[7]),mes_fim=mes(r[8]))
            oficinas[cod]=row;ofnames[chave_texto(nome)]=cod;tables['oficina'].append(row);decide(k,'aceito','CADASTRO_VALIDO',cod,row)
            transform(k,'hora_inicio',r[4],h[1],'separacao de intervalo sem inventar dia do mes')
        except (ValueError,KeyError) as e:reject(k,e)
    def participante(v):
        s=normalizar_texto(v)
        if s in participantes:return s
        found=names.get(chave_texto(v),[])
        if len(found)==1:return found[0]
        raise ValueError('RF-07_PARTICIPANTE_INEXISTENTE_OU_AMBIGUO')
    def oficina(v):
        s=normalizar_texto(v)
        if s in oficinas:return s
        if chave_texto(v) in ofnames:return ofnames[chave_texto(v)]
        raise ValueError('RF-07_OFICINA_INEXISTENTE')
    # Lotes separados: xlsx e fonte primaria; CSV legado e reconciliacao, nunca soma duplicada.
    freq_batches=[]
    freq_batches.append([(k,list(r)) for k,r in sheet('Frequencia')])
    with (BR/'frequencia_export_sistema_antigo.csv').open(encoding='latin-1',newline='') as f:
        freq_batches.append([(register('frequencia_export_sistema_antigo.csv','CSV',i,r),r) for i,r in enumerate(list(csv.reader(f,delimiter=';'))[1:],2)])
    freq={};reserved=set()
    for batchno,batch in enumerate(freq_batches):
        cand=defaultdict(list)
        for k,r in batch:
            if str(r[0] or '').startswith('OBS:'):
                reject(k,'LINHA_NAO_CADASTRAL');continue
            presence[(k[0],str(r[3] or ''))]+=1
            try:
                # Encontros sao extraidos independentemente do estado de cada participante.
                d=data(r[0],negocio=True);o=oficina(r[1]);encounters[(o,d)]=dict(id_oficina=o,data_encontro=d)
                p=participante(r[2]);s=presenca_oficial(r[3])
                if participantes[p]['situacao']=='desligado':raise ValueError('RN-04_DATA_DESLIGAMENTO_AUSENTE')
                if not texto(r[4]) or texto(r[4])=='?':raise ValueError('RF-10_RESPONSAVEL_AUSENTE')
                who=colaborador(r[4],'token_legado')
                row=dict(id_participante=p,id_oficina=o,data_encontro=d,presenca=s,id_registrador=who,registrado_em=None,origem='legado',arquivo_origem=k[0],linha_origem=k[2])
                key=(p,o,d)
                if batchno and key in reserved:raise ValueError('RN-03_SOBREPOSICAO_FONTE_SECUNDARIA')
                cand[key].append((k,row,r))
            except (ValueError,KeyError) as e:reject(k,e)
        for key,rows in cand.items():
            reserved.add(key)
            semantic={(r['presenca'],r['id_registrador']) for _,r,_ in rows}
            if len(semantic)>1:
                for k,row,raw in rows:reject(k,'RN-03_DUPLICATA_CONFLITANTE')
                continue
            k,row,raw=rows[0];freq[key]=row;decide(k,'aceito','FREQUENCIA_VALIDA','|'.join(key),row)
            for field,old in [('id_participante',raw[2]),('id_oficina',raw[1]),('data_encontro',raw[0]),('presenca',raw[3])]:transform(k,field,old,row[field],'RN-01 / correspondencia univoca / data normalizada')
            for dk,_,_ in rows[1:]:reject(dk,'RN-03_DUPLICATA_EQUIVALENTE')
    tables['encontro']=sorted(encounters.values(),key=lambda r:(r['id_oficina'],r['data_encontro']))
    tables['frequencia']=sorted(freq.values(),key=lambda r:(r['data_encontro'],r['id_oficina'],r['id_participante']))
    # Doacoes: chave de conciliacao tem origem na linha primaria. Conflitos de valor nao sobrescrevem o xlsx.
    donations={}
    d_batches=[[(k,list(r)) for k,r in sheet('Doacoes')]]
    with (BR/'doacoes_2026.csv').open(encoding='utf-8',newline='') as f:
        d_batches.append([(register('doacoes_2026.csv','CSV',i,r),r) for i,r in enumerate(list(csv.reader(f))[1:],2)])
    for bn,batch in enumerate(d_batches):
        for k,r in batch:
            try:
                d=data(r[0],negocio=True);don=texto(r[1]);tipo=chave_texto(r[2]).lower();item=texto(r[3]);key=(d,chave_texto(don),tipo,chave_texto(item))
                if not don or not tipo or not item:raise ValueError('DOACAO_CAMPO_OBRIGATORIO_AUSENTE')
                if bn and key in donations:raise ValueError('DOACAO_SOBREPOSICAO_FONTE_SECUNDARIA')
                if key in donations:raise ValueError('DOACAO_DUPLICATA')
                qraw=texto(r[4]);quant=None
                if qraw and chave_texto(qraw)!='VARIAS':quant=valor(qraw)
                row=dict(id_doacao='D%04d'%(len(donations)+1),data_doacao=d,doador=don,tipo=tipo,item=item,quantidade=quant,unidade=(chave_texto(r[5]).lower() or None),destino=texto(r[6]),valor_estimado=valor(r[7]),arquivo_origem=k[0],linha_origem=k[2])
                donations[key]=row;tables['doacao'].append(row);decide(k,'aceito','DOACAO_VALIDA',row['id_doacao'],row)
                for field,old in [('valor_estimado',r[7]),('data_doacao',r[0]),('tipo',r[2])]:transform(k,field,old,row[field],'normalizacao; valor desconhecido continua NULL')
            except (ValueError,KeyError) as e:reject(k,e)
    orgaos={}
    for k,r in sheet('Encaminhamentos'):
        try:
            d=data(r[0],negocio=True);p=participante(r[1]);serv=texto(r[2]);org=texto(r[3]);situ=chave_texto(r[4]).lower() or None
            if situ in {'-','nao informado'}:situ=None
            if situ not in {None,'sem retorno','encaminhado','aguardando','atendido'}:raise ValueError('SITUACAO_ENCAMINHAMENTO_INVALIDA')
            if not org or not serv:raise ValueError('ORGAO_OU_SERVICO_AUSENTE')
            nk=chave_texto(org)
            if nk not in orgaos:
                oid='O%03d'%(len(orgaos)+1);orgaos[nk]=oid;tables['orgao'].append(dict(id_orgao=oid,nome=org))
            row=dict(id_encaminhamento='E%04d'%(len(tables['encaminhamento'])+1),data_encaminhamento=d,id_participante=p,servico=serv,id_orgao=orgaos[nk],situacao=situ,retorno=(chave_texto(r[5]).lower() if texto(r[5]) else None),arquivo_origem=k[0],linha_origem=k[2])
            tables['encaminhamento'].append(row);decide(k,'aceito','ENCAMINHAMENTO_VALIDO',row['id_encaminhamento'],row)
        except (ValueError,KeyError) as e:reject(k,e)
    tables['lacuna_frequencia']=[dict(id_lacuna=1,id_oficina='OF08',inicio='2025-09-01',fim='2025-09-30',motivo='Recado na linha 437 de Frequencia: caderno sumiu; faltam chamadas do mes.')]
    for name,rows in tables.items():gravar_csv(OUT/(name+'.csv'),rows)
    assert all(v['decisao'] in {'aceito','rejeitado'} for v in ledger.values())
    gravar_csv(OUT/'decisoes_por_linha.csv',ledger.values());gravar_csv(OUT/'rejeicoes.csv',(v for v in ledger.values() if v['decisao']=='rejeitado'),list(next(iter(ledger.values()))))
    gravar_csv(OUT/'transformacoes.csv',transformations)
    marks=[]
    for (src,mark),n in sorted(presence.items()):
        try:target=presenca_oficial(mark)
        except ValueError:target='REJEITAR'
        marks.append(dict(arquivo=src,marca=mark or '<vazio>',destino=target,quantidade=n))
    gravar_csv(OUT/'conversao_presenca.csv',marks)
    summary=[]
    for src,sheetname in sorted({k[:2] for k in ledger}):
        vals=[v for k,v in ledger.items() if k[:2]==(src,sheetname)];acc=sum(x['decisao']=='aceito' for x in vals)
        summary.append(dict(arquivo=src,aba=sheetname,lidas=len(vals),aceitas=acc,rejeitadas=len(vals)-acc))
    reasons=Counter(v['regra'] for v in ledger.values() if v['decisao']=='rejeitado')
    report=dict(data_referencia=str(REF),fontes=summary,tabelas={k:len(v) for k,v in tables.items()},rejeicoes_por_regra=dict(sorted(reasons.items())),total_lidas=len(ledger),total_aceitas=sum(v['aceitas'] for v in summary),total_rejeitadas=sum(v['rejeitadas'] for v in summary),transformacoes=len(transformations),sha256_brutos={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in BR.iterdir() if p.is_file()})
    (EV/'carga.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (EV/'dados_modelo.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
    def lit(v):
        if v is None:return 'NULL'
        if isinstance(v,(int,float)):return str(v)
        return "'"+str(v).replace("'","''")+"'"
    sql=['-- Gerado por scripts/tratar_dados.py; PostgreSQL 16+; nao editar.','BEGIN;']
    for table in ['familia','participante','colaborador','oficina','encontro','frequencia','orgao','doacao','encaminhamento','lacuna_frequencia']:
        rows=tables[table]
        if not rows:continue
        fields=list(rows[0]);sql.append('INSERT INTO '+table+' ('+', '.join(fields)+') VALUES\n'+',\n'.join('('+', '.join(lit(r[x]) for x in fields)+')' for r in rows)+';')
    sql.append('COMMIT;')
    (R/'banco/02_carregar_dados.sql').write_text('\n'.join(sql)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
