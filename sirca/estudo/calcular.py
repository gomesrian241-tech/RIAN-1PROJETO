"""Volumes e ajuste obtidos da carga; tempos e reais sao cenario do modelo,
nao entrevista ou medicao humana. Otimizacao: premissas explicitas s=9,w=1.
"""
import json,csv,math
from pathlib import Path
from collections import Counter
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 d=json.loads((R/'evidencias/dados_modelo.json').read_text())
 months=sorted({r['data_encontro'][:7] for r in d['encontro']});fr=Counter(r['data_encontro'][:7] for r in d['frequencia']);enc=Counter(r['data_encontro'][:7] for r in d['encontro'])
 monthly=[dict(mes=m,t=i,frequencias=fr[m],encontros=enc[m]) for i,m in enumerate(months)]
 x=np.arange(len(months),dtype=float);y=np.array([fr[m] for m in months],dtype=float);b,a=np.polyfit(x,y,1);pred=a+b*x
 sse=float(sum((y-pred)**2));sst=float(sum((y-y.mean())**2));r2=1-sse/sst if sst else 1
 mean=float(y.mean());E=sum(enc.values())/len(months)
 active=sum(r['situacao']=='ativo' for r in d['participante']);entradas2025=sum(r['data_entrada'].startswith('2025') for r in d['participante'])
 H=E*(6+9)/60+35*14/60+16;problem=H*18.5+320+450+95
 N=mean;s=9.;w=1.;costhora=18.5
 continuous=math.sqrt(2*N*s/w);candidates=sorted({max(1,min(int(N),math.floor(continuous))),max(1,min(int(N),math.ceil(continuous)))})
 def c(k):return costhora*(N*s/k+w*k/2)/60
 optimal=min(candidates,key=c)
 pmap={r['id_participante']:r for r in d['participante']}
 before=[r for r in d['frequencia'] if r['data_encontro']<pmap[r['id_participante']]['data_entrada']]
 weekdays={'segunda':0,'terca':1,'quarta':2,'quinta':3,'sexta':4}
 import datetime as dt
 omap={r['id_oficina']:r for r in d['oficina']}
 wrongweekday=[r for r in d['encontro'] if dt.date.fromisoformat(r['data_encontro']).weekday()!=weekdays[omap[r['id_oficina']]['dia_semana']]]
 result=dict(periodo_observado=[months[0],months[-1]],datas_extremas=[min(r['data_encontro'] for r in d['encontro']),max(r['data_encontro'] for r in d['encontro'])],mensal=monthly,participantes_ativos=active,entradas_2025=entradas2025,media_entradas_2025=entradas2025/12,media_frequencias=mean,media_encontros=E,ajuste_linear=dict(intercepto=float(a),inclinacao=float(b),r2=r2,sse=sse),modelo_preferido='ajuste linear descritivo; media observada como cenario de capacidade, sem previsao de demanda',cenario_custo=dict(status='ILUSTRATIVO; parametros humanos e monetarios do modelo fornecido, nao medidos pela equipe',chamada_min=6,transcricao_min=9,busca_min=14,consultas_mes=35,prestacao_horas_mes=16,custo_hora=18.5,horas_mes=H,custo_problema_mes=problem,beneficio_mes=problem*.6,investimento_exemplo=22140,custo_recorrente_exemplo=265),otimizacao=dict(status='CENARIO; s=9 min/lote e w=1 min por unidade de lote sao hipoteses de engenharia nao medidas',N=N,s=s,w=w,custo_hora=costhora,x_continuo=continuous,candidatos=[dict(x=k,custo=c(k)) for k in candidates],x_otimo=optimal,custo_minimo=c(optimal),custo_unitario=c(1),custo_lote_maximo=c(int(N))),alertas=dict(frequencias_anteriores_a_data_entrada=len(before),encontros_fora_do_dia_cadastrado=len(wrongweekday),observacao='Ambas sao inconsistencias da fonte sem regra oficial de correcao. Preservadas e sinalizadas; nao se inventou data correta.'))
 (R/'evidencias/quantitativo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 with (R/'estudo/volumes_mensais.csv').open('w',newline='') as f:
  z=csv.DictWriter(f,fieldnames=monthly[0]);z.writeheader();z.writerows(monthly)
 with (R/'dados/tratados/alertas_cronologia.csv').open('w',newline='') as f:
  z=csv.DictWriter(f,fieldnames=['id_participante','id_oficina','data_encontro','data_entrada','motivo']);z.writeheader();z.writerows(dict(id_participante=r['id_participante'],id_oficina=r['id_oficina'],data_encontro=r['data_encontro'],data_entrada=pmap[r['id_participante']]['data_entrada'],motivo='Anterior a entrada cadastral; confirmar historico de cadastro') for r in before)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
