# AutoRepCuentas - Automatización de Reportes de Marketing

Sistema de extracción y generación de reportes de Meta Ads integrado con Django.

## 📁 Estructura del Proyecto

```
autorepcuentas/
├── conexiones/              # Conexiones a servicios externos
│   ├── connection_supabase.py
│   ├── connection_meta_api.py
│   └── inicializar_supabase.sql
├── controllers/             # Lógica de negocio
│   ├── campaigns_controller.py
│   ├── adsets_controller.py
│   ├── ads_controller.py
│   └── accounts_controller.py
├── services/               # Servicios de alto nivel
│   └── reporte_service.py
├── utils/                  # Utilidades
│   ├── date_utils.py
│   └── db_validator.py
├── views/                  # Vistas y endpoints
│   ├── api_views.py
│   └── campaigns_view.py
├── management/            # Django management commands
│   └── commands/
│       └── generar_reporte.py
├── REPORTES_EXCEL/        # Carpeta donde se guardan los reportes
├── models.py              # Modelos de Django
└── README.md
```

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install pandas openpyxl supabase
```

### 2. Crear esquema en Supabase

1. Ve a tu proyecto en https://supabase.com
2. Abre el **SQL Editor**
3. Ejecuta el script: `conexiones/inicializar_supabase.sql`

### 3. Configurar variables de entorno

Asegúrate de tener las credenciales de Supabase en tu configuración de Django.

## 📊 Generación de Reportes

### Comando Django

```bash
# Reporte de campaigns (últimos 30 días)
python manage.py generar_reporte --tipo campaigns --account_id 123456789 --ultimos30

# Reporte de adsets con fechas específicas
python manage.py generar_reporte --tipo adsets --account_id 123456789 --fecha_inicio 2025-01-01 --fecha_fin 2025-01-31

# Reporte de ads
python manage.py generar_reporte --tipo ads --account_id 123456789 --fecha_inicio 2025-01-01 --fecha_fin 2025-01-31

# Reporte consolidado (campaigns + adsets + ads)
python manage.py generar_reporte --tipo consolidado --account_id 123456789 --ultimos30
```

### Parámetros

- `--tipo`: Tipo de reporte (`campaigns`, `adsets`, `ads`, `consolidado`)
- `--account_id`: ID de la cuenta de Meta Ads (requerido)
- `--fecha_inicio`: Fecha de inicio en formato YYYY-MM-DD (opcional)
- `--fecha_fin`: Fecha de fin en formato YYYY-MM-DD (opcional)
- `--ultimos30`: Flag para generar reporte de últimos 30 días automáticamente

## 🔧 Uso Programático

### Desde código Python

```python
from autorepcuentas.services.reporte_service import ReporteMarketingService

# Crear instancia del servicio
service = ReporteMarketingService()

# Generar reporte
success, filepath = service.generar_reporte(
    tipo='campaigns',
    account_id='123456789',
    fecha_inicio='2025-01-01',
    fecha_fin='2025-01-31'
)

if success:
    print(f"Reporte generado: {filepath}")
```

### Desde una vista de Django

```python
from django.http import FileResponse
from autorepcuentas.services.reporte_service import ReporteMarketingService

def generar_reporte_view(request):
    service = ReporteMarketingService()

    success, filepath = service.generar_reporte(
        tipo='campaigns',
        account_id=request.GET.get('account_id'),
        fecha_inicio=request.GET.get('fecha_inicio'),
        fecha_fin=request.GET.get('fecha_fin')
    )

    if success:
        return FileResponse(open(filepath, 'rb'), as_attachment=True)
    else:
        return JsonResponse({'error': 'No se pudo generar el reporte'}, status=500)
```

## 📝 Estructura de Base de Datos

### Schema: "Markeitng"

#### Tabla: accounts
- `account_id` (PK): ID de la cuenta
- `account_name`: Nombre de la cuenta
- `account_key`: Clave única
- Otros campos de configuración

#### Tabla: campaigns
- **PRIMARY KEY compuesta**: (`campaign_id`, `insights_date_start`)
- Permite múltiples insights diarios por campaña
- Métricas: spend, impressions, clicks, reach, cpm, cpc, ctr

#### Tabla: adsets
- **PRIMARY KEY compuesta**: (`adset_id`, `insights_date_start`)
- Permite múltiples insights diarios por adset
- Métricas: spend, impressions, clicks, reach, cpm, cpc, ctr

#### Tabla: ads
- **PRIMARY KEY compuesta**: (`ad_id`, `insights_date_start`)
- Permite múltiples insights diarios por ad
- Métricas: spend, impressions, clicks, reach, cpm, cpc, ctr

## 🎯 Tipos de Reportes

### 1. Campaigns
Reportes de campañas con métricas agregadas por campaña.

### 2. Adsets
Reportes de conjuntos de anuncios con métricas agregadas por adset.

### 3. Ads
Reportes de anuncios individuales con métricas agregadas por ad.

### 4. Consolidado
Reporte que incluye campaigns, adsets y ads en hojas separadas de Excel.

## 📈 Formato de Reportes Excel

Cada reporte incluye 3 hojas:

1. **💰 INVERSIÓN TOTAL**: Resumen ejecutivo con inversión total y métricas principales
2. **Datos Detallados**: Tabla con todos los datos según el tipo de reporte
3. **Resumen**: Información adicional y metadatos del reporte

## ⚙️ Extracción de Datos

### Usando Controllers

```python
from autorepcuentas.controllers import campaigns_controller

# Obtener datos de la cuenta desde config
account_data = {
    'account_id': '123456789',
    'access_token': 'tu_token',
    'nombre': 'Nombre Cuenta'
}

# Obtener campañas
result = campaigns_controller.get_all_campaigns(account_data)

if result['status'] == 'success':
    campaigns = result['campaigns']
    print(f"Se obtuvieron {result['count']} campañas")

# Obtener insights
result = campaigns_controller.get_campaigns_insights(account_data, campaigns)

if result['status'] == 'success':
    insights = result['insights']
    print(f"Se obtuvieron {result['count']} insights")

# Sincronizar con Supabase
result = campaigns_controller.sync_campaigns_to_supabase(
    campaigns,
    insights,
    account_data
)

if result['status'] == 'success':
    print(f"Insertados: {result['inserted']}")
    print(f"Actualizados: {result['updated']}")
```

## 🔄 Migración desde LEO MASTER

Si vienes desde LEO MASTER, la estructura es muy similar:

### Equivalencias:

| LEO MASTER | AutoRepCuentas Django |
|------------|----------------------|
| `PY/reporte_marketing.py` | `services/reporte_service.py` |
| `PY/campanas.py` | `controllers/campaigns_controller.py` |
| `conexiones/` | `conexiones/` (igual) |
| Scripts `.bat` | Management commands de Django |
| `config.json` | Variables de entorno / Settings Django |

## 📦 Dependencias

```
django>=4.0
pandas>=2.0
openpyxl>=3.1
supabase>=2.0
requests>=2.31
```

## 🐛 Troubleshooting

### Error: "No se encontraron datos"
- Verifica que el `account_id` sea correcto
- Asegúrate de que las fechas tengan datos en Supabase
- Verifica la conexión a Supabase

### Error: "Tabla no existe"
- Ejecuta el script SQL `inicializar_supabase.sql`
- Verifica que el esquema "Markeitng" exista en Supabase

### Error: "Permission denied"
- Verifica las políticas RLS en Supabase
- Usa el `service_role_key` en lugar de `anon_key`

## 📧 Soporte

Para problemas o dudas, revisa la documentación de Django y Supabase.

---

**Generado por AutoRepCuentas - Django Marketing Automation**
