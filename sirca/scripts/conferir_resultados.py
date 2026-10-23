import json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'componente/src'))
from consultas import pn01,pn02,pn03,pn04,pn05
D=json.loads((R/'evidencias/dados_modelo.json').read_text());B=json.loads((R/'evidencias/banco.json').read_text())
indep={'PN-01':[{'participantes_atendidos':pn01(D)}],'PN-02':pn02(D),'PN-03':pn03(D),'PN-04':pn04(D),'PN-05':pn05(D)}
report=[]
for pn,answer in indep.items():
    sql=B['resultados'][pn]
    for r in sql:
        for k,v in r.items():
            if k in {'data_evento','primeira_falta','ultima_falta'} and v:r[k]=v[:10]
    ok=sql==answer
    assert ok,(pn,sql,answer)
    report.append(dict(consulta=pn,sql_vs_python=ok,linhas=len(answer)))
(R/'evidencias/conferencia_independente.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
