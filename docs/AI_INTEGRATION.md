# Integración futura con una capa de IA

El cálculo termodinámico debe permanecer en el motor determinista de Python. Una IA puede usarse para transformar un enunciado en datos estructurados y para redactar la explicación, pero no debe inventar propiedades de agua o vapor.

## Contrato mínimo de entrada

Para el solver Rankine ideal actual:

```json
{
  "cycle": "rankine_ideal",
  "boiler_pressure_bar": 80.0,
  "condenser_pressure_bar": 0.1,
  "turbine_inlet_temperature_C": 480.0
}
```

## Flujo propuesto

```text
Enunciado del usuario
        ↓
Parser IA / reglas
        ↓
JSON validado
        ↓
Motor termodinámico
        ↓
Resultados + procedencia + interpolaciones
        ↓
Explicación breve para el usuario
```

La capa de IA debe conservar las unidades del problema y convertirlas explícitamente antes de llamar al motor. El núcleo del repositorio utiliza bar, °C, kJ/kg y kJ/(kg·K).

## Próximas extensiones

- Rankine real con eficiencia isentrópica de turbina y bomba.
- Recalentamiento.
- Regeneración con calentadores abiertos/cerrados.
- Extracciones de turbina.
- Ciclos combinados y balances de planta.
- Parser de enunciados en lenguaje natural.
