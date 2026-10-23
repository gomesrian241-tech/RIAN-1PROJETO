"""Pilha e fila com funcoes e tipos nativos; sem classes proprias.
Prioritarios (idoso, gestante e pcd) compartilham uma fila FIFO; nao ha
hierarquia adicional entre esses grupos no edital. Normais usam outra FIFO.
"""
from collections import deque

def criar_pilha(): return []
def empilhar(pilha,item): pilha.append(item)
def desempilhar(pilha):
    if not pilha: raise IndexError('Pilha vazia')
    return pilha.pop()
def criar_fila(): return {'prioritaria':deque(),'comum':deque(),'presentes':set()}
def enfileirar(fila,codigo,prioridade='comum'):
    if prioridade not in {'comum','idoso','gestante','pcd'}:raise ValueError('Prioridade invalida')
    if codigo in fila['presentes']:raise ValueError('Participante ja esta na fila')
    grupo='comum' if prioridade=='comum' else 'prioritaria'
    fila[grupo].append({'codigo':codigo,'prioridade':prioridade});fila['presentes'].add(codigo)
def desenfileirar(fila):
    grupo='prioritaria' if fila['prioritaria'] else 'comum'
    if not fila[grupo]:raise IndexError('Fila vazia')
    item=fila[grupo].popleft();fila['presentes'].remove(item['codigo']);return item
def listar_fila(fila): return list(fila['prioritaria'])+list(fila['comum'])
