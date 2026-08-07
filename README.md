# Rdev System V1.0

## Clonar el proyecto

```bash
git clone https://github.com/Rannie2005/Rdev_system_V1.0.git
cd Rdev_system_V1.0
```

## Crear el entorno virtual

```bash
python -m venv .venv
```

## Activarlo

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Aplicar migraciones

```bash
python manage.py migrate
```
LUEGO EJECUTA, py manage.py createsuperuser  , esto es para crear el usuario con el que podras entar

## Ejecutar el servidor

```bash
python manage.py runserver
```

Abrir:

```
http://127.0.0.1:8000/
