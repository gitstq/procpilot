"""
ProcPilot Core Module - Process Manager
进程管理核心模块
"""

import os
import sys
import time
import signal
import platform
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import subprocess
import threading
import json
from pathlib import Path


class ProcessStatus(Enum):
    """进程状态枚举"""
    RUNNING = "running"
    SLEEPING = "sleeping"
    STOPPED = "stopped"
    ZOMBIE = "zombie"
    IDLE = "idle"
    UNKNOWN = "unknown"


class ProcessPriority(Enum):
    """进程优先级枚举"""
    REALTIME = "realtime"
    HIGH = "high"
    ABOVE_NORMAL = "above_normal"
    NORMAL = "normal"
    BELOW_NORMAL = "below_normal"
    LOW = "low"


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    name: str
    status: ProcessStatus
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    create_time: float = 0.0
    username: str = ""
    command: str = ""
    ppid: int = 0
    priority: ProcessPriority = ProcessPriority.NORMAL
    num_threads: int = 1
    children: List[int] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    group: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pid": self.pid,
            "name": self.name,
            "status": self.status.value,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_mb": self.memory_mb,
            "create_time": self.create_time,
            "username": self.username,
            "command": self.command,
            "ppid": self.ppid,
            "priority": self.priority.value,
            "num_threads": self.num_threads,
            "children": self.children,
            "tags": self.tags,
            "group": self.group,
        }


class ProcessManager:
    """
    进程管理器核心类
    
    提供进程列表、进程信息获取、进程操作等功能
    支持跨平台（Linux、macOS、Windows）
    """
    
    def __init__(self):
        self._platform = platform.system().lower()
        self._processes: Dict[int, ProcessInfo] = {}
        self._groups: Dict[str, List[int]] = {}
        self._tags: Dict[str, List[int]] = {}
        self._last_update: float = 0
        self._update_interval: float = 1.0
        self._lock = threading.RLock()
        
    def get_all_processes(self, refresh: bool = True) -> Dict[int, ProcessInfo]:
        """
        获取所有进程信息
        
        Args:
            refresh: 是否刷新缓存
            
        Returns:
            进程字典 {pid: ProcessInfo}
        """
        if refresh or time.time() - self._last_update > self._update_interval:
            self._refresh_processes()
        return self._processes.copy()
    
    def get_process(self, pid: int) -> Optional[ProcessInfo]:
        """
        获取指定进程信息
        
        Args:
            pid: 进程ID
            
        Returns:
            ProcessInfo 或 None
        """
        if pid in self._processes:
            return self._processes[pid]
        
        # 尝试获取单个进程
        try:
            info = self._get_process_info(pid)
            if info:
                with self._lock:
                    self._processes[pid] = info
                return info
        except Exception:
            pass
        return None
    
    def _refresh_processes(self) -> None:
        """刷新进程列表"""
        processes = {}
        
        if self._platform == "linux":
            processes = self._get_linux_processes()
        elif self._platform == "darwin":
            processes = self._get_macos_processes()
        elif self._platform == "windows":
            processes = self._get_windows_processes()
        else:
            processes = self._get_generic_processes()
        
        with self._lock:
            self._processes = processes
            self._last_update = time.time()
    
    def _get_linux_processes(self) -> Dict[int, ProcessInfo]:
        """获取Linux进程列表"""
        processes = {}
        
        try:
            for entry in os.listdir("/proc"):
                if not entry.isdigit():
                    continue
                
                pid = int(entry)
                try:
                    info = self._get_linux_process_info(pid)
                    if info:
                        processes[pid] = info
                except (PermissionError, FileNotFoundError, ProcessLookupError):
                    continue
        except PermissionError:
            pass
        
        return processes
    
    def _get_linux_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """获取Linux单个进程信息"""
        try:
            proc_path = Path(f"/proc/{pid}")
            
            # 读取进程状态
            stat_file = proc_path / "stat"
            if not stat_file.exists():
                return None
            
            with open(stat_file, "r") as f:
                stat = f.read().split()
            
            # 解析进程名（可能包含括号）
            name = stat[1].strip("()")
            status_map = {
                "R": ProcessStatus.RUNNING,
                "S": ProcessStatus.SLEEPING,
                "D": ProcessStatus.SLEEPING,
                "Z": ProcessStatus.ZOMBIE,
                "T": ProcessStatus.STOPPED,
                "I": ProcessStatus.IDLE,
            }
            status = status_map.get(stat[2], ProcessStatus.UNKNOWN)
            ppid = int(stat[3])
            
            # 读取命令行
            cmdline_file = proc_path / "cmdline"
            command = ""
            try:
                with open(cmdline_file, "r") as f:
                    cmdline = f.read().replace("\x00", " ").strip()
                    command = cmdline if cmdline else name
            except Exception:
                command = name
            
            # 读取用户名
            username = ""
            try:
                import pwd
                uid = os.stat(proc_path).st_uid
                username = pwd.getpwuid(uid).pw_name
            except Exception:
                pass
            
            # 读取内存信息
            memory_mb = 0.0
            memory_percent = 0.0
            try:
                status_file = proc_path / "status"
                with open(status_file, "r") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            memory_mb = float(line.split()[1]) / 1024
                            break
                
                # 计算内存百分比
                try:
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                total_mb = float(line.split()[1]) / 1024
                                if total_mb > 0:
                                    memory_percent = (memory_mb / total_mb) * 100
                                break
                except Exception:
                    pass
            except Exception:
                pass
            
            # 读取创建时间
            create_time = float(stat[21]) / os.sysconf("SC_CLK_TCK")
            
            # 优先级
            priority_val = int(stat[17])
            if priority_val < -10:
                priority = ProcessPriority.REALTIME
            elif priority_val < 0:
                priority = ProcessPriority.HIGH
            elif priority_val == 0:
                priority = ProcessPriority.NORMAL
            elif priority_val < 10:
                priority = ProcessPriority.BELOW_NORMAL
            else:
                priority = ProcessPriority.LOW
            
            # 线程数
            num_threads = int(stat[19])
            
            return ProcessInfo(
                pid=pid,
                name=name,
                status=status,
                cpu_percent=0.0,  # 需要两次采样计算
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                create_time=create_time,
                username=username,
                command=command,
                ppid=ppid,
                priority=priority,
                num_threads=num_threads,
            )
        except Exception:
            return None
    
    def _get_macos_processes(self) -> Dict[int, ProcessInfo]:
        """获取macOS进程列表"""
        processes = {}
        
        try:
            # 使用ps命令获取进程列表
            result = subprocess.run(
                ["ps", "-ax", "-o", "pid,ppid,user,%cpu,%mem,rss,state,command"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split("\n")[1:]  # 跳过标题行
            
            for line in lines:
                parts = line.split(None, 7)
                if len(parts) < 8:
                    continue
                
                try:
                    pid = int(parts[0])
                    ppid = int(parts[1])
                    username = parts[2]
                    cpu_percent = float(parts[3])
                    memory_percent = float(parts[4])
                    memory_mb = float(parts[5]) / 1024
                    state = parts[6]
                    command = parts[7] if len(parts) > 7 else ""
                    
                    status_map = {
                        "R": ProcessStatus.RUNNING,
                        "S": ProcessStatus.SLEEPING,
                        "I": ProcessStatus.IDLE,
                        "T": ProcessStatus.STOPPED,
                        "Z": ProcessStatus.ZOMBIE,
                    }
                    status = status_map.get(state[0], ProcessStatus.UNKNOWN)
                    
                    name = command.split("/")[-1] if "/" in command else command.split()[0] if command else "unknown"
                    
                    processes[pid] = ProcessInfo(
                        pid=pid,
                        name=name,
                        status=status,
                        cpu_percent=cpu_percent,
                        memory_percent=memory_percent,
                        memory_mb=memory_mb,
                        create_time=0,
                        username=username,
                        command=command,
                        ppid=ppid,
                        priority=ProcessPriority.NORMAL,
                        num_threads=1,
                    )
                except (ValueError, IndexError):
                    continue
        except Exception:
            pass
        
        return processes
    
    def _get_windows_processes(self) -> Dict[int, ProcessInfo]:
        """获取Windows进程列表"""
        processes = {}
        
        try:
            # 使用wmic获取进程信息
            result = subprocess.run(
                ["wmic", "process", "get", 
                 "ProcessId,ParentProcessId,Name,ExecutablePath,PageFileUsage,UserModeTime,KernelModeTime",
                 "/format:csv"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.strip().split("\n")[1:]  # 跳过标题行
            
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) < 8:
                    continue
                
                try:
                    name = parts[1] if parts[1] else "unknown"
                    exe_path = parts[2] if parts[2] else ""
                    ppid = int(parts[3]) if parts[3] else 0
                    pid = int(parts[4]) if parts[4] else 0
                    page_file = float(parts[5]) / 1024 if parts[5] else 0  # KB to MB
                    user_time = int(parts[6]) if parts[6] else 0
                    kernel_time = int(parts[7]) if parts[7] else 0
                    
                    if pid <= 0:
                        continue
                    
                    processes[pid] = ProcessInfo(
                        pid=pid,
                        name=name,
                        status=ProcessStatus.RUNNING,
                        cpu_percent=0.0,
                        memory_percent=0.0,
                        memory_mb=page_file,
                        create_time=0,
                        username="",
                        command=exe_path,
                        ppid=ppid,
                        priority=ProcessPriority.NORMAL,
                        num_threads=1,
                    )
                except (ValueError, IndexError):
                    continue
        except Exception:
            pass
        
        return processes
    
    def _get_generic_processes(self) -> Dict[int, ProcessInfo]:
        """获取通用进程列表（备用方案）"""
        processes = {}
        
        try:
            result = subprocess.run(
                ["ps", "-e", "-o", "pid,ppid,comm"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split("\n")[1:]
            
            for line in lines:
                parts = line.split(None, 2)
                if len(parts) < 3:
                    continue
                
                try:
                    pid = int(parts[0])
                    ppid = int(parts[1])
                    name = parts[2]
                    
                    processes[pid] = ProcessInfo(
                        pid=pid,
                        name=name,
                        status=ProcessStatus.UNKNOWN,
                        cpu_percent=0.0,
                        memory_percent=0.0,
                        memory_mb=0.0,
                        create_time=0,
                        username="",
                        command=name,
                        ppid=ppid,
                        priority=ProcessPriority.NORMAL,
                        num_threads=1,
                    )
                except (ValueError, IndexError):
                    continue
        except Exception:
            pass
        
        return processes
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """
        终止进程
        
        Args:
            pid: 进程ID
            force: 是否强制终止
            
        Returns:
            是否成功
        """
        try:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            return True
        except (PermissionError, ProcessLookupError, OSError):
            return False
    
    def suspend_process(self, pid: int) -> bool:
        """暂停进程"""
        try:
            if self._platform in ["linux", "darwin"]:
                os.kill(pid, signal.SIGSTOP)
                return True
            elif self._platform == "windows":
                # Windows需要使用其他方法
                subprocess.run(
                    ["powershell", "-Command", f"(Get-Process -Id {pid}).Suspend()"],
                    timeout=5
                )
                return True
        except Exception:
            pass
        return False
    
    def resume_process(self, pid: int) -> bool:
        """恢复进程"""
        try:
            if self._platform in ["linux", "darwin"]:
                os.kill(pid, signal.SIGCONT)
                return True
            elif self._platform == "windows":
                subprocess.run(
                    ["powershell", "-Command", f"(Get-Process -Id {pid}).Resume()"],
                    timeout=5
                )
                return True
        except Exception:
            pass
        return False
    
    def set_priority(self, pid: int, priority: ProcessPriority) -> bool:
        """设置进程优先级"""
        try:
            if self._platform in ["linux", "darwin"]:
                nice_map = {
                    ProcessPriority.REALTIME: -20,
                    ProcessPriority.HIGH: -10,
                    ProcessPriority.ABOVE_NORMAL: -5,
                    ProcessPriority.NORMAL: 0,
                    ProcessPriority.BELOW_NORMAL: 5,
                    ProcessPriority.LOW: 10,
                }
                os.setpriority(os.PRIO_PROCESS, pid, nice_map[priority])
                return True
            elif self._platform == "windows":
                # Windows优先级设置
                priority_map = {
                    ProcessPriority.REALTIME: 256,
                    ProcessPriority.HIGH: 128,
                    ProcessPriority.ABOVE_NORMAL: 32768,
                    ProcessPriority.NORMAL: 32,
                    ProcessPriority.BELOW_NORMAL: 16384,
                    ProcessPriority.LOW: 64,
                }
                subprocess.run(
                    ["wmic", "process", "where", f"ProcessId={pid}", 
                     "call", "setpriority", str(priority_map[priority])],
                    timeout=5
                )
                return True
        except Exception:
            pass
        return False
    
    def add_tag(self, pid: int, tag: str) -> bool:
        """为进程添加标签"""
        with self._lock:
            if pid not in self._processes:
                return False
            
            if tag not in self._processes[pid].tags:
                self._processes[pid].tags.append(tag)
            
            if tag not in self._tags:
                self._tags[tag] = []
            if pid not in self._tags[tag]:
                self._tags[tag].append(pid)
            
            return True
    
    def remove_tag(self, pid: int, tag: str) -> bool:
        """移除进程标签"""
        with self._lock:
            if pid not in self._processes:
                return False
            
            if tag in self._processes[pid].tags:
                self._processes[pid].tags.remove(tag)
            
            if tag in self._tags and pid in self._tags[tag]:
                self._tags[tag].remove(pid)
            
            return True
    
    def get_processes_by_tag(self, tag: str) -> List[ProcessInfo]:
        """根据标签获取进程"""
        with self._lock:
            if tag not in self._tags:
                return []
            return [self._processes[pid] for pid in self._tags[tag] if pid in self._processes]
    
    def set_group(self, pid: int, group: str) -> bool:
        """设置进程分组"""
        with self._lock:
            if pid not in self._processes:
                return False
            
            # 从旧分组移除
            old_group = self._processes[pid].group
            if old_group and old_group in self._groups:
                if pid in self._groups[old_group]:
                    self._groups[old_group].remove(pid)
            
            # 添加到新分组
            self._processes[pid].group = group
            if group not in self._groups:
                self._groups[group] = []
            if pid not in self._groups[group]:
                self._groups[group].append(pid)
            
            return True
    
    def get_processes_by_group(self, group: str) -> List[ProcessInfo]:
        """根据分组获取进程"""
        with self._lock:
            if group not in self._groups:
                return []
            return [self._processes[pid] for pid in self._groups[group] if pid in self._processes]
    
    def search_processes(self, query: str) -> List[ProcessInfo]:
        """
        搜索进程
        
        Args:
            query: 搜索关键词（进程名、命令、用户名）
            
        Returns:
            匹配的进程列表
        """
        query = query.lower()
        results = []
        
        for proc in self.get_all_processes().values():
            if (query in proc.name.lower() or
                query in proc.command.lower() or
                query in proc.username.lower() or
                str(proc.pid) == query):
                results.append(proc)
        
        return results
    
    def get_process_tree(self) -> Dict[int, List[int]]:
        """获取进程树结构"""
        tree = {}
        processes = self.get_all_processes()
        
        for pid, proc in processes.items():
            if proc.ppid not in tree:
                tree[proc.ppid] = []
            tree[proc.ppid].append(pid)
        
        return tree
    
    def get_children(self, pid: int, recursive: bool = True) -> List[int]:
        """
        获取子进程
        
        Args:
            pid: 父进程ID
            recursive: 是否递归获取
            
        Returns:
            子进程PID列表
        """
        tree = self.get_process_tree()
        children = tree.get(pid, [])
        
        if recursive:
            all_children = children.copy()
            for child in children:
                all_children.extend(self.get_children(child, recursive=True))
            return all_children
        
        return children
    
    def export_to_json(self, filepath: str) -> bool:
        """导出进程信息到JSON文件"""
        try:
            processes = self.get_all_processes()
            data = {
                "timestamp": datetime.now().isoformat(),
                "platform": self._platform,
                "process_count": len(processes),
                "processes": [p.to_dict() for p in processes.values()]
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取进程统计信息"""
        processes = self.get_all_processes()
        
        if not processes:
            return {}
        
        total_cpu = sum(p.cpu_percent for p in processes.values())
        total_memory = sum(p.memory_mb for p in processes.values())
        
        status_count = {}
        for status in ProcessStatus:
            status_count[status.value] = sum(
                1 for p in processes.values() if p.status == status
            )
        
        return {
            "total_processes": len(processes),
            "total_cpu_percent": total_cpu,
            "total_memory_mb": total_memory,
            "status_distribution": status_count,
            "groups_count": len(self._groups),
            "tags_count": len(self._tags),
        }
