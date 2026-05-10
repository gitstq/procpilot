"""
ProcPilot Alerts Module - Intelligent Alert System
智能告警系统模块
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """告警类型"""
    CPU_HIGH = "cpu_high"
    MEMORY_HIGH = "memory_high"
    PROCESS_ZOMBIE = "process_zombie"
    PROCESS_CRASHED = "process_crashed"
    PROCESS_STARTED = "process_started"
    PROCESS_STOPPED = "process_stopped"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CUSTOM = "custom"


@dataclass
class Alert:
    """告警数据类"""
    id: str
    alert_type: AlertType
    level: AlertLevel
    message: str
    pid: Optional[int] = None
    process_name: str = ""
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "alert_type": self.alert_type.value,
            "level": self.level.value,
            "message": self.message,
            "pid": self.pid,
            "process_name": self.process_name,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
            "details": self.details,
        }


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    alert_type: AlertType
    condition: Callable[[Any], bool]
    level: AlertLevel = AlertLevel.WARNING
    cooldown: float = 60.0  # 冷却时间（秒）
    enabled: bool = True
    last_triggered: float = 0


class AlertManager:
    """
    告警管理器
    
    提供告警规则管理、告警触发、告警通知等功能
    """
    
    def __init__(self):
        self._alerts: List[Alert] = []
        self._rules: Dict[str, AlertRule] = {}
        self._callbacks: List[Callable[[Alert], None]] = []
        self._lock = threading.RLock()
        self._alert_counter = 0
        self._max_alerts = 1000
        
        # 初始化默认规则
        self._init_default_rules()
    
    def _init_default_rules(self) -> None:
        """初始化默认告警规则"""
        # CPU高使用率告警
        self.add_rule(AlertRule(
            name="cpu_high_warning",
            alert_type=AlertType.CPU_HIGH,
            condition=lambda p: p.cpu_percent > 80,
            level=AlertLevel.WARNING,
            cooldown=60,
        ))
        
        self.add_rule(AlertRule(
            name="cpu_high_critical",
            alert_type=AlertType.CPU_HIGH,
            condition=lambda p: p.cpu_percent > 95,
            level=AlertLevel.CRITICAL,
            cooldown=30,
        ))
        
        # 内存高使用率告警
        self.add_rule(AlertRule(
            name="memory_high_warning",
            alert_type=AlertType.MEMORY_HIGH,
            condition=lambda p: p.memory_percent > 80,
            level=AlertLevel.WARNING,
            cooldown=60,
        ))
        
        self.add_rule(AlertRule(
            name="memory_high_critical",
            alert_type=AlertType.MEMORY_HIGH,
            condition=lambda p: p.memory_percent > 95,
            level=AlertLevel.CRITICAL,
            cooldown=30,
        ))
    
    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        with self._lock:
            self._rules[rule.name] = rule
    
    def remove_rule(self, name: str) -> bool:
        """移除告警规则"""
        with self._lock:
            if name in self._rules:
                del self._rules[name]
                return True
            return False
    
    def enable_rule(self, name: str) -> bool:
        """启用告警规则"""
        with self._lock:
            if name in self._rules:
                self._rules[name].enabled = True
                return True
            return False
    
    def disable_rule(self, name: str) -> bool:
        """禁用告警规则"""
        with self._lock:
            if name in self._rules:
                self._rules[name].enabled = False
                return True
            return False
    
    def get_rules(self) -> List[AlertRule]:
        """获取所有规则"""
        with self._lock:
            return list(self._rules.values())
    
    def check_process(self, process_info: Any) -> List[Alert]:
        """
        检查进程是否触发告警
        
        Args:
            process_info: 进程信息对象
            
        Returns:
            触发的告警列表
        """
        triggered_alerts = []
        current_time = time.time()
        
        with self._lock:
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                
                # 检查冷却时间
                if current_time - rule.last_triggered < rule.cooldown:
                    continue
                
                try:
                    if rule.condition(process_info):
                        alert = self._create_alert(
                            alert_type=rule.alert_type,
                            level=rule.level,
                            message=f"Process '{process_info.name}' (PID: {process_info.pid}) triggered {rule.name}",
                            pid=process_info.pid,
                            process_name=process_info.name,
                            details={
                                "rule_name": rule.name,
                                "cpu_percent": process_info.cpu_percent,
                                "memory_percent": process_info.memory_percent,
                            }
                        )
                        triggered_alerts.append(alert)
                        rule.last_triggered = current_time
                except Exception:
                    pass
        
        return triggered_alerts
    
    def check_processes(self, processes: Dict[int, Any]) -> List[Alert]:
        """
        批量检查进程
        
        Args:
            processes: 进程字典
            
        Returns:
            触发的告警列表
        """
        all_alerts = []
        for proc in processes.values():
            alerts = self.check_process(proc)
            all_alerts.extend(alerts)
        
        return all_alerts
    
    def _create_alert(self,
                      alert_type: AlertType,
                      level: AlertLevel,
                      message: str,
                      pid: Optional[int] = None,
                      process_name: str = "",
                      details: Optional[Dict[str, Any]] = None) -> Alert:
        """创建告警"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"alert_{int(time.time())}_{self._alert_counter}"
            
            alert = Alert(
                id=alert_id,
                alert_type=alert_type,
                level=level,
                message=message,
                pid=pid,
                process_name=process_name,
                timestamp=time.time(),
                details=details or {},
            )
            
            self._alerts.append(alert)
            
            # 限制告警数量
            if len(self._alerts) > self._max_alerts:
                self._alerts = self._alerts[-self._max_alerts:]
            
            # 通知回调
            self._notify_callbacks(alert)
            
            return alert
    
    def create_custom_alert(self,
                           level: AlertLevel,
                           message: str,
                           pid: Optional[int] = None,
                           process_name: str = "",
                           details: Optional[Dict[str, Any]] = None) -> Alert:
        """创建自定义告警"""
        return self._create_alert(
            alert_type=AlertType.CUSTOM,
            level=level,
            message=message,
            pid=pid,
            process_name=process_name,
            details=details,
        )
    
    def add_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加告警回调"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Alert], None]) -> None:
        """移除告警回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, alert: Alert) -> None:
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception:
                pass
    
    def get_alerts(self,
                   level: Optional[AlertLevel] = None,
                   alert_type: Optional[AlertType] = None,
                   acknowledged: Optional[bool] = None,
                   limit: int = 100) -> List[Alert]:
        """
        获取告警列表
        
        Args:
            level: 按级别过滤
            alert_type: 按类型过滤
            acknowledged: 按确认状态过滤
            limit: 最大数量
            
        Returns:
            告警列表
        """
        with self._lock:
            alerts = self._alerts.copy()
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        return alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    return True
            return False
    
    def acknowledge_all(self) -> int:
        """确认所有告警"""
        count = 0
        with self._lock:
            for alert in self._alerts:
                if not alert.acknowledged:
                    alert.acknowledged = True
                    count += 1
        return count
    
    def clear_alerts(self,
                    level: Optional[AlertLevel] = None,
                    alert_type: Optional[AlertType] = None) -> int:
        """
        清除告警
        
        Args:
            level: 按级别清除
            alert_type: 按类型清除
            
        Returns:
            清除的数量
        """
        with self._lock:
            original_count = len(self._alerts)
            
            if level:
                self._alerts = [a for a in self._alerts if a.level != level]
            elif alert_type:
                self._alerts = [a for a in self._alerts if a.alert_type != alert_type]
            else:
                self._alerts = []
            
            return original_count - len(self._alerts)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        with self._lock:
            alerts = self._alerts.copy()
        
        if not alerts:
            return {
                "total": 0,
                "unacknowledged": 0,
                "by_level": {},
                "by_type": {},
            }
        
        by_level = {}
        for level in AlertLevel:
            by_level[level.value] = sum(1 for a in alerts if a.level == level)
        
        by_type = {}
        for atype in AlertType:
            by_type[atype.value] = sum(1 for a in alerts if a.alert_type == atype)
        
        return {
            "total": len(alerts),
            "unacknowledged": sum(1 for a in alerts if not a.acknowledged),
            "by_level": by_level,
            "by_type": by_type,
        }
    
    def export_alerts(self, filepath: str) -> bool:
        """导出告警到文件"""
        try:
            with self._lock:
                data = {
                    "exported_at": datetime.now().isoformat(),
                    "statistics": self.get_alert_statistics(),
                    "alerts": [a.to_dict() for a in self._alerts],
                }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def import_rules(self, filepath: str) -> int:
        """
        从文件导入规则
        
        Returns:
            导入的规则数量
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            count = 0
            for rule_data in data.get("rules", []):
                # 简化导入，只支持基本规则
                rule = AlertRule(
                    name=rule_data["name"],
                    alert_type=AlertType(rule_data["alert_type"]),
                    condition=lambda p: False,  # 需要手动设置
                    level=AlertLevel(rule_data.get("level", "warning")),
                    cooldown=rule_data.get("cooldown", 60),
                    enabled=rule_data.get("enabled", True),
                )
                self.add_rule(rule)
                count += 1
            
            return count
        except Exception:
            return 0
