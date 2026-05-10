#!/usr/bin/env python3
"""
ProcPilot CLI Entry Point
命令行入口
"""

import argparse
import sys
import json
from typing import Optional

from procpilot import __version__
from procpilot.core import ProcessManager, ProcessStatus
from procpilot.monitor import ProcessMonitor
from procpilot.tree import ProcessTree
from procpilot.alerts import AlertManager, AlertLevel


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="procpilot",
        description="🚀 ProcPilot - Lightweight Terminal Process Intelligence Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  procpilot                    Start interactive TUI
  procpilot list               List all processes
  procpilot top                Show top processes by CPU
  procpilot tree               Show process tree
  procpilot search python      Search for python processes
  procpilot kill 1234          Kill process with PID 1234
  procpilot info 1234          Show process details
  procpilot export report.json Export process report
  procpilot alerts             Show recent alerts

For more information, visit: https://github.com/gitstq/procpilot
        """
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="List all processes")
    list_parser.add_argument("-s", "--sort", choices=["cpu", "memory", "pid", "name"], 
                            default="cpu", help="Sort by field")
    list_parser.add_argument("-r", "--reverse", action="store_true", 
                            help="Reverse sort order")
    list_parser.add_argument("-f", "--filter", type=str, 
                            help="Filter processes by name/command")
    list_parser.add_argument("-l", "--limit", type=int, default=20,
                            help="Maximum number of processes to show")
    list_parser.add_argument("--json", action="store_true",
                            help="Output in JSON format")
    
    # top 命令
    top_parser = subparsers.add_parser("top", help="Show top processes")
    top_parser.add_argument("-n", "--number", type=int, default=10,
                           help="Number of processes to show")
    top_parser.add_argument("--cpu", action="store_true",
                           help="Sort by CPU (default)")
    top_parser.add_argument("--memory", action="store_true",
                           help="Sort by memory")
    
    # tree 命令
    tree_parser = subparsers.add_parser("tree", help="Show process tree")
    tree_parser.add_argument("-p", "--pid", type=int,
                            help="Root process PID")
    tree_parser.add_argument("-d", "--depth", type=int, default=5,
                            help="Maximum tree depth")
    tree_parser.add_argument("--compact", action="store_true",
                            help="Compact output format")
    
    # search 命令
    search_parser = subparsers.add_parser("search", help="Search processes")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-l", "--limit", type=int, default=20,
                              help="Maximum results")
    
    # kill 命令
    kill_parser = subparsers.add_parser("kill", help="Kill a process")
    kill_parser.add_argument("pid", type=int, help="Process ID")
    kill_parser.add_argument("-f", "--force", action="store_true",
                            help="Force kill (SIGKILL)")
    
    # suspend 命令
    suspend_parser = subparsers.add_parser("suspend", help="Suspend a process")
    suspend_parser.add_argument("pid", type=int, help="Process ID")
    
    # resume 命令
    resume_parser = subparsers.add_parser("resume", help="Resume a process")
    resume_parser.add_argument("pid", type=int, help="Process ID")
    
    # info 命令
    info_parser = subparsers.add_parser("info", help="Show process details")
    info_parser.add_argument("pid", type=int, help="Process ID")
    
    # export 命令
    export_parser = subparsers.add_parser("export", help="Export process report")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument("-f", "--format", choices=["json", "csv"],
                              default="json", help="Output format")
    
    # alerts 命令
    alerts_parser = subparsers.add_parser("alerts", help="Show alerts")
    alerts_parser.add_argument("-l", "--level", 
                              choices=["info", "warning", "critical", "emergency"],
                              help="Filter by alert level")
    alerts_parser.add_argument("-n", "--number", type=int, default=20,
                              help="Number of alerts to show")
    
    # monitor 命令
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring")
    monitor_parser.add_argument("-i", "--interval", type=float, default=1.0,
                               help="Monitoring interval in seconds")
    monitor_parser.add_argument("-d", "--duration", type=float,
                               help="Monitoring duration in seconds")
    
    # tag 命令
    tag_parser = subparsers.add_parser("tag", help="Manage process tags")
    tag_parser.add_argument("pid", type=int, help="Process ID")
    tag_parser.add_argument("tag", help="Tag name")
    tag_parser.add_argument("-r", "--remove", action="store_true",
                           help="Remove tag")
    
    # group 命令
    group_parser = subparsers.add_parser("group", help="Manage process groups")
    group_parser.add_argument("pid", type=int, help="Process ID")
    group_parser.add_argument("group", help="Group name")
    
    return parser


def cmd_list(args) -> int:
    """list命令实现"""
    manager = ProcessManager()
    processes = manager.get_all_processes()
    
    # 过滤
    if args.filter:
        query = args.filter.lower()
        processes = {
            k: v for k, v in processes.items()
            if query in v.name.lower() or query in v.command.lower()
        }
    
    # 排序
    sort_key = {
        "cpu": lambda p: p.cpu_percent,
        "memory": lambda p: p.memory_mb,
        "pid": lambda p: p.pid,
        "name": lambda p: p.name.lower(),
    }[args.sort]
    
    sorted_procs = sorted(processes.values(), key=sort_key, reverse=not args.reverse)
    
    # 限制数量
    sorted_procs = sorted_procs[:args.limit]
    
    if args.json:
        data = [p.to_dict() for p in sorted_procs]
        print(json.dumps(data, indent=2))
    else:
        print(f"\n{'PID':<8} {'NAME':<20} {'CPU%':>8} {'MEM(MB)':>10} {'STATUS':<10} {'USER':<12}")
        print("-" * 75)
        
        for proc in sorted_procs:
            print(f"{proc.pid:<8} {proc.name[:18]:<20} {proc.cpu_percent:>7.1f}% "
                  f"{proc.memory_mb:>9.1f} {proc.status.value:<10} "
                  f"{(proc.username or 'unknown')[:10]:<12}")
    
    return 0


def cmd_top(args) -> int:
    """top命令实现"""
    manager = ProcessManager()
    monitor = ProcessMonitor(manager)
    
    if args.memory:
        top_procs = monitor.get_top_memory_processes(args.number)
        print(f"\n📊 Top {args.number} Processes by Memory Usage\n")
        print(f"{'PID':<8} {'NAME':<20} {'MEMORY(MB)':>12} {'MEM%':>8}")
        print("-" * 55)
        for proc in top_procs:
            print(f"{proc.pid:<8} {proc.name[:18]:<20} {proc.memory_mb:>11.1f} "
                  f"{proc.memory_percent:>7.1f}%")
    else:
        top_procs = monitor.get_top_cpu_processes(args.number)
        print(f"\n📊 Top {args.number} Processes by CPU Usage\n")
        print(f"{'PID':<8} {'NAME':<20} {'CPU%':>8} {'MEM(MB)':>10}")
        print("-" * 50)
        for proc in top_procs:
            print(f"{proc.pid:<8} {proc.name[:18]:<20} {proc.cpu_percent:>7.1f}% "
                  f"{proc.memory_mb:>9.1f}")
    
    return 0


def cmd_tree(args) -> int:
    """tree命令实现"""
    manager = ProcessManager()
    tree = ProcessTree(manager)
    
    root = tree.build_tree(args.pid)
    
    if root is None:
        print("❌ No processes found or invalid PID")
        return 1
    
    if args.compact:
        print(tree.render_compact(root, args.depth))
    else:
        print("\n🌳 Process Tree\n")
        print(tree.render_ascii(root, args.depth, show_info=True))
    
    stats = tree.get_tree_statistics(root)
    print(f"\n📈 Statistics: {stats['total_nodes']} nodes, "
          f"max depth: {stats['max_depth']}, "
          f"leaves: {stats['leaf_count']}")
    
    return 0


def cmd_search(args) -> int:
    """search命令实现"""
    manager = ProcessManager()
    results = manager.search_processes(args.query)
    
    if not results:
        print(f"❌ No processes found matching '{args.query}'")
        return 1
    
    results = results[:args.limit]
    
    print(f"\n🔍 Search Results for '{args.query}' ({len(results)} found)\n")
    print(f"{'PID':<8} {'NAME':<20} {'CPU%':>8} {'MEM(MB)':>10} {'COMMAND':<30}")
    print("-" * 80)
    
    for proc in results:
        cmd = proc.command[:28] if proc.command else proc.name
        print(f"{proc.pid:<8} {proc.name[:18]:<20} {proc.cpu_percent:>7.1f}% "
              f"{proc.memory_mb:>9.1f} {cmd:<30}")
    
    return 0


def cmd_kill(args) -> int:
    """kill命令实现"""
    manager = ProcessManager()
    proc = manager.get_process(args.pid)
    
    if not proc:
        print(f"❌ Process with PID {args.pid} not found")
        return 1
    
    success = manager.kill_process(args.pid, force=args.force)
    
    if success:
        sig = "SIGKILL" if args.force else "SIGTERM"
        print(f"✅ Sent {sig} to process '{proc.name}' (PID: {args.pid})")
        return 0
    else:
        print(f"❌ Failed to kill process '{proc.name}' (PID: {args.pid})")
        print("   Try with --force or check permissions")
        return 1


def cmd_suspend(args) -> int:
    """suspend命令实现"""
    manager = ProcessManager()
    proc = manager.get_process(args.pid)
    
    if not proc:
        print(f"❌ Process with PID {args.pid} not found")
        return 1
    
    success = manager.suspend_process(args.pid)
    
    if success:
        print(f"✅ Suspended process '{proc.name}' (PID: {args.pid})")
        return 0
    else:
        print(f"❌ Failed to suspend process '{proc.name}' (PID: {args.pid})")
        return 1


def cmd_resume(args) -> int:
    """resume命令实现"""
    manager = ProcessManager()
    proc = manager.get_process(args.pid)
    
    if not proc:
        print(f"❌ Process with PID {args.pid} not found")
        return 1
    
    success = manager.resume_process(args.pid)
    
    if success:
        print(f"✅ Resumed process '{proc.name}' (PID: {args.pid})")
        return 0
    else:
        print(f"❌ Failed to resume process '{proc.name}' (PID: {args.pid})")
        return 1


def cmd_info(args) -> int:
    """info命令实现"""
    manager = ProcessManager()
    proc = manager.get_process(args.pid)
    
    if not proc:
        print(f"❌ Process with PID {args.pid} not found")
        return 1
    
    print(f"\n📋 Process Details\n")
    print(f"  PID:         {proc.pid}")
    print(f"  Name:        {proc.name}")
    print(f"  Status:      {proc.status.value}")
    print(f"  CPU:         {proc.cpu_percent:.1f}%")
    print(f"  Memory:      {proc.memory_mb:.1f} MB ({proc.memory_percent:.1f}%)")
    print(f"  Parent PID:  {proc.ppid}")
    print(f"  User:        {proc.username or 'unknown'}")
    print(f"  Threads:     {proc.num_threads}")
    print(f"  Priority:    {proc.priority.value}")
    print(f"  Command:     {proc.command or proc.name}")
    print(f"  Tags:        {', '.join(proc.tags) if proc.tags else 'none'}")
    print(f"  Group:       {proc.group or 'none'}")
    
    return 0


def cmd_export(args) -> int:
    """export命令实现"""
    manager = ProcessManager()
    monitor = ProcessMonitor(manager)
    
    if args.format == "json":
        success = monitor.export_report(args.output)
        if success:
            print(f"✅ Exported report to {args.output}")
            return 0
    else:
        # CSV格式
        import csv
        processes = manager.get_all_processes()
        
        with open(args.output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["PID", "Name", "Status", "CPU%", "Memory(MB)", 
                           "Memory%", "User", "Command"])
            
            for proc in processes.values():
                writer.writerow([
                    proc.pid, proc.name, proc.status.value,
                    f"{proc.cpu_percent:.1f}", f"{proc.memory_mb:.1f}",
                    f"{proc.memory_percent:.1f}", proc.username, proc.command
                ])
        
        print(f"✅ Exported {len(processes)} processes to {args.output}")
        return 0
    
    print(f"❌ Failed to export report")
    return 1


def cmd_alerts(args) -> int:
    """alerts命令实现"""
    manager = ProcessManager()
    monitor = ProcessMonitor(manager)
    alerts = AlertManager()
    
    # 检查当前进程
    processes = manager.get_all_processes()
    alerts.check_processes(processes)
    
    level = None
    if args.level:
        level = AlertLevel(args.level)
    
    alert_list = alerts.get_alerts(level=level, limit=args.number)
    
    if not alert_list:
        print("✅ No alerts")
        return 0
    
    print(f"\n🚨 Recent Alerts ({len(alert_list)} total)\n")
    
    level_colors = {
        AlertLevel.INFO: "\033[36m",      # Cyan
        AlertLevel.WARNING: "\033[33m",   # Yellow
        AlertLevel.CRITICAL: "\033[31m",  # Red
        AlertLevel.EMERGENCY: "\033[41m", # Red background
    }
    
    for alert in alert_list:
        color = level_colors.get(alert.level, "")
        reset = "\033[0m"
        print(f"{color}[{alert.level.value.upper()}]{reset} {alert.message}")
        print(f"         PID: {alert.pid}, Time: {alert.timestamp}")
        print()
    
    return 0


def cmd_monitor(args) -> int:
    """monitor命令实现"""
    import time
    
    manager = ProcessManager()
    monitor = ProcessMonitor(manager)
    
    print(f"\n📊 Starting process monitor (interval: {args.interval}s)")
    print("Press Ctrl+C to stop\n")
    
    monitor.start_monitoring(args.interval)
    
    try:
        if args.duration:
            time.sleep(args.duration)
        else:
            while True:
                time.sleep(1)
                summary = monitor.get_system_summary()
                print(f"\rProcesses: {summary['total_processes']} | "
                      f"CPU: {summary['total_cpu_percent']:.1f}% | "
                      f"Memory: {summary['total_memory_mb']:.0f}MB", end="")
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped")
    finally:
        monitor.stop_monitoring()
    
    return 0


def cmd_tag(args) -> int:
    """tag命令实现"""
    manager = ProcessManager()
    proc = manager.get_process(args.pid)
    
    if not proc:
        print(f"❌ Process with PID {args.pid} not found")
        return 1
    
    if args.remove:
        success = manager.remove_tag(args.pid, args.tag)
        if success:
            print(f"✅ Removed tag '{args.tag}' from process {proc.name}")
        else:
            print(f"❌ Tag '{args.tag}' not found on process")
        return 0 if success else 1
    else:
        success = manager.add_tag(args.pid, args.tag)
        if success:
            print(f"✅ Added tag '{args.tag}' to process {proc.name}")
        else:
            print(f"❌ Failed to add tag")
        return 0 if success else 1


def cmd_group(args) -> int:
    """group命令实现"""
    manager = ProcessManager()
    proc = manager.get_process(args.pid)
    
    if not proc:
        print(f"❌ Process with PID {args.pid} not found")
        return 1
    
    success = manager.set_group(args.pid, args.group)
    
    if success:
        print(f"✅ Set group '{args.group}' for process {proc.name}")
        return 0
    else:
        print(f"❌ Failed to set group")
        return 1


def main() -> int:
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 无命令时启动TUI
    if not args.command:
        try:
            from procpilot.tui import run_tui
            run_tui()
            return 0
        except ImportError:
            print("❌ TUI not available. Please use a command.")
            print("   Run 'procpilot --help' for available commands.")
            return 1
    
    # 路由到对应命令
    commands = {
        "list": cmd_list,
        "top": cmd_top,
        "tree": cmd_tree,
        "search": cmd_search,
        "kill": cmd_kill,
        "suspend": cmd_suspend,
        "resume": cmd_resume,
        "info": cmd_info,
        "export": cmd_export,
        "alerts": cmd_alerts,
        "monitor": cmd_monitor,
        "tag": cmd_tag,
        "group": cmd_group,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
