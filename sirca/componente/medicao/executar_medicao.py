"""Medicao de hash x varredura, incluindo base real e dados sinteticos de escala.
31 lotes de 100 consultas por algoritmo; 3 lotes de aquecimento; mesmo conjunto
de alvos; resultados verificados. Construcao do indice e ordenacao fora da busca.
"""
import csv,sys,time,statistics,json,platform,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'componente/src'))
from carregador import carregar_modelo
from indice import indexar_por_chave,buscar_em_lista,buscar_no_indice
from busca import preparar_nomes,buscar_nome

def main():
 actual=carregar_modelo()['participante'];output=[];raw=[]
 for n in [len(actual),1000,5000,10000]:
  base=actual if n==len(actual) else [{'id_participante':f'SIM{i:06d}','nome':f'Pessoa sintetica {i:06d}'} for i in range(n)]
  t=time.perf_counter_ns();ix=indexar_por_chave(base,'id_participante');build=(time.perf_counter_ns()-t)/1e6
  nomes=preparar_nomes(base);codename={r['id_participante']:r['nome'] for r in base}
  targets=[base[int((n-1)*k/4)]['id_participante'] for k in range(5)]+['NAO_EXISTE']
  targets=(targets*17)[:100]
  for a in set(targets):assert buscar_em_lista(base,'id_participante',a)==buscar_no_indice(ix,a)
  for alg in ['sequencial','indice_hash','nome_binaria']:
   samples=[]
   for rep in range(34):
    t=time.perf_counter_ns()
    for target in targets:
     if alg=='sequencial':buscar_em_lista(base,'id_participante',target)
     elif alg=='indice_hash':buscar_no_indice(ix,target)
     else:buscar_nome(nomes,codename.get(target,'NAO EXISTE'))
    ms=(time.perf_counter_ns()-t)/1e6/len(targets)
    if rep>=3:samples.append(ms);raw.append(dict(volume=n,algoritmo=alg,lote=rep-2,ms_por_consulta=ms))
   output.append(dict(volume=n,fonte='base tratada' if n==len(actual) else 'escala sintetica sem dados pessoais',algoritmo=alg,media_ms=statistics.mean(samples),mediana_ms=statistics.median(samples),desvio_ms=statistics.pstdev(samples),minimo_ms=min(samples),maximo_ms=max(samples),construcao_indice_ms=build,lotes=31,consultas_por_lote=100))
 for name,rows in [('tempos.csv',output),('tempos_brutos.csv',raw)]:
  with (R/'evidencias'/name).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 env=dict(python=platform.python_version(),sistema=platform.platform(),maquina=platform.machine(),processador=platform.processor(),nucleos=os.cpu_count(),metodo='perf_counter_ns; 31x100; 3 aquecimentos; indice e ordenacao fora da busca; alvos identicos entre sequencial e hash; nome consulta o mesmo participante por chave nominal')
 (R/'evidencias/ambiente_medicao.json').write_text(json.dumps(env,indent=2))
 print(json.dumps(output,indent=2))
if __name__=='__main__':main()
