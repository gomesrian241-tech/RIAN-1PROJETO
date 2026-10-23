"""CLI do SIRCA; execute python componente/src/main.py. Nao usa o banco."""
import argparse,json
from pathlib import Path
from carregador import carregar_modelo,RAIZ
from indice import indexar_por_chave,buscar_no_indice
from busca import preparar_nomes,buscar_nome
from sessao import iniciar,lancar,desfazer,refazer,entrar_fila
from estruturas import desenfileirar,listar_fila
from consultas import pn01,pn02,pn03,pn04,pn05

def mostrar(obj):print(json.dumps(obj,ensure_ascii=False,indent=2,default=str))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resumo',action='store_true');args=ap.parse_args()
    dados=carregar_modelo();s=iniciar(dados);ix=indexar_por_chave(dados['participante'],'id_participante');nomes=preparar_nomes(dados['participante'])
    if args.resumo:mostrar({k:len(v) for k,v in dados.items()});return
    while True:
        print('\nSIRCA - Equipe E - Ciclo 2')
        print('1 Listar | 2 Codigo | 3 Nome exato | 4 Historico | 5 Presenca')
        print('6 Desfazer | 7 Refazer | 8 Entrar na fila | 9 Proximo atendimento')
        print('10 Consultas trimestrais | 11 Exportar sessao | 12 Ver fila | 0 Sair')
        try:
            opc=input('Opcao: ').strip()
            if opc=='0':return
            if opc=='1':mostrar([{'codigo':r['id_participante'],'nome':r['nome']} for r in dados['participante']])
            elif opc=='2':mostrar(buscar_no_indice(ix,input('Codigo: ').strip().upper()))
            elif opc=='3':mostrar(buscar_nome(nomes,input('Nome completo: ')))
            elif opc=='4':
                atual=dict(dados,frequencia=list(s['frequencias'].values()));mostrar(pn05(atual,input('Codigo: ').strip().upper()))
            elif opc=='5':
                p=input('Participante: ').strip().upper();o=input('Oficina: ').strip().upper();d=input('Data AAAA-MM-DD: ').strip();marca=input('presente / falta / falta justificada: ').strip();resp=input('ID do responsavel (consulte colaborador.csv): ').strip().upper();mostrar(lancar(s,p,o,d,marca,resp))
            elif opc=='6':mostrar(desfazer(s))
            elif opc=='7':mostrar(refazer(s))
            elif opc=='8':entrar_fila(s,input('Codigo: ').strip().upper(),input('comum / idoso / gestante / pcd: ').strip());mostrar(listar_fila(s['fila']))
            elif opc=='9':mostrar(desenfileirar(s['fila']))
            elif opc=='10':
                atual=dict(dados,frequencia=list(s['frequencias'].values()));mostrar({'periodo':'2025-07-01 a 2025-09-30','criterio':'RN-05: >=1 presente; ID distinto','PN-01':pn01(atual),'PN-02':pn02(atual),'PN-03':pn03(atual),'PN-04':pn04(atual)})
            elif opc=='11':
                # Um nome novo evita sobrescrever resultados ou os arquivos brutos.
                from datetime import datetime,timezone
                dest=Path(RAIZ)/'dados'/('sessao-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
                with dest.open('x',encoding='utf-8') as f:json.dump([r for r in s['frequencias'].values() if r['origem']=='sessao'],f,ensure_ascii=False,indent=2)
                print('Sessao exportada:',dest)
            elif opc=='12':mostrar(listar_fila(s['fila']))
            else:print('Opcao invalida')
        except (ValueError,IndexError) as e:print('Operacao recusada:',str(e))
        except (EOFError,KeyboardInterrupt):print('\nSessao encerrada. Use a opcao 11 para exportar antes de sair.');return
if __name__=='__main__':main()
