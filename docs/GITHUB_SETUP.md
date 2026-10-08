# Subir el proyecto a GitHub

El ZIP entregado está listo para convertirse en un repositorio Git.

## Repositorio nuevo

Desde la carpeta raíz del proyecto:

```bash
git init
git add .
git commit -m "Initial thermodynamic solver"
git branch -M main
git remote add origin https://github.com/USUARIO/NOMBRE-REPO.git
git push -u origin main
```

Si el repositorio remoto ya existe y contiene archivos, sincronice primero antes de forzar cualquier cambio.

## Verificación previa

```bash
python scripts/validate_database.py
python -m unittest discover -s tests -v
python thermo.py rankine --boiler-bar 80 --condenser-bar 0.1 --turbine-inlet-c 480
```

## GitHub Actions

El archivo `.github/workflows/ci.yml` ejecuta automáticamente la validación SQLite y las pruebas con Python 3.11 y 3.12.

## Recomendación

No confirme carpetas `outputs/`, `exports/`, entornos virtuales ni archivos temporales de SQLite; ya están excluidos mediante `.gitignore`.
