# Ejemplos rápidos

## Consulta P-T con interpolación

```bash
python thermo.py lookup-pt --pressure 7 --temperature 202.5 --output outputs/pt_7bar
```

El comando consulta `P=7 bar` y `T=202.5 °C`. Como la tabla tiene valores a 200 °C y 205 °C, el motor interpola `h` y `s` y crea diagramas SVG.

## Interpolación también en presión

```bash
python thermo.py lookup-pt --pressure 7.25 --temperature 202.5 --output outputs/pt_bilineal
```

En este caso el motor interpola primero a la temperatura requerida en las presiones vecinas y luego interpola en presión.

## Rankine ideal

```bash
python thermo.py rankine \
  --boiler-bar 80 \
  --condenser-bar 0.1 \
  --turbine-inlet-c 480 \
  --output outputs/rankine_demo
```

Se generan:

- `solution.txt`: salida simple y rápida;
- `solution.md`: salida Markdown con tablas y figuras;
- `solution.json`: datos estructurados;
- `figures/*.svg`: esquemas de las interpolaciones que hayan sido necesarias.

## Resolver desde JSON

```bash
python thermo.py solve-json --input examples/rankine_ideal.json --output outputs/rankine_json
```

Este comando permite conectar más adelante un parser de lenguaje natural o una capa de IA.
