package com.compiler.semantic;

import static spark.Spark.*;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;

public class SemanticServer {
    public static void main(String[] args) {
        port(8080);
        Gson gson = new Gson();

        post("/api/evaluate", (request, response) -> {
            response.type("application/json");
            try {
                JsonObject ast = gson.fromJson(request.body(), JsonObject.class);
                
                // Parse AST
                double valor = 0;
                String origen = "";
                String destino = "";

                JsonArray hijos = ast.getAsJsonArray("hijos");
                for (JsonElement elemento : hijos) {
                    JsonObject nodo = elemento.getAsJsonObject();
                    String tipo = nodo.get("nodo").getAsString();
                    if (tipo.equals("VALOR")) valor = nodo.get("valor").getAsDouble();
                    if (tipo.equals("ORIGEN")) origen = nodo.get("unidad").getAsString();
                    if (tipo.equals("DESTINO")) destino = nodo.get("unidad").getAsString();
                }

                // Regla 1: Identidad
                if (origen.equals(destino)) {
                    response.status(400);
                    return "{\"status\": \"error_semantico\", \"mensaje\": \"No tiene sentido convertir una unidad a sí misma.\"}";
                }

                // Regla 2: Cero Absoluto
                if (origen.equals("UNIDAD_ORIGEN_C") && valor < -273.15) {
                    response.status(400);
                    return "{\"status\": \"error_semantico\", \"mensaje\": \"La temperatura " + valor + " °C es inferior al cero absoluto (-273.15 °C).\"}";
                }

                if (origen.equals("UNIDAD_DESTINO_F") && valor < -459.67) {
                    response.status(400);
                    return "{\"status\": \"error_semantico\", \"mensaje\": \"La temperatura " + valor + " °F es inferior al cero absoluto (-459.67 °F).\"}";
                }

                double resultado = 0;
                String simboloOrigen = origen.equals("UNIDAD_ORIGEN_C") ? "°C" : "°F";
                String simboloDestino = destino.equals("UNIDAD_DESTINO_F") ? "°F" : "°C";

                if (origen.equals("UNIDAD_ORIGEN_C") && destino.equals("UNIDAD_DESTINO_F")) {
                    resultado = (valor * 9.0 / 5.0) + 32;
                } else if (origen.equals("UNIDAD_DESTINO_F") && destino.equals("UNIDAD_ORIGEN_C")) {
                    resultado = (valor - 32) * 5.0 / 9.0;
                }
                
                // Redondear a 2 decimales
                resultado = Math.round(resultado * 100.0) / 100.0;

                JsonObject res = new JsonObject();
                res.addProperty("status", "success");
                res.addProperty("resultado_valor", resultado);
                res.addProperty("resultado_texto", valor + " " + simboloOrigen + " = " + resultado + " " + simboloDestino);
                res.addProperty("mensaje_semantico", "Evaluado correctamente por Microservicio Java");
                
                return res.toString();

            } catch (Exception e) {
                response.status(500);
                return "{\"status\": \"error_interno\", \"mensaje\": \"JSON inválido o malformado.\"}";
            }
        });
        
        System.out.println("Semantic Analyzer running on port 8080 (SparkJava)");
    }
}
