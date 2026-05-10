"""
ProcPilot TUI Module - Terminal User Interface
终端用户界面模块
"""

import os
import sys
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import shutil

from .core import ProcessManager, ProcessInfo, ProcessStatus
from .monitor import ProcessMonitor
from .tree import ProcessTree
from .alerts import AlertManager, AlertLevel


class Color:
    """ANSI颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 背景色
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


class KeyCode:
    """按键代码"""
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    LEFT = "\x1b[D"
    RIGHT = "\x1b[C"
    ENTER = "\r"
    ESCAPE = "\x1b"
    TAB = "\t"
    BACKSPACE = "\x7f"
    DELETE = "\x1b[3~"
    HOME = "\x1b[H"
    END = "\x1b[F"
    PAGE_UP = "\x1b[5~"
    PAGE_DOWN = "\x1b[6~"


@dataclass
class ViewConfig:
    """视图配置"""
    sort_by: str = "cpu"
    sort_reverse: bool = True
    filter_query: str = ""
    show_tree: bool = False
    selected_pid: Optional[int] = None
    scroll_offset: int = 0
    page_size: int = 20


class ProcessTUI:
    """
    进程管理TUI界面
    
    提供交互式终端界面，支持进程浏览、搜索、操作等功能
    """
    
    def __init__(self):
        self.manager = ProcessManager()
        self.monitor = ProcessMonitor(self.manager)
        self.tree = ProcessTree(self.manager)
        self.alerts = AlertManager()
        
        self.config = ViewConfig()
        self._running = False
        self._input_thread: Optional[threading.Thread] = None
        self._refresh_thread: Optional[threading.Thread] = None
        self._last_key = ""
        self._message = ""
        self._message_time = 0
        self._width = 80
        self._height = 24
        
        # 进程列表缓存
        self._process_list: List[ProcessInfo] = []
        self._filtered_list: List[ProcessInfo] = []
        
        # 设置告警回调
        self.alerts.add_callback(self._on_alert)
    
    def _on_alert(self, alert) -> None:
        """告警回调"""
        self._message = f"[{alert.level.value.upper()}] {alert.message}"
        self._message_time = time.time()
    
    def start(self) -> None:
        """启动TUI"""
        self._running = True
        self._setup_terminal()
        
        # 启动刷新线程
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()
        
        # 启动输入线程
        self._input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self._input_thread.start()
        
        # 主渲染循环
        try:
            while self._running:
                self._render()
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self._restore_terminal()
    
    def stop(self) -> None:
        """停止TUI"""
        self._running = False
        self.monitor.stop_monitoring()
    
    def _setup_terminal(self) -> None:
        """设置终端"""
        # 保存原始设置
        os.system("stty sane")
        
        # 设置原始模式
        os.system("stty -echo -icanon")
        
        # 隐藏光标
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        
        # 启用鼠标支持
        sys.stdout.write("\033[?1000h")
        sys.stdout.flush()
        
        # 获取终端大小
        self._update_terminal_size()
    
    def _restore_terminal(self) -> None:
        """恢复终端"""
        # 恢复光标
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        
        # 禁用鼠标支持
        sys.stdout.write("\033[?1000l")
        sys.stdout.flush()
        
        # 恢复终端设置
        os.system("stty sane")
        
        # 清屏
        os.system("clear")
    
    def _update_terminal_size(self) -> None:
        """更新终端大小"""
        try:
            size = shutil.get_terminal_size()
            self._width = size.columns
            self._height = size.lines
            self.config.page_size = max(10, self._height - 10)
        except Exception:
            pass
    
    def _refresh_loop(self) -> None:
        """刷新循环"""
        while self._running:
            try:
                self._refresh_process_list()
            except Exception:
                pass
            time.sleep(1.0)
    
    def _refresh_process_list(self) -> None:
        """刷新进程列表"""
        processes = self.manager.get_all_processes()
        self._process_list = list(processes.values())
        
        # 检查告警
        self.alerts.check_processes(processes)
        
        # 应用过滤和排序
        self._apply_filter_and_sort()
    
    def _apply_filter_and_sort(self) -> None:
        """应用过滤和排序"""
        # 过滤
        if self.config.filter_query:
            query = self.config.filter_query.lower()
            self._filtered_list = [
                p for p in self._process_list
                if query in p.name.lower() or
                   query in p.command.lower() or
                   str(p.pid) == query
            ]
        else:
            self._filtered_list = self._process_list.copy()
        
        # 排序
        sort_key = {
            "cpu": lambda p: p.cpu_percent,
            "memory": lambda p: p.memory_mb,
            "pid": lambda p: p.pid,
            "name": lambda p: p.name.lower(),
            "status": lambda p: p.status.value,
        }.get(self.config.sort_by, lambda p: p.cpu_percent)
        
        self._filtered_list.sort(key=sort_key, reverse=self.config.sort_reverse)
    
    def _input_loop(self) -> None:
        """输入循环"""
        while self._running:
            try:
                char = sys.stdin.read(1)
                if char:
                    self._handle_input(char)
            except Exception:
                pass
    
    def _handle_input(self, char: str) -> None:
        """处理输入"""
        # 处理转义序列
        if char == "\x1b":
            # 读取后续字符
            seq = char
            try:
                seq += sys.stdin.read(2)
            except Exception:
                pass
            
            if seq == KeyCode.UP:
                self._move_selection(-1)
            elif seq == KeyCode.DOWN:
                self._move_selection(1)
            elif seq == KeyCode.PAGE_UP:
                self._move_selection(-self.config.page_size)
            elif seq == KeyCode.PAGE_DOWN:
                self._move_selection(self.config.page_size)
            elif seq == KeyCode.HOME:
                self.config.scroll_offset = 0
                if self._filtered_list:
                    self.config.selected_pid = self._filtered_list[0].pid
            elif seq == KeyCode.END:
                if self._filtered_list:
                    self.config.selected_pid = self._filtered_list[-1].pid
                    self._scroll_to_selected()
            return
        
        # 单字符命令
        if char == "q":
            self._running = False
        elif char == "k":
            self._kill_selected()
        elif char == "K":
            self._kill_selected(force=True)
        elif char == "s":
            self._suspend_selected()
        elif char == "r":
            self._resume_selected()
        elif char == "t":
            self.config.show_tree = not self.config.show_tree
        elif char == "/":
            self._start_search()
        elif char == "n":
            self._cycle_sort()
        elif char == "?":
            self._show_help()
        elif char == "a":
            self._show_alerts()
        elif char == "\r":
            self._show_process_detail()
    
    def _move_selection(self, delta: int) -> None:
        """移动选择"""
        if not self._filtered_list:
            return
        
        # 找到当前选中索引
        current_idx = -1
        for i, p in enumerate(self._filtered_list):
            if p.pid == self.config.selected_pid:
                current_idx = i
                break
        
        # 计算新索引
        if current_idx == -1:
            new_idx = 0 if delta > 0 else len(self._filtered_list) - 1
        else:
            new_idx = max(0, min(len(self._filtered_list) - 1, current_idx + delta))
        
        self.config.selected_pid = self._filtered_list[new_idx].pid
        
        # 调整滚动
        self._scroll_to_selected()
    
    def _scroll_to_selected(self) -> None:
        """滚动到选中项"""
        if not self._filtered_list:
            return
        
        for i, p in enumerate(self._filtered_list):
            if p.pid == self.config.selected_pid:
                if i < self.config.scroll_offset:
                    self.config.scroll_offset = i
                elif i >= self.config.scroll_offset + self.config.page_size:
                    self.config.scroll_offset = i - self.config.page_size + 1
                break
    
    def _kill_selected(self, force: bool = False) -> None:
        """终止选中进程"""
        if self.config.selected_pid is None:
            return
        
        proc = self.manager.get_process(self.config.selected_pid)
        if proc:
            success = self.manager.kill_process(self.config.selected_pid, force=force)
            if success:
                self._message = f"{'Force k' if force else 'K'}illed process {proc.name} (PID: {proc.pid})"
            else:
                self._message = f"Failed to kill process {proc.name} (PID: {proc.pid})"
            self._message_time = time.time()
    
    def _suspend_selected(self) -> None:
        """暂停选中进程"""
        if self.config.selected_pid is None:
            return
        
        proc = self.manager.get_process(self.config.selected_pid)
        if proc:
            success = self.manager.suspend_process(self.config.selected_pid)
            if success:
                self._message = f"Suspended process {proc.name} (PID: {proc.pid})"
            else:
                self._message = f"Failed to suspend process {proc.name}"
            self._message_time = time.time()
    
    def _resume_selected(self) -> None:
        """恢复选中进程"""
        if self.config.selected_pid is None:
            return
        
        proc = self.manager.get_process(self.config.selected_pid)
        if proc:
            success = self.manager.resume_process(self.config.selected_pid)
            if success:
                self._message = f"Resumed process {proc.name} (PID: {proc.pid})"
            else:
                self._message = f"Failed to resume process {proc.name}"
            self._message_time = time.time()
    
    def _start_search(self) -> None:
        """开始搜索"""
        # 简化实现：提示用户输入
        self._message = "Search mode: type query and press Enter (ESC to cancel)"
        self._message_time = time.time()
    
    def _cycle_sort(self) -> None:
        """切换排序方式"""
        sort_options = ["cpu", "memory", "pid", "name"]
        current_idx = sort_options.index(self.config.sort_by) if self.config.sort_by in sort_options else 0
        self.config.sort_by = sort_options[(current_idx + 1) % len(sort_options)]
        self._message = f"Sort by: {self.config.sort_by}"
        self._message_time = time.time()
    
    def _show_help(self) -> None:
        """显示帮助"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    ProcPilot Help                            ║
╠══════════════════════════════════════════════════════════════╣
║  ↑/↓     - Navigate processes                                ║
║  PgUp/PgDn - Page up/down                                    ║
║  k        - Kill selected process (SIGTERM)                  ║
║  K        - Force kill (SIGKILL)                             ║
║  s        - Suspend process (SIGSTOP)                        ║
║  r        - Resume process (SIGCONT)                         ║
║  t        - Toggle tree view                                 ║
║  /        - Search processes                                 ║
║  n        - Cycle sort mode                                  ║
║  a        - View alerts                                      ║
║  Enter    - View process details                             ║
║  q        - Quit                                             ║
║  ?        - Show this help                                   ║
╚══════════════════════════════════════════════════════════════╝
Press any key to close...
"""
        self._message = help_text
        self._message_time = time.time() + 10  # 显示更长时间
    
    def _show_alerts(self) -> None:
        """显示告警"""
        alerts = self.alerts.get_alerts(limit=10)
        if not alerts:
            self._message = "No alerts"
            self._message_time = time.time()
            return
        
        lines = ["Recent Alerts:"]
        for alert in alerts[-10:]:
            level_color = {
                AlertLevel.INFO: Color.CYAN,
                AlertLevel.WARNING: Color.YELLOW,
                AlertLevel.CRITICAL: Color.RED,
                AlertLevel.EMERGENCY: Color.BG_RED,
            }.get(alert.level, Color.WHITE)
            lines.append(f"{level_color}[{alert.level.value.upper()}]{Color.RESET} {alert.message}")
        
        self._message = "\n".join(lines)
        self._message_time = time.time() + 5
    
    def _show_process_detail(self) -> None:
        """显示进程详情"""
        if self.config.selected_pid is None:
            return
        
        proc = self.manager.get_process(self.config.selected_pid)
        if not proc:
            return
        
        detail = f"""
╔══════════════════════════════════════════════════════════════╗
║  Process Details                                             ║
╠══════════════════════════════════════════════════════════════╣
║  PID:        {proc.pid:<46} ║
║  Name:       {proc.name:<46} ║
║  Status:     {proc.status.value:<46} ║
║  CPU:        {proc.cpu_percent:.1f}%{' ':<43} ║
║  Memory:     {proc.memory_mb:.1f} MB ({proc.memory_percent:.1f}%){' ':<29} ║
║  Parent PID: {proc.ppid:<46} ║
║  User:       {proc.username:<46} ║
║  Threads:    {proc.num_threads:<46} ║
║  Priority:   {proc.priority.value:<46} ║
║  Command:    {proc.command[:44]:<44} ║
╚══════════════════════════════════════════════════════════════╝
"""
        self._message = detail
        self._message_time = time.time() + 5
    
    def _render(self) -> None:
        """渲染界面"""
        # 清屏
        sys.stdout.write("\033[2J\033[H")
        
        # 渲染标题栏
        self._render_header()
        
        # 渲染进程列表
        self._render_process_list()
        
        # 渲染状态栏
        self._render_status_bar()
        
        # 渲染消息
        self._render_message()
        
        sys.stdout.flush()
    
    def _render_header(self) -> None:
        """渲染标题栏"""
        stats = self.manager.get_statistics()
        header = f"{Color.BOLD}{Color.CYAN}╔{'═' * (self._width - 2)}╗{Color.RESET}\n"
        header += f"{Color.BOLD}{Color.CYAN}║{Color.RESET} {Color.BOLD}ProcPilot{Color.RESET} - Process Intelligence Manager "
        header += f"{' ' * (self._width - 45)}{Color.BOLD}{Color.CYAN}║{Color.RESET}\n"
        header += f"{Color.BOLD}{Color.CYAN}║{Color.RESET} Processes: {stats.get('total_processes', 0)} "
        header += f"| CPU: {stats.get('total_cpu_percent', 0):.1f}% "
        header += f"| Memory: {stats.get('total_memory_mb', 0):.0f}MB "
        header += f"{' ' * (self._width - 60)}{Color.BOLD}{Color.CYAN}║{Color.RESET}\n"
        header += f"{Color.BOLD}{Color.CYAN}╠{'═' * (self._width - 2)}╣{Color.RESET}"
        
        sys.stdout.write(header + "\n")
    
    def _render_process_list(self) -> None:
        """渲染进程列表"""
        # 列标题
        col_widths = {
            "pid": 8,
            "name": 20,
            "cpu": 8,
            "mem": 10,
            "status": 10,
            "user": 12,
        }
        
        header = f"{Color.BOLD}{Color.CYAN}║{Color.RESET} "
        header += f"{'PID':<{col_widths['pid']}} "
        header += f"{'NAME':<{col_widths['name']}} "
        header += f"{'CPU%':>{col_widths['cpu']}} "
        header += f"{'MEMORY':>{col_widths['mem']}} "
        header += f"{'STATUS':<{col_widths['status']}} "
        header += f"{'USER':<{col_widths['user']}} "
        header += f"{' ' * (self._width - 75)}{Color.BOLD}{Color.CYAN}║{Color.RESET}"
        
        sys.stdout.write(header + "\n")
        sys.stdout.write(f"{Color.BOLD}{Color.CYAN}╠{'─' * (self._width - 2)}╣{Color.RESET}\n")
        
        # 进程列表
        visible_processes = self._filtered_list[
            self.config.scroll_offset:
            self.config.scroll_offset + self.config.page_size
        ]
        
        for proc in visible_processes:
            is_selected = proc.pid == self.config.selected_pid
            
            # 状态颜色
            status_color = {
                ProcessStatus.RUNNING: Color.GREEN,
                ProcessStatus.SLEEPING: Color.BLUE,
                ProcessStatus.STOPPED: Color.YELLOW,
                ProcessStatus.ZOMBIE: Color.RED,
                ProcessStatus.IDLE: Color.DIM,
            }.get(proc.status, Color.WHITE)
            
            # CPU颜色
            cpu_color = Color.GREEN
            if proc.cpu_percent > 80:
                cpu_color = Color.RED
            elif proc.cpu_percent > 50:
                cpu_color = Color.YELLOW
            
            # 内存颜色
            mem_color = Color.GREEN
            if proc.memory_percent > 80:
                mem_color = Color.RED
            elif proc.memory_percent > 50:
                mem_color = Color.YELLOW
            
            # 选中背景
            bg = Color.BG_BLUE if is_selected else ""
            reset_bg = Color.RESET if is_selected else ""
            
            line = f"{Color.BOLD}{Color.CYAN}║{Color.RESET}{bg} "
            line += f"{proc.pid:<{col_widths['pid']}} "
            
            name = proc.name[:col_widths['name'] - 1]
            line += f"{name:<{col_widths['name']}} "
            
            line += f"{cpu_color}{proc.cpu_percent:>{col_widths['cpu'] - 1}.1f}%{reset_bg if is_selected else ''}{Color.RESET}{bg} "
            line += f"{mem_color}{proc.memory_mb:>{col_widths['mem'] - 3}.1f}MB{reset_bg if is_selected else ''}{Color.RESET}{bg} "
            line += f"{status_color}{proc.status.value:<{col_widths['status']}}{Color.RESET}{bg} "
            
            user = proc.username[:col_widths['user'] - 1] if proc.username else "unknown"
            line += f"{user:<{col_widths['user']}} "
            
            line += f"{' ' * (self._width - 75)}{reset_bg}{Color.BOLD}{Color.CYAN}║{Color.RESET}"
            
            sys.stdout.write(line + "\n")
        
        # 填充空白行
        empty_lines = self.config.page_size - len(visible_processes)
        for _ in range(empty_lines):
            sys.stdout.write(f"{Color.BOLD}{Color.CYAN}║{' ' * (self._width - 2)}║{Color.RESET}\n")
    
    def _render_status_bar(self) -> None:
        """渲染状态栏"""
        sys.stdout.write(f"{Color.BOLD}{Color.CYAN}╠{'═' * (self._width - 2)}╣{Color.RESET}\n")
        
        status = f"{Color.BOLD}{Color.CYAN}║{Color.RESET} "
        status += f"Sort: {self.config.sort_by} | "
        status += f"Filter: {self.config.filter_query or 'none'} | "
        status += f"Press ? for help | q to quit"
        status += f"{' ' * max(0, self._width - len(status) - 10)}"
        status += f"{Color.BOLD}{Color.CYAN}║{Color.RESET}"
        
        sys.stdout.write(status + "\n")
    
    def _render_message(self) -> None:
        """渲染消息"""
        if self._message and time.time() - self._message_time < 5:
            sys.stdout.write(f"{Color.BOLD}{Color.CYAN}╠{'─' * (self._width - 2)}╣{Color.RESET}\n")
            
            # 截断消息以适应宽度
            msg_lines = self._message.split("\n")
            for line in msg_lines[:5]:  # 最多显示5行
                truncated = line[:self._width - 4]
                sys.stdout.write(f"{Color.BOLD}{Color.CYAN}║{Color.RESET} {truncated}{' ' * max(0, self._width - len(truncated) - 4)}{Color.BOLD}{Color.CYAN}║{Color.RESET}\n")
        
        sys.stdout.write(f"{Color.BOLD}{Color.CYAN}╚{'═' * (self._width - 2)}╝{Color.RESET}\n")


def run_tui() -> None:
    """运行TUI入口"""
    tui = ProcessTUI()
    try:
        tui.start()
    except KeyboardInterrupt:
        pass
    finally:
        tui.stop()
