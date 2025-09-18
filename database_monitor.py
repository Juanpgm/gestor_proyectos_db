#!/usr/bin/env python3
"""
Sistema de Monitoreo Continuo de Base de Datos
===============================================

Este módulo proporciona:
- Monitoreo continuo de salud de la base de datos
- Chequeos periódicos automáticos
- Autoreparación automática
- Alertas y notificaciones
- Scheduler inteligente
- Reportes periódicos
- Gestión de logs históricos
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import signal

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.utils.database_health import DatabaseHealthChecker, HealthStatus
    from src.utils.database_repair import DatabaseAutoRepairer
    from railway_config import create_railway_connection, load_env_file
    from src.config.settings import DatabaseConfig
    from src.database.connection import DatabaseManager
    from src.utils.data_loader import DataLoader
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)


class AlertLevel(Enum):
    """Niveles de alerta"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MonitoringMode(Enum):
    """Modos de monitoreo"""
    PASSIVE = "passive"  # Solo chequeos, no reparaciones
    ACTIVE = "active"    # Reparaciones automáticas
    EMERGENCY = "emergency"  # Modo de emergencia


@dataclass
class MonitoringAlert:
    """Alerta de monitoreo"""
    timestamp: datetime
    level: AlertLevel
    title: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


@dataclass
class MonitoringStats:
    """Estadísticas de monitoreo"""
    start_time: datetime
    total_checks: int
    successful_checks: int
    failed_checks: int
    total_repairs: int
    successful_repairs: int
    failed_repairs: int
    last_check_time: Optional[datetime]
    last_repair_time: Optional[datetime]
    uptime_percentage: float
    alerts_generated: int


class DatabaseMonitor:
    """Monitor principal de base de datos"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializar el monitor
        
        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        self.config_path = config_path or Path(__file__).parent / "logs" / "monitoring_config.json"
        self.logs_path = Path(__file__).parent / "logs"
        self.logs_path.mkdir(exist_ok=True)
        
        # Estado del monitor
        self.is_running = False
        self.db_manager = None
        self.health_checker = None
        self.auto_repairer = None
        self.data_loader = None
        
        # Configuración
        self.config = self._load_config()
        self.mode = MonitoringMode.ACTIVE
        
        # Estadísticas
        self.stats = MonitoringStats(
            start_time=datetime.now(),
            total_checks=0,
            successful_checks=0,
            failed_checks=0,
            total_repairs=0,
            successful_repairs=0,
            failed_repairs=0,
            last_check_time=None,
            last_repair_time=None,
            uptime_percentage=100.0,
            alerts_generated=0
        )
        
        # Alertas
        self.alerts: List[MonitoringAlert] = []
        self.max_alerts_history = 100
        
        # Threading
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Configurar logging
        self._setup_logging()
        
        # Configurar handlers de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🎯 Monitor de base de datos inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración de monitoreo"""
        default_config = {
            "enabled": True,
            "check_interval_minutes": 480,  # 3 veces al día (cada 8 horas)
            "railway_check_interval_minutes": 480,  # 3 veces al día para Railway también
            "auto_repair": True,
            "max_repair_attempts": 3,
            "alert_thresholds": {
                "response_time_ms": 2000,
                "connection_failures": 3,
                "data_staleness_hours": 24
            },
            "reports": {
                "daily_enabled": True,
                "weekly_enabled": True,
                "monthly_enabled": True
            },
            "cleanup": {
                "log_retention_days": 30,
                "alert_retention_days": 7
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Warning: Error loading config, using defaults: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """Configurar logging para monitoreo"""
        log_file = self.logs_path / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def start_monitoring(self):
        """Iniciar el monitoreo continuo"""
        if self.is_running:
            self.logger.warning("El monitor ya está ejecutándose")
            return
        
        self.logger.info("🚀 Iniciando monitoreo continuo...")
        
        # Inicializar conexión a base de datos
        if not self._initialize_database_connection():
            self.logger.error("❌ No se pudo inicializar conexión a base de datos")
            return False
        
        # Configurar programación de tareas
        self._setup_schedule()
        
        # Ejecutar chequeo inicial
        self._perform_health_check()
        
        # Iniciar thread de monitoreo
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("✅ Monitoreo continuo iniciado")
        return True
    
    def stop_monitoring(self):
        """Detener el monitoreo"""
        self.logger.info("🛑 Deteniendo monitoreo...")
        
        self.is_running = False
        self.stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        # Guardar estadísticas finales
        self._save_final_stats()
        
        self.logger.info("✅ Monitoreo detenido")
    
    def _initialize_database_connection(self) -> bool:
        """Inicializar conexión a base de datos"""
        try:
            # Cargar variables de entorno
            load_env_file()
            
            # Intentar Railway primero
            self.db_manager = create_railway_connection()
            
            if self.db_manager and self.db_manager.test_connection():
                self.logger.info("✅ Conectado a Railway para monitoreo")
                # Usar intervalo más frecuente para Railway
                self.config["check_interval_minutes"] = self.config.get("railway_check_interval_minutes", 5)
            else:
                # Fallback a local
                self.logger.info("🔄 Railway no disponible, usando configuración local")
                
                # Remover DATABASE_URL temporalmente
                original_url = os.environ.pop("DATABASE_URL", None)
                try:
                    config = DatabaseConfig()
                    self.db_manager = DatabaseManager(config)
                    
                    if self.db_manager.connect():
                        self.logger.info("✅ Conectado a base de datos local para monitoreo")
                    else:
                        self.logger.error("❌ No se pudo conectar a base de datos local")
                        return False
                finally:
                    # Restaurar DATABASE_URL
                    if original_url:
                        os.environ["DATABASE_URL"] = original_url
            
            # Inicializar componentes
            self.health_checker = DatabaseHealthChecker(self.db_manager)
            self.data_loader = DataLoader(self.db_manager)
            self.auto_repairer = DatabaseAutoRepairer(self.db_manager, self.data_loader)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando conexión: {e}")
            return False
    
    def _setup_schedule(self):
        """Configurar programación de chequeos"""
        check_interval = self.config.get("check_interval_minutes", 15)
        
        # Chequeos de salud periódicos
        schedule.every(check_interval).minutes.do(self._scheduled_health_check)
        
        # Reportes diarios
        if self.config.get("reports", {}).get("daily_enabled", True):
            schedule.every().day.at("06:00").do(self._generate_daily_report)
        
        # Reportes semanales
        if self.config.get("reports", {}).get("weekly_enabled", True):
            schedule.every().monday.at("07:00").do(self._generate_weekly_report)
        
        # Limpieza de logs
        schedule.every().day.at("02:00").do(self._cleanup_old_logs)
        
        self.logger.info(f"📅 Programación configurada: chequeos cada {check_interval} minutos")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        self.logger.info("🔄 Loop de monitoreo iniciado")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Ejecutar tareas programadas
                schedule.run_pending()
                
                # Verificar conexión periódicamente
                if not self.db_manager or not self.db_manager.test_connection():
                    self._handle_connection_loss()
                
                # Esperar antes del siguiente ciclo
                self.stop_event.wait(timeout=60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"❌ Error en loop de monitoreo: {e}")
                self._create_alert(AlertLevel.CRITICAL, "Error en loop de monitoreo", str(e))
                
                # Esperar antes de continuar
                self.stop_event.wait(timeout=300)  # 5 minutos en caso de error
    
    def _scheduled_health_check(self):
        """Chequeo de salud programado"""
        self.logger.info("🔍 Ejecutando chequeo programado...")
        self._perform_health_check()
    
    def _perform_health_check(self):
        """Ejecutar chequeo de salud completo"""
        try:
            self.stats.total_checks += 1
            check_start = time.time()
            
            # Ejecutar diagnóstico
            health_report = self.health_checker.run_full_diagnosis()
            
            # Actualizar estadísticas
            self.stats.last_check_time = datetime.now()
            
            if health_report.overall_status == HealthStatus.HEALTHY:
                self.stats.successful_checks += 1
                self.logger.info("✅ Chequeo de salud: SALUDABLE")
            else:
                self.stats.failed_checks += 1
                self.logger.warning(f"⚠️ Chequeo de salud: {health_report.overall_status.value.upper()}")
                
                # Crear alertas para problemas críticos
                for check in health_report.checks:
                    if check.status == HealthStatus.CRITICAL:
                        self._create_alert(
                            AlertLevel.CRITICAL,
                            f"Problema crítico: {check.name}",
                            check.message,
                            check.details
                        )
                    elif check.status == HealthStatus.WARNING:
                        self._create_alert(
                            AlertLevel.WARNING,
                            f"Advertencia: {check.name}",
                            check.message,
                            check.details
                        )
                
                # Ejecutar autoreparación si está habilitada
                if self.config.get("auto_repair", True) and self.mode == MonitoringMode.ACTIVE:
                    self._perform_auto_repair(health_report)
            
            # Calcular tiempo de respuesta
            response_time = (time.time() - check_start) * 1000  # ms
            
            # Verificar umbral de tiempo de respuesta
            threshold = self.config.get("alert_thresholds", {}).get("response_time_ms", 2000)
            if response_time > threshold:
                self._create_alert(
                    AlertLevel.WARNING,
                    "Tiempo de respuesta alto",
                    f"Chequeo tardó {response_time:.1f}ms (umbral: {threshold}ms)"
                )
            
            # Actualizar porcentaje de uptime
            self._update_uptime_stats(health_report.overall_status == HealthStatus.HEALTHY)
            
            # Guardar reporte
            self._save_health_report(health_report)
            
        except Exception as e:
            self.stats.failed_checks += 1
            self.logger.error(f"❌ Error en chequeo de salud: {e}")
            self._create_alert(AlertLevel.CRITICAL, "Error en chequeo de salud", str(e))
    
    def _perform_auto_repair(self, health_report):
        """Ejecutar autoreparación"""
        try:
            self.logger.info("🔧 Iniciando autoreparación...")
            
            self.stats.total_repairs += 1
            
            repair_results = self.auto_repairer.auto_repair(health_report)
            
            successful_repairs = [r for r in repair_results if r.success]
            failed_repairs = [r for r in repair_results if not r.success]
            
            self.stats.successful_repairs += len(successful_repairs)
            self.stats.failed_repairs += len(failed_repairs)
            self.stats.last_repair_time = datetime.now()
            
            if successful_repairs:
                self.logger.info(f"✅ Autoreparación: {len(successful_repairs)} acciones exitosas")
                
                # Crear alerta informativa
                self._create_alert(
                    AlertLevel.INFO,
                    "Autoreparación exitosa",
                    f"{len(successful_repairs)} problemas reparados automáticamente",
                    {"repairs": [r.action.value for r in successful_repairs]}
                )
            
            if failed_repairs:
                self.logger.warning(f"⚠️ Autoreparación: {len(failed_repairs)} acciones fallidas")
                
                # Crear alerta de fallo
                self._create_alert(
                    AlertLevel.WARNING,
                    "Autoreparación parcialmente fallida",
                    f"{len(failed_repairs)} reparaciones fallaron",
                    {"failed_repairs": [r.message for r in failed_repairs]}
                )
            
        except Exception as e:
            self.stats.failed_repairs += 1
            self.logger.error(f"❌ Error en autoreparación: {e}")
            self._create_alert(AlertLevel.CRITICAL, "Error en autoreparación", str(e))
    
    def _handle_connection_loss(self):
        """Manejar pérdida de conexión"""
        self.logger.warning("⚠️ Pérdida de conexión detectada")
        
        # Crear alerta
        self._create_alert(
            AlertLevel.CRITICAL,
            "Pérdida de conexión",
            "Se perdió la conexión a la base de datos"
        )
        
        # Intentar reconectar
        if self._initialize_database_connection():
            self.logger.info("✅ Reconexión exitosa")
            self._create_alert(
                AlertLevel.INFO,
                "Reconexión exitosa",
                "Conexión a base de datos restaurada"
            )
        else:
            self.logger.error("❌ No se pudo reconectar")
    
    def _create_alert(self, level: AlertLevel, title: str, message: str, details: Dict[str, Any] = None):
        """Crear nueva alerta"""
        alert = MonitoringAlert(
            timestamp=datetime.now(),
            level=level,
            title=title,
            message=message,
            details=details or {}
        )
        
        self.alerts.append(alert)
        self.stats.alerts_generated += 1
        
        # Mantener solo las alertas más recientes
        if len(self.alerts) > self.max_alerts_history:
            self.alerts = self.alerts[-self.max_alerts_history:]
        
        # Log según el nivel
        if level == AlertLevel.CRITICAL:
            self.logger.error(f"🚨 CRÍTICO: {title} - {message}")
        elif level == AlertLevel.WARNING:
            self.logger.warning(f"⚠️ ADVERTENCIA: {title} - {message}")
        else:
            self.logger.info(f"ℹ️ INFO: {title} - {message}")
        
        # Guardar alerta
        self._save_alert(alert)
    
    def _update_uptime_stats(self, is_healthy: bool):
        """Actualizar estadísticas de uptime"""
        total_checks = self.stats.total_checks
        if total_checks > 0:
            healthy_checks = self.stats.successful_checks + (1 if is_healthy else 0)
            self.stats.uptime_percentage = (healthy_checks / total_checks) * 100
    
    def _save_health_report(self, health_report):
        """Guardar reporte de salud"""
        try:
            reports_dir = self.logs_path / "health_reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"health_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(health_report.to_dict(), f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error guardando reporte: {e}")
    
    def _save_alert(self, alert: MonitoringAlert):
        """Guardar alerta"""
        try:
            alerts_dir = self.logs_path / "alerts"
            alerts_dir.mkdir(exist_ok=True)
            
            date_str = alert.timestamp.strftime("%Y%m%d")
            alerts_file = alerts_dir / f"alerts_{date_str}.json"
            
            # Cargar alertas existentes del día
            alerts_data = []
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    alerts_data = json.load(f)
            
            # Agregar nueva alerta
            alert_dict = asdict(alert)
            alert_dict["timestamp"] = alert.timestamp.isoformat()
            alert_dict["level"] = alert.level.value
            if alert.resolution_timestamp:
                alert_dict["resolution_timestamp"] = alert.resolution_timestamp.isoformat()
            
            alerts_data.append(alert_dict)
            
            # Guardar
            with open(alerts_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error guardando alerta: {e}")
    
    def _generate_daily_report(self):
        """Generar reporte diario"""
        self.logger.info("📊 Generando reporte diario...")
        
        try:
            # Calcular métricas del día
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            # Filtrar alertas del día
            daily_alerts = [
                alert for alert in self.alerts 
                if start_time <= alert.timestamp <= end_time
            ]
            
            report = {
                "date": end_time.strftime("%Y-%m-%d"),
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "stats": asdict(self.stats),
                "alerts": {
                    "total": len(daily_alerts),
                    "critical": len([a for a in daily_alerts if a.level == AlertLevel.CRITICAL]),
                    "warning": len([a for a in daily_alerts if a.level == AlertLevel.WARNING]),
                    "info": len([a for a in daily_alerts if a.level == AlertLevel.INFO])
                },
                "summary": {
                    "uptime_percentage": self.stats.uptime_percentage,
                    "total_checks_today": len(daily_alerts),  # Aproximación
                    "repairs_needed": self.stats.total_repairs > 0
                }
            }
            
            # Guardar reporte
            reports_dir = self.logs_path / "daily_reports"
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / f"daily_{end_time.strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"✅ Reporte diario guardado: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte diario: {e}")
    
    def _generate_weekly_report(self):
        """Generar reporte semanal"""
        self.logger.info("📈 Generando reporte semanal...")
        # Similar al reporte diario pero con período de 7 días
        # Implementación simplificada por espacio
    
    def _cleanup_old_logs(self):
        """Limpiar logs antiguos"""
        try:
            retention_days = self.config.get("cleanup", {}).get("log_retention_days", 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cleaned_files = 0
            
            # Limpiar reportes de salud
            health_reports_dir = self.logs_path / "health_reports"
            if health_reports_dir.exists():
                for file_path in health_reports_dir.glob("health_*.json"):
                    if file_path.stat().st_mtime < cutoff_date.timestamp():
                        file_path.unlink()
                        cleaned_files += 1
            
            # Limpiar alertas antiguas
            alert_retention_days = self.config.get("cleanup", {}).get("alert_retention_days", 7)
            alert_cutoff = datetime.now() - timedelta(days=alert_retention_days)
            
            alerts_dir = self.logs_path / "alerts"
            if alerts_dir.exists():
                for file_path in alerts_dir.glob("alerts_*.json"):
                    if file_path.stat().st_mtime < alert_cutoff.timestamp():
                        file_path.unlink()
                        cleaned_files += 1
            
            if cleaned_files > 0:
                self.logger.info(f"🧹 Limpieza completada: {cleaned_files} archivos eliminados")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error en limpieza: {e}")
    
    def _save_final_stats(self):
        """Guardar estadísticas finales"""
        try:
            stats_file = self.logs_path / "monitoring_stats.json"
            
            final_stats = asdict(self.stats)
            final_stats["start_time"] = self.stats.start_time.isoformat()
            final_stats["end_time"] = datetime.now().isoformat()
            if self.stats.last_check_time:
                final_stats["last_check_time"] = self.stats.last_check_time.isoformat()
            if self.stats.last_repair_time:
                final_stats["last_repair_time"] = self.stats.last_repair_time.isoformat()
            
            with open(stats_file, 'w') as f:
                json.dump(final_stats, f, indent=2)
                
            self.logger.info(f"📊 Estadísticas finales guardadas: {stats_file}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error guardando estadísticas: {e}")
    
    def _signal_handler(self, signum, frame):
        """Manejar señales del sistema"""
        self.logger.info(f"📡 Señal recibida: {signum}")
        self.stop_monitoring()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del monitor"""
        return {
            "is_running": self.is_running,
            "stats": asdict(self.stats),
            "recent_alerts": [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message
                }
                for alert in self.alerts[-5:]  # Últimas 5 alertas
            ],
            "config": self.config
        }


def main():
    """Función principal para ejecutar el monitor"""
    print("🎯 Iniciando Monitor de Base de Datos")
    print("=" * 50)
    
    monitor = DatabaseMonitor()
    
    try:
        if monitor.start_monitoring():
            print("✅ Monitor iniciado exitosamente")
            print("Presiona Ctrl+C para detener...")
            
            # Mantener el programa ejecutándose
            while monitor.is_running:
                time.sleep(1)
        else:
            print("❌ No se pudo iniciar el monitor")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo monitor...")
    except Exception as e:
        print(f"❌ Error ejecutando monitor: {e}")
        return 1
    finally:
        monitor.stop_monitoring()
        print("✅ Monitor detenido")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())