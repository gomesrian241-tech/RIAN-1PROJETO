"""Busca binaria exige lista ordenada; preparacao ocorre uma vez, fora da busca."""
from carregador import chave_texto

def busca_linear(lista,alvo):
    for i,x in enumerate(lista):
        if x==alvo:return i
    return -1

def busca_binaria(lista_ordenada,alvo):
    lo,hi=0,len(lista_ordenada)
    while lo<hi:
        mid=(lo+hi)//2
        if lista_ordenada[mid]<alvo:lo=mid+1
        else:hi=mid
    return lo if lo<len(lista_ordenada) and lista_ordenada[lo]==alvo else -1

def ordenacao_por_selecao(lista):
    a=list(lista)
    for i in range(len(a)):
        j=min(range(i,len(a)),key=a.__getitem__)
        a[i],a[j]=a[j],a[i]
    return a

def ordenacao_por_insercao(lista):
    a=list(lista)
    for i in range(1,len(a)):
        value=a[i];j=i-1
        while j>=0 and a[j]>value:a[j+1]=a[j];j-=1
        a[j+1]=value
    return a

def preparar_nomes(registros):
    return sorted((chave_texto(r['nome']),r['id_participante']) for r in registros)

def buscar_nome(nomes_ordenados,nome):
    alvo=chave_texto(nome);lo,hi=0,len(nomes_ordenados)
    while lo<hi:
        mid=(lo+hi)//2
        if nomes_ordenados[mid][0]<alvo:lo=mid+1
        else:hi=mid
    found=[]
    while lo<len(nomes_ordenados) and nomes_ordenados[lo][0]==alvo:
        found.append(nomes_ordenados[lo][1]);lo+=1
    return found
