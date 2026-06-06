#!/usr/bin/env python3
"""
Shell Tool - Secure command execution and system operations for MCP Server

This tool provides safe command execution with intelligent output analysis,
security controls, and system monitoring. Optimized for GitHub Copilot 
agent mode with comprehensive error handling and actionable insights.
"""

import os
import logging
import subprocess
import asyncio
import platform
import psutil
import shutil
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class ShellTool:
    """
    Secure shell command execution with intelligent analysis and safety controls
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system_info = self._get_system_info()
        self.command_history = []
        self.max_history = 100
        
        # Security settings
        self.dangerous_commands = {
            'rm -rf', 'del /s', 'format', 'fdisk', 'mkfs', 'dd if=', 'kill -9',
            'shutdown', 'reboot', 'halt', 'init 0', 'init 6', 'sudo rm',
            'chmod 777', 'chown -R', '> /dev/', 'curl | bash', 'wget | bash'
        }
        
        # Command timeout settings
        self.default_timeout = 300
        self.max_timeout = 300
        
        self.logger.info(f"Shell tool initialized on {self.system_info['platform']}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cwd': os.getcwd(),
                'user': os.environ.get('USER', os.environ.get('USERNAME', 'unknown')),
                'shell': os.environ.get('SHELL', os.environ.get('COMSPEC', 'unknown')),
                'path_separator': os.pathsep,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {'platform': 'unknown', 'system': 'unknown'}
    
    async def bb7_run_command(self, arguments: Dict[str, Any]) -> str:
        """
        ⚡ Execute shell commands safely with intelligent output analysis, error diagnosis, and 
        security controls. Perfect for development tasks, system administration, and automation.
        Provides detailed execution results, performance metrics, and actionable suggestions for 
        command optimization and troubleshooting.
        """
        command = arguments.get('command', '')
        working_directory = arguments.get('working_directory', '.')
        timeout = arguments.get('timeout', self.default_timeout)
        capture_output = arguments.get('capture_output', True)
        environment = arguments.get('environment', {})
        
        if not command:
            return "❌ Please provide a command to execute. Example: 'ls -la' or 'git status'"
        
        # Security check
        security_check = self._check_command_security(command)
        if not security_check['safe']:
            return f"❌ **Security Warning:** {security_check['reason']}\n\n💡 **Suggestion:** {security_check['suggestion']}"
        
        try:
            start_time = time.time()
            
            # Prepare environment
            env = os.environ.copy()
            env.update(environment)
            
            # Validate working directory
            work_dir = Path(working_directory).expanduser().resolve()
            if not work_dir.exists():
                return f"❌ Working directory '{working_directory}' does not exist"
            
            # Execute command
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(work_dir),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=min(timeout, self.max_timeout)
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(work_dir),
                    env=env,
                    timeout=min(timeout, self.max_timeout)
                )
                self.set_default_output(result)
            
            execution_time = time.time() - start_time
            
            # Store in history
            history_entry = {
                'command': command,
                'working_directory': str(work_dir),
                'exit_code': result.returncode,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat(),
                'environment_vars': list(environment.keys()) if environment else []
            }
            
            self.command_history.append(history_entry)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
            
            # Build response
            response = f"⚡ **Command Executed:** `{command}`\n"
            response += f"📁 **Directory:** {work_dir}\n"
            response += f"⏱️ **Execution Time:** {execution_time:.2f}s\n"
            
            # Ensure stdout and stderr are strings
            stdout_str = result.stdout if isinstance(result.stdout, str) else (result.stdout.decode('utf-8', errors='replace') if result.stdout else "")
            stderr_str = result.stderr if isinstance(result.stderr, str) else (result.stderr.decode('utf-8', errors='replace') if result.stderr else "")
            
            if result.returncode == 0:
                response += f"✅ **Status:** Success (exit code: 0)\n\n"
                
                if stdout_str and stdout_str.strip():
                    # Analyze and format output
                    output_analysis = await self._analyze_command_output(command, stdout_str)
                    
                    response += f"📤 **Output:**\n```\n{stdout_str.strip()}\n```\n"
                    
                    if output_analysis:
                        response += f"\n🔍 **Analysis:** {output_analysis}\n"
                    
                    # Performance insights
                    perf_insights = self._get_performance_insights(command, execution_time, stdout_str)
                    if perf_insights:
                        response += f"📊 **Performance:** {perf_insights}\n"
                else:
                    response += f"📤 **Output:** Command completed successfully with no output\n"
                
                # Command-specific suggestions
                suggestions = await self._get_command_suggestions(command, stdout_str)
                if suggestions:
                    response += f"💡 **Suggestions:** {suggestions}"
                    
            else:
                response += f"❌ **Status:** Failed (exit code: {result.returncode})\n\n"
                
                if stderr_str and stderr_str.strip():
                    response += f"🚨 **Error Output:**\n```\n{stderr_str.strip()}\n```\n"
                    
                    # Error analysis and solutions
                    error_analysis = await self._analyze_error_output(command, stderr_str, result.returncode)
                    if error_analysis:
                        response += f"\n🔧 **Error Analysis:** {error_analysis['diagnosis']}\n"
                        response += f"💡 **Suggested Solution:** {error_analysis['solution']}\n"
                        
                        if error_analysis.get('alternative_commands'):
                            response += f"🔄 **Alternative Commands:**\n"
                            for alt_cmd in error_analysis['alternative_commands']:
                                response += f"  • `{alt_cmd}`\n"
                
                if stdout_str and stdout_str.strip():
                    response += f"\n📤 **Standard Output:**\n```\n{stdout_str.strip()}\n```\n"
            
            self.logger.info(f"Executed command: {command} (exit: {result.returncode}, time: {execution_time:.2f}s)")
            return response
            
        except subprocess.TimeoutExpired:
            return f"⏰ **Timeout:** Command '{command}' exceeded {timeout} seconds\n\n💡 **Suggestions:**\n  • Try with a longer timeout\n  • Check if the command is hanging or waiting for input\n  • Consider running the command in background mode"
        
        except FileNotFoundError:
            return f"❌ **Command Not Found:** '{command}' is not recognized\n\n💡 **Suggestions:**\n  • Check if the program is installed\n  • Verify the command spelling\n  • Check your PATH environment variable\n  • Use 'which {command.split()[0]}' to locate the program"
        
        except PermissionError:
            return f"🔒 **Permission Denied:** Insufficient privileges to execute '{command}'\n\n💡 **Suggestions:**\n  • Run as administrator/sudo if needed\n  • Check file permissions\n  • Verify you have execute permissions in the directory"
        
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            return f"❌ **Execution Error:** {str(e)}\n\n💡 **Suggestion:** Check command syntax and system requirements"

    def set_default_output(self, result):
        result.stdout = "Command executed without output capture"
        result.stderr = ""
    
    async def bb7_get_system_info(self, arguments: Dict[str, Any]) -> str:
        """
        💻 Get comprehensive system information including hardware specs, OS details, running processes, 
        disk usage, memory utilization, and network status. Perfect for troubleshooting, performance 
        monitoring, and understanding your development environment. Provides actionable insights for 
        system optimization and resource management.
        """
        include_processes = arguments.get('include_processes', False)
        include_network = arguments.get('include_network', False)
        include_disk_usage = arguments.get('include_disk_usage', True)
        
        try:
            # Refresh system info
            current_info = self._get_system_info()
            
            response = f"💻 **System Information**\n\n"
            
            # Basic system info
            response += f"🖥️ **Platform:**\n"
            response += f"  • OS: {current_info['platform']}\n"
            response += f"  • System: {current_info['system']}\n"
            response += f"  • Architecture: {current_info['architecture']}\n"
            response += f"  • Processor: {current_info['processor']}\n"
            response += f"  • Python: {current_info['python_version']}\n\n"
            
            # Environment info
            response += f"🌍 **Environment:**\n"
            response += f"  • User: {current_info['user']}\n"
            response += f"  • Shell: {current_info['shell']}\n"
            response += f"  • Working Directory: {current_info['cwd']}\n"
            response += f"  • PATH Separator: {current_info['path_separator']}\n\n"
            
            # Hardware info
            response += f"⚙️ **Hardware:**\n"
            response += f"  • CPU Cores: {current_info['cpu_count']}\n"
            response += f"  • Total Memory: {self._format_bytes(current_info['memory_total'])}\n"
            response += f"  • Available Memory: {self._format_bytes(current_info['memory_available'])}\n"
            
            # CPU and memory usage
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                response += f"  • CPU Usage: {cpu_percent}%\n"
                response += f"  • Memory Usage: {memory.percent}% ({self._format_bytes(memory.used)} used)\n"
            except Exception as e:
                response += f"  • Usage info unavailable: {e}\n"
            
            response += "\n"
            
            # Disk usage
            if include_disk_usage:
                try:
                    disk_usage = []
                    for partition in psutil.disk_partitions():
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            disk_usage.append({
                                'device': partition.device,
                                'mountpoint': partition.mountpoint,
                                'fstype': partition.fstype,
                                'total': usage.total,
                                'used': usage.used,
                                'free': usage.free,
                                'percent': (usage.used / usage.total) * 100
                            })
                        except PermissionError:
                            continue
                    
                    if disk_usage:
                        response += f"💾 **Disk Usage:**\n"
                        for disk in disk_usage:
                            response += f"  • **{disk['device']}** ({disk['fstype']})\n"
                            response += f"    Mount: {disk['mountpoint']}\n"
                            response += f"    Total: {self._format_bytes(disk['total'])}\n"
                            response += f"    Used: {self._format_bytes(disk['used'])} ({disk['percent']:.1f}%)\n"
                            response += f"    Free: {self._format_bytes(disk['free'])}\n"
                        response += "\n"
                        
                        # Disk usage warnings
                        high_usage_disks = [disk for disk in disk_usage if disk['percent'] > 85]
                        if high_usage_disks:
                            response += f"⚠️ **Disk Space Warning:** High usage detected on:\n"
                            for disk in high_usage_disks:
                                response += f"  • {disk['device']}: {disk['percent']:.1f}% full\n"
                            response += "\n"
                
                except Exception as e:
                    response += f"💾 **Disk Usage:** Unable to retrieve disk information: {e}\n\n"
            
            # Network information
            if include_network:
                try:
                    network_info = psutil.net_if_addrs()
                    network_stats = psutil.net_io_counters()
                    
                    response += f"🌐 **Network:**\n"
                    response += f"  • Bytes Sent: {self._format_bytes(network_stats.bytes_sent)}\n"
                    response += f"  • Bytes Received: {self._format_bytes(network_stats.bytes_recv)}\n"
                    response += f"  • Packets Sent: {network_stats.packets_sent:,}\n"
                    response += f"  • Packets Received: {network_stats.packets_recv:,}\n"
                    
                    # Show active network interfaces
                    active_interfaces = []
                    for interface, addresses in network_info.items():
                        for addr in addresses:
                            if addr.family.name == 'AF_INET' and addr.address != '127.0.0.1':
                                active_interfaces.append(f"{interface}: {addr.address}")
                    
                    if active_interfaces:
                        response += f"  • Active Interfaces:\n"
                        for interface in active_interfaces[:5]:  # Show top 5
                            response += f"    - {interface}\n"
                    
                    response += "\n"
                    
                except Exception as e:
                    response += f"🌐 **Network:** Unable to retrieve network information: {e}\n\n"
            
            # Process information
            if include_processes:
                try:
                    processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                        try:
                            proc_info = proc.info
                            if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 1:
                                processes.append(proc_info)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    # Sort by CPU usage
                    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                    
                    response += f"📊 **Top Processes by CPU Usage:**\n"
                    for proc in processes[:10]:  # Top 10 processes
                        response += f"  • **{proc['name']}** (PID: {proc['pid']})\n"
                        response += f"    CPU: {proc['cpu_percent']:.1f}% | Memory: {proc['memory_percent']:.1f}%\n"
                    
                    response += "\n"
                    
                except Exception as e:
                    response += f"📊 **Processes:** Unable to retrieve process information: {e}\n\n"
            
            # Development environment detection
            dev_tools = await self._detect_development_tools()
            if dev_tools:
                response += f"🛠️ **Development Tools Detected:**\n"
                for tool, version in dev_tools.items():
                    response += f"  • {tool}: {version}\n"
                response += "\n"
            
            # System health assessment
            health_issues = self._assess_system_health(current_info)
            if health_issues:
                response += f"🏥 **System Health Issues:**\n"
                for issue in health_issues:
                    response += f"  • {issue}\n"
                response += "\n"
            
            # Performance recommendations
            recommendations = self._get_performance_recommendations(current_info)
            if recommendations:
                response += f"💡 **Performance Recommendations:**\n"
                for rec in recommendations:
                    response += f"  • {rec}\n"
            
            self.logger.info("Generated comprehensive system information")
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return f"❌ Error retrieving system information: {str(e)}"
    
    async def bb7_list_processes(self, arguments: Dict[str, Any]) -> str:
        """
        📊 List and analyze running processes with intelligent filtering, resource usage analysis, 
        and performance insights. Perfect for troubleshooting resource issues, monitoring system 
        performance, and identifying processes that may be affecting development work. Provides 
        actionable recommendations for process management and optimization.
        """
        filter_pattern = arguments.get('filter', '')
        sort_by = arguments.get('sort_by', 'cpu')  # cpu, memory, name, pid
        limit = arguments.get('limit', 20)
        show_system_processes = arguments.get('show_system_processes', False)
        
        try:
            processes = []
            
            # Collect process information
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'create_time', 'status', 'username']):
                try:
                    proc_info = proc.info
                    
                    # Apply filter if specified
                    if filter_pattern and filter_pattern.lower() not in proc_info['name'].lower():
                        continue
                    
                    # Skip system processes if not requested
                    if not show_system_processes:
                        system_users = ['SYSTEM', 'NT AUTHORITY\\SYSTEM', 'root', '_windowsupdate']
                        if proc_info.get('username') in system_users:
                            continue
                    
                    # Calculate additional metrics
                    proc_info['memory_mb'] = proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
                    proc_info['age_hours'] = (time.time() - proc_info['create_time']) / 3600 if proc_info['create_time'] else 0
                    
                    processes.append(proc_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort processes
            sort_keys = {
                'cpu': lambda x: x['cpu_percent'],
                'memory': lambda x: x['memory_percent'],
                'name': lambda x: x['name'].lower(),
                'pid': lambda x: x['pid'],
                'age': lambda x: x['age_hours']
            }
            
            if sort_by in sort_keys:
                processes.sort(key=sort_keys[sort_by], reverse=(sort_by in ['cpu', 'memory', 'age']))
            
            # Limit results
            processes = processes[:limit]
            
            if not processes:
                return f"📊 **Process List:** No processes found matching criteria\n\n💡 **Tips:**\n  • Try removing filters\n  • Enable system processes with show_system_processes=true\n  • Check if the system is running normally"
            
            # Build response
            response = f"📊 **Running Processes** (sorted by {sort_by})\n"
            if filter_pattern:
                response += f"🔍 **Filter:** {filter_pattern}\n"
            response += f"📈 **Showing:** {len(processes)} of {len(list(psutil.process_iter()))} total processes\n\n"
            
            # Summary statistics
            total_cpu = sum(proc['cpu_percent'] for proc in processes)
            total_memory = sum(proc['memory_percent'] for proc in processes)
            avg_age = sum(proc['age_hours'] for proc in processes) / len(processes)
            
            response += f"📊 **Summary:**\n"
            response += f"  • Total CPU (shown): {total_cpu:.1f}%\n"
            response += f"  • Total Memory (shown): {total_memory:.1f}%\n"
            response += f"  • Average Age: {avg_age:.1f} hours\n\n"
            
            # Process list
            response += f"📋 **Process Details:**\n"
            for i, proc in enumerate(processes, 1):
                # Status emoji
                status_emoji = "🟢" if proc['status'] == 'running' else "🟡" if proc['status'] == 'sleeping' else "🔴"
                
                # Resource usage indicators
                cpu_indicator = "🔥" if proc['cpu_percent'] > 20 else "⚡" if proc['cpu_percent'] > 5 else "💤"
                memory_indicator = "🧠" if proc['memory_percent'] > 10 else "📝" if proc['memory_percent'] > 1 else "💾"
                
                response += f"**{i}. {proc['name']}** {status_emoji}\n"
                response += f"   PID: {proc['pid']} | User: {proc.get('username', 'unknown')}\n"
                response += f"   {cpu_indicator} CPU: {proc['cpu_percent']:.1f}% | {memory_indicator} Memory: {proc['memory_percent']:.1f}% ({proc['memory_mb']:.1f} MB)\n"
                response += f"   ⏰ Age: {proc['age_hours']:.1f} hours | Status: {proc['status']}\n\n"
            
            # Identify resource-heavy processes
            high_cpu = [p for p in processes if p['cpu_percent'] > 25]
            high_memory = [p for p in processes if p['memory_percent'] > 15]
            
            if high_cpu:
                response += f"🔥 **High CPU Usage Processes:**\n"
                for proc in high_cpu:
                    response += f"  • **{proc['name']}**: {proc['cpu_percent']:.1f}% CPU\n"
                response += "\n"
            
            if high_memory:
                response += f"🧠 **High Memory Usage Processes:**\n"
                for proc in high_memory:
                    response += f"  • **{proc['name']}**: {proc['memory_percent']:.1f}% Memory ({proc['memory_mb']:.1f} MB)\n"
                response += "\n"
            
            # Development-related processes
            dev_processes = [p for p in processes if any(dev_tool in p['name'].lower() for dev_tool in 
                           ['python', 'node', 'npm', 'yarn', 'java', 'code', 'git', 'docker', 'postgres', 'mysql', 'redis'])]
            
            if dev_processes:
                response += f"🛠️ **Development-Related Processes:**\n"
                for proc in dev_processes:
                    response += f"  • **{proc['name']}**: {proc['cpu_percent']:.1f}% CPU, {proc['memory_percent']:.1f}% Memory\n"
                response += "\n"
            
            # Recommendations
            recommendations = []
            
            if high_cpu:
                recommendations.append("Consider investigating high CPU usage processes")
            
            if high_memory:
                recommendations.append("Monitor high memory usage processes for potential memory leaks")
            
            if total_cpu > 80:
                recommendations.append("System CPU usage is high - consider closing unnecessary applications")
            
            if total_memory > 85:
                recommendations.append("System memory usage is high - consider restarting memory-heavy applications")
            
            old_processes = [p for p in processes if p['age_hours'] > 72]  # 3 days
            if old_processes:
                recommendations.append(f"{len(old_processes)} processes have been running for over 3 days - consider if restarts are needed")
            
            if recommendations:
                response += f"💡 **Recommendations:**\n"
                for rec in recommendations:
                    response += f"  • {rec}\n"
                response += "\n"
            
            response += f"💡 **Tips:**\n"
            response += f"  • Use bb7_run_command with 'kill [PID]' to terminate processes\n"
            response += f"  • Filter processes: bb7_list_processes filter='python'\n"
            response += f"  • Sort by memory: bb7_list_processes sort_by='memory'"
            
            self.logger.info(f"Listed {len(processes)} processes (sorted by {sort_by})")
            return response
            
        except Exception as e:
            self.logger.error(f"Error listing processes: {e}")
            return f"❌ Error listing processes: {str(e)}"
    
    async def bb7_get_command_history(self, arguments: Dict[str, Any]) -> str:
        """
        📜 View command execution history with performance analysis, success rates, and usage patterns.
        Perfect for reviewing recent development activities, analyzing command performance, and 
        identifying frequently used commands for automation opportunities. Provides insights into 
        command efficiency and suggests optimizations.
        """
        limit = arguments.get('limit', 20)
        filter_pattern = arguments.get('filter', '')
        show_successful_only = arguments.get('show_successful_only', False)
        
        try:
            if not self.command_history:
                return f"📜 **Command History:** No commands executed yet\n\n💡 **Tip:** Execute some commands using bb7_run_command to build up history"
            
            # Filter history
            filtered_history = self.command_history.copy()
            
            if filter_pattern:
                filtered_history = [cmd for cmd in filtered_history if filter_pattern.lower() in cmd['command'].lower()]
            
            if show_successful_only:
                filtered_history = [cmd for cmd in filtered_history if cmd['exit_code'] == 0]
            
            # Sort by timestamp (most recent first)
            filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Limit results
            displayed_history = filtered_history[:limit]
            
            if not displayed_history:
                filter_msg = f" matching '{filter_pattern}'" if filter_pattern else ""
                success_msg = " (successful only)" if show_successful_only else ""
                return f"📜 **Command History:** No commands found{filter_msg}{success_msg}"
            
            # Build response
            response = f"📜 **Command History** (last {len(displayed_history)} commands)\n"
            if filter_pattern:
                response += f"🔍 **Filter:** {filter_pattern}\n"
            if show_successful_only:
                response += f"✅ **Showing:** Successful commands only\n"
            response += "\n"
            
            # Summary statistics
            total_commands = len(self.command_history)
            successful_commands = len([cmd for cmd in self.command_history if cmd['exit_code'] == 0])
            avg_execution_time = sum(cmd['execution_time'] for cmd in self.command_history) / len(self.command_history)
            
            response += f"📊 **Statistics:**\n"
            response += f"  • Total Commands: {total_commands}\n"
            response += f"  • Success Rate: {(successful_commands / total_commands * 100):.1f}%\n"
            response += f"  • Average Execution Time: {avg_execution_time:.2f}s\n\n"
            
            # Command list
            response += f"📋 **Recent Commands:**\n"
            for i, cmd in enumerate(displayed_history, 1):
                # Status indicators
                status_emoji = "✅" if cmd['exit_code'] == 0 else "❌"
                
                # Performance indicators
                if cmd['execution_time'] < 1:
                    perf_emoji = "⚡"
                elif cmd['execution_time'] < 5:
                    perf_emoji = "🏃"
                else:
                    perf_emoji = "🐌"
                
                # Time formatting
                cmd_time = datetime.fromisoformat(cmd['timestamp'])
                time_ago = self._format_time_ago(cmd_time)
                
                response += f"**{i}. {cmd['command']}** {status_emoji}\n"
                response += f"   📁 Directory: {cmd['working_directory']}\n"
                response += f"   {perf_emoji} Time: {cmd['execution_time']:.2f}s | Exit: {cmd['exit_code']} | {time_ago}\n"
                
                if cmd.get('environment_vars'):
                    response += f"   🌍 Environment: {', '.join(cmd['environment_vars'])}\n"
                
                response += "\n"
            
            # Command frequency analysis
            command_names = [cmd['command'].split()[0] for cmd in self.command_history if cmd['command'].split()]
            from collections import Counter
            command_counter = Counter(command_names)
            top_commands = command_counter.most_common(5)
            
            if top_commands:
                response += f"🔥 **Most Used Commands:**\n"
                for cmd_name, count in top_commands:
                    percentage = (count / total_commands) * 100
                    response += f"  • **{cmd_name}**: {count} times ({percentage:.1f}%)\n"
                response += "\n"
            
            # Performance analysis
            slow_commands = [cmd for cmd in self.command_history if cmd['execution_time'] > 10]
            if slow_commands:
                response += f"🐌 **Slow Commands** (>10s):\n"
                for cmd in slow_commands[-3:]:  # Show last 3 slow commands
                    response += f"  • `{cmd['command']}`: {cmd['execution_time']:.2f}s\n"
                response += "\n"
            
            # Error analysis
            failed_commands = [cmd for cmd in self.command_history if cmd['exit_code'] != 0]
            if failed_commands:
                error_rate = (len(failed_commands) / total_commands) * 100
                response += f"❌ **Failed Commands:** {len(failed_commands)} ({error_rate:.1f}% error rate)\n"
                
                # Show recent failures
                recent_failures = [cmd for cmd in failed_commands[-3:]]
                for cmd in recent_failures:
                    response += f"  • `{cmd['command']}` (exit: {cmd['exit_code']})\n"
                response += "\n"
            
            # Recommendations
            recommendations = []
            
            if len(failed_commands) > total_commands * 0.2:
                recommendations.append("High error rate detected - review command syntax and environment setup")
            
            if slow_commands:
                recommendations.append("Some commands are slow - consider optimization or alternative approaches")
            
            if top_commands:
                most_common = top_commands[0][0]
                if top_commands[0][1] > 5:
                    recommendations.append(f"Consider creating an alias or script for frequently used '{most_common}' commands")
            
            # Check for repetitive patterns
            recent_commands = [cmd['command'] for cmd in self.command_history[-10:]]
            if len(set(recent_commands)) < len(recent_commands) * 0.5:
                recommendations.append("Repetitive command patterns detected - consider automation with scripts")
            
            if recommendations:
                response += f"💡 **Recommendations:**\n"
                for rec in recommendations:
                    response += f"  • {rec}\n"
                response += "\n"
            
            response += f"💡 **Tips:**\n"
            response += f"  • Filter history: bb7_get_command_history filter='git'\n"
            response += f"  • Show only successful: bb7_get_command_history show_successful_only=true\n"
            response += f"  • Use command history to identify automation opportunities"
            
            self.logger.info(f"Retrieved command history: {len(displayed_history)} entries")
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting command history: {e}")
            return f"❌ Error retrieving command history: {str(e)}"
    
    # Helper methods for intelligent analysis
    def _check_command_security(self, command: str) -> Dict[str, Any]:
        """Check if command is safe to execute"""
        command_lower = command.lower()
        
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return {
                    'safe': False,
                    'reason': f"Command contains potentially dangerous pattern: '{dangerous}'",
                    'suggestion': "Review the command carefully and run manually if you're certain it's safe"
                }
        
        # Check for suspicious patterns
        if '|' in command and any(unsafe in command_lower for unsafe in ['curl', 'wget', 'bash', 'sh']):
            return {
                'safe': False,
                'reason': "Command uses piping with potentially unsafe download/execution patterns",
                'suggestion': "Download and inspect scripts before executing them"
            }
        
        if command.count(';') > 3:
            return {
                'safe': False,
                'reason': "Command contains many chained operations which could be risky",
                'suggestion': "Break down into smaller, individual commands for safety"
            }
        
        return {'safe': True}
    
    async def _analyze_command_output(self, command: str, output: str) -> Optional[str]:
        """Analyze command output for insights"""
        cmd_parts = command.lower().split()
        if not cmd_parts:
            return None
        
        base_cmd = cmd_parts[0]
        
        # Git command analysis
        if base_cmd == 'git':
            if 'status' in command:
                if 'nothing to commit' in output:
                    return "Repository is clean - all changes committed"
                elif 'Changes not staged' in output:
                    return "Unstaged changes detected - use 'git add' to stage files"
                elif 'Changes to be committed' in output:
                    return "Staged changes ready for commit"
            elif 'log' in command:
                commit_count = output.count('commit ')
                return f"Showing {commit_count} commits in history"
            elif 'branch' in command:
                branches = [line.strip() for line in output.split('\n') if line.strip()]
                return f"Repository has {len(branches)} branches"
        
        # Directory listing analysis
        elif base_cmd in ['ls', 'dir']:
            lines = [line for line in output.split('\n') if line.strip()]
            return f"Directory contains {len(lines)} items"
        
        # Python command analysis
        elif base_cmd == 'python':
            if '--version' in command:
                return "Python version information"
            elif 'pip' in command:
                if 'install' in command:
                    return "Package installation completed"
                elif 'list' in command:
                    packages = [line for line in output.split('\n') if line.strip() and not line.startswith('Package')]
                    return f"Found {len(packages)} installed packages"
        
        # Node.js/npm analysis
        elif base_cmd in ['npm', 'yarn']:
            if 'install' in command:
                if 'added' in output:
                    return "Dependencies installed successfully"
                elif 'WARN' in output:
                    return "Installation completed with warnings - check for deprecated packages"
            elif 'list' in command:
                return "Package dependency tree displayed"
        
        # Process analysis
        elif base_cmd in ['ps', 'tasklist']:
            lines = [line for line in output.split('\n') if line.strip()]
            return f"System running {len(lines)} processes"
        
        return None
    
    async def _analyze_error_output(self, command: str, error: str, exit_code: int) -> Optional[Dict[str, Any]]:
        """Analyze error output and provide solutions"""
        error_lower = error.lower()
        cmd_parts = command.split()
        base_cmd = cmd_parts[0] if cmd_parts else ""
        
        # Common error patterns
        if 'command not found' in error_lower or 'is not recognized' in error_lower:
            return {
                'diagnosis': f"Command '{base_cmd}' is not installed or not in PATH",
                'solution': f"Install {base_cmd} or check if it's properly added to your PATH environment variable",
                'alternative_commands': [f'which {base_cmd}', f'where {base_cmd}', 'echo $PATH']
            }
        
        elif 'permission denied' in error_lower:
            return {
                'diagnosis': "Insufficient permissions to execute command",
                'solution': "Run with elevated privileges (sudo on Unix/Linux, Administrator on Windows) or check file permissions",
                'alternative_commands': [f'ls -la {cmd_parts[-1] if len(cmd_parts) > 1 else "."}']
            }
        
        elif 'no such file or directory' in error_lower:
            return {
                'diagnosis': "File or directory does not exist",
                'solution': "Check the path spelling and ensure the file/directory exists",
                'alternative_commands': ['ls -la', 'pwd', 'find . -name "*pattern*"']
            }
        
        elif 'connection refused' in error_lower or 'connection timeout' in error_lower:
            return {
                'diagnosis': "Network connection failed",
                'solution': "Check network connectivity, firewall settings, and target service availability",
                'alternative_commands': ['ping google.com', 'curl -I http://example.com']
            }
        
        # Git-specific errors
        elif base_cmd == 'git':
            if 'not a git repository' in error_lower:
                return {
                    'diagnosis': "Current directory is not a Git repository",
                    'solution': "Navigate to a Git repository or initialize one with 'git init'",
                    'alternative_commands': ['git init', 'git status', 'ls -la .git']
                }
            elif 'your branch is behind' in error_lower:
                return {
                    'diagnosis': "Local branch is behind remote",
                    'solution': "Pull latest changes with 'git pull' or merge manually",
                    'alternative_commands': ['git pull', 'git fetch', 'git merge origin/main']
                }
        
        # Python-specific errors
        elif 'python' in base_cmd:
            if 'modulenotfounderror' in error_lower:
                module_match = re.search(r"no module named '([^']+)'", error_lower)
                if module_match:
                    module_name = module_match.group(1)
                    return {
                        'diagnosis': f"Python module '{module_name}' is not installed",
                        'solution': f"Install the module using pip install {module_name}",
                        'alternative_commands': [f'pip install {module_name}', 'pip list', 'python -m pip install --upgrade pip']
                    }
        
        # Generic solutions based on exit codes
        if exit_code == 1:
            return {
                'diagnosis': "General error occurred",
                'solution': "Check command syntax and arguments",
                'alternative_commands': [f'{base_cmd} --help', f'man {base_cmd}']
            }
        elif exit_code == 2:
            return {
                'diagnosis': "Incorrect command usage",
                'solution': "Review command syntax and required arguments",
                'alternative_commands': [f'{base_cmd} --help']
            }
        
        return None
    
    def _get_performance_insights(self, command: str, execution_time: float, output: str) -> Optional[str]:
        """Generate performance insights for command execution"""
        insights = []
        
        if execution_time < 0.1:
            insights.append("Very fast execution")
        elif execution_time < 1:
            insights.append("Fast execution")
        elif execution_time < 5:
            insights.append("Moderate execution time")
        elif execution_time < 15:
            insights.append("Slow execution - consider optimization")
        else:
            insights.append("Very slow execution - investigate performance issues")
        
        # Output size analysis
        output_size = len(output)
        if output_size > 10000:
            insights.append("Large output generated - consider filtering or pagination")
        
        # Command-specific insights
        cmd_lower = command.lower()
        if 'find' in cmd_lower and execution_time > 2:
            insights.append("Find operation was slow - consider using more specific paths or filters")
        elif 'grep' in cmd_lower and execution_time > 1:
            insights.append("Grep search was slow - consider using more specific patterns")
        
        return " | ".join(insights) if insights else None
    
    async def _get_command_suggestions(self, command: str, output: str) -> Optional[str]:
        """Get suggestions for improving command usage"""
        suggestions = []
        cmd_lower = command.lower()
        
        # Git suggestions
        if cmd_lower.startswith('git'):
            if 'git status' in cmd_lower:
                suggestions.append("Use 'git status -s' for compact output")
            elif 'git log' in cmd_lower and '--oneline' not in cmd_lower:
                suggestions.append("Try 'git log --oneline' for compact history")
        
        # Directory listing suggestions
        elif cmd_lower.startswith('ls') and '-l' not in cmd_lower:
            suggestions.append("Use 'ls -la' for detailed file information including hidden files")
        
        # Python suggestions
        elif 'python' in cmd_lower:
            if 'pip install' in cmd_lower and '--user' not in cmd_lower:
                suggestions.append("Consider using 'pip install --user' for user-local installation")
        
        return " | ".join(suggestions) if suggestions else None
    
    async def _detect_development_tools(self) -> Dict[str, str]:
        """Detect installed development tools and their versions"""
        tools = {}
        
        tool_commands = {
            'Python': 'python --version',
            'Node.js': 'node --version',
            'npm': 'npm --version',
            'Git': 'git --version',
            'Docker': 'docker --version',
            'Java': 'java -version',
            'Go': 'go version',
            'Rust': 'rustc --version'
        }
        
        for tool_name, version_cmd in tool_commands.items():
            try:
                result = subprocess.run(
                    version_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version_output = result.stdout.strip() or result.stderr.strip()
                    # Extract version number from output
                    version_match = re.search(r'(\d+\.\d+\.\d+)', version_output)
                    if version_match:
                        tools[tool_name] = version_match.group(1)
                    else:
                        tools[tool_name] = version_output.split('\n')[0][:50]
                        
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                continue
        
        return tools
    
    def _assess_system_health(self, system_info: Dict[str, Any]) -> List[str]:
        """Assess system health and identify potential issues"""
        issues = []
        
        try:
            # Memory assessment
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                issues.append(f"Critical memory usage: {memory.percent}%")
            elif memory.percent > 80:
                issues.append(f"High memory usage: {memory.percent}%")
            
            # CPU assessment
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                issues.append(f"Critical CPU usage: {cpu_percent}%")
            elif cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            # Disk assessment
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    percent_used = (usage.used / usage.total) * 100
                    if percent_used > 95:
                        issues.append(f"Critical disk space on {partition.device}: {percent_used:.1f}%")
                    elif percent_used > 85:
                        issues.append(f"Low disk space on {partition.device}: {percent_used:.1f}%")
                except PermissionError:
                    continue
        
        except Exception as e:
            issues.append(f"Unable to assess system health: {e}")
        
        return issues
    
    def _get_performance_recommendations(self, system_info: Dict[str, Any]) -> List[str]:
        """Get system performance recommendations"""
        recommendations = []
        
        try:
            # Memory recommendations
            memory = psutil.virtual_memory()
            if memory.available < 1024 * 1024 * 1024:  # Less than 1GB available
                recommendations.append("Low available memory - consider closing unused applications")
            
            
            # Development recommendations
            if 'python' in str(system_info).lower():
                recommendations.append("Consider using virtual environments for Python development")
            
            if 'docker' not in str(system_info).lower():
                recommendations.append("Consider installing Docker for containerized development")
        
        except Exception:
            pass
        
        return recommendations
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
        return f"{bytes_value:.1f} PB"
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format time difference as human readable string"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all available shell tools with proper MCP formatting"""
        return {
            'bb7_run_command': {
                'description': '⚡ Execute shell commands safely with intelligent output analysis, error diagnosis, and security controls. Perfect for development tasks, system administration, and automation. Provides detailed execution results, performance metrics, and actionable suggestions for command optimization and troubleshooting.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'Shell command to execute'
                        },
                        'working_directory': {
                            'type': 'string',
                            'description': 'Directory to run command in (defaults to current directory)',
                            'default': '.'
                        },
                        'timeout': {
                            'type': 'integer',
                            'description': 'Command timeout in seconds',
                            'default': 30
                        },
                        'capture_output': {
                            'type': 'boolean',
                            'description': 'Whether to capture command output',
                            'default': True
                        },
                        'environment': {
                            'type': 'object',
                            'description': 'Additional environment variables',
                            'additionalProperties': {'type': 'string'}
                        }
                    },
                    'required': ['command']
                },
                'function': self.bb7_run_command
            },
            'bb7_get_system_info': {
                'description': '💻 Get comprehensive system information including hardware specs, OS details, running processes, disk usage, memory utilization, and network status. Perfect for troubleshooting, performance monitoring, and understanding your development environment. Provides actionable insights for system optimization and resource management.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'include_processes': {
                            'type': 'boolean',
                            'description': 'Include running processes information',
                            'default': False
                        },
                        'include_network': {
                            'type': 'boolean',
                            'description': 'Include network interface information',
                            'default': False
                        },
                        'include_disk_usage': {
                            'type': 'boolean',
                            'description': 'Include disk usage information',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_get_system_info
            },
            'bb7_list_processes': {
                'description': '📊 List and analyze running processes with intelligent filtering, resource usage analysis, and performance insights. Perfect for troubleshooting resource issues, monitoring system performance, and identifying processes that may be affecting development work. Provides actionable recommendations for process management and optimization.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'filter': {
                            'type': 'string',
                            'description': 'Filter processes by name pattern'
                        },
                        'sort_by': {
                            'type': 'string',
                            'description': 'Sort processes by specified criteria',
                            'enum': ['cpu', 'memory', 'name', 'pid', 'age'],
                            'default': 'cpu'
                        },
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of processes to show',
                            'default': 20
                        },
                        'show_system_processes': {
                            'type': 'boolean',
                            'description': 'Include system processes in results',
                            'default': False
                        }
                    }
                },
                'function': self.bb7_list_processes
            },
            'bb7_get_command_history': {
                'description': '📜 View command execution history with performance analysis, success rates, and usage patterns. Perfect for reviewing recent development activities, analyzing command performance, and identifying frequently used commands for automation opportunities. Provides insights into command efficiency and suggests optimizations.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of commands to show',
                            'default': 20
                        },
                        'filter': {
                            'type': 'string',
                            'description': 'Filter commands by pattern'
                        },
                        'show_successful_only': {
                            'type': 'boolean',
                            'description': 'Show only successful commands',
                            'default': False
                        }
                    }
                },
                'function': self.bb7_get_command_history
            }
        }


# For standalone testing
if __name__ == "__main__":
    import asyncio
    
    async def test_shell_tool():
        logging.basicConfig(level=logging.INFO)
        tool = ShellTool()
        
        print("=== Testing Shell Tool ===")
        
        # Test system info
        result = await tool.bb7_get_system_info({'include_disk_usage': True})
        print(f"System info:\n{result}\n")
        
        # Test safe command execution
        result = await tool.bb7_run_command({'command': 'echo "Hello from shell tool"'})
        print(f"Command result:\n{result}\n")
        
        # Test command history
        result = await tool.bb7_get_command_history({'limit': 5})
        print(f"Command history:\n{result}\n")
    
    asyncio.run(test_shell_tool())
