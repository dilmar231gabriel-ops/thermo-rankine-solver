# Contribuir

1. Cree una rama para el cambio.
2. No modifique `data/thermodynamic_tables.sqlite` sin documentar el origen y actualizar la auditoría.
3. Ejecute antes de enviar cambios:

```bash
python scripts/validate_database.py
python -m unittest discover -s tests -v
```

4. Si añade un nuevo ciclo, incluya al menos una prueba de humo y un ejemplo de uso.
5. Mantenga las unidades internas del núcleo: bar, °C, kJ/kg y kJ/(kg·K).
