"""
ProcPilot Tree Module - Process Tree Visualization
进程树可视化模块
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from .core import ProcessManager, ProcessInfo


@dataclass
class TreeNode:
    """树节点"""
    pid: int
    name: str
    level: int
    children: List["TreeNode"]
    info: Optional[ProcessInfo] = None


class ProcessTree:
    """
    进程树可视化器
    
    提供进程树构建、可视化、遍历等功能
    """
    
    def __init__(self, process_manager: Optional[ProcessManager] = None):
        self.manager = process_manager or ProcessManager()
        self._tree_cache: Dict[int, TreeNode] = {}
        self._last_refresh: float = 0
    
    def build_tree(self, root_pid: Optional[int] = None) -> Optional[TreeNode]:
        """
        构建进程树
        
        Args:
            root_pid: 根进程PID，None表示从PID 0或1开始
            
        Returns:
            树根节点
        """
        processes = self.manager.get_all_processes()
        
        if not processes:
            return None
        
        # 构建父子关系映射
        children_map: Dict[int, List[int]] = {}
        for pid, proc in processes.items():
            if proc.ppid not in children_map:
                children_map[proc.ppid] = []
            children_map[proc.ppid].append(pid)
        
        # 确定根节点
        if root_pid is None:
            # 查找根进程（通常是PID 0或1）
            if 0 in children_map:
                root_pid = 0
            elif 1 in processes:
                root_pid = 1
            else:
                # 找到没有父进程的进程
                for pid, proc in processes.items():
                    if proc.ppid not in processes:
                        root_pid = pid
                        break
        
        if root_pid is None or root_pid not in processes:
            return None
        
        # 递归构建树
        def build_node(pid: int, level: int) -> Optional[TreeNode]:
            if pid not in processes:
                return None
            
            proc = processes[pid]
            node = TreeNode(
                pid=pid,
                name=proc.name,
                level=level,
                children=[],
                info=proc
            )
            
            for child_pid in children_map.get(pid, []):
                child_node = build_node(child_pid, level + 1)
                if child_node:
                    node.children.append(child_node)
            
            return node
        
        return build_node(root_pid, 0)
    
    def get_subtree(self, pid: int) -> Optional[TreeNode]:
        """
        获取指定进程的子树
        
        Args:
            pid: 进程PID
            
        Returns:
            子树根节点
        """
        return self.build_tree(root_pid=pid)
    
    def render_ascii(self, 
                     root: Optional[TreeNode] = None,
                     max_depth: int = 10,
                     show_info: bool = False) -> str:
        """
        渲染ASCII进程树
        
        Args:
            root: 根节点，None则自动构建
            max_depth: 最大深度
            show_info: 是否显示详细信息
            
        Returns:
            ASCII树字符串
        """
        if root is None:
            root = self.build_tree()
        
        if root is None:
            return "No processes found."
        
        lines = []
        
        def render_node(node: TreeNode, prefix: str = "", is_last: bool = True, depth: int = 0):
            if depth > max_depth:
                return
            
            # 构建当前行
            connector = "└── " if is_last else "├── "
            
            if show_info and node.info:
                info_str = f" [CPU: {node.info.cpu_percent:.1f}%, MEM: {node.info.memory_mb:.1f}MB, Status: {node.info.status.value}]"
            else:
                info_str = ""
            
            line = f"{prefix}{connector}{node.name} (PID: {node.pid}){info_str}"
            lines.append(line)
            
            # 递归渲染子节点
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(node.children):
                is_last_child = i == len(node.children) - 1
                render_node(child, new_prefix, is_last_child, depth + 1)
        
        # 渲染根节点
        root_info = ""
        if show_info and root.info:
            root_info = f" [CPU: {root.info.cpu_percent:.1f}%, MEM: {root.info.memory_mb:.1f}MB]"
        
        lines.append(f"{root.name} (PID: {root.pid}){root_info}")
        
        for i, child in enumerate(root.children):
            is_last = i == len(root.children) - 1
            render_node(child, "", is_last, 1)
        
        return "\n".join(lines)
    
    def render_compact(self, 
                       root: Optional[TreeNode] = None,
                       max_depth: int = 5) -> str:
        """
        渲染紧凑格式进程树
        
        Args:
            root: 根节点
            max_depth: 最大深度
            
        Returns:
            紧凑格式树字符串
        """
        if root is None:
            root = self.build_tree()
        
        if root is None:
            return "No processes found."
        
        lines = []
        
        def render_node(node: TreeNode, indent: int = 0, depth: int = 0):
            if depth > max_depth:
                return
            
            line = "  " * indent + f"→ {node.name} [{node.pid}]"
            lines.append(line)
            
            for child in node.children:
                render_node(child, indent + 1, depth + 1)
        
        render_node(root)
        return "\n".join(lines)
    
    def find_path(self, from_pid: int, to_pid: int) -> List[int]:
        """
        查找两个进程之间的路径
        
        Args:
            from_pid: 起始PID
            to_pid: 目标PID
            
        Returns:
            路径PID列表
        """
        processes = self.manager.get_all_processes()
        
        if from_pid not in processes or to_pid not in processes:
            return []
        
        # 从目标向上查找祖先
        path = [to_pid]
        current = to_pid
        
        while current in processes:
            proc = processes[current]
            if proc.ppid == from_pid:
                path.append(proc.ppid)
                return list(reversed(path))
            if proc.ppid == 0 or proc.ppid == current:
                break
            path.append(proc.ppid)
            current = proc.ppid
        
        return []
    
    def get_ancestors(self, pid: int) -> List[ProcessInfo]:
        """
        获取进程的所有祖先
        
        Args:
            pid: 进程PID
            
        Returns:
            祖先进程列表（从近到远）
        """
        processes = self.manager.get_all_processes()
        ancestors = []
        
        if pid not in processes:
            return ancestors
        
        current = pid
        visited = {pid}
        
        while current in processes:
            proc = processes[current]
            if proc.ppid in visited or proc.ppid == 0:
                break
            if proc.ppid in processes:
                ancestors.append(processes[proc.ppid])
                visited.add(proc.ppid)
            current = proc.ppid
        
        return ancestors
    
    def get_descendants(self, pid: int) -> List[ProcessInfo]:
        """
        获取进程的所有后代
        
        Args:
            pid: 进程PID
            
        Returns:
            后代进程列表
        """
        processes = self.manager.get_all_processes()
        descendants = []
        
        # 构建父子关系
        children_map: Dict[int, List[int]] = {}
        for p, proc in processes.items():
            if proc.ppid not in children_map:
                children_map[proc.ppid] = []
            children_map[proc.ppid].append(p)
        
        # BFS遍历
        queue = children_map.get(pid, [])
        visited = {pid}
        
        while queue:
            child_pid = queue.pop(0)
            if child_pid in visited:
                continue
            visited.add(child_pid)
            
            if child_pid in processes:
                descendants.append(processes[child_pid])
                queue.extend(children_map.get(child_pid, []))
        
        return descendants
    
    def count_descendants(self, pid: int) -> int:
        """统计后代进程数量"""
        return len(self.get_descendants(pid))
    
    def get_process_depth(self, pid: int) -> int:
        """
        获取进程在树中的深度
        
        Args:
            pid: 进程PID
            
        Returns:
            深度（根进程为0）
        """
        ancestors = self.get_ancestors(pid)
        return len(ancestors)
    
    def find_common_ancestor(self, pid1: int, pid2: int) -> Optional[ProcessInfo]:
        """
        查找两个进程的最近公共祖先
        
        Args:
            pid1: 第一个进程PID
            pid2: 第二个进程PID
            
        Returns:
            最近公共祖先进程
        """
        ancestors1 = set(p.pid for p in self.get_ancestors(pid1))
        ancestors2 = self.get_ancestors(pid2)
        
        for ancestor in ancestors2:
            if ancestor.pid in ancestors1:
                return ancestor
        
        return None
    
    def export_tree_json(self, root: Optional[TreeNode] = None) -> Dict[str, Any]:
        """
        导出树结构为JSON
        
        Args:
            root: 根节点
            
        Returns:
            JSON兼容的字典
        """
        if root is None:
            root = self.build_tree()
        
        if root is None:
            return {}
        
        def node_to_dict(node: TreeNode) -> Dict[str, Any]:
            return {
                "pid": node.pid,
                "name": node.name,
                "level": node.level,
                "info": node.info.to_dict() if node.info else None,
                "children": [node_to_dict(c) for c in node.children]
            }
        
        return node_to_dict(root)
    
    def get_tree_statistics(self, root: Optional[TreeNode] = None) -> Dict[str, Any]:
        """
        获取树统计信息
        
        Args:
            root: 根节点
            
        Returns:
            统计信息字典
        """
        if root is None:
            root = self.build_tree()
        
        if root is None:
            return {}
        
        total_nodes = 0
        max_depth = 0
        leaf_count = 0
        branch_count = 0
        
        def traverse(node: TreeNode, depth: int):
            nonlocal total_nodes, max_depth, leaf_count, branch_count
            
            total_nodes += 1
            max_depth = max(max_depth, depth)
            
            if node.children:
                branch_count += 1
                for child in node.children:
                    traverse(child, depth + 1)
            else:
                leaf_count += 1
        
        traverse(root, 0)
        
        return {
            "total_nodes": total_nodes,
            "max_depth": max_depth,
            "leaf_count": leaf_count,
            "branch_count": branch_count,
            "avg_branching_factor": round(branch_count / total_nodes, 2) if total_nodes > 0 else 0,
        }
