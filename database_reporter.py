#!/usr/bin/env python3
"""
Sistema de Reportes Avanzado
============================

Este módulo proporciona:
- Generación de reportes detallados
- Análisis de tendencias y métricas
- Reportes visuales (ASCII charts)
- Alertas inteligentes
- Recomendaciones automáticas
- Exportación en múltiples formatos
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.utils.database_health import HealthStatus
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)


class ReportType(Enum):
    """Tipos de reporte"""
    HEALTH_SUMMARY = "health_summary"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    TREND_ANALYSIS = "trend_analysis"
    ALERT_ANALYSIS = "alert_analysis"
    MAINTENANCE_REPORT = "maintenance_report"
    EXECUTIVE_SUMMARY = "executive_summary"


class ReportFormat(Enum):
    """Formatos de reporte"""
    JSON = "json"
    HTML = "html"
    TXT = "txt"
    CSV = "csv"
    MARKDOWN = "md"


@dataclass
class MetricData:
    """Datos de métricas"""
    timestamp: datetime
    name: str
    value: float
    unit: str
    status: HealthStatus


@dataclass
class TrendAnalysis:
    """Análisis de tendencias"""
    metric_name: str
    period_days: int
    average: float
    median: float
    min_value: float
    max_value: float
    trend_direction: str  # "up", "down", "stable"
    change_percentage: float
    is_concerning: bool
    recommendation: str


@dataclass
class AlertSummary:
    """Resumen de alertas"""
    total_alerts: int
    critical_count: int
    warning_count: int
    info_count: int
    resolved_count: int
    average_resolution_time: Optional[float]
    most_common_alert: str
    alert_frequency_trend: str


class DatabaseReporter:
    """Generador de reportes de base de datos"""
    
    def __init__(self, logs_path: Optional[Path] = None):
        """
        Inicializar el generador de reportes
        
        Args:
            logs_path: Ruta a los logs (opcional)
        """
        self.logs_path = logs_path or Path(__file__).parent / "logs"
        self.reports_path = self.logs_path / "reports"
        self.reports_path.mkdir(exist_ok=True)
        
        # Configuración de reportes
        self.config = {
            "trend_analysis_days": 7,
            "performance_threshold_ms": 1000,
            "concerning_change_threshold": 20.0,  # Porcentaje
            "include_raw_data": False
        }
    
    def generate_health_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Generar resumen de salud
        
        Args:
            days: Número de días a analizar
            
        Returns:
            Dict con resumen de salud
        """
        print(f"📊 Generando resumen de salud ({days} días)...")
        
        # Cargar datos de salud
        health_data = self._load_health_data(days)
        
        if not health_data:
            return {"error": "No hay datos de salud disponibles"}
        
        # Calcular métricas
        total_checks = len(health_data)
        healthy_checks = len([d for d in health_data if d.get("overall_status") == "HEALTHY"])
        warning_checks = len([d for d in health_data if d.get("overall_status") == "WARNING"])
        critical_checks = len([d for d in health_data if d.get("overall_status") == "CRITICAL"])
        
        uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Análisis por categorías
        category_analysis = self._analyze_health_categories(health_data)
        
        # Análisis de tiempo de respuesta
        response_times = self._extract_response_times(health_data)
        response_analysis = self._analyze_response_times(response_times)
        
        summary = {
            "period": {
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat(),
                "days": days
            },
            "overview": {
                "total_checks": total_checks,
                "uptime_percentage": round(uptime_percentage, 2),
                "healthy_checks": healthy_checks,
                "warning_checks": warning_checks,
                "critical_checks": critical_checks
            },
            "health_distribution": {
                "healthy": round((healthy_checks / total_checks * 100), 1) if total_checks > 0 else 0,
                "warning": round((warning_checks / total_checks * 100), 1) if total_checks > 0 else 0,
                "critical": round((critical_checks / total_checks * 100), 1) if total_checks > 0 else 0
            },
            "category_analysis": category_analysis,
            "response_analysis": response_analysis,
            "generated_at": datetime.now().isoformat()
        }
        
        return summary
    
    def generate_performance_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Generar análisis de rendimiento"""
        print(f"📈 Generando análisis de rendimiento ({days} días)...")
        
        # Cargar datos de rendimiento
        health_data = self._load_health_data(days)
        
        if not health_data:
            return {"error": "No hay datos de rendimiento disponibles"}
        
        # Extraer métricas de rendimiento
        connection_times = []
        query_times = []
        memory_usage = []
        
        for data in health_data:
            if "checks" in data:
                for check in data["checks"]:
                    details = check.get("details", {})
                    
                    if "connection_time_ms" in details:
                        connection_times.append(details["connection_time_ms"])
                    
                    if "query_time_ms" in details:
                        query_times.append(details["query_time_ms"])
                    
                    if "memory_usage_mb" in details:
                        memory_usage.append(details["memory_usage_mb"])
        
        analysis = {
            "period": {
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat(),
                "days": days
            },
            "connection_performance": self._analyze_metric_list(connection_times, "ms", "connection_time"),
            "query_performance": self._analyze_metric_list(query_times, "ms", "query_time"),
            "memory_usage": self._analyze_metric_list(memory_usage, "MB", "memory"),
            "recommendations": self._generate_performance_recommendations(connection_times, query_times, memory_usage),
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis
    
    def generate_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Generar análisis de tendencias"""
        print(f"📊 Generando análisis de tendencias ({days} días)...")
        
        # Cargar datos históricos
        health_data = self._load_health_data(days)
        alert_data = self._load_alert_data(days)
        
        if not health_data:
            return {"error": "No hay datos suficientes para análisis de tendencias"}
        
        # Agrupar datos por día
        daily_metrics = self._group_data_by_day(health_data)
        
        # Analizar tendencias
        trends = []
        
        # Tendencia de uptime
        uptime_trend = self._analyze_uptime_trend(daily_metrics)
        trends.append(uptime_trend)
        
        # Tendencia de alertas
        alert_trend = self._analyze_alert_trend(alert_data)
        trends.append(alert_trend)
        
        # Tendencia de rendimiento
        performance_trend = self._analyze_performance_trend(daily_metrics)
        trends.append(performance_trend)
        
        analysis = {
            "period": {
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat(),
                "days": days
            },
            "trends": trends,
            "summary": self._summarize_trends(trends),
            "predictions": self._generate_predictions(trends),
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis
    
    def generate_alert_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Generar análisis de alertas"""
        print(f"🚨 Generando análisis de alertas ({days} días)...")
        
        alert_data = self._load_alert_data(days)
        
        if not alert_data:
            return {"error": "No hay datos de alertas disponibles"}
        
        # Contar alertas por tipo
        alert_counts = {"critical": 0, "warning": 0, "info": 0}
        resolved_alerts = 0
        resolution_times = []
        alert_types = {}
        
        for alert in alert_data:
            level = alert.get("level", "info")
            alert_counts[level] = alert_counts.get(level, 0) + 1
            
            # Contar tipos de alerta
            title = alert.get("title", "Unknown")
            alert_types[title] = alert_types.get(title, 0) + 1
            
            # Calcular tiempo de resolución si está resuelto
            if alert.get("resolved", False) and alert.get("resolution_timestamp"):
                try:
                    created = datetime.fromisoformat(alert["timestamp"])
                    resolved = datetime.fromisoformat(alert["resolution_timestamp"])
                    resolution_time = (resolved - created).total_seconds() / 60  # minutos
                    resolution_times.append(resolution_time)
                    resolved_alerts += 1
                except:
                    pass
        
        # Alerta más común
        most_common_alert = max(alert_types.items(), key=lambda x: x[1])[0] if alert_types else "None"
        
        # Tiempo promedio de resolución
        avg_resolution_time = statistics.mean(resolution_times) if resolution_times else None
        
        analysis = {
            "period": {
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat(),
                "days": days
            },
            "summary": {
                "total_alerts": len(alert_data),
                "critical_count": alert_counts.get("critical", 0),
                "warning_count": alert_counts.get("warning", 0),
                "info_count": alert_counts.get("info", 0),
                "resolved_count": resolved_alerts,
                "resolution_rate": round((resolved_alerts / len(alert_data) * 100), 1) if alert_data else 0
            },
            "alert_types": dict(sorted(alert_types.items(), key=lambda x: x[1], reverse=True)),
            "most_common_alert": most_common_alert,
            "resolution_metrics": {
                "average_resolution_time_minutes": round(avg_resolution_time, 1) if avg_resolution_time else None,
                "total_resolved": resolved_alerts
            },
            "recommendations": self._generate_alert_recommendations(alert_data, alert_types),
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis
    
    def generate_executive_summary(self, days: int = 30) -> Dict[str, Any]:
        """Generar resumen ejecutivo"""
        print(f"📋 Generando resumen ejecutivo ({days} días)...")
        
        # Generar sub-reportes
        health_summary = self.generate_health_summary(days)
        performance_analysis = self.generate_performance_analysis(days)
        alert_analysis = self.generate_alert_analysis(days)
        
        # Calcular métricas clave
        key_metrics = {
            "uptime_percentage": health_summary.get("overview", {}).get("uptime_percentage", 0),
            "total_checks": health_summary.get("overview", {}).get("total_checks", 0),
            "total_alerts": alert_analysis.get("summary", {}).get("total_alerts", 0),
            "critical_alerts": alert_analysis.get("summary", {}).get("critical_count", 0),
            "resolution_rate": alert_analysis.get("summary", {}).get("resolution_rate", 0)
        }
        
        # Determinar estado general
        overall_status = self._determine_overall_status(key_metrics)
        
        # Generar recomendaciones principales
        top_recommendations = self._generate_top_recommendations(
            health_summary, performance_analysis, alert_analysis
        )
        
        summary = {
            "report_type": "executive_summary",
            "period": {
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat(),
                "days": days
            },
            "overall_status": overall_status,
            "key_metrics": key_metrics,
            "health_score": self._calculate_health_score(key_metrics),
            "top_issues": self._identify_top_issues(alert_analysis),
            "top_recommendations": top_recommendations,
            "system_stability": self._assess_system_stability(health_summary, alert_analysis),
            "generated_at": datetime.now().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return summary
    
    def export_report(self, report_data: Dict[str, Any], format_type: ReportFormat, 
                     filename: Optional[str] = None) -> Path:
        """
        Exportar reporte en formato específico
        
        Args:
            report_data: Datos del reporte
            format_type: Formato de exportación
            filename: Nombre del archivo (opcional)
            
        Returns:
            Path del archivo generado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_type = report_data.get("report_type", "report")
            filename = f"{report_type}_{timestamp}"
        
        file_path = self.reports_path / f"{filename}.{format_type.value}"
        
        if format_type == ReportFormat.JSON:
            self._export_json(report_data, file_path)
        elif format_type == ReportFormat.HTML:
            self._export_html(report_data, file_path)
        elif format_type == ReportFormat.TXT:
            self._export_txt(report_data, file_path)
        elif format_type == ReportFormat.CSV:
            self._export_csv(report_data, file_path)
        elif format_type == ReportFormat.MARKDOWN:
            self._export_markdown(report_data, file_path)
        
        print(f"✅ Reporte exportado: {file_path}")
        return file_path
    
    def _load_health_data(self, days: int) -> List[Dict[str, Any]]:
        """Cargar datos de salud de los últimos días"""
        health_reports_dir = self.logs_path / "health_reports"
        
        if not health_reports_dir.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        health_data = []
        
        for file_path in health_reports_dir.glob("health_*.json"):
            try:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time >= cutoff_date:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        health_data.append(data)
            except Exception:
                continue
        
        return sorted(health_data, key=lambda x: x.get("timestamp", ""))
    
    def _load_alert_data(self, days: int) -> List[Dict[str, Any]]:
        """Cargar datos de alertas de los últimos días"""
        alerts_dir = self.logs_path / "alerts"
        
        if not alerts_dir.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        alert_data = []
        
        for file_path in alerts_dir.glob("alerts_*.json"):
            try:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time >= cutoff_date:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            alert_data.extend(data)
                        else:
                            alert_data.append(data)
            except Exception:
                continue
        
        return alert_data
    
    def _analyze_health_categories(self, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar salud por categorías"""
        categories = {}
        
        for data in health_data:
            if "checks" in data:
                for check in data["checks"]:
                    category = check.get("category", "unknown")
                    status = check.get("status", "unknown")
                    
                    if category not in categories:
                        categories[category] = {"total": 0, "healthy": 0, "warning": 0, "critical": 0}
                    
                    categories[category]["total"] += 1
                    
                    if status == "HEALTHY":
                        categories[category]["healthy"] += 1
                    elif status == "WARNING":
                        categories[category]["warning"] += 1
                    elif status == "CRITICAL":
                        categories[category]["critical"] += 1
        
        # Calcular porcentajes
        for category, stats in categories.items():
            total = stats["total"]
            if total > 0:
                stats["health_percentage"] = round((stats["healthy"] / total * 100), 1)
        
        return categories
    
    def _extract_response_times(self, health_data: List[Dict[str, Any]]) -> List[float]:
        """Extraer tiempos de respuesta"""
        response_times = []
        
        for data in health_data:
            if "response_time_ms" in data:
                response_times.append(data["response_time_ms"])
        
        return response_times
    
    def _analyze_response_times(self, response_times: List[float]) -> Dict[str, Any]:
        """Analizar tiempos de respuesta"""
        if not response_times:
            return {"error": "No hay datos de tiempo de respuesta"}
        
        return {
            "average_ms": round(statistics.mean(response_times), 2),
            "median_ms": round(statistics.median(response_times), 2),
            "min_ms": round(min(response_times), 2),
            "max_ms": round(max(response_times), 2),
            "total_samples": len(response_times),
            "performance_grade": self._grade_performance(statistics.mean(response_times))
        }
    
    def _analyze_metric_list(self, values: List[float], unit: str, metric_name: str) -> Dict[str, Any]:
        """Analizar lista de métricas"""
        if not values:
            return {"error": f"No hay datos para {metric_name}"}
        
        analysis = {
            "average": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "unit": unit,
            "samples": len(values)
        }
        
        # Agregar desviación estándar si hay suficientes datos
        if len(values) > 1:
            analysis["std_deviation"] = round(statistics.stdev(values), 2)
        
        return analysis
    
    def _generate_performance_recommendations(self, connection_times: List[float], 
                                           query_times: List[float], 
                                           memory_usage: List[float]) -> List[str]:
        """Generar recomendaciones de rendimiento"""
        recommendations = []
        
        # Analizar tiempo de conexión
        if connection_times:
            avg_connection = statistics.mean(connection_times)
            if avg_connection > 1000:  # > 1 segundo
                recommendations.append("Tiempo de conexión alto. Considerar optimización de red o pool de conexiones.")
        
        # Analizar tiempo de consultas
        if query_times:
            avg_query = statistics.mean(query_times)
            if avg_query > 500:  # > 500ms
                recommendations.append("Consultas lentas detectadas. Revisar índices y optimizar consultas.")
        
        # Analizar uso de memoria
        if memory_usage:
            avg_memory = statistics.mean(memory_usage)
            if avg_memory > 1024:  # > 1GB
                recommendations.append("Alto uso de memoria. Considerar ajustar configuración de PostgreSQL.")
        
        if not recommendations:
            recommendations.append("Rendimiento dentro de parámetros normales.")
        
        return recommendations
    
    def _grade_performance(self, avg_response_time: float) -> str:
        """Calificar rendimiento basado en tiempo de respuesta"""
        if avg_response_time < 100:
            return "Excellent"
        elif avg_response_time < 500:
            return "Good"
        elif avg_response_time < 1000:
            return "Fair"
        else:
            return "Poor"
    
    def _group_data_by_day(self, health_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupar datos por día"""
        daily_data = {}
        
        for data in health_data:
            timestamp_str = data.get("timestamp", "")
            if timestamp_str:
                try:
                    date = datetime.fromisoformat(timestamp_str).date()
                    date_str = date.isoformat()
                    
                    if date_str not in daily_data:
                        daily_data[date_str] = []
                    
                    daily_data[date_str].append(data)
                except:
                    continue
        
        return daily_data
    
    def _analyze_uptime_trend(self, daily_metrics: Dict[str, List[Dict[str, Any]]]) -> TrendAnalysis:
        """Analizar tendencia de uptime"""
        daily_uptimes = []
        
        for date, day_data in daily_metrics.items():
            healthy_count = len([d for d in day_data if d.get("overall_status") == "HEALTHY"])
            total_count = len(day_data)
            uptime = (healthy_count / total_count * 100) if total_count > 0 else 0
            daily_uptimes.append(uptime)
        
        if len(daily_uptimes) < 2:
            return TrendAnalysis(
                metric_name="uptime",
                period_days=len(daily_uptimes),
                average=daily_uptimes[0] if daily_uptimes else 0,
                median=daily_uptimes[0] if daily_uptimes else 0,
                min_value=daily_uptimes[0] if daily_uptimes else 0,
                max_value=daily_uptimes[0] if daily_uptimes else 0,
                trend_direction="stable",
                change_percentage=0,
                is_concerning=False,
                recommendation="Datos insuficientes para análisis de tendencia"
            )
        
        # Calcular tendencia
        first_half = daily_uptimes[:len(daily_uptimes)//2]
        second_half = daily_uptimes[len(daily_uptimes)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        if abs(change) < 5:
            trend_direction = "stable"
        elif change > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"
        
        is_concerning = change < -10  # Disminución de más del 10%
        
        recommendation = "Mantener monitoreo" if not is_concerning else "Investigar causa de degradación"
        
        return TrendAnalysis(
            metric_name="uptime",
            period_days=len(daily_metrics),
            average=round(statistics.mean(daily_uptimes), 2),
            median=round(statistics.median(daily_uptimes), 2),
            min_value=round(min(daily_uptimes), 2),
            max_value=round(max(daily_uptimes), 2),
            trend_direction=trend_direction,
            change_percentage=round(change, 2),
            is_concerning=is_concerning,
            recommendation=recommendation
        )
    
    def _analyze_alert_trend(self, alert_data: List[Dict[str, Any]]) -> TrendAnalysis:
        """Analizar tendencia de alertas"""
        # Agrupar alertas por día
        daily_alerts = {}
        
        for alert in alert_data:
            timestamp_str = alert.get("timestamp", "")
            if timestamp_str:
                try:
                    date = datetime.fromisoformat(timestamp_str).date()
                    date_str = date.isoformat()
                    
                    if date_str not in daily_alerts:
                        daily_alerts[date_str] = 0
                    
                    daily_alerts[date_str] += 1
                except:
                    continue
        
        if not daily_alerts:
            return TrendAnalysis(
                metric_name="alerts",
                period_days=0,
                average=0,
                median=0,
                min_value=0,
                max_value=0,
                trend_direction="stable",
                change_percentage=0,
                is_concerning=False,
                recommendation="Sin alertas en el período"
            )
        
        alert_counts = list(daily_alerts.values())
        
        # Si solo hay un día de datos
        if len(alert_counts) < 2:
            return TrendAnalysis(
                metric_name="alerts",
                period_days=len(alert_counts),
                average=alert_counts[0],
                median=alert_counts[0],
                min_value=alert_counts[0],
                max_value=alert_counts[0],
                trend_direction="stable",
                change_percentage=0,
                is_concerning=alert_counts[0] > 10,
                recommendation="Datos insuficientes para análisis de tendencia"
            )
        
        # Calcular tendencia
        first_half = alert_counts[:len(alert_counts)//2]
        second_half = alert_counts[len(alert_counts)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        if abs(change) < 20:
            trend_direction = "stable"
        elif change > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"
        
        is_concerning = change > 50 or statistics.mean(alert_counts) > 20
        
        if trend_direction == "up":
            recommendation = "Incremento de alertas detectado. Revisar causas."
        elif is_concerning:
            recommendation = "Nivel alto de alertas. Acción requerida."
        else:
            recommendation = "Nivel de alertas normal."
        
        return TrendAnalysis(
            metric_name="alerts",
            period_days=len(daily_alerts),
            average=round(statistics.mean(alert_counts), 2),
            median=round(statistics.median(alert_counts), 2),
            min_value=min(alert_counts),
            max_value=max(alert_counts),
            trend_direction=trend_direction,
            change_percentage=round(change, 2),
            is_concerning=is_concerning,
            recommendation=recommendation
        )
    
    def _analyze_performance_trend(self, daily_metrics: Dict[str, List[Dict[str, Any]]]) -> TrendAnalysis:
        """Analizar tendencia de rendimiento"""
        daily_response_times = []
        
        for date, day_data in daily_metrics.items():
            response_times = []
            for data in day_data:
                if "response_time_ms" in data:
                    response_times.append(data["response_time_ms"])
            
            if response_times:
                daily_avg = statistics.mean(response_times)
                daily_response_times.append(daily_avg)
        
        if len(daily_response_times) < 2:
            avg_time = daily_response_times[0] if daily_response_times else 0
            return TrendAnalysis(
                metric_name="response_time",
                period_days=len(daily_response_times),
                average=avg_time,
                median=avg_time,
                min_value=avg_time,
                max_value=avg_time,
                trend_direction="stable",
                change_percentage=0,
                is_concerning=avg_time > 1000,
                recommendation="Datos insuficientes para análisis de tendencia"
            )
        
        # Calcular tendencia
        first_half = daily_response_times[:len(daily_response_times)//2]
        second_half = daily_response_times[len(daily_response_times)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        if abs(change) < 10:
            trend_direction = "stable"
        elif change > 0:
            trend_direction = "up"  # Empeorando
        else:
            trend_direction = "down"  # Mejorando
        
        avg_time = statistics.mean(daily_response_times)
        is_concerning = change > 25 or avg_time > 1000
        
        if trend_direction == "up":
            recommendation = "Degradación de rendimiento detectada."
        elif is_concerning:
            recommendation = "Tiempo de respuesta alto. Optimización requerida."
        else:
            recommendation = "Rendimiento estable."
        
        return TrendAnalysis(
            metric_name="response_time",
            period_days=len(daily_metrics),
            average=round(statistics.mean(daily_response_times), 2),
            median=round(statistics.median(daily_response_times), 2),
            min_value=round(min(daily_response_times), 2),
            max_value=round(max(daily_response_times), 2),
            trend_direction=trend_direction,
            change_percentage=round(change, 2),
            is_concerning=is_concerning,
            recommendation=recommendation
        )
    
    def _summarize_trends(self, trends: List[TrendAnalysis]) -> Dict[str, Any]:
        """Resumir análisis de tendencias"""
        concerning_trends = [t for t in trends if t.is_concerning]
        improving_trends = [t for t in trends if t.trend_direction == "down" and t.metric_name != "alerts"]
        degrading_trends = [t for t in trends if t.trend_direction == "up" and t.metric_name != "response_time"]
        
        return {
            "total_metrics_analyzed": len(trends),
            "concerning_trends": len(concerning_trends),
            "improving_trends": len(improving_trends),
            "degrading_trends": len(degrading_trends),
            "overall_trend": "concerning" if concerning_trends else "stable",
            "key_concerns": [t.metric_name for t in concerning_trends]
        }
    
    def _generate_predictions(self, trends: List[TrendAnalysis]) -> Dict[str, Any]:
        """Generar predicciones basadas en tendencias"""
        predictions = {}
        
        for trend in trends:
            if trend.period_days >= 7 and abs(trend.change_percentage) > 5:
                # Predicción simple basada en tendencia lineal
                if trend.trend_direction == "up" and trend.metric_name == "alerts":
                    predictions[f"{trend.metric_name}_forecast"] = "Incremento de alertas esperado en próximos días"
                elif trend.trend_direction == "up" and trend.metric_name == "response_time":
                    predictions[f"{trend.metric_name}_forecast"] = "Posible degradación de rendimiento"
                elif trend.trend_direction == "down" and trend.metric_name == "uptime":
                    predictions[f"{trend.metric_name}_forecast"] = "Riesgo de reducción en disponibilidad"
        
        if not predictions:
            predictions["overall"] = "Tendencias estables, no se esperan cambios significativos"
        
        return predictions
    
    def _generate_alert_recommendations(self, alert_data: List[Dict[str, Any]], 
                                      alert_types: Dict[str, int]) -> List[str]:
        """Generar recomendaciones basadas en alertas"""
        recommendations = []
        
        # Analizar tipos más comunes
        if alert_types:
            most_common = max(alert_types.items(), key=lambda x: x[1])
            if most_common[1] > 5:
                recommendations.append(f"Alerta más frecuente: '{most_common[0]}'. Considerar solución preventiva.")
        
        # Analizar alertas críticas
        critical_count = len([a for a in alert_data if a.get("level") == "critical"])
        if critical_count > 3:
            recommendations.append(f"{critical_count} alertas críticas detectadas. Revisión urgente requerida.")
        
        # Analizar resolución
        unresolved = len([a for a in alert_data if not a.get("resolved", False)])
        if unresolved > 0:
            recommendations.append(f"{unresolved} alertas sin resolver. Revisar y cerrar alertas pendientes.")
        
        if not recommendations:
            recommendations.append("Gestión de alertas en buen estado.")
        
        return recommendations
    
    def _determine_overall_status(self, key_metrics: Dict[str, Any]) -> str:
        """Determinar estado general del sistema"""
        uptime = key_metrics.get("uptime_percentage", 0)
        critical_alerts = key_metrics.get("critical_alerts", 0)
        
        if uptime >= 99 and critical_alerts == 0:
            return "Excellent"
        elif uptime >= 95 and critical_alerts <= 2:
            return "Good"
        elif uptime >= 90 and critical_alerts <= 5:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_top_recommendations(self, health_summary: Dict[str, Any], 
                                    performance_analysis: Dict[str, Any], 
                                    alert_analysis: Dict[str, Any]) -> List[str]:
        """Generar principales recomendaciones"""
        recommendations = []
        
        # Basado en uptime
        uptime = health_summary.get("overview", {}).get("uptime_percentage", 0)
        if uptime < 95:
            recommendations.append("PRIORIDAD ALTA: Mejorar estabilidad del sistema (uptime < 95%)")
        
        # Basado en alertas críticas
        critical_alerts = alert_analysis.get("summary", {}).get("critical_count", 0)
        if critical_alerts > 0:
            recommendations.append(f"ACCIÓN REQUERIDA: Resolver {critical_alerts} alertas críticas pendientes")
        
        # Basado en rendimiento
        if "connection_performance" in performance_analysis:
            avg_conn = performance_analysis["connection_performance"].get("average_ms", 0)
            if avg_conn > 1000:
                recommendations.append("OPTIMIZACIÓN: Mejorar tiempo de conexión (>1 segundo)")
        
        # Recomendación de monitoreo
        if len(recommendations) == 0:
            recommendations.append("Sistema estable. Mantener monitoreo regular.")
        
        return recommendations[:5]  # Top 5 recomendaciones
    
    def _identify_top_issues(self, alert_analysis: Dict[str, Any]) -> List[str]:
        """Identificar principales problemas"""
        issues = []
        
        alert_types = alert_analysis.get("alert_types", {})
        for alert_type, count in list(alert_types.items())[:3]:  # Top 3
            issues.append(f"{alert_type} ({count} ocurrencias)")
        
        return issues
    
    def _assess_system_stability(self, health_summary: Dict[str, Any], 
                               alert_analysis: Dict[str, Any]) -> str:
        """Evaluar estabilidad del sistema"""
        uptime = health_summary.get("overview", {}).get("uptime_percentage", 0)
        critical_alerts = alert_analysis.get("summary", {}).get("critical_count", 0)
        total_alerts = alert_analysis.get("summary", {}).get("total_alerts", 0)
        
        if uptime >= 99.5 and critical_alerts == 0 and total_alerts < 10:
            return "Very Stable"
        elif uptime >= 99 and critical_alerts <= 1 and total_alerts < 20:
            return "Stable"
        elif uptime >= 95 and critical_alerts <= 3 and total_alerts < 50:
            return "Moderately Stable"
        else:
            return "Unstable"
    
    def _calculate_health_score(self, key_metrics: Dict[str, Any]) -> int:
        """Calcular puntuación de salud (0-100)"""
        uptime = key_metrics.get("uptime_percentage", 0)
        critical_alerts = key_metrics.get("critical_alerts", 0)
        resolution_rate = key_metrics.get("resolution_rate", 0)
        
        # Puntuación base según uptime
        base_score = min(uptime, 100)
        
        # Penalización por alertas críticas
        critical_penalty = min(critical_alerts * 10, 30)
        
        # Bonificación por tasa de resolución
        resolution_bonus = (resolution_rate / 100) * 10
        
        final_score = max(0, base_score - critical_penalty + resolution_bonus)
        
        return int(min(final_score, 100))
    
    def _export_json(self, data: Dict[str, Any], file_path: Path):
        """Exportar como JSON"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_html(self, data: Dict[str, Any], file_path: Path):
        """Exportar como HTML"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Database Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
        .metric {{ margin: 10px 0; padding: 5px; background: #f9f9f9; }}
        .critical {{ color: red; }}
        .warning {{ color: orange; }}
        .success {{ color: green; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Database Report</h1>
        <p>Generated: {data.get('generated_at', 'N/A')}</p>
    </div>
    
    <h2>Summary</h2>
    <pre>{json.dumps(data, indent=2)}</pre>
</body>
</html>
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_txt(self, data: Dict[str, Any], file_path: Path):
        """Exportar como texto plano"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("DATABASE REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Generated: {data.get('generated_at', 'N/A')}\n\n")
            
            # Escribir contenido de manera legible
            self._write_dict_as_text(data, f, 0)
    
    def _export_csv(self, data: Dict[str, Any], file_path: Path):
        """Exportar como CSV (métricas principales)"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow(['Metric', 'Value', 'Timestamp'])
            
            # Escribir métricas clave
            timestamp = data.get('generated_at', '')
            
            if 'key_metrics' in data:
                for key, value in data['key_metrics'].items():
                    writer.writerow([key, value, timestamp])
    
    def _export_markdown(self, data: Dict[str, Any], file_path: Path):
        """Exportar como Markdown"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Database Report\n\n")
            f.write(f"**Generated:** {data.get('generated_at', 'N/A')}\n\n")
            
            # Escribir secciones principales
            if 'overall_status' in data:
                f.write(f"## Overall Status: {data['overall_status']}\n\n")
            
            if 'key_metrics' in data:
                f.write("## Key Metrics\n\n")
                for key, value in data['key_metrics'].items():
                    f.write(f"- **{key}:** {value}\n")
                f.write("\n")
            
            if 'top_recommendations' in data:
                f.write("## Top Recommendations\n\n")
                for i, rec in enumerate(data['top_recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")
    
    def _write_dict_as_text(self, data: Any, file, indent: int):
        """Escribir diccionario como texto con indentación"""
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                file.write(f"{prefix}{key}:\n")
                self._write_dict_as_text(value, file, indent + 1)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                file.write(f"{prefix}[{i}]:\n")
                self._write_dict_as_text(item, file, indent + 1)
        else:
            file.write(f"{prefix}{data}\n")


def main():
    """Función principal para generar reportes"""
    print("📊 Generador de Reportes de Base de Datos")
    print("=" * 50)
    
    reporter = DatabaseReporter()
    
    try:
        # Generar resumen ejecutivo
        print("\n🎯 Generando resumen ejecutivo...")
        executive_summary = reporter.generate_executive_summary(30)
        
        # Exportar en múltiples formatos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_path = reporter.export_report(executive_summary, ReportFormat.JSON, f"executive_summary_{timestamp}")
        
        # HTML
        html_path = reporter.export_report(executive_summary, ReportFormat.HTML, f"executive_summary_{timestamp}")
        
        # Markdown
        md_path = reporter.export_report(executive_summary, ReportFormat.MARKDOWN, f"executive_summary_{timestamp}")
        
        print(f"\n✅ Reportes generados:")
        print(f"   📄 JSON: {json_path}")
        print(f"   🌐 HTML: {html_path}")
        print(f"   📝 Markdown: {md_path}")
        
        # Mostrar resumen en consola
        print(f"\n📋 RESUMEN EJECUTIVO")
        print(f"   Estado General: {executive_summary.get('overall_status', 'N/A')}")
        print(f"   Puntuación de Salud: {executive_summary.get('health_score', 'N/A')}/100")
        print(f"   Estabilidad: {executive_summary.get('system_stability', 'N/A')}")
        
        if 'top_recommendations' in executive_summary:
            print(f"\n🎯 PRINCIPALES RECOMENDACIONES:")
            for i, rec in enumerate(executive_summary['top_recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        
    except Exception as e:
        print(f"❌ Error generando reportes: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())