import sys,datetime as dt,json
from pathlib import Path
import pytest
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'componente/src'))
from carregador import normalizar_data,presenca_oficial,carregar_modelo
from estruturas import *
from indice import *
from busca import preparar_nomes,buscar_nome
from sessao import iniciar,lancar,desfazer,refazer,entrar_fila
from consultas import pn01,pn02,pn03,pn05

@pytest.fixture
def dados():
 return {'participante':[{'id_participante':'P1','nome':'Ana','situacao':'ativo','data_desligamento':None},{'id_participante':'P2','nome':'Ana','situacao':'desligado','data_desligamento':'2025-07-02'}],'oficina':[{'id_oficina':'OF1','nome':'Oficina'}],'colaborador':[{'id_colaborador':'C1','nome':'Educador'}],'frequencia':[],'encontro':[{'id_oficina':'OF1','data_encontro':'2025-07-0'+str(i)} for i in range(1,5)],'encaminhamento':[],'orgao':[],'lacuna_frequencia':[],'familia':[]}

@pytest.mark.parametrize('v',[None,'','-','?','ausente'])
def test_oficial_nao_aceita_indefinido(v):
 with pytest.raises(ValueError):presenca_oficial(v)

def test_oficial_nome_exato():assert presenca_oficial('J')=='falta justificada'
@pytest.mark.parametrize('v',['3 de mar de 2025','03/03/25','2025-03-03'])
def test_datas_variantes(v):assert normalizar_data(v)==dt.date(2025,3,3)
@pytest.mark.parametrize('v',['31/02/2025','02/30/25','recado',''])
def test_data_invalida(v):
 with pytest.raises((ValueError,KeyError)):normalizar_data(v)

def test_ano_50_e_1950():assert normalizar_data('08/01/50').year==1950

def test_pilha_lifo():
 p=criar_pilha();empilhar(p,1);empilhar(p,2);assert desempilhar(p)==2;assert desempilhar(p)==1
 with pytest.raises(IndexError):desempilhar(p)

def test_fila_prioridade_e_estabilidade():
 f=criar_fila()
 for c,p in [('A','comum'),('B','gestante'),('C','idoso'),('D','pcd'),('E','comum')]:enfileirar(f,c,p)
 assert [desenfileirar(f)['codigo'] for _ in range(5)]==['B','C','D','A','E']
 with pytest.raises(IndexError):desenfileirar(f)

def test_fila_repetido_e_prioridade_invalida():
 f=criar_fila();enfileirar(f,'A')
 with pytest.raises(ValueError):enfileirar(f,'A')
 with pytest.raises(ValueError):enfileirar(f,'B','vip')

def test_indice_colisoes_e_sem_chave():
 rs=[{'id':'A','v':1},{'id':'A','v':2}];ix=indexar_por_chave(rs,'id')
 assert buscar_no_indice(ix,'A')==rs;assert buscar_no_indice(ix,'Z')==[]
 with pytest.raises(ValueError):indexar_por_chave([{}],'id')
 got=buscar_no_indice(ix,'A');got[0]['v']=9;assert buscar_no_indice(ix,'A')[0]['v']==1

def test_indice_nao_varre_registros():
 # O indice precisa continuar consultavel depois de remover a fonte original.
 rs=[{'id':'P1','nome':'Cadastro'}];ix=indexar_por_chave(rs,'id');rs.clear()
 assert buscar_no_indice(ix,'P1')==[{'id':'P1','nome':'Cadastro'}]

def test_nome_homonimos_e_normalizacao(dados):
 nomes=preparar_nomes(dados['participante']);assert buscar_nome(nomes,'  ána ')==['P1','P2'];assert buscar_nome(nomes,'Nao existe')==[]

def test_desfazer_refazer_e_invalida_redo(dados):
 s=iniciar(dados);lancar(s,'P1','OF1','2025-07-01','presente','C1');desfazer(s);assert not s['frequencias'];refazer(s);assert len(s['frequencias'])==1
 desfazer(s);lancar(s,'P1','OF1','2025-07-03','falta','C1')
 with pytest.raises(IndexError):refazer(s)

def test_nao_desfaz_legado(dados):
 dados['frequencia']=[dict(id_participante='P1',id_oficina='OF1',data_encontro='2025-07-01',presenca='presente',origem='legado')]
 s=iniciar(dados)
 with pytest.raises(IndexError):desfazer(s)
 assert len(s['frequencias'])==1

@pytest.mark.parametrize('args',[
 ('XX','OF1','2025-07-01','presente','C1'),('P1','XX','2025-07-01','presente','C1'),('P1','OF1','2025-07-01','P','C1'),('P1','OF1','2025-07-01','presente','XX'),('P2','OF1','2025-07-02','presente','C1')])
def test_lancamentos_invalidos_atomicos(dados,args):
 s=iniciar(dados)
 with pytest.raises(ValueError):lancar(s,*args)
 assert not s['frequencias'] and not s['desfazer']

def test_duplicata_nao_altera_pilha(dados):
 s=iniciar(dados);lancar(s,'P1','OF1','2025-07-01','presente','C1')
 with pytest.raises(ValueError):lancar(s,'P1','OF1','2025-07-01','falta','C1')
 assert len(s['desfazer'])==1

def test_rn04_antes_data_aceita_sem_data_recusa(dados):
 s=iniciar(dados);lancar(s,'P2','OF1','2025-07-01','presente','C1')
 s['participantes']['P2']['data_desligamento']=None
 with pytest.raises(ValueError):lancar(s,'P2','OF1','2025-07-03','presente','C1')

def test_timestamp_com_fuso(dados):
 s=iniciar(dados)
 with pytest.raises(ValueError):lancar(s,'P1','OF1','2025-07-01','presente','C1',agora=dt.datetime(2025,7,1))
 assert not s['frequencias']
 r=lancar(s,'P1','OF1','2025-07-01','presente','C1',agora=dt.datetime(2025,7,1,tzinfo=dt.timezone.utc));assert r['registrado_em'].endswith('+00:00')

def test_refazer_revalida_regra(dados):
 s=iniciar(dados);lancar(s,'P1','OF1','2025-07-01','presente','C1');desfazer(s);s['participantes']['P1']['situacao']='desligado'
 with pytest.raises(ValueError):refazer(s)
 assert len(s['refazer'])==1 and not s['frequencias']

def test_fila_so_cadastrado(dados):
 s=iniciar(dados)
 with pytest.raises(ValueError):entrar_fila(s,'P999','comum')

def fr(day,status='falta',p='P1'):return dict(id_participante=p,id_oficina='OF1',data_encontro='2025-07-0'+str(day),presenca=status,id_registrador='C1',registrado_em=None,origem='legado')

def test_pn01_distintos_e_limites(dados):
 dados['frequencia']=[fr(1,'presente'),fr(2,'presente'),dict(fr(1,'presente',p='P2'),data_encontro='2025-10-01'),fr(3,'falta justificada')]
 assert pn01(dados)==1

def test_pn02_inclui_justificadas_e_zero(dados):
 assert pn02(dados)[0]['taxa_percentual'] is None
 dados['frequencia']=[fr(1,'presente'),fr(2,'falta'),fr(3,'falta justificada')]
 assert pn02(dados)[0]['taxa_percentual']=='33.33'

def test_pn03_nao_confunde_tres_registros_com_tres_encontros(dados):
 dados['frequencia']=[fr(1),fr(3),fr(4)];assert pn03(dados)==[]
 dados['frequencia']=[fr(1),fr(2),fr(3),fr(4)];assert pn03(dados)[0]['encontros_consecutivos']==4
 dados['lacuna_frequencia']=[{'id_oficina':'OF1','inicio':'2025-07-02','fim':'2025-07-02'}];assert pn03(dados)==[]

def test_pn05_une_encaminhamento_e_frequencia(dados):
 dados['frequencia']=[fr(2,'presente')];dados['orgao']=[{'id_orgao':'O1','nome':'Municipio'}];dados['encaminhamento']=[dict(id_participante='P1',data_encaminhamento='2025-07-01',id_encaminhamento='E1',servico='CRAS',id_orgao='O1',situacao=None)]
 assert [r['tipo'] for r in pn05(dados,'P1')]==['encaminhamento','frequencia'];assert pn05(dados,'inexistente')==[]

def test_csv_igual_modelo_etl():
 d=carregar_modelo();original=json.loads((R/'evidencias/dados_modelo.json').read_text());assert d==original

def test_carga_balanco_sem_descartes_ocultos():
 c=json.loads((R/'evidencias/carga.json').read_text());assert c['total_lidas']==c['total_aceitas']+c['total_rejeitadas'];assert sum(c['rejeicoes_por_regra'].values())==c['total_rejeitadas']
