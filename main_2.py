with open('entrada.txt', 'r') as f:
    linhas = [linha.strip() for linha in f if linha.strip()]


numero_de_voos = int(linhas[0])
numero_de_pistas = int(linhas[1])


r = list(map(int, linhas[2].split()))
c = list(map(int, linhas[3].split()))
p = list(map(int, linhas[4].split()))

# matriz t
t = []
for i in range(5, 5 + numero_de_voos):
    t.append(list(map(int, linhas[i].split())))


# Representação de um voo
class Voo:
    def __init__(self, id_voo, r, c, p):
        self.id = id_voo
        self.r = r  # horário de chegada
        self.c = c  # tempo necessário pra decolar/pousar
        self.p = p  # penalidade por minuto de espera
        self.horario_atribuido = None  # será preenchido na solução
        self.pista_atribuida = None    # idem

# Representação de uma pista
class Pista:
    def __init__(self, id_pista):
        self.id = id_pista
        self.ocupada_em = set()  # horários em que essa pista já está ocupada

# Função que inicializa as estruturas
def inicializar_instancia(numero_de_voos, numero_de_pistas, r, c, p, t):
    voos = [Voo(i, r[i], c[i], p[i]) for i in range(numero_de_voos)]
    pistas = [Pista(i) for i in range(numero_de_pistas)]
    matriz_tempo = t  # matriz t[i][j] = tempo de separação entre voo i e j na mesma pista
    return voos, pistas, matriz_tempo


def printar_instancia(voos, pistas, matriz_tempo):
    print("📦 VOOS:")
    for voo in voos:
        print(
            f"Voo {voo.id}: r = {voo.r}, c = {voo.c}, p = {voo.p}, "
            f"horário atribuído = {voo.horario_atribuido}, pista = {voo.pista_atribuida}"
        )

    print("\n🛬 PISTAS:")
    for pista in pistas:
        print(f"Pista {pista.id}, horários ocupados: {sorted(pista.ocupada_em)}")

    print("\n⏱ MATRIZ DE SEPARAÇÃO (t):")
    for i, linha in enumerate(matriz_tempo):
        print(f"Voo {i}: {linha}")

# GULOSO ========================================================================================================================
def heuristica_gulosa(voos, pistas, matriz_tempo):
    custo_total = 0

    # Ordena os voos pelo tempo de liberação
    voos_ordenados = sorted(voos, key=lambda v: v.r)

    for voo in voos_ordenados:
        melhor_inicio = float('inf')
        melhor_pista = None

        for pista in pistas:
            
            # Tenta alocar o voo no tempo mais cedo possível respeitando separação
            tempo_minimo = voo.r

            for outro_voo in voos:
                 
                
                if outro_voo.pista_atribuida == pista.id and outro_voo.horario_atribuido is not None:
                    tempo_final = outro_voo.horario_atribuido + outro_voo.c
                    separacao = matriz_tempo[outro_voo.id][voo.id]
                    tempo_minimo = max(tempo_minimo, tempo_final + separacao)

            # Verifica se essa pista é melhor que a anterior
            if tempo_minimo < melhor_inicio:
                melhor_inicio = tempo_minimo
                melhor_pista = pista

        # Atribui voo à pista escolhida
        voo.horario_atribuido = melhor_inicio
        voo.pista_atribuida = melhor_pista.id

        # Marca os horários ocupados
        for t in range(voo.horario_atribuido, voo.horario_atribuido + voo.c):
            melhor_pista.ocupada_em.add(t)

        # Calcula custo de penalidade
        atraso = max(0, voo.horario_atribuido - voo.r)
        penalidade = atraso * voo.p
        custo_total += penalidade

    print(f"\n💸 Custo total de penalidade: {custo_total}")

# VIZINHANÇA ===============================================================================================================

## Funções Auxiliares:
def calcular_custo_total(voos):
    """Calcula o custo total da solução atual"""
    custo = 0
    for voo in voos:
        if voo.horario_atribuido is not None:
            atraso = max(0, voo.horario_atribuido - voo.r)
            custo += atraso * voo.p
    return custo

def recalcular_horarios(voos, pistas, matriz_tempo, pistas_afetadas):
    """
    Recalcula os horários para todas as pistas afetadas
    Retorna True se conseguiu uma alocação válida, False caso contrário
    """
    for pista_id in pistas_afetadas:
        # Pega todos os voos nesta pista, ordenados pelo horário atual
        voos_pista = [v for v in voos if v.pista_atribuida == pista_id]
        voos_pista.sort(key=lambda v: v.horario_atribuido if v.horario_atribuido is not None else float('inf'))
        
        # Limpa os horários da pista
        pistas[pista_id].ocupada_em = set()
        
        # Tenta realocar todos os voos na pista
        for i, voo in enumerate(voos_pista):
            tempo_minimo = voo.r
            
            # Verifica restrições com voos anteriores na mesma pista
            if i > 0:
                voo_anterior = voos_pista[i-1]
                tempo_final = voo_anterior.horario_atribuido + voo_anterior.c
                separacao = matriz_tempo[voo_anterior.id][voo.id]
                tempo_minimo = max(tempo_minimo, tempo_final + separacao)
                
            voo.horario_atribuido = tempo_minimo
            
            # Verifica se o voo não conflita com os próximos (para garantir consistência)
            if i < len(voos_pista) - 1:
                voo_proximo = voos_pista[i+1]
                if voo_proximo.horario_atribuido is not None:
                    tempo_final = voo.horario_atribuido + voo.c
                    separacao = matriz_tempo[voo.id][voo_proximo.id]
                    if tempo_final + separacao > voo_proximo.horario_atribuido:
                        return False
                        
            # Marca os horários ocupados
            for t in range(voo.horario_atribuido, voo.horario_atribuido + voo.c):
                pistas[pista_id].ocupada_em.add(t)
                
    return True

def recalcular_horarios_pista(voos_pista, pista, matriz_tempo):
    """
    Recalcula horários para uma única pista com uma nova ordem de voos
    Retorna True se conseguiu uma alocação válida, False caso contrário
    """
    # Limpa os horários da pista
    pista.ocupada_em = set()
    
    for i, voo in enumerate(voos_pista):
        tempo_minimo = voo.r
        
        # Verifica restrições com voos anteriores na mesma pista
        if i > 0:
            voo_anterior = voos_pista[i-1]
            tempo_final = voo_anterior.horario_atribuido + voo_anterior.c
            separacao = matriz_tempo[voo_anterior.id][voo.id]
            tempo_minimo = max(tempo_minimo, tempo_final + separacao)
            
        voo.horario_atribuido = tempo_minimo
        
        # Verifica consistência com próximos voos
        if i < len(voos_pista) - 1:
            voo_proximo = voos_pista[i+1]
            if voo_proximo.horario_atribuido is not None:
                tempo_final = voo.horario_atribuido + voo.c
                separacao = matriz_tempo[voo.id][voo_proximo.id]
                if tempo_final + separacao > voo_proximo.horario_atribuido:
                    return False
                    
        # Marca os horários ocupados
        for t in range(voo.horario_atribuido, voo.horario_atribuido + voo.c):
            pista.ocupada_em.add(t)
            
    return True
## Fim Funções auxiliares

## 1 Movimento Swap
def movimento_swap(voos, pistas, matriz_tempo):
    """
    Troca a alocação de dois voos entre si (podendo ser na mesma pista ou entre pistas diferentes)
    Retorna True se encontrou uma melhoria, False caso contrário
    """
    melhor_custo = calcular_custo_total(voos)
    melhorou = False
    
    for i in range(len(voos)):
        for j in range(i+1, len(voos)):
            voo1 = voos[i]
            voo2 = voos[j]
            
            # Faz backup dos valores atuais
            pista1_original = voo1.pista_atribuida
            pista2_original = voo2.pista_atribuida
            horario1_original = voo1.horario_atribuido
            horario2_original = voo2.horario_atribuido
            
            # Realiza a troca
            voo1.pista_atribuida, voo2.pista_atribuida = voo2.pista_atribuida, voo1.pista_atribuida
            voo1.horario_atribuido, voo2.horario_atribuido = voo2.horario_atribuido, voo1.horario_atribuido
            
            # Recalcula os horários para as pistas afetadas
            pistas_afetadas = list({pista1_original, pista2_original})
            if recalcular_horarios(voos, pistas, matriz_tempo, pistas_afetadas):
                novo_custo = calcular_custo_total(voos)
                if novo_custo < melhor_custo:
                    melhor_custo = novo_custo
                    print("SWAP: MELHOR CUSTOOOOO AQUI MIZERA:", melhor_custo)
                    melhorou = True
                    break  # Aceita a primeira melhoria encontrada
                else:
                    # Desfaz a troca se não melhorou
                    voo1.pista_atribuida, voo2.pista_atribuida = pista1_original, pista2_original
                    voo1.horario_atribuido, voo2.horario_atribuido = horario1_original, horario2_original
            else:
                # Desfaz a troca se não foi viável
                voo1.pista_atribuida, voo2.pista_atribuida = pista1_original, pista2_original
                voo1.horario_atribuido, voo2.horario_atribuido = horario1_original, horario2_original
                
        if melhorou:
            break
            
    return melhorou

## 2 Movimento Re Insertion
def movimento_reinsertion(voos, pistas, matriz_tempo):
    """
    Remove um voo de sua pista atual e o reinsere na mesma pista ou em outra
    Retorna True se encontrou uma melhoria, False caso contrário
    """
    melhor_custo = calcular_custo_total(voos)
    melhorou = False
    
    for voo in voos:
        pista_original = voo.pista_atribuida
        horario_original = voo.horario_atribuido
        
        # Remove temporariamente o voo de sua pista atual
        voo.pista_atribuida = None
        voo.horario_atribuido = None
        
        # Tenta reinserir o voo em todas as pistas possíveis
        for pista in pistas:
            # Encontra a melhor posição para inserir nesta pista
            voos_pista = [v for v in voos if v.pista_atribuida == pista.id and v.horario_atribuido is not None]
            voos_pista.sort(key=lambda v: v.horario_atribuido)
            
            # Tenta inserir em todas as posições possíveis na pista
            for pos in range(len(voos_pista) + 1):
                # Atribui temporariamente o voo à pista
                voo.pista_atribuida = pista.id
                
                # Recalcula todos os horários na pista
                if recalcular_horarios_pista(voos_pista + [voo], pista, matriz_tempo):
                    novo_custo = calcular_custo_total(voos)
                    if novo_custo < melhor_custo:
                        melhor_custo = novo_custo
                        print("REINSERTION: MELHOR CUSTOOOOO AQUI MIZERA:", melhor_custo)
                        melhorou = True
                        break  # Aceita a primeira melhoria encontrada
                    else:
                        # Remove o voo da pista se não melhorou
                        voo.pista_atribuida = None
                        voo.horario_atribuido = None
                else:
                    # Remove o voo da pista se não foi viável
                    voo.pista_atribuida = None
                    voo.horario_atribuido = None
                    
            if melhorou:
                break
                
        if not melhorou:
            # Se não encontrou melhoria, devolve o voo à posição original
            voo.pista_atribuida = pista_original
            voo.horario_atribuido = horario_original
        else:
            break
                
    return melhorou

## 3 Movimento OPT
def movimento_2opt(voos, pistas, matriz_tempo):
    """
    Seleciona dois pontos em uma pista e inverte a ordem dos voos entre eles
    Retorna True se encontrou uma melhoria, False caso contrário
    """
    melhor_custo = calcular_custo_total(voos)
    melhorou = False
    
    for pista in pistas:
        # Pega todos os voos nesta pista, ordenados pelo horário atual
        voos_pista = [v for v in voos if v.pista_atribuida == pista.id]
        voos_pista.sort(key=lambda v: v.horario_atribuido)
        
        # Tenta todas as combinações possíveis de inversão
        for i in range(len(voos_pista)):
            for j in range(i+1, len(voos_pista)):
                # Faz backup da ordem atual
                ordem_original = [v.id for v in voos_pista]
                horarios_originais = [v.horario_atribuido for v in voos_pista]
                
                # Inverte a ordem entre i e j
                voos_pista[i:j+1] = voos_pista[i:j+1][::-1]
                
                # Tenta recalcular os horários mantendo a nova ordem
                if recalcular_horarios_pista(voos_pista, pista, matriz_tempo):
                    novo_custo = calcular_custo_total(voos)
                    if novo_custo < melhor_custo:
                        melhor_custo = novo_custo
                        print("OPT: MELHOR CUSTOOOOO AQUI MIZERA:", melhor_custo)
                        melhorou = True
                        break  # Aceita a primeira melhoria encontrada
                    else:
                        # Desfaz a inversão
                        voos_pista[i:j+1] = voos_pista[i:j+1][::-1]
                        for idx, voo in enumerate(voos_pista):
                            voo.horario_atribuido = horarios_originais[idx]
                else:
                    # Desfaz a inversão se não foi viável
                    voos_pista[i:j+1] = voos_pista[i:j+1][::-1]
                    
            if melhorou:
                break
                
    return melhorou

def VND(voos, pistas, matriz_tempo):
    """
    Algoritmo VND que aplica os movimentos de vizinhança em ordem
    até não encontrar mais melhorias
    """
    melhor_custo = calcular_custo_total(voos)
    print(f"Custo inicial: {melhor_custo}")
    
    # Ordem dos movimentos de vizinhança (do menos para o mais disruptivo)
    movimentos = [
        movimento_swap,
        movimento_reinsertion,
        movimento_2opt
    ]
    
    k = 0
    while k < len(movimentos):
        movimento = movimentos[k]
        melhorou = movimento(voos, pistas, matriz_tempo)
        
        if melhorou:
            novo_custo = calcular_custo_total(voos)
            print(f"Movimento {k+1} melhorou para: {novo_custo}")
            melhor_custo = novo_custo
            k = 0  # Volta ao primeiro movimento
        else:
            k += 1  # Passa para o próximo movimento
            
    print(f"Melhor custo encontrado: {melhor_custo}")
    return melhor_custo



import time

# Gera solução inicial com heurística gulosa
voos, pistas, matriz_tempo = inicializar_instancia(numero_de_voos, numero_de_pistas, r, c, p, t)
heuristica_gulosa(voos, pistas, matriz_tempo)
print('\n\n ===============================MINHA PICA')

print('\n\n ===============================AIIIIIIIIIIIIIIIIIIINNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN VND AIINNNNNNNNNNNNNNNNN')
VND(voos, pistas, matriz_tempo)



custo_inicial = calcular_custo_total(voos)
print(f"\n💡 Custo inicial da solução gulosa: {custo_inicial}")
'''
# Executa VND
inicio = time.time()
solucao_final, custo_final = VND(voos, pistas, matriz_tempo)
fim = time.time()

print("\n🎯 RESULTADO FINAL APÓS VND")
print(f"🔸 Melhor custo encontrado: {custo_final}")
print(f"⏱ Tempo de execução: {fim - inicio:.4f} segundos")

# Se quiser mostrar a solução final detalhada:
print("\n📦 Atribuições finais dos voos:")
for voo in sorted(solucao_final, key=lambda v: v.horario_atribuido):
    atraso = max(0, voo.horario_atribuido - voo.r)
    custo = atraso * voo.p
    print(f"Voo {voo.id} → Pista {voo.pista_atribuida} | Início: {voo.horario_atribuido} | Duração: {voo.c} | Atraso: {atraso} | Penalidade: {custo}")
'''