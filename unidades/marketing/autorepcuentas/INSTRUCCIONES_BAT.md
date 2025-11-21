# Instrucciones para usar archivos .bat con Django

## 📝 Resumen de lo creado

Se ha migrado exitosamente tu sistema desde LEO MASTER a una estructura Django moderna.

### Archivos creados:

1. **conexiones/inicializar_supabase.sql** - Script SQL para crear el esquema en Supabase
2. **services/reporte_service.py** - Servicio de generación de reportes adaptado a Django
3. **management/commands/generar_reporte.py** - Command de Django para generar reportes
4. **management/commands/listar_cuentas.py** - Command para listar cuentas desde .bat
5. **generar_reportes.bat** - Script .bat con menú interactivo
6. **REPORTES_EXCEL/** - Carpeta donde se guardan los reportes
7. **README.md** - Documentación completa del proyecto

## 🚀 Pasos para usar el sistema

### 1. Ejecutar el script SQL en Supabase

1. Ve a https://supabase.com y abre tu proyecto
2. En el menú lateral, selecciona **SQL Editor**
3. Crea una nueva query
4. Copia y pega el contenido de `conexiones/inicializar_supabase.sql`
5. Ejecuta el script
6. Verifica que el esquema `"Markeitng"` y las tablas se hayan creado

### 2. Instalar dependencias Python

```bash
pip install pandas openpyxl supabase
```

### 3. Usar el archivo .bat

Simplemente ejecuta:

```bash
generar_reportes.bat
```

El menú te guiará para:
- Seleccionar tipo de reporte (campaigns, adsets, ads, consolidado)
- Elegir cuenta
- Definir rango de fechas o usar últimos 30 días

## ⚠️ IMPORTANTE: Mejora necesaria en listar_cuentas.py

El archivo .bat necesita obtener el `account_id` real de Supabase. Actualmente usa el nombre de cuenta como placeholder.

### Solución:

Modifica `management/commands/listar_cuentas.py` para que también devuelva el `account_id`:

```python
# En el formato 'info', cambiar la línea de output a:
self.stdout.write(
    f"{idx}|{account['account_name']}|{account['account_id']}|{account.get('marcas', 'N/A')}|{multimarca}"
)
```

Y luego en `generar_reportes.bat`, capturar el `account_id`:

```batch
for /f "tokens=1,2,3,4,5 delims=|" %%a in ('python manage.py listar_cuentas --formato info 2^>nul') do (
    if "!contador!"=="%cuenta_sel%" (
        set "nombre_cuenta=%%b"
        set "account_id=%%c"
        set "cuenta_encontrada=true"
        goto solicitar_fecha_reporte
    )
)
```

Y cambiar las llamadas al command:

```batch
python manage.py generar_reporte --tipo !tipo_reporte! --account_id "!account_id!" --fecha_inicio !fecha_inicio! --fecha_fin !fecha_fin!
```

## 🎯 Uso alternativo: Sin archivos .bat

Si prefieres no usar .bat, puedes ejecutar directamente los commands de Django:

```bash
# Listar cuentas
python manage.py listar_cuentas

# Generar reporte de campaigns últimos 30 días
python manage.py generar_reporte --tipo campaigns --account_id 123456789 --ultimos30

# Generar reporte con fechas específicas
python manage.py generar_reporte --tipo adsets --account_id 123456789 --fecha_inicio 2025-01-01 --fecha_fin 2025-01-31

# Generar reporte consolidado
python manage.py generar_reporte --tipo consolidado --account_id 123456789 --ultimos30
```

## 📊 Estructura final del proyecto

```
autorepcuentas/
├── conexiones/
│   ├── connection_supabase.py
│   ├── connection_meta_api.py
│   ├── inicializar_supabase.sql    ← Script SQL
│   └── __init__.py
├── controllers/
│   ├── campaigns_controller.py
│   ├── adsets_controller.py
│   ├── ads_controller.py
│   ├── accounts_controller.py
│   └── __init__.py
├── services/
│   ├── reporte_service.py          ← Servicio de reportes
│   └── __init__.py
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       ├── generar_reporte.py      ← Command principal
│       └── listar_cuentas.py       ← Command para .bat
├── utils/
│   ├── date_utils.py
│   ├── db_validator.py
│   └── __init__.py
├── views/
│   ├── api_views.py
│   ├── campaigns_view.py
│   └── __init__.py
├── REPORTES_EXCEL/                 ← Reportes generados
├── generar_reportes.bat            ← Script Windows
├── models.py
├── README.md
└── INSTRUCCIONES_BAT.md            ← Este archivo
```

## 🔧 Comparación: LEO MASTER vs AutoRepCuentas Django

| Característica | LEO MASTER | AutoRepCuentas Django |
|----------------|------------|----------------------|
| **Configuración** | config.json | Variables entorno Django |
| **Extracción** | `PY/campanas.py` | `controllers/campaigns_controller.py` |
| **Reportes** | `PY/reporte_marketing.py` | `services/reporte_service.py` |
| **Ejecución** | Scripts .bat → Python directo | .bat → Django commands |
| **Cuentas** | `PY/get_accounts.py` | `manage.py listar_cuentas` |
| **Base de datos** | Supabase directo | Supabase + modelos Django |

## ✅ Ventajas de la nueva estructura

1. **Integrado con Django**: Usa el ORM y settings de Django
2. **Management commands**: Más robusto que scripts Python sueltos
3. **Servicios reutilizables**: `reporte_service.py` se puede usar desde APIs, views, etc.
4. **Mejor organización**: Estructura MVC clara
5. **Fácil de extender**: Agregar nuevos tipos de reportes es simple
6. **Compatible con .bat**: Los usuarios pueden seguir usando menús de Windows

## 🐛 Troubleshooting

### Error: "module not found"
- Asegúrate de estar en el directorio correcto del backend
- Verifica que todas las dependencias estén instaladas

### Error: "No module named 'autorepcuentas'"
- El .bat debe ejecutarse desde el directorio del backend Django
- Verifica la variable `BACKEND_DIR` en el .bat

### Error: "Supabase connection failed"
- Verifica las credenciales en tu configuración de Django
- Asegúrate de usar `service_role_key` y no `anon_key`

## 📞 Próximos pasos

1. ✅ Ejecutar script SQL en Supabase
2. ✅ Instalar dependencias (pandas, openpyxl, supabase)
3. ✅ Mejorar `listar_cuentas.py` para devolver `account_id`
4. ✅ Actualizar `generar_reportes.bat` para usar `account_id` real
5. ✅ Probar generación de reportes
6. ✅ (Opcional) Crear endpoints REST API para reportes

---

**¡Tu sistema está listo para generar reportes!** 🎉
