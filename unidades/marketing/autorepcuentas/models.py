from django.db import models
from datetime import datetime

#? Tabla de cuentas de Meta Ads
class Accounts(models.Model):
    account_id = models.CharField(max_length=50, primary_key=True)
    account_name = models.CharField(max_length=255)
    account_key = models.CharField(max_length=10, unique=True)
    multimarca = models.CharField(max_length=10, null=True, blank=True)
    marcas = models.TextField(null=True, blank=True)
    app_id = models.CharField(max_length=100, null=True, blank=True)
    has_valid_token = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(default=datetime.now)
    last_sync_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = '"marketing"."accounts"'


#? Tabla de campañas de Meta Ads con insights diarios
class Campaigns(models.Model):
    # PRIMARY KEY compuesta (campaign_id, insights_date_start)
    campaign_id = models.CharField(max_length=50)
    insights_date_start = models.DateField()

    # Timestamps
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(default=datetime.now)

    # Relación con account
    account_id = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255, null=True, blank=True)

    # Información de campaña
    campaign_name = models.TextField(null=True, blank=True)
    campaign_status = models.CharField(max_length=50, null=True, blank=True)
    campaign_objective = models.CharField(max_length=100, null=True, blank=True)
    campaign_created_time = models.DateTimeField(null=True, blank=True)
    campaign_updated_time = models.DateTimeField(null=True, blank=True)
    campaign_start_time = models.DateTimeField(null=True, blank=True)
    campaign_stop_time = models.DateTimeField(null=True, blank=True)

    # Configuración
    buying_type = models.CharField(max_length=50, null=True, blank=True)
    bid_strategy = models.CharField(max_length=100, null=True, blank=True)
    budget_remaining = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    configured_status = models.CharField(max_length=50, null=True, blank=True)
    effective_status = models.CharField(max_length=50, null=True, blank=True)
    special_ad_category = models.CharField(max_length=50, null=True, blank=True)
    can_use_spend_cap = models.BooleanField(null=True, blank=True)
    budget_rebalance_flag = models.BooleanField(null=True, blank=True)
    is_skadnetwork_attribution = models.BooleanField(null=True, blank=True)
    smart_promotion_type = models.CharField(max_length=100, null=True, blank=True)
    can_create_brand_lift_study = models.BooleanField(null=True, blank=True)

    # Período de insights
    insights_date_stop = models.DateField(null=True, blank=True)

    # Métricas de rendimiento
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reach = models.BigIntegerField(default=0)
    frequency = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas de costos
    cpm = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    cpc = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas de clics
    inline_link_clicks = models.BigIntegerField(default=0)
    inline_link_click_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    unique_clicks = models.BigIntegerField(default=0)
    unique_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Configuración de optimización
    optimization_goal = models.CharField(max_length=100, null=True, blank=True)

    # Metadatos
    extraction_date = models.DateTimeField(default=datetime.now)
    data_source = models.CharField(max_length=50, default='LEO_4.0_EXTRACTOR')

    class Meta:
        db_table = '"marketing"."campaigns"'
        unique_together = ('campaign_id', 'insights_date_start')


#? Tabla de Ad Sets de Meta Ads con insights diarios
class Adsets(models.Model):
    # PRIMARY KEY compuesta (adset_id, insights_date_start)
    adset_id = models.CharField(max_length=50)
    insights_date_start = models.DateField()

    # Timestamps
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(default=datetime.now)

    # Relaciones
    account_id = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    campaign_id = models.CharField(max_length=50)

    # Información de adset
    adset_name = models.TextField(null=True, blank=True)
    adset_status = models.CharField(max_length=50, null=True, blank=True)
    configured_status = models.CharField(max_length=50, null=True, blank=True)
    effective_status = models.CharField(max_length=50, null=True, blank=True)

    # Fechas de adset
    adset_created_time = models.DateTimeField(null=True, blank=True)
    adset_updated_time = models.DateTimeField(null=True, blank=True)
    adset_start_time = models.DateTimeField(null=True, blank=True)
    adset_end_time = models.DateTimeField(null=True, blank=True)

    # Configuración
    optimization_goal = models.CharField(max_length=100, null=True, blank=True)
    billing_event = models.CharField(max_length=50, null=True, blank=True)
    bid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_remaining = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    lifetime_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bid_strategy = models.CharField(max_length=100, null=True, blank=True)
    destination_type = models.CharField(max_length=100, null=True, blank=True)
    pacing_type = models.CharField(max_length=50, null=True, blank=True)
    is_dynamic_creative = models.BooleanField(default=False)

    # Datos complejos (JSON)
    targeting = models.TextField(null=True, blank=True)
    attribution_spec = models.TextField(null=True, blank=True)
    promoted_object = models.TextField(null=True, blank=True)

    # Período de insights
    insights_date_stop = models.DateField(null=True, blank=True)

    # Métricas de rendimiento
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reach = models.BigIntegerField(default=0)
    frequency = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas de costos
    cpm = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    cpc = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas de clics
    inline_link_clicks = models.BigIntegerField(default=0)
    inline_link_click_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    unique_clicks = models.BigIntegerField(default=0)
    unique_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Metadatos
    extraction_date = models.DateTimeField(default=datetime.now)
    data_source = models.CharField(max_length=50, default='LEO_4.0_ADSETS_EXTRACTOR')

    class Meta:
        db_table = '"marketing"."adsets"'
        unique_together = ('adset_id', 'insights_date_start')


#? Tabla de Ads de Meta Ads con insights diarios
class Ads(models.Model):
    # PRIMARY KEY compuesta (ad_id, insights_date_start)
    ad_id = models.CharField(max_length=50)
    insights_date_start = models.DateField()

    # Timestamps
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(default=datetime.now)

    # Relaciones
    account_id = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    adset_id = models.CharField(max_length=50)
    campaign_id = models.CharField(max_length=50)

    # Información de ad
    ad_name = models.TextField(null=True, blank=True)
    ad_status = models.CharField(max_length=50, null=True, blank=True)
    configured_status = models.CharField(max_length=50, null=True, blank=True)
    effective_status = models.CharField(max_length=50, null=True, blank=True)

    # Fechas de ad
    ad_created_time = models.DateTimeField(null=True, blank=True)
    ad_updated_time = models.DateTimeField(null=True, blank=True)

    # Configuración
    bid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    last_updated_by_app_id = models.CharField(max_length=100, null=True, blank=True)
    source_ad_id = models.CharField(max_length=50, null=True, blank=True)
    demolink_hash = models.CharField(max_length=255, null=True, blank=True)
    preview_shareable_link = models.TextField(null=True, blank=True)

    # Datos complejos (JSON)
    creative = models.TextField(null=True, blank=True)
    tracking_specs = models.TextField(null=True, blank=True)
    conversion_specs = models.TextField(null=True, blank=True)
    recommendations = models.TextField(null=True, blank=True)

    # Período de insights
    insights_date_stop = models.DateField(null=True, blank=True)

    # Métricas de rendimiento
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reach = models.BigIntegerField(default=0)
    frequency = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas de costos
    cpm = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    cpc = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas de clics
    inline_link_clicks = models.BigIntegerField(default=0)
    inline_link_click_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    unique_clicks = models.BigIntegerField(default=0)
    unique_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Métricas adicionales
    social_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unique_inline_link_clicks = models.BigIntegerField(default=0)
    unique_inline_link_click_ctr = models.DecimalField(max_digits=8, decimal_places=6, default=0)

    # Metadatos
    extraction_date = models.DateTimeField(default=datetime.now)
    data_source = models.CharField(max_length=50, default='LEO_4.0_ADS_EXTRACTOR')

    class Meta:
        db_table = '"marketing"."ads"'
        unique_together = ('ad_id', 'insights_date_start')
