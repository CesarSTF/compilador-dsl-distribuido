import asyncio
import aiohttp
import time
import json
from collections import Counter

URL_BALANCEADOR = "http://cesarServer/api/estado"
URL_COMPILAR = "http://cesarServer/api/compilar"
NUM_REQUESTS = 100

async def fetch_estado(session):
    start = time.time()
    try:
        async with session.get(URL_BALANCEADOR) as response:
            data = await response.json()
            elapsed = time.time() - start
            return data.get("nodo_procesador", "Desconocido"), elapsed
    except Exception as e:
        return f"Error: {str(e)}", time.time() - start

async def main():
    print(f"Iniciando prueba de carga con {NUM_REQUESTS} peticiones al endpoint de estado...")
    start_total = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_estado(session) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_total
    
    # Analizar resultados
    nodos = Counter([res[0] for res in results])
    tiempos = [res[1] for res in results]
    avg_time = sum(tiempos) / len(tiempos)
    
    print("\n" + "="*40)
    print("RESULTADOS DE LA PRUEBA DE CARGA")
    print("="*40)
    print(f"Peticiones totales: {NUM_REQUESTS}")
    print(f"Tiempo total: {total_time:.2f} segundos")
    print(f"Tiempo promedio por petición: {avg_time*1000:.2f} ms")
    print("-" * 40)
    print("Distribución de carga por nodo (Round Robin):")
    for nodo, count in nodos.items():
        porcentaje = (count / NUM_REQUESTS) * 100
        print(f" - {nodo}: {count} peticiones ({porcentaje:.1f}%)")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
