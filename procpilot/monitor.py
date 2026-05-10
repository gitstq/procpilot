"""
ProcPilot Monitor Module - Real-time Process Monitoring
实时进程监控模块
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import statistics

from .core import ProcessManager, ProcessInfo, ProcessStatus


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float


@dataclass
class ProcessMetrics:
    """进程指标历史"""
    pid: int
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=60))
    memory_history: deque = field(default_factory=lambda: deque(maxlen=60))
    last_update: float = 0


class ProcessMonitor:
    """
    进程监控器
    
    提供实时监控、资源追踪、历史数据分析等功能
    """
    
    def __init__(self, process_manager: Optional[ProcessManager] = None):
        self.manager = process_manager or ProcessManager()
        self._metrics: Dict[int, ProcessMetrics] = {}
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._interval: float = 1.0
        self._callbacks: List[Callable[[Dict[int, ProcessInfo]], None]] = []
        self._lock = threading.RLock()
        self._start_time: float = 0
        
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        开始监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self._monitoring:
            return
        
        self._interval = interval
        self._monitoring = True
        self._start_time = time.time()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
            self._monitor_thread = None
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self._monitoring:
            try:
                processes = self.manager.get_all_processes(refresh=True)
                self._update_metrics(processes)
                self._notify_callbacks(processes)
            except Exception:
                pass
            
            time.sleep(self._interval)
    
    def _update_metrics(self, processes: Dict[int, ProcessInfo]) -> None:
        """更新指标"""
        current_time = time.time()
        
        with self._lock:
            # 清理已结束进程的指标
            active_pids = set(processes.keys())
            inactive_pids = set(self._metrics.keys()) - active_pids
            for pid in inactive_pids:
                del self._metrics[pid]
            
            # 更新活跃进程指标
            for pid, proc in processes.items():
                if pid not in self._metrics:
                    self._metrics[pid] = ProcessMetrics(pid=pid)
                
                metrics = self._metrics[pid]
                metrics.cpu_history.append(MetricPoint(
                    timestamp=current_time,
                    value=proc.cpu_percent
                ))
                metrics.memory_history.append(MetricPoint(
                    timestamp=current_time,
                    value=proc.memory_mb
                ))
                metrics.last_update = current_time
    
    def add_callback(self, callback: Callable[[Dict[int, ProcessInfo]], None]) -> None:
        """添加监控回调"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict[int, ProcessInfo]], None]) -> None:
        """移除监控回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, processes: Dict[int, ProcessInfo]) -> None:
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(processes)
            except Exception:
                pass
    
    def get_process_metrics(self, pid: int) -> Optional[ProcessMetrics]:
        """获取进程指标历史"""
        with self._lock:
            return self._metrics.get(pid)
    
    def get_cpu_trend(self, pid: int, seconds: int = 30) -> List[float]:
        """
        获取CPU趋势
        
        Args:
            pid: 进程ID
            seconds: 时间范围（秒）
            
        Returns:
            CPU使用率列表
        """
        metrics = self.get_process_metrics(pid)
        if not metrics:
            return []
        
        current_time = time.time()
        cutoff = current_time - seconds
        
        return [
            p.value for p in metrics.cpu_history
            if p.timestamp >= cutoff
        ]
    
    def get_memory_trend(self, pid: int, seconds: int = 30) -> List[float]:
        """
        获取内存趋势
        
        Args:
            pid: 进程ID
            seconds: 时间范围（秒）
            
        Returns:
            内存使用量列表（MB）
        """
        metrics = self.get_process_metrics(pid)
        if not metrics:
            return []
        
        current_time = time.time()
        cutoff = current_time - seconds
        
        return [
            p.value for p in metrics.memory_history
            if p.timestamp >= cutoff
        ]
    
    def get_average_cpu(self, pid: int, seconds: int = 30) -> float:
        """获取平均CPU使用率"""
        trend = self.get_cpu_trend(pid, seconds)
        return statistics.mean(trend) if trend else 0.0
    
    def get_average_memory(self, pid: int, seconds: int = 30) -> float:
        """获取平均内存使用量"""
        trend = self.get_memory_trend(pid, seconds)
        return statistics.mean(trend) if trend else 0.0
    
    def get_peak_cpu(self, pid: int, seconds: int = 30) -> float:
        """获取峰值CPU使用率"""
        trend = self.get_cpu_trend(pid, seconds)
        return max(trend) if trend else 0.0
    
    def get_peak_memory(self, pid: int, seconds: int = 30) -> float:
        """获取峰值内存使用量"""
        trend = self.get_memory_trend(pid, seconds)
        return max(trend) if trend else 0.0
    
    def get_top_cpu_processes(self, limit: int = 10) -> List[ProcessInfo]:
        """获取CPU使用率最高的进程"""
        processes = self.manager.get_all_processes()
        sorted_procs = sorted(
            processes.values(),
            key=lambda p: p.cpu_percent,
            reverse=True
        )
        return sorted_procs[:limit]
    
    def get_top_memory_processes(self, limit: int = 10) -> List[ProcessInfo]:
        """获取内存使用量最高的进程"""
        processes = self.manager.get_all_processes()
        sorted_procs = sorted(
            processes.values(),
            key=lambda p: p.memory_mb,
            reverse=True
        )
        return sorted_procs[:limit]
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        processes = self.manager.get_all_processes()
        
        if not processes:
            return {}
        
        total_cpu = sum(p.cpu_percent for p in processes.values())
        total_memory = sum(p.memory_mb for p in processes.values())
        
        running = sum(1 for p in processes.values() if p.status == ProcessStatus.RUNNING)
        sleeping = sum(1 for p in processes.values() if p.status == ProcessStatus.SLEEPING)
        stopped = sum(1 for p in processes.values() if p.status == ProcessStatus.STOPPED)
        zombie = sum(1 for p in processes.values() if p.status == ProcessStatus.ZOMBIE)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
            "total_processes": len(processes),
            "total_cpu_percent": round(total_cpu, 2),
            "total_memory_mb": round(total_memory, 2),
            "running": running,
            "sleeping": sleeping,
            "stopped": stopped,
            "zombie": zombie,
            "monitoring": self._monitoring,
            "interval": self._interval,
        }
    
    def find_resource_hogs(self, 
                          cpu_threshold: float = 50.0,
                          memory_threshold: float = 500.0) -> List[ProcessInfo]:
        """
        查找资源占用高的进程
        
        Args:
            cpu_threshold: CPU阈值（%）
            memory_threshold: 内存阈值（MB）
            
        Returns:
            资源占用高的进程列表
        """
        processes = self.manager.get_all_processes()
        hogs = []
        
        for proc in processes.values():
            if proc.cpu_percent >= cpu_threshold or proc.memory_mb >= memory_threshold:
                hogs.append(proc)
        
        return sorted(hogs, key=lambda p: (p.cpu_percent + p.memory_percent), reverse=True)
    
    def find_zombie_processes(self) -> List[ProcessInfo]:
        """查找僵尸进程"""
        processes = self.manager.get_all_processes()
        return [p for p in processes.values() if p.status == ProcessStatus.ZOMBIE]
    
    def find_orphan_processes(self) -> List[ProcessInfo]:
        """查找孤儿进程（父进程已结束）"""
        processes = self.manager.get_all_processes()
        pids = set(processes.keys())
        
        orphans = []
        for proc in processes.values():
            if proc.ppid > 0 and proc.ppid not in pids:
                orphans.append(proc)
        
        return orphans
    
    def export_report(self, filepath: str) -> bool:
        """导出监控报告"""
        try:
            import json
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "system_summary": self.get_system_summary(),
                "top_cpu_processes": [
                    p.to_dict() for p in self.get_top_cpu_processes(20)
                ],
                "top_memory_processes": [
                    p.to_dict() for p in self.get_top_memory_processes(20)
                ],
                "resource_hogs": [
                    p.to_dict() for p in self.find_resource_hogs()
                ],
                "zombie_processes": [
                    p.to_dict() for p in self.find_zombie_processes()
                ],
                "orphan_processes": [
                    p.to_dict() for p in self.find_orphan_processes()
                ],
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
