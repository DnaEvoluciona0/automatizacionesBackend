#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TOKEN SERVICE - AutoRepCuentas
Servicio para verificar y renovar tokens de Meta Ads
Adaptado de LEO MASTER autoTokens para Django
"""

import os
import json
import requests
from datetime import datetime, timedelta


class TokenService:
    """Servicio para gestionar tokens de Meta Ads"""

    def __init__(self):
        """Inicializa el servicio de tokens"""
        self.api_base_url = "https://graph.facebook.com/v18.0"
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config.json'
        )
        self.log_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'token_log.json'
        )
        self.config = None
        self.log = None

    def load_config(self):
        """Carga la configuración desde config.json"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return True
        except Exception as e:
            print(f"Error cargando config.json: {e}")
            return False

    def save_config(self):
        """Guarda la configuración actualizada en config.json"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando config.json: {e}")
            return False

    def load_log(self):
        """Carga el log de renovaciones"""
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    self.log = json.load(f)
            else:
                self.log = {"renovations": [], "last_check": None}
        except:
            self.log = {"renovations": [], "last_check": None}

    def save_log(self):
        """Guarda el log de renovaciones"""
        try:
            self.log["last_check"] = datetime.now().isoformat()
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(self.log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando log: {e}")

    def check_token_info(self, access_token, app_id, app_secret):
        """Verifica información del token (si es válido, tipo, expiración)"""
        if not access_token or not access_token.strip():
            return {"valid": False, "error": "Token vacío"}

        try:
            url = f"{self.api_base_url}/debug_token"
            params = {
                "input_token": access_token,
                "access_token": f"{app_id}|{app_secret}"
            }

            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if "data" in data:
                token_data = data["data"]
                is_valid = token_data.get("is_valid", False)
                expires_at = token_data.get("expires_at", 0)

                if expires_at == 0:
                    expiry_info = "Nunca expira"
                    days_remaining = 9999
                    expiry_date = None
                else:
                    expiry_date = datetime.fromtimestamp(expires_at)
                    days_remaining = (expiry_date - datetime.now()).days
                    expiry_info = f"{expiry_date.strftime('%d/%m/%Y %H:%M')} ({days_remaining} días)"

                return {
                    "valid": is_valid,
                    "expires_at": expires_at,
                    "expiry_date": expiry_date,
                    "expiry_info": expiry_info,
                    "days_remaining": days_remaining,
                    "app_id": token_data.get("app_id"),
                    "type": token_data.get("type"),
                    "scopes": token_data.get("scopes", [])
                }
            else:
                error = data.get("error", {}).get("message", "Error desconocido")
                return {"valid": False, "error": error}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def exchange_for_long_lived_token(self, short_token, app_id, app_secret):
        """Intercambia un token de corta duración por uno de larga duración (60 días)"""
        try:
            url = f"{self.api_base_url}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": short_token
            }

            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if "access_token" in data:
                return {
                    "success": True,
                    "access_token": data["access_token"],
                    "expires_in": data.get("expires_in", 5184000)
                }
            else:
                error = data.get("error", {}).get("message", "Error desconocido")
                return {"success": False, "error": error}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_tokens_status(self):
        """Obtiene el estado de todos los tokens"""
        if not self.load_config():
            return {"status": "error", "message": "No se pudo cargar config.json"}

        accounts = self.config.get("accounts", {})
        results = []

        for account_key, account_data in accounts.items():
            nombre = account_data.get("nombre", "Sin nombre")
            app_id = account_data.get("app_id", "")
            app_secret = account_data.get("app_secret", "")
            access_token = account_data.get("access_token", "")

            result = {
                "account_key": account_key,
                "nombre": nombre,
                "has_credentials": bool(app_id and app_secret),
                "has_token": bool(access_token and access_token.strip()),
            }

            if not app_id or not app_secret:
                result["status"] = "sin_credenciales"
                result["status_class"] = "secondary"
                result["status_text"] = "Sin credenciales"
                result["days_remaining"] = None
            elif not access_token or not access_token.strip():
                result["status"] = "sin_token"
                result["status_class"] = "warning"
                result["status_text"] = "Sin token"
                result["days_remaining"] = None
            else:
                token_info = self.check_token_info(access_token, app_id, app_secret)

                if not token_info.get("valid"):
                    result["status"] = "invalido"
                    result["status_class"] = "danger"
                    result["status_text"] = f"Inválido: {token_info.get('error', 'Error')}"
                    result["days_remaining"] = None
                else:
                    days = token_info.get("days_remaining", 0)
                    result["days_remaining"] = days
                    result["expiry_info"] = token_info.get("expiry_info")
                    result["expiry_date"] = token_info.get("expiry_date")

                    if days == 9999:
                        result["status"] = "permanente"
                        result["status_class"] = "info"
                        result["status_text"] = "Permanente"
                    elif days > 15:
                        result["status"] = "ok"
                        result["status_class"] = "success"
                        result["status_text"] = f"OK ({days} días)"
                    elif days > 7:
                        result["status"] = "advertencia"
                        result["status_class"] = "warning"
                        result["status_text"] = f"Advertencia ({days} días)"
                    elif days > 0:
                        result["status"] = "critico"
                        result["status_class"] = "danger"
                        result["status_text"] = f"Crítico ({days} días)"
                    else:
                        result["status"] = "expirado"
                        result["status_class"] = "danger"
                        result["status_text"] = "Expirado"

            results.append(result)

        # Calcular resumen
        resumen = {
            "total": len(results),
            "ok": len([r for r in results if r["status"] in ["ok", "permanente"]]),
            "advertencia": len([r for r in results if r["status"] == "advertencia"]),
            "critico": len([r for r in results if r["status"] == "critico"]),
            "expirado": len([r for r in results if r["status"] == "expirado"]),
            "invalido": len([r for r in results if r["status"] == "invalido"]),
            "sin_token": len([r for r in results if r["status"] == "sin_token"]),
            "sin_credenciales": len([r for r in results if r["status"] == "sin_credenciales"]),
        }

        return {
            "status": "success",
            "tokens": results,
            "resumen": resumen,
            "fecha_verificacion": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

    def renovar_token(self, account_key):
        """Renueva el token de una cuenta específica"""
        if not self.load_config():
            return {"status": "error", "message": "No se pudo cargar config.json"}

        self.load_log()

        accounts = self.config.get("accounts", {})
        if account_key not in accounts:
            return {"status": "error", "message": f"Cuenta {account_key} no encontrada"}

        account_data = accounts[account_key]
        nombre = account_data.get("nombre", "Sin nombre")
        app_id = account_data.get("app_id", "")
        app_secret = account_data.get("app_secret", "")
        access_token = account_data.get("access_token", "")

        if not app_id or not app_secret:
            return {"status": "error", "message": "Cuenta sin credenciales de app"}

        if not access_token:
            return {"status": "error", "message": "Cuenta sin token de acceso"}

        # Verificar token actual
        token_info = self.check_token_info(access_token, app_id, app_secret)
        if not token_info.get("valid"):
            return {"status": "error", "message": f"Token inválido: {token_info.get('error')}"}

        # Intentar renovar
        result = self.exchange_for_long_lived_token(access_token, app_id, app_secret)

        if result.get("success"):
            new_token = result["access_token"]
            expires_in = result.get("expires_in", 5184000)
            days = expires_in // 86400

            # Actualizar config
            self.config["accounts"][account_key]["access_token"] = new_token
            self.save_config()

            # Registrar en log
            self.log["renovations"].append({
                "account": account_key,
                "nombre": nombre,
                "date": datetime.now().isoformat(),
                "expires_in_days": days,
                "success": True
            })
            self.save_log()

            return {
                "status": "success",
                "message": f"Token renovado exitosamente. Válido por {days} días",
                "days": days
            }
        else:
            error = result.get("error", "Error desconocido")

            self.log["renovations"].append({
                "account": account_key,
                "nombre": nombre,
                "date": datetime.now().isoformat(),
                "success": False,
                "error": error
            })
            self.save_log()

            return {"status": "error", "message": f"Error renovando: {error}"}

    def renovar_todos(self, solo_proximos_a_expirar=True):
        """Renueva todos los tokens (o solo los próximos a expirar)"""
        if not self.load_config():
            return {"status": "error", "message": "No se pudo cargar config.json"}

        self.load_log()

        accounts = self.config.get("accounts", {})
        stats = {
            "total": len(accounts),
            "ok": 0,
            "renovados": 0,
            "saltados": 0,
            "invalidos": 0,
            "errores": 0
        }
        detalles = []

        for account_key, account_data in accounts.items():
            nombre = account_data.get("nombre", "Sin nombre")
            app_id = account_data.get("app_id", "")
            app_secret = account_data.get("app_secret", "")
            access_token = account_data.get("access_token", "")

            detalle = {"account_key": account_key, "nombre": nombre}

            if not app_id or not app_secret:
                detalle["resultado"] = "saltado"
                detalle["mensaje"] = "Sin credenciales"
                stats["saltados"] += 1
                detalles.append(detalle)
                continue

            if not access_token:
                detalle["resultado"] = "saltado"
                detalle["mensaje"] = "Sin token"
                stats["saltados"] += 1
                detalles.append(detalle)
                continue

            # Verificar token
            token_info = self.check_token_info(access_token, app_id, app_secret)

            if not token_info.get("valid"):
                detalle["resultado"] = "invalido"
                detalle["mensaje"] = token_info.get("error", "Token inválido")
                stats["invalidos"] += 1
                detalles.append(detalle)
                continue

            days = token_info.get("days_remaining", 0)

            # Decidir si renovar
            if solo_proximos_a_expirar and days > 15 and days < 9999:
                detalle["resultado"] = "ok"
                detalle["mensaje"] = f"No necesita renovación ({days} días)"
                stats["ok"] += 1
                detalles.append(detalle)
                continue

            if days == 9999:
                detalle["resultado"] = "ok"
                detalle["mensaje"] = "Token permanente"
                stats["ok"] += 1
                detalles.append(detalle)
                continue

            # Renovar
            result = self.exchange_for_long_lived_token(access_token, app_id, app_secret)

            if result.get("success"):
                new_token = result["access_token"]
                expires_in = result.get("expires_in", 5184000)
                new_days = expires_in // 86400

                self.config["accounts"][account_key]["access_token"] = new_token

                self.log["renovations"].append({
                    "account": account_key,
                    "nombre": nombre,
                    "date": datetime.now().isoformat(),
                    "expires_in_days": new_days,
                    "success": True
                })

                detalle["resultado"] = "renovado"
                detalle["mensaje"] = f"Renovado. Válido por {new_days} días"
                stats["renovados"] += 1
            else:
                error = result.get("error", "Error desconocido")

                self.log["renovations"].append({
                    "account": account_key,
                    "nombre": nombre,
                    "date": datetime.now().isoformat(),
                    "success": False,
                    "error": error
                })

                detalle["resultado"] = "error"
                detalle["mensaje"] = f"Error: {error}"
                stats["errores"] += 1

            detalles.append(detalle)

        # Guardar cambios
        if stats["renovados"] > 0:
            self.save_config()
        self.save_log()

        return {
            "status": "success",
            "stats": stats,
            "detalles": detalles,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

    def get_log(self, limit=50):
        """Obtiene el historial de renovaciones"""
        self.load_log()
        renovations = self.log.get("renovations", [])

        # Ordenar por fecha descendente
        renovations_sorted = sorted(
            renovations,
            key=lambda x: x.get("date", ""),
            reverse=True
        )[:limit]

        return {
            "status": "success",
            "last_check": self.log.get("last_check"),
            "renovations": renovations_sorted
        }
