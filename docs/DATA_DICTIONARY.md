# Diccionario de datos

## `saturated_water`

Una fila representa un estado de saturación recuperado de la fuente indicada.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER | Identificador único. |
| `source_file` | TEXT | Archivo fuente del registro. |
| `pdf_page` | INTEGER | Página de procedencia. |
| `source_row` | INTEGER | Número de fila dentro de la página fuente. |
| `T_C` | TEXT | Temperatura en grados Celsius. |
| `P_bar` | TEXT | Presión en bar. |
| `h_f`, `h_fg`, `h_g` | TEXT | Entalpías de líquido, vaporización y vapor, en kJ/kg. |
| `s_f`, `s_fg`, `s_g` | TEXT | Entropías de líquido, vaporización y vapor, en kJ/(kg·K). |
| `status` | TEXT | Estado de recuperación o inferencia. |
| `notes` | TEXT | Notas de procedencia y revisión. |
| `original_json` | TEXT/JSON | Valores originales adicionales, incluidas densidades y volúmenes específicos. |

## `superheated_compressed`

Una fila representa un estado a presión constante de agua comprimida o vapor
sobrecalentado. Algunas filas identificadas en `notes` representan los límites
de líquido y vapor saturados.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER | Identificador único. |
| `source_pdf` | TEXT | Documento fuente. |
| `pdf_page` | INTEGER | Página de procedencia. |
| `physical_page` | TEXT | Sector físico de la tabla original. |
| `P_bar` | TEXT | Presión en bar. |
| `T_C` | TEXT | Temperatura en grados Celsius. |
| `h_kJkg` | TEXT | Entalpía específica en kJ/kg. |
| `s_kJkgK` | TEXT | Entropía específica en kJ/(kg·K). |
| `estimated_h` | INTEGER | Indicador heredado de estimación de entalpía. |
| `estimated_s` | INTEGER | Indicador heredado de estimación de entropía. |
| `notes` | TEXT | Notas de OCR, saturación y procedencia. |

## `inference_audit`

Registro reproducible de todas las celdas completadas o corregidas.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER | Identificador de la operación. |
| `source_table` | TEXT | Tabla modificada. |
| `source_row_id` | INTEGER | Identificador de la fila modificada. |
| `column_name` | TEXT | Columna afectada. |
| `original_value` | TEXT | Valor anterior; puede ser nulo. |
| `inferred_value` | TEXT | Valor utilizado. |
| `method` | TEXT | Método de inferencia o corrección. |
| `detail` | TEXT | Anclas, fase, temperatura u otra información de auditoría. |

## Unidades principales

- Presión: bar.
- Temperatura: °C.
- Entalpía específica: kJ/kg.
- Entropía específica: kJ/(kg·K).
- Densidad: kg/m³, dentro de `original_json`.
- Volumen específico: según el factor impreso indicado en la fuente y conservado
  dentro de `original_json`.
