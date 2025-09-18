#!/usr/bin/env python3
"""
Script Maestro de Despliegue Inteligente
========================================

Este script unifica todos los componentes de despliegue inteligente:
- Detección automática de entorno (Railway vs Local)
- Despliegue inteligente con auto-diagnóstico
- Monitoreo continuo automático
- Generación de reportes
- Autoreparación automática
- Gestión completa del ciclo de vida de la base de datos

Características principales:
- Detección automática del mejor entorno disponible
- Fallback automático entre Railway y local
- Monitoreo continuo con chequeos de salud
- Autoreparación automática de problemas
- Reportes ejecutivos periódicos
- Interfaz de línea de comandos intuitiva
"""

import os
import sys
import json
import time
import argparse
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Importar módulos de despliegue
    from intelligent_local_deploy import LocalDatabaseDeployment, LocalEnvironmentDetector
    from intelligent_railway_deploy import RailwayDatabaseDeployment, RailwayConnectionMonitor
    from database_monitor import DatabaseMonitor
    from database_reporter import DatabaseReporter, ReportFormat
    from schema_manager import SchemaManager
    from railway_config import load_env_file, load_local_env
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Asegúrate de que todos los scripts estén en el mismo directorio.")
    sys.exit(1)


class DeploymentEnvironment:
    """Enumeración de entornos de despliegue"""
    RAILWAY = "railway"
    LOCAL = "local"
    AUTO = "auto"


class IntelligentDatabaseManager:
    """
    Gestor Maestro de Base de Datos Inteligente
    
    Coordina todos los aspectos del ciclo de vida de la base de datos:
    - Despliegue inteligente
    - Monitoreo continuo
    - Autoreparación
    - Reportes
    """
    
    def __init__(self, preferred_environment: str = DeploymentEnvironment.AUTO):
        """
        Inicializar el gestor maestro
        
        Args:
            preferred_environment: Entorno preferido (auto, railway, local)
        """
        self.preferred_environment = preferred_environment
        self.current_environment = None
        self.deployment = None
        self.monitor = None
        self.reporter = None
        
        # Estado del sistema
        self.is_deployed = False
        self.is_monitoring = False
        self.deployment_info = {}
        
        # Configuración
        self.config = self._load_master_config()
        
        print("🎯 Gestor Maestro de Base de Datos Inteligente")
        print("=" * 60)
    
    def _load_master_config(self) -> Dict[str, Any]:
        """Cargar configuración maestra"""
        config_path = Path(__file__).parent / "master_config.json"
        
        default_config = {
            "auto_monitor": True,
            "auto_reports": True,
            "fallback_enabled": True,
            "health_check_on_deploy": True,
            "monitoring_config": {
                "check_interval_minutes": 480,  # 3 veces al día (cada 8 horas)
                "auto_repair": True,
                "generate_reports": True
            },
            "report_config": {
                "daily_reports": True,
                "weekly_reports": True,
                "executive_summary": True
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"⚠️ Error cargando configuración, usando defaults: {e}")
        
        return default_config
    
    def deploy(self, force_environment: Optional[str] = None) -> bool:
        """
        Ejecutar despliegue inteligente
        
        Args:
            force_environment: Forzar entorno específico
            
        Returns:
            True si el despliegue fue exitoso
        """
        print("🚀 Iniciando Despliegue Inteligente...")
        print("-" * 40)
        
        # Determinar entorno
        target_environment = force_environment or self.preferred_environment
        
        if target_environment == DeploymentEnvironment.AUTO:
            target_environment = self._detect_best_environment()
        
        print(f"🎯 Entorno objetivo: {target_environment.upper()}")
        
        # Ejecutar despliegue según entorno
        success = False
        
        if target_environment == DeploymentEnvironment.RAILWAY:
            success = self._deploy_railway()
            if not success and self.config.get("fallback_enabled", True):
                print("🔄 Railway falló, intentando fallback a local...")
                success = self._deploy_local()
        elif target_environment == DeploymentEnvironment.LOCAL:
            success = self._deploy_local()
        
        if success:
            self.is_deployed = True
            print("✅ Despliegue completado exitosamente")
            
            # Chequeo de salud post-despliegue
            if self.config.get("health_check_on_deploy", True):
                self._post_deployment_health_check()
            
            # Iniciar monitoreo automático si está habilitado
            if self.config.get("auto_monitor", True):
                self.start_monitoring()
            
            # Generar reporte inicial si está habilitado
            if self.config.get("auto_reports", True):
                self._generate_initial_report()
        else:
            print("❌ Fallo en el despliegue")
        
        return success
    
    def _detect_best_environment(self) -> str:
        """Detectar el mejor entorno disponible"""
        print("🔍 Detectando mejor entorno disponible...")
        
        # Cargar variables de entorno por defecto
        load_env_file()
        
        # Verificar Railway primero
        if os.getenv("DATABASE_URL"):
            print("   🚂 Railway detectado (DATABASE_URL presente)")
            
            # Test quick de conectividad Railway
            try:
                # Crear una configuración temporal para probar
                sys.path.insert(0, str(Path(__file__).parent / "src"))
                from src.config.settings import DatabaseConfig
                from src.database.connection import DatabaseManager
                
                config = DatabaseConfig()
                db_manager = DatabaseManager(config)
                
                railway_monitor = RailwayConnectionMonitor(db_manager)
                if railway_monitor.check_railway_availability():
                    print("   ✅ Railway disponible y accesible")
                    return DeploymentEnvironment.RAILWAY
                else:
                    print("   ⚠️ Railway no disponible, verificando local...")
            except Exception as e:
                print(f"   ⚠️ Error verificando Railway: {e}")
                print("   🔄 Continuando con verificación local...")
        
        # Si llegamos aquí, usar configuración local
        print("   🏠 Configurando para entorno local...")
        load_local_env()  # Cargar configuración local que anula Railway
        
        # Verificar PostgreSQL local
        local_detector = LocalEnvironmentDetector()
        if local_detector.detect_postgresql():
            print("   🏠 PostgreSQL local detectado y disponible")
            return DeploymentEnvironment.LOCAL
        
        # Si no hay nada disponible, intentar Railway de todas formas
        print("   ⚠️ No se detectó PostgreSQL local, intentando Railway...")
        return DeploymentEnvironment.RAILWAY
    
    def _deploy_railway(self) -> bool:
        """Ejecutar despliegue en Railway"""
        print("🚂 Ejecutando despliegue Railway...")
        
        try:
            railway_deployment = RailwayDatabaseDeployment()
            success = railway_deployment.run_intelligent_railway_deployment()
            
            if success:
                self.current_environment = DeploymentEnvironment.RAILWAY
                self.deployment = railway_deployment
                self.deployment_info = {
                    "environment": "railway",
                    "deployed_at": datetime.now().isoformat(),
                    "database_url": "***hidden***",
                    "features": ["auto_scaling", "backup", "monitoring"]
                }
                print("✅ Despliegue Railway exitoso")
                
                # Crear esquemas automáticamente
                self._create_database_schema()
            else:
                print("❌ Fallo en despliegue Railway")
            
            return success
            
        except Exception as e:
            print(f"❌ Error en despliegue Railway: {e}")
            return False
    
    def _deploy_local(self) -> bool:
        """Ejecutar despliegue local"""
        print("🏠 Ejecutando despliegue local...")
        
        try:
            local_deployment = LocalDatabaseDeployment()
            success = local_deployment.run_intelligent_deployment()
            
            if success:
                self.current_environment = DeploymentEnvironment.LOCAL
                self.deployment = local_deployment
                self.deployment_info = {
                    "environment": "local",
                    "deployed_at": datetime.now().isoformat(),
                    "postgresql_version": "detected",
                    "features": ["local_control", "custom_config", "development"]
                }
                print("✅ Despliegue local exitoso")
                
                # Crear esquemas automáticamente
                self._create_database_schema()
            else:
                print("❌ Fallo en despliegue local")
            
            return success
            
        except Exception as e:
            print(f"❌ Error en despliegue local: {e}")
            return False
    
    def _post_deployment_health_check(self):
        """Ejecutar chequeo de salud post-despliegue"""
        print("\n🔍 Ejecutando chequeo de salud post-despliegue...")
        
        try:
            # Crear monitor temporal para chequeo
            temp_monitor = DatabaseMonitor()
            if temp_monitor._initialize_database_connection():
                temp_monitor._perform_health_check()
                print("✅ Chequeo de salud completado")
            else:
                print("⚠️ No se pudo realizar chequeo de salud")
        except Exception as e:
            print(f"⚠️ Error en chequeo de salud: {e}")
    
    def start_monitoring(self) -> bool:
        """Iniciar monitoreo continuo"""
        if self.is_monitoring:
            print("⚠️ El monitoreo ya está activo")
            return True
        
        print("\n📊 Iniciando monitoreo continuo...")
        
        try:
            self.monitor = DatabaseMonitor()
            success = self.monitor.start_monitoring()
            
            if success:
                self.is_monitoring = True
                print("✅ Monitoreo continuo iniciado")
                
                # Configurar thread para mantener el monitoreo
                self._start_monitoring_thread()
            else:
                print("❌ Fallo al iniciar monitoreo")
            
            return success
            
        except Exception as e:
            print(f"❌ Error iniciando monitoreo: {e}")
            return False
    
    def stop_monitoring(self):
        """Detener monitoreo continuo"""
        if not self.is_monitoring:
            print("⚠️ El monitoreo no está activo")
            return
        
        print("🛑 Deteniendo monitoreo...")
        
        if self.monitor:
            self.monitor.stop_monitoring()
            self.is_monitoring = False
            print("✅ Monitoreo detenido")
    
    def _start_monitoring_thread(self):
        """Iniciar thread de monitoreo en background"""
        def monitoring_worker():
            """Worker thread para mantener monitoreo activo"""
            try:
                while self.is_monitoring and self.monitor and self.monitor.is_running:
                    time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"⚠️ Error en thread de monitoreo: {e}")
        
        monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        monitoring_thread.start()
    
    def generate_report(self, report_type: str = "executive", days: int = 7) -> bool:
        """
        Generar reporte
        
        Args:
            report_type: Tipo de reporte (executive, health, performance, alerts)
            days: Número de días a analizar
            
        Returns:
            True si el reporte se generó exitosamente
        """
        print(f"\n📊 Generando reporte {report_type} ({days} días)...")
        
        try:
            if not self.reporter:
                self.reporter = DatabaseReporter()
            
            if report_type == "executive":
                report_data = self.reporter.generate_executive_summary(days)
            elif report_type == "health":
                report_data = self.reporter.generate_health_summary(days)
            elif report_type == "performance":
                report_data = self.reporter.generate_performance_analysis(days)
            elif report_type == "alerts":
                report_data = self.reporter.generate_alert_analysis(days)
            else:
                print(f"❌ Tipo de reporte desconocido: {report_type}")
                return False
            
            # Exportar en múltiples formatos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON para procesamiento automático
            json_path = self.reporter.export_report(
                report_data, ReportFormat.JSON, f"{report_type}_{timestamp}"
            )
            
            # HTML para visualización
            html_path = self.reporter.export_report(
                report_data, ReportFormat.HTML, f"{report_type}_{timestamp}"
            )
            
            print(f"✅ Reporte generado:")
            print(f"   📄 JSON: {json_path}")
            print(f"   🌐 HTML: {html_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
            return False
    
    def _generate_initial_report(self):
        """Generar reporte inicial post-despliegue"""
        print("\n📋 Generando reporte inicial...")
        
        # Esperar un poco para que haya datos
        time.sleep(5)
        
        try:
            self.generate_report("executive", 1)  # Reporte del día actual
        except Exception as e:
            print(f"⚠️ Error generando reporte inicial: {e}")
    
    def _create_database_schema(self):
        """Crear esquema de base de datos automáticamente"""
        print("\n🔧 Verificando y creando esquema de base de datos...")
        
        try:
            # Importar aquí para evitar dependencias circulares
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from src.config.settings import DatabaseConfig
            from src.database.connection import DatabaseManager
            
            # Crear configuración y manager
            config = DatabaseConfig()
            db_manager = DatabaseManager(config)
            
            if db_manager.connect():
                schema_manager = SchemaManager(db_manager)
                
                # Verificar y crear esquema
                results = schema_manager.check_and_create_schema()
                
                # Mostrar resultados
                if results['tables_created']:
                    print(f"✅ Tablas creadas: {', '.join(results['tables_created'])}")
                
                if results['tables_existed']:
                    print(f"ℹ️ Tablas existentes: {', '.join(results['tables_existed'])}")
                
                if results['indexes_created']:
                    print(f"🔧 Índices creados: {len(results['indexes_created'])}")
                
                if results['triggers_created']:
                    print(f"⚙️ Triggers creados: {len(results['triggers_created'])}")
                
                if results['views_created']:
                    print(f"📊 Vistas creadas: {len(results['views_created'])}")
                
                if results['errors']:
                    print(f"⚠️ Errores durante creación: {len(results['errors'])}")
                    for error in results['errors']:
                        print(f"   - {error}")
                
                # Verificar integridad final
                integrity = schema_manager.verify_schema_integrity()
                print(f"🔍 Estado del esquema: {integrity['overall_status']}")
                
                if integrity['missing_tables']:
                    print(f"⚠️ Tablas faltantes: {', '.join(integrity['missing_tables'])}")
                
                db_manager.disconnect()
                print("✅ Verificación de esquema completada")
            else:
                print("❌ No se pudo conectar para verificar esquema")
                
        except Exception as e:
            print(f"❌ Error creando esquema: {e}")
            import traceback
            traceback.print_exc()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "deployment": {
                "is_deployed": self.is_deployed,
                "environment": self.current_environment,
                "deployment_info": self.deployment_info
            },
            "monitoring": {
                "is_active": self.is_monitoring,
                "monitor_status": self.monitor.get_status() if self.monitor else None
            },
            "configuration": self.config
        }
        
        return status
    
    def health_check(self) -> bool:
        """Ejecutar chequeo de salud manual"""
        print("🔍 Ejecutando chequeo de salud manual...")
        
        try:
            if not self.monitor:
                self.monitor = DatabaseMonitor()
            
            if self.monitor._initialize_database_connection():
                self.monitor._perform_health_check()
                print("✅ Chequeo de salud completado")
                return True
            else:
                print("❌ No se pudo conectar para chequeo de salud")
                return False
        except Exception as e:
            print(f"❌ Error en chequeo de salud: {e}")
            return False
    
    def repair_database(self) -> bool:
        """Ejecutar reparación manual de base de datos"""
        print("🔧 Ejecutando reparación manual...")
        
        try:
            if not self.monitor:
                self.monitor = DatabaseMonitor()
            
            if self.monitor._initialize_database_connection():
                # Ejecutar diagnóstico primero
                health_report = self.monitor.health_checker.run_full_diagnosis()
                
                # Ejecutar autoreparación
                self.monitor._perform_auto_repair(health_report)
                print("✅ Reparación completada")
                return True
            else:
                print("❌ No se pudo conectar para reparación")
                return False
        except Exception as e:
            print(f"❌ Error en reparación: {e}")
            return False
    
    def cleanup(self):
        """Limpiar recursos"""
        print("🧹 Limpiando recursos...")
        
        if self.is_monitoring:
            self.stop_monitoring()
        
        # Guardar estado final
        final_status = self.get_status()
        status_file = Path(__file__).parent / "logs" / "final_status.json"
        status_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(status_file, 'w') as f:
                json.dump(final_status, f, indent=2)
            print(f"📄 Estado final guardado: {status_file}")
        except Exception as e:
            print(f"⚠️ Error guardando estado final: {e}")
        
        print("✅ Limpieza completada")


def create_argument_parser():
    """Crear parser de argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Gestor Maestro de Base de Datos Inteligente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Despliegue automático (detecta mejor entorno)
  python intelligent_master_deploy.py deploy

  # Forzar despliegue en Railway
  python intelligent_master_deploy.py deploy --environment railway

  # Forzar despliegue local
  python intelligent_master_deploy.py deploy --environment local

  # Solo iniciar monitoreo (requiere DB ya desplegada)
  python intelligent_master_deploy.py monitor

  # Generar reporte ejecutivo
  python intelligent_master_deploy.py report --type executive --days 30

  # Chequeo de salud manual
  python intelligent_master_deploy.py health-check

  # Reparación manual
  python intelligent_master_deploy.py repair

  # Estado completo del sistema
  python intelligent_master_deploy.py status

  # Despliegue completo con monitoreo
  python intelligent_master_deploy.py full-deploy
        """
    )
    
    # Comando principal
    parser.add_argument(
        "command",
        choices=["deploy", "monitor", "report", "health-check", "repair", "status", "full-deploy"],
        help="Comando a ejecutar"
    )
    
    # Opciones de despliegue
    parser.add_argument(
        "--environment", "-e",
        choices=["auto", "railway", "local"],
        default="auto",
        help="Entorno de despliegue (default: auto)"
    )
    
    # Opciones de reporte
    parser.add_argument(
        "--type", "-t",
        choices=["executive", "health", "performance", "alerts"],
        default="executive",
        help="Tipo de reporte (default: executive)"
    )
    
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=7,
        help="Días a analizar en reportes (default: 7)"
    )
    
    # Opciones generales
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="No iniciar monitoreo automático tras despliegue"
    )
    
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="No generar reportes automáticos"
    )
    
    parser.add_argument(
        "--config",
        help="Ruta a archivo de configuración personalizado"
    )
    
    return parser


def main():
    """Función principal"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Crear gestor maestro
        manager = IntelligentDatabaseManager(args.environment)
        
        # Actualizar configuración según argumentos
        if args.no_monitor:
            manager.config["auto_monitor"] = False
        if args.no_reports:
            manager.config["auto_reports"] = False
        
        # Ejecutar comando
        success = True
        
        if args.command == "deploy":
            success = manager.deploy()
            
        elif args.command == "monitor":
            success = manager.start_monitoring()
            if success:
                print("💡 Presiona Ctrl+C para detener el monitoreo...")
                try:
                    while manager.is_monitoring:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Deteniendo monitoreo...")
                    manager.stop_monitoring()
        
        elif args.command == "report":
            success = manager.generate_report(args.type, args.days)
        
        elif args.command == "health-check":
            success = manager.health_check()
        
        elif args.command == "repair":
            success = manager.repair_database()
        
        elif args.command == "status":
            status = manager.get_status()
            print("\n📊 ESTADO DEL SISTEMA")
            print("=" * 50)
            print(json.dumps(status, indent=2))
            
        elif args.command == "full-deploy":
            print("🚀 DESPLIEGUE COMPLETO INICIADO")
            print("=" * 50)
            
            # Despliegue
            success = manager.deploy()
            
            if success:
                print("\n⏳ Esperando estabilización del sistema...")
                time.sleep(10)
                
                # Generar reporte inicial
                manager.generate_report("executive", 1)
                
                # Mostrar estado
                status = manager.get_status()
                print(f"\n✅ DESPLIEGUE COMPLETO EXITOSO")
                print(f"   🎯 Entorno: {status['deployment']['environment'].upper()}")
                print(f"   📊 Monitoreo: {'ACTIVO' if status['monitoring']['is_active'] else 'INACTIVO'}")
                print(f"   🕐 Desplegado: {status['deployment']['deployment_info'].get('deployed_at', 'N/A')}")
                
                if manager.is_monitoring:
                    print("\n💡 El sistema está ejecutándose. Presiona Ctrl+C para detener...")
                    try:
                        while manager.is_monitoring:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n🛑 Deteniendo sistema...")
        
        # Cleanup
        manager.cleanup()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Operación cancelada por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())