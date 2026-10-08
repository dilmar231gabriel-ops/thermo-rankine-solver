# Base de datos termodinámica + solver Rankine

Repositorio académico para consultar propiedades de agua/vapor desde una base SQLite y resolver ejercicios de centrales térmicas de forma reproducible.

El objetivo del proyecto es que la resolución sea **corta, visible y trazable**: primero se arma la tabla de estados con los datos del problema, luego se consultan las tablas termodinámicas, después se analiza cada estado y, si falta un valor tabulado, se interpola mostrando una gráfica representativa.

> La base de datos sigue siendo la fuente termodinámica principal del repositorio: `data/thermodynamic_tables.sqlite`.

## Funciones actuales

- Agua saturada por presión.
- Agua comprimida y vapor sobrecalentado mediante pares `P-T`.
- Resolución inversa `P-s` para estados de salida de turbina.
- Interpolación lineal y bilineal.
- Diagramas SVG de interpolación, deliberadamente representativos y no necesariamente a escala.
- Ciclo Rankine ideal simple de cuatro estados.
- Tabla inicial, tabla con datos obtenidos de las tablas, análisis breve estado por estado y tabla final.
- Salidas TXT, Markdown y JSON.
- Validación de la base y pruebas automatizadas en GitHub Actions.

## Estructura

```text
base-datos-termodinamica/
├── .github/workflows/ci.yml
├── data/
│   └── thermodynamic_tables.sqlite
├── docs/
│   ├── AI_INTEGRATION.md
│   ├── DATA_DICTIONARY.md
│   ├── EXAMPLES.md
│   ├── GITHUB_SETUP.md
│   └── SOLVER_FLOW.md
├── examples/
│   └── rankine_ideal.json
├── scripts/
│   ├── export_csv.py
│   └── validate_database.py
├── src/thermo_solver/
│   ├── cli.py
│   ├── database.py
│   ├── interpolation.py
│   ├── models.py
│   ├── rankine.py
│   ├── report.py
│   └── state_table.py
├── tests/
├── thermo.py
├── pyproject.toml
├── CONTRIBUTING.md
├── CHANGELOG.md
└── README.md
```

## Requisitos

- Python 3.11 o superior.
- No se requieren dependencias externas para el núcleo.

## Inicio rápido

### 1. Validar la base

```bash
python scripts/validate_database.py
```

### 2. Consultar una propiedad con interpolación

```bash
python thermo.py lookup-pt \
  --pressure 7 \
  --temperature 202.5 \
  --output outputs/consulta
```

La carpeta de salida contiene `lookup.md`, `lookup.json` y las figuras SVG de cualquier interpolación realizada.

### 3. Resolver un Rankine ideal

```bash
python thermo.py rankine \
  --boiler-bar 80 \
  --condenser-bar 0.1 \
  --turbine-inlet-c 480 \
  --output outputs/rankine_demo
```

La salida sigue este orden:

1. tabla inicial con los datos del problema;
2. propiedades obtenidas directamente de las tablas;
3. análisis breve estado por estado;
4. interpolaciones necesarias, con fórmula y figura;
5. tabla final;
6. trabajo de turbina, trabajo de bomba, calor de entrada, calor rechazado, trabajo neto y rendimiento térmico.

## Entrada estructurada para una futura IA

El motor también puede recibir el JSON de `examples/rankine_ideal.json`:

```bash
python thermo.py solve-json \
  --input examples/rankine_ideal.json \
  --output outputs/rankine_desde_json
```

Este es el punto de integración previsto para que una futura capa de IA convierta el enunciado a datos estructurados sin encargarse del cálculo numérico.

## Instalación opcional como paquete

```bash
python -m pip install -e .
thermo-solver --help
```

También puede usarse sin instalar nada mediante `python thermo.py ...`.

## Base de datos

| Tabla | Filas | Descripción |
|---|---:|---|
| `saturated_water` | 793 | Propiedades del agua saturada por presión y temperatura. |
| `superheated_compressed` | 22 122 | Agua comprimida y vapor sobrecalentado a presión constante. |
| `inference_audit` | 1 841 | Historial de valores completados o corregidos. |
| `metadata` | variable | Metadatos de procedencia. |

La base contiene operaciones de completado y correcciones auditadas. Consulte `docs/DATA_DICTIONARY.md` para el detalle de columnas y procedencia.

## Filosofía de cálculo

La futura capa de IA puede interpretar el enunciado y convertirlo a datos estructurados, pero el cálculo numérico debe permanecer en el motor determinista. De esta manera una IA no inventa valores de tablas: cada propiedad procede de la base, de una interpolación registrada o de una ecuación termodinámica explícita.

Consulte `docs/AI_INTEGRATION.md` para el contrato propuesto entre lenguaje natural y solver y `docs/GITHUB_SETUP.md` para publicarlo en GitHub.

## Validación y pruebas

```bash
python scripts/validate_database.py
python -m unittest discover -s tests -v
```

GitHub Actions ejecutará ambos pasos automáticamente en cada `push` y `pull_request`.

## Consideración técnica

Los datos de la base provienen de la digitalización y revisión descritas en el diccionario y la auditoría. Para diseño, seguridad, certificación o decisiones industriales, contraste los resultados con una fuente termodinámica oficial independiente.
