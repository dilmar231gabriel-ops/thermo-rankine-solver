# Flujo de resolución

El solver sigue una metodología breve y visible, pensada para ejercicios de centrales térmicas.

1. **Leer los datos del problema.** Se crea una tabla inicial de estados únicamente con lo conocido.
2. **Consultar las tablas termodinámicas.** Se completan las propiedades que pueden obtenerse directamente de la base SQLite.
3. **Analizar estado por estado.** Cada estado recibe una explicación corta: qué se conoce, qué relación se usa y qué propiedad se obtiene.
4. **Interpolar cuando haga falta.** Si el valor exacto no existe, se toman los dos valores vecinos, se aplica interpolación lineal y se genera un esquema gráfico representativo en SVG. El esquema no pretende estar a escala.
5. **Completar la tabla final.** Cuando ya se conocen las propiedades necesarias, se calculan trabajos, calores y rendimiento del ciclo.

## Regla de trazabilidad

El motor no debe inventar propiedades. Los valores deben proceder de:

- un dato explícito del problema;
- una fila exacta de la base;
- una interpolación registrada;
- una relación termodinámica declarada.

## Orden de salida recomendado

```text
1. Tabla inicial
2. Datos directos de tablas
3. Estado 1
4. Estado 2
5. Estado 3
6. Estado 4
7. Tabla final
8. Trabajo, calor y rendimiento
```

Las explicaciones deben ser breves. La parte gráfica se reserva para interpolaciones o extrapolaciones autorizadas.
