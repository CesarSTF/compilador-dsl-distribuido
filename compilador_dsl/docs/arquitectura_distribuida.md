# Arquitectura Distribuida y Tolerancia a Fallos

Este documento detalla la implementación del sistema distribuido del compilador, basado en la "Guía Nro. 012 - Replicación para Distribución de Carga".

## 1. Topología del Sistema

La arquitectura está basada en contenedores Docker y un balanceador de carga externo (Nginx).

```
                            ┌────────────────┐
                            │    Usuario     │
                            │ (Insomnia/Web) │
                            └───────┬────────┘
                                    │ HTTP (Puerto 80)
                                    ▼
                          ┌──────────────────┐
                          │ Balanceador      │
                          │ NGINX            │
                          │ (cesarServer)    │
                          └────┬────────┬────┘
                    Round Robin│        │
                ┌──────────────┘        └──────────────┐
                ▼                                      ▼
      ┌──────────────────┐                   ┌──────────────────┐
      │  Contenedor 1    │                   │  Contenedor 2    │
      │  dsl_nodo1       │                   │  dsl_nodo2       │
      │  IP: 192.168.1.10│                   │  IP: 192.168.1.11│
      │  NODE_ID=nodo-1  │                   │  NODE_ID=nodo-2  │
      └──────────────────┘                   └──────────────────┘
```

## 2. Configuración NGINX (El Orquestador de Round Robin)

El balanceo de carga se realiza de manera nativa mediante Nginx usando un bloque `upstream`. 

**Archivo: `/etc/nginx/conf.d/balanceador.conf`**
```nginx
upstream servers {
    server 192.168.1.10;
    server 192.168.1.11;
}

server {
    listen 80;
    server_name cesarServer;

    location / {
        proxy_pass http://servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
**Algoritmo:** Al no definir un método específico (como `ip_hash` o `least_conn`), Nginx emplea por defecto el algoritmo **Round Robin**.

## 3. Comprobación de Distribución de Carga

Para permitir la observabilidad y demostrar que el Round Robin está funcionando, se implementaron mecanismos en la API (Python):

### Endpoint de Estado (`/api/estado`)
Sirve como "ping" para el balanceador. Cada contenedor devuelve su propia variable de entorno `NODE_ID`.

### Identificación de Compilación
Las respuestas del endpoint `/api/compilar` devuelven el campo `nodo_procesador`. Esto ayuda a rastrear en qué nodo exacto se ejecutó el proceso léxico-semántico.

## 4. Pruebas de Carga (Stress Testing)

Para satisfacer la "Parte 5 y 6" de la guía (simulación de fallos y prueba de carga), se provee el script asíncrono `test_carga.py`.

**Comando de ejecución:**
```bash
make test
```

**Comportamiento del script:**
El script lanza **100 peticiones GET concurrentes** hacia `http://cesarServer/api/estado`.

**Salida Esperada:**
```text
========================================
RESULTADOS DE LA PRUEBA DE CARGA
========================================
Peticiones totales: 100
Tiempo total: 0.15 segundos
Tiempo promedio por petición: 1.50 ms
----------------------------------------
Distribución de carga por nodo (Round Robin):
 - nodo-1: 50 peticiones (50.0%)
 - nodo-2: 50 peticiones (50.0%)
========================================
```
La distribución `50/50` demuestra el correcto funcionamiento del algoritmo Round Robin. Si se diera de baja temporalmente al `nodo-1` (`docker stop dsl_nodo1`), Nginx enrutaría el 100% del tráfico al `nodo-2`, demostrando la **Tolerancia a Fallos** del sistema distribuido.
