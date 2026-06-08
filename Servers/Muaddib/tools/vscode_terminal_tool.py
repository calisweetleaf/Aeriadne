#!/usr/bin/env python3
"""
VSCode Terminal Integration Tool - Advanced terminal session management for MCP Server

This tool provides seamless integration with VS Code's terminal environment,
offering intelligent command execution, session management, and development
workflow optimization. Optimized for GitHub Copilot agent mode with context
awareness and comprehensive terminal state management.
"""

import asyncio
import logging
import os
import json
import time
import subprocess
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import platform
import psutil


class VSCodeTerminalTool:
    """
    Advanced VS Code terminal integration with intelligent session management
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Terminal state tracking
        self.terminal_history = []
        self.current_directory = os.getcwd()
        self.environment_snapshot = dict(os.environ)
        self.session_data = {}
        
        # VS Code specific detection
        self.is_vscode_context = self._detect_vscode_context()
        
        # Terminal capabilities
        self.shell_type = self._detect_shell_type()
        self.system_info = self._get_system_info()
        
        # Command history and patterns
        self.command_patterns = {}
        self.performance_metrics = {}
        
        self.logger.info(f"VS Code terminal tool initialized (VS Code: {self.is_vscode_context}, Shell: {self.shell_type})")
    
    def _detect_vscode_context(self) -> bool:
        """Detect if running in VS Code context"""
        vscode_indicators = [
            'VSCODE_PID', 'VSCODE_CWD', 'TERM_PROGRAM', 
            'VSCODE_INJECTION', 'VSCODE_NONCE'
        ]
        
        for indicator in vscode_indicators:
            if os.environ.get(indicator):
                return True
        
        # Check if VS Code process is running
        try:
            for proc in psutil.process_iter(['name']):
                if 'code' in proc.info['name'].lower():
                    return True
        except:
            pass
        
        return False
    
    def _detect_shell_type(self) -> str:
        """Detect the current shell type"""
        shell = os.environ.get('SHELL', os.environ.get('COMSPEC', ''))
        
        if 'bash' in shell.lower():
            return 'bash'
        elif 'zsh' in shell.lower():
            return 'zsh'
        elif 'fish' in shell.lower():
            return 'fish'
        elif 'powershell' in shell.lower() or 'pwsh' in shell.lower():
            return 'powershell'
        elif 'cmd' in shell.lower():
            return 'cmd'
        else:
            return 'unknown'
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            'platform': platform.system(),
            'architecture': platform.architecture()[0],
            'cwd': os.getcwd(),
            'shell': self.shell_type,
            'python_version': platform.python_version(),
            'user': os.environ.get('USER', os.environ.get('USERNAME', 'unknown')),
            'home': os.path.expanduser('~')
        }
    
    def bb7_terminal_status(self, arguments: Dict[str, Any]) -> str:
        """
        🖥️ Get comprehensive VS Code terminal status including session information, environment 
        variables, development context, and integration state. Perfect for understanding your 
        current development environment, troubleshooting terminal issues, and optimizing your 
        workflow setup. Provides actionable insights for terminal configuration and usage.
        """
        include_environment = arguments.get('include_environment', True)
        include_integrations = arguments.get('include_integrations', True)
        include_performance = arguments.get('include_performance', True)
        
        try:
            # Build comprehensive status response
            response = f"🖥️ **VS Code Terminal Status**\n\n"
            
            # Basic terminal information
            response += f"📊 **Terminal Overview:**\n"
            response += f"  • VS Code Integration: {'✅ Active' if self.is_vscode_context else '❌ Not Detected'}\n"
            response += f"  • Shell Type: {self.shell_type.title()}\n"
            response += f"  • Current Directory: {self.current_directory}\n"
            response += f"  • Platform: {self.system_info['platform']} ({self.system_info['architecture']})\n"
            response += f"  • User: {self.system_info['user']}\n"
            response += f"  • Python Version: {self.system_info['python_version']}\n\n"
            
            # VS Code specific status
            if self.is_vscode_context:
                response += f"🎯 **VS Code Integration Details:**\n"
                
                vscode_vars = {
                    'VSCODE_PID': 'VS Code Process ID',
                    'VSCODE_CWD': 'VS Code Working Directory',
                    'TERM_PROGRAM': 'Terminal Program',
                    'VSCODE_INJECTION': 'VS Code Injection Status'
                }
                
                for var, description in vscode_vars.items():
                    value = os.environ.get(var)
                    if value:
                        response += f"  • {description}: {value}\n"
                
                # Detect workspace
                workspace_path = self._detect_workspace_path()
                if workspace_path:
                    response += f"  • Workspace: {workspace_path}\n"
                
                response += "\n"
            
            # Development environment detection
            dev_context = self._analyze_development_context()
            if dev_context:
                response += f"🛠️ **Development Context:**\n"
                
                if dev_context.get('project_type'):
                    response += f"  • Project Type: {dev_context['project_type']}\n"
                
                if dev_context.get('version_control'):
                    response += f"  • Version Control: {dev_context['version_control']}\n"
                
                if dev_context.get('virtual_environment'):
                    response += f"  • Virtual Environment: {dev_context['virtual_environment']}\n"
                
                if dev_context.get('package_managers'):
                    response += f"  • Package Managers: {', '.join(dev_context['package_managers'])}\n"
                
                response += "\n"
            
            # Environment variables (filtered)
            if include_environment:
                response += f"🌍 **Environment Summary:**\n"
                
                important_vars = {
                    'PATH': 'System PATH',
                    'VIRTUAL_ENV': 'Python Virtual Environment',
                    'CONDA_DEFAULT_ENV': 'Conda Environment',
                    'NODE_ENV': 'Node Environment',
                    'PYTHONPATH': 'Python Path',
                    'JAVA_HOME': 'Java Home',
                    'GO_PATH': 'Go Path'
                }
                
                for var, description in important_vars.items():
                    value = os.environ.get(var)
                    if value:
                        # Truncate long paths
                        display_value = value[:50] + '...' if len(value) > 50 else value
                        response += f"  • {description}: {display_value}\n"
                
                # PATH analysis
                path_dirs = os.environ.get('PATH', '').split(os.pathsep)
                response += f"  • PATH Directories: {len(path_dirs)} entries\n"
                
                response += "\n"
            
            # Terminal integrations and tools
            if include_integrations:
                integrations = self._detect_terminal_integrations()
                if integrations:
                    response += f"🔗 **Terminal Integrations:**\n"
                    for integration, status in integrations.items():
                        status_emoji = "✅" if status['available'] else "❌"
                        response += f"  • {integration}: {status_emoji} {status['description']}\n"
                    response += "\n"
            
            # Performance metrics
            if include_performance and self.terminal_history:
                response += f"📈 **Performance Metrics:**\n"
                
                recent_commands = self.terminal_history[-10:]
                avg_execution_time = sum(cmd.get('execution_time', 0) for cmd in recent_commands) / len(recent_commands)
                success_rate = sum(1 for cmd in recent_commands if cmd.get('success', False)) / len(recent_commands) * 100
                
                response += f"  • Recent Commands: {len(recent_commands)}\n"
                response += f"  • Average Execution Time: {avg_execution_time:.3f}s\n"
                response += f"  • Success Rate: {success_rate:.1f}%\n"
                response += f"  • Total Command History: {len(self.terminal_history)}\n"
                
                response += "\n"
            
            # Active processes (development-related)
            dev_processes = self._get_development_processes()
            if dev_processes:
                response += f"⚙️ **Development Processes:**\n"
                for proc in dev_processes[:5]:  # Show top 5
                    response += f"  • {proc['name']}: PID {proc['pid']} ({proc['cpu_percent']:.1f}% CPU)\n"
                response += "\n"
            
            # Terminal capabilities and features
            capabilities = self._analyze_terminal_capabilities()
            response += f"🎛️ **Terminal Capabilities:**\n"
            for capability, status in capabilities.items():
                status_emoji = "✅" if status else "❌"
                response += f"  • {capability.replace('_', ' ').title()}: {status_emoji}\n"
            response += "\n"
            
            # Recommendations and tips
            recommendations = self._generate_terminal_recommendations()
            if recommendations:
                response += f"💡 **Optimization Recommendations:**\n"
                for rec in recommendations:
                    response += f"  • {rec}\n"
                response += "\n"
            
            # Quick actions
            response += f"🚀 **Quick Actions:**\n"
            response += f"  • Use bb7_terminal_run_command to execute commands\n"
            response += f"  • Use bb7_terminal_environment for detailed environment analysis\n"
            response += f"  • Use bb7_terminal_history to review recent activity\n"
            response += f"  • Use bb7_terminal_cd to navigate directories with context tracking"
            
            self.logger.info("Generated comprehensive terminal status")
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting terminal status: {e}")
            return f"❌ **Error getting terminal status:** {str(e)}\n\n💡 **Suggestion:** Check system permissions and try again"
    
    def bb7_terminal_run_command(self, arguments: Dict[str, Any]) -> str:
        """
        ⚡ Execute commands in VS Code terminal context with intelligent output analysis, directory 
        tracking, and environment awareness. Perfect for development workflows, build processes, 
        testing, and automation. Maintains session continuity and provides smart error diagnosis 
        with actionable solutions for common development scenarios.
        """
        command = arguments.get('command', '')
        change_directory = arguments.get('change_directory', True)
        timeout = arguments.get('timeout', 30)
        capture_environment = arguments.get('capture_environment', True)
        
        if not command.strip():
            return "❌ Please provide a command to execute. Example: 'git status' or 'npm install'"
        
        try:
            start_time = time.time()
            
            # Pre-execution analysis
            command_analysis = self._analyze_command_intent(command)
            
            # Determine working directory
            work_dir = self.current_directory if change_directory else os.getcwd()
            
            # Execute command with context awareness
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
            
            execution_time = time.time() - start_time
            
            # Update directory tracking for navigation commands
            if change_directory:
                self.current_directory = self._update_current_directory(command, work_dir, result)
            
            # Store command in history
            command_record = {
                'command': command,
                'directory': work_dir,
                'success': result.returncode == 0,
                'execution_time': execution_time,
                'timestamp': time.time(),
                'intent': command_analysis.get('intent', 'unknown')
            }
            
            self.terminal_history.append(command_record)
            if len(self.terminal_history) > 100:  # Keep last 100 commands
                self.terminal_history.pop(0)
            
            # Build intelligent response
            response = f"⚡ **Command Executed in VS Code Terminal**\n\n"
            
            # Command info
            response += f"💻 **Command:** `{command}`\n"
            response += f"📁 **Directory:** {work_dir}\n"
            response += f"⏱️ **Execution Time:** {execution_time:.3f}s\n"
            
            # Execution status
            if result.returncode == 0:
                response += f"✅ **Status:** Success\n\n"
                
                # Command intent and context
                if command_analysis.get('intent'):
                    response += f"🎯 **Intent:** {command_analysis['intent'].title()}\n"
                
                # Output analysis
                if result.stdout and result.stdout.strip():
                    output_analysis = self._analyze_command_output(command, result.stdout)
                    
                    response += f"📤 **Output:**\n```\n{result.stdout.strip()}\n```\n"
                    
                    if output_analysis:
                        response += f"\n🔍 **Analysis:** {output_analysis}\n"
                else:
                    response += f"📤 **Output:** Command completed successfully with no output\n"
                
                # Smart suggestions based on command type
                suggestions = self._get_command_suggestions(command, result.stdout, command_analysis)
                if suggestions:
                    response += f"\n💡 **Smart Suggestions:**\n"
                    for suggestion in suggestions:
                        response += f"  • {suggestion}\n"
                        
            else:
                response += f"❌ **Status:** Failed (exit code: {result.returncode})\n\n"
                
                # Error analysis
                if result.stderr and result.stderr.strip():
                    error_analysis = self._analyze_command_error(command, result.stderr, result.returncode)
                    
                    response += f"🚨 **Error Output:**\n```\n{result.stderr.strip()}\n```\n"
                    
                    if error_analysis:
                        response += f"\n🔧 **Error Diagnosis:** {error_analysis['diagnosis']}\n"
                        response += f"💡 **Suggested Fix:** {error_analysis['solution']}\n"
                        
                        if error_analysis.get('alternative_commands'):
                            response += f"\n🔄 **Try These Commands:**\n"
                            for alt_cmd in error_analysis['alternative_commands']:
                                response += f"  • `{alt_cmd}`\n"
                
                if result.stdout and result.stdout.strip():
                    response += f"\n📤 **Standard Output:**\n```\n{result.stdout.strip()}\n```\n"
            
            # Directory context update
            if self.current_directory != work_dir:
                response += f"\n📁 **Directory Changed:** {self.current_directory}\n"
            
            # Environment changes detection
            if capture_environment:
                env_changes = self._detect_environment_changes()
                if env_changes:
                    response += f"\n🌍 **Environment Changes:**\n"
                    for change in env_changes[:3]:  # Show top 3 changes
                        response += f"  • {change}\n"
            
            # Performance insights
            perf_insights = self._get_command_performance_insights(command, execution_time, result)
            if perf_insights:
                response += f"\n📊 **Performance:** {perf_insights}\n"
            
            # Context-aware next steps
            next_steps = self._suggest_next_steps(command, result, command_analysis)
            if next_steps:
                response += f"\n🎯 **Suggested Next Steps:**\n"
                for step in next_steps:
                    response += f"  • {step}\n"
            
            self.logger.info(f"Executed terminal command: {command} ({'success' if result.returncode == 0 else 'failed'})")
            return response
            
        except subprocess.TimeoutExpired:
            return f"⏰ **Command Timeout:** '{command}' exceeded {timeout} seconds\n\n💡 **Suggestions:**\n  • Try with a longer timeout\n  • Check if the command is waiting for input\n  • Consider running in background mode\n  • Break down complex operations into smaller steps"
        
        except Exception as e:
            self.logger.error(f"Error executing terminal command '{command}': {e}")
            return f"❌ **Execution Error:** {str(e)}\n\n💡 **Suggestions:**\n  • Check command syntax\n  • Verify required tools are installed\n  • Check file permissions\n  • Try with a simpler command first"
    
    def bb7_terminal_environment(self, arguments: Dict[str, Any]) -> str:
        """
        🌍 Analyze and display VS Code terminal environment with intelligent insights about 
        development setup, tool availability, and configuration optimization. Perfect for 
        troubleshooting environment issues, setting up new projects, and ensuring proper 
        development tool configuration. Provides actionable recommendations for environment improvement.
        """
        include_paths = arguments.get('include_paths', True)
        include_tools = arguments.get('include_tools', True)
        include_suggestions = arguments.get('include_suggestions', True)
        
        try:
            response = f" **VS Code Terminal Environment Analysis**\n\n"
            
            # Environment overview
            response += f" **Environment Overview:**\n"
            response += f"  • Shell: {self.shell_type.title()}\n"
            response += f"  • Platform: {self.system_info['platform']}\n"
            response += f"  • Architecture: {self.system_info['architecture']}\n"
            response += f"  • Home Directory: {self.system_info['home']}\n"
            response += f"  • Current Directory: {self.current_directory}\n\n"
            
            # Development environment detection
            dev_env = self._detect_development_environment()
            if dev_env:
                response += f"🛠️ **Development Environment:**\n"
                
                if dev_env.get('python'):
                    py_info = dev_env['python']
                    response += f"  • **Python:** {py_info['version']}\n"
                    if py_info.get('virtual_env'):
                        response += f"    - Virtual Environment: {py_info['virtual_env']}\n"
                    if py_info.get('packages'):
                        response += f"    - Key Packages: {', '.join(py_info['packages'][:5])}\n"
                
                if dev_env.get('node'):
                    node_info = dev_env['node']
                    response += f"  • **Node.js:** {node_info['version']}\n"
                    if node_info.get('npm_version'):
                        response += f"    - npm: {node_info['npm_version']}\n"
                
                if dev_env.get('git'):
                    git_info = dev_env['git']
                    response += f"  • **Git:** {git_info['version']}\n"
                    if git_info.get('user_name'):
                        response += f"    - User: {git_info['user_name']}\n"
                
                response += "\n"
            
            # PATH analysis
            if include_paths:
                path_analysis = self._analyze_path_environment()
                response += f"🛤️ **PATH Analysis:**\n"
                response += f"  • Total Directories: {path_analysis['total_dirs']}\n"
                response += f"  • Valid Directories: {path_analysis['valid_dirs']}\n"
                response += f"  • Development Tools Found: {path_analysis['dev_tools_count']}\n"
                
                if path_analysis.get('important_paths'):
                    response += f"  • **Key Development Paths:**\n"
                    for path_info in path_analysis['important_paths'][:5]:
                        response += f"    - {path_info['path']}: {path_info['tools']}\n"
                
                if path_analysis.get('issues'):
                    response += f"  • **PATH Issues:**\n"
                    for issue in path_analysis['issues'][:3]:
                        response += f"    ⚠️ {issue}\n"
                
                response += "\n"
            
            # Tool availability
            if include_tools:
                tools_status = self._check_development_tools()
                response += f"🔧 **Development Tools Status:**\n"
                
                for category, tools in tools_status.items():
                    if tools:
                        response += f"  • **{category.title()}:**\n"
                        for tool, status in tools.items():
                            status_emoji = "✅" if status['available'] else "❌"
                            version_info = f" ({status['version']})" if status.get('version') else ""
                            response += f"    {status_emoji} {tool}{version_info}\n"
                            if not status['available'] and status.get('install_hint'):
                                response += f"      💡 Install: {status['install_hint']}\n"
                
                response += "\n"
            
            # Environment variables analysis
            env_analysis = self._analyze_environment_variables()
            response += f"🔬 **Environment Variables Analysis:**\n"
            response += f"  • Total Variables: {env_analysis['total_count']}\n"
            response += f"  • Development-Related: {env_analysis['dev_related_count']}\n"
            
            if env_analysis.get('important_missing'):
                response += f"  • **Missing Important Variables:**\n"
                for var, description in env_analysis['important_missing'].items():
                    response += f"    ❌ {var}: {description}\n"
            
            if env_analysis.get('potential_issues'):
                response += f"  • **Potential Issues:**\n"
                for issue in env_analysis['potential_issues']:
                    response += f"    ⚠️ {issue}\n"
            
            response += "\n"
            
            # Shell configuration analysis
            shell_config = self._analyze_shell_configuration()
            if shell_config:
                response += f"🐚 **Shell Configuration:**\n"
                response += f"  • Configuration File: {shell_config.get('config_file', 'Unknown')}\n"
                response += f"  • Aliases Defined: {shell_config.get('aliases_count', 0)}\n"
                response += f"  • Functions Defined: {shell_config.get('functions_count', 0)}\n"
                
                if shell_config.get('features'):
                    response += f"  • **Features:**\n"
                    for feature, status in shell_config['features'].items():
                        status_emoji = "✅" if status else "❌"
                        response += f"    {status_emoji} {feature.replace('_', ' ').title()}\n"
                
                response += "\n"
            
            # Optimization suggestions
            if include_suggestions:
                suggestions = self._generate_environment_suggestions(dev_env, path_analysis, tools_status)
                if suggestions:
                    response += f"💡 **Environment Optimization Suggestions:**\n"
                    
                    for category, items in suggestions.items():
                        if items:
                            response += f"  • **{category.replace('_', ' ').title()}:**\n"
                            for item in items:
                                response += f"    - {item}\n"
                    
                    response += "\n"
            
            # VS Code specific recommendations
            if self.is_vscode_context:
                vscode_tips = self._get_vscode_terminal_tips()
                response += f"🎯 **VS Code Terminal Tips:**\n"
                for tip in vscode_tips:
                    response += f"  • {tip}\n"
                response += "\n"
            
            # Quick diagnostics
            response += f"🩺 **Quick Diagnostics:**\n"
            diagnostics = self._run_environment_diagnostics()
            for diagnostic in diagnostics:
                status_emoji = "✅" if diagnostic['status'] == 'ok' else "⚠️" if diagnostic['status'] == 'warning' else "❌"
                response += f"  {status_emoji} {diagnostic['message']}\n"
            
            self.logger.info("Generated comprehensive environment analysis")
            return response
            
        except Exception as e:
            self.logger.error(f"Error analyzing terminal environment: {e}")
            return f"❌ **Environment Analysis Error:** {str(e)}\n\n💡 **Suggestion:** Check system permissions and try again"
    
    def bb7_terminal_history(self, arguments: Dict[str, Any]) -> str:
        """
        📜 Display and analyze terminal command history with intelligent insights, pattern detection, 
        and usage analytics. Perfect for reviewing recent development activities, identifying 
        workflow patterns, finding frequently used commands, and optimizing development processes. 
        Provides smart suggestions for command automation and workflow improvement.
        """
        limit = arguments.get('limit', 20)
        filter_pattern = arguments.get('filter', '')
        include_analytics = arguments.get('include_analytics', True)
        show_performance = arguments.get('show_performance', True)
        
        try:
            if not self.terminal_history:
                return f"📜 **Terminal History:** No commands executed yet in this session\n\n💡 **Tip:** Use bb7_terminal_run_command to execute commands and build history"
            
            # Filter history if pattern provided
            filtered_history = self.terminal_history.copy()
            if filter_pattern:
                filtered_history = [
                    cmd for cmd in filtered_history 
                    if filter_pattern.lower() in cmd['command'].lower()
                ]
            
            if not filtered_history:
                return f"📜 **Terminal History:** No commands found matching '{filter_pattern}'\n\n💡 **Tip:** Try a different filter pattern or remove the filter"
            
            # Sort by timestamp (most recent first)
            filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
            displayed_history = filtered_history[:limit]
            
            # Build response
            response = f"📜 **VS Code Terminal Command History**\n"
            if filter_pattern:
                response += f"🔍 **Filter:** {filter_pattern}\n"
            response += f"📊 **Showing:** {len(displayed_history)} of {len(filtered_history)} commands\n\n"
            
            # Analytics overview
            if include_analytics and len(filtered_history) > 1:
                analytics = self._analyze_command_history(filtered_history)
                response += f"📈 **Usage Analytics:**\n"
                response += f"  • Total Commands: {len(filtered_history)}\n"
                response += f"  • Success Rate: {analytics['success_rate']:.1f}%\n"
                response += f"  • Average Execution Time: {analytics['avg_execution_time']:.3f}s\n"
                response += f"  • Session Duration: {analytics['session_duration']}\n"
                
                if analytics.get('most_used_commands'):
                    response += f"  • **Most Used Commands:**\n"
                    for cmd, count in analytics['most_used_commands'][:3]:
                        response += f"    - `{cmd}`: {count} times\n"
                
                response += "\n"
            
            # Command history details
            response += f"📋 **Recent Commands:**\n"
            
            for i, cmd in enumerate(displayed_history, 1):
                # Status and timing
                status_emoji = "✅" if cmd['success'] else "❌"
                timestamp = datetime.fromtimestamp(cmd['timestamp'])
                time_ago = self._format_time_ago(timestamp)
                
                # Performance indicator
                exec_time = cmd.get('execution_time', 0)
                if exec_time < 0.1:
                    perf_emoji = "⚡"
                elif exec_time < 1.0:
                    perf_emoji = "🏃"
                else:
                    perf_emoji = "🐌"
                
                response += f"**{i}. {cmd['command']}** {status_emoji}\n"
                response += f"   📁 {cmd.get('directory', 'Unknown directory')}\n"
                response += f"   {perf_emoji} {exec_time:.3f}s | {time_ago}\n"
                
                # Command intent if available
                if cmd.get('intent'):
                    response += f"   🎯 Intent: {cmd['intent'].title()}\n"
                
                response += "\n"
            
            # Performance analysis
            if show_performance and len(displayed_history) > 1:
                perf_analysis = self._analyze_performance_trends(displayed_history)
                response += f"📊 **Performance Analysis:**\n"
                
                if perf_analysis.get('slow_commands'):
                    response += f"  • **Slowest Commands:**\n"
                    for cmd_info in perf_analysis['slow_commands'][:3]:
                        response += f"    🐌 `{cmd_info['command']}`: {cmd_info['time']:.3f}s\n"
                
                if perf_analysis.get('trends'):
                    for trend in perf_analysis['trends']:
                        response += f"  • {trend}\n"
                
                response += "\n"
            
            # Pattern detection
            patterns = self._detect_command_patterns(filtered_history)
            if patterns:
                response += f"🎯 **Command Patterns Detected:**\n"
                
                for pattern_type, pattern_info in patterns.items():
                    if pattern_info['count'] > 1:
                        response += f"  • **{pattern_type.replace('_', ' ').title()}:** {pattern_info['count']} occurrences\n"
                        response += f"    Example: `{pattern_info['example']}`\n"
                        if pattern_info.get('suggestion'):
                            response += f"    💡 {pattern_info['suggestion']}\n"
                
                response += "\n"
            
            # Workflow insights
            workflow_insights = self._analyze_workflow_patterns(filtered_history)
            if workflow_insights:
                response += f"🔄 **Workflow Insights:**\n"
                for insight in workflow_insights:
                    response += f"  • {insight}\n"
                response += "\n"
            
            # Error analysis
            failed_commands = [cmd for cmd in filtered_history if not cmd['success']]
            if failed_commands:
                response += f"🚨 **Error Analysis:**\n"
                response += f"  • Failed Commands: {len(failed_commands)} ({(len(failed_commands)/len(filtered_history)*100):.1f}%)\n"
                
                # Most common failures
                error_patterns = {}
                for cmd in failed_commands:
                    base_cmd = cmd['command'].split()[0]
                    error_patterns[base_cmd] = error_patterns.get(base_cmd, 0) + 1
                
                if error_patterns:
                    response += f"  • **Common Failures:**\n"
                    for cmd, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:3]:
                        response += f"    - `{cmd}`: {count} failures\n"
                
                response += "\n"
            
            # Automation suggestions
            automation_suggestions = self._suggest_automation_opportunities(filtered_history)
            if automation_suggestions:
                response += f"🤖 **Automation Opportunities:**\n"
                for suggestion in automation_suggestions:
                    response += f"  • {suggestion}\n"
                response += "\n"
            
            # Quick actions
            response += f"🚀 **Quick Actions:**\n"
            response += f"  • Use bb7_terminal_run_command to execute commands\n"
            response += f"  • Filter history: bb7_terminal_history filter='git'\n"
            response += f"  • Use bb7_terminal_status for current environment info\n"
            response += f"  • Create aliases for frequently used commands"
            
            self.logger.info(f"Generated terminal history analysis: {len(displayed_history)} commands")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating terminal history: {e}")
            return f"❌ **History Error:** {str(e)}\n\n💡 **Suggestion:** Try again or check system resources"
    
    def bb7_terminal_cd(self, arguments: Dict[str, Any]) -> str:
        """
        📁 Navigate directories with intelligent context tracking, project detection, and workspace 
        awareness. Perfect for development workflow navigation with automatic environment detection, 
        project structure analysis, and smart suggestions for development tasks. Maintains directory 
        context across VS Code terminal sessions with comprehensive path intelligence.
        """
        path = arguments.get('path', '')
        analyze_context = arguments.get('analyze_context', True)
        track_session = arguments.get('track_session', True)
        
        if not path:
            # Show current directory if no path provided
            response = f"📁 **Current Directory:** {self.current_directory}\n\n"
            
            if analyze_context:
                context = self._analyze_directory_context(self.current_directory)
                response += f"🔍 **Directory Analysis:**\n"
                for item in context:
                    response += f"  • {item}\n"
            
            return response
        
        try:
            # Resolve and validate path
            if path == '..':
                new_path = str(Path(self.current_directory).parent)
            elif path == '~':
                new_path = os.path.expanduser('~')
            elif path.startswith('~/'):
                new_path = os.path.expanduser(path)
            elif os.path.isabs(path):
                new_path = path
            else:
                new_path = str(Path(self.current_directory) / path)
            
            # Normalize path
            new_path = str(Path(new_path).resolve())
            
            # Validate directory exists
            if not os.path.exists(new_path):
                # Try to find similar directories
                suggestions = self._find_similar_directories(path, self.current_directory)
                error_msg = f"❌ **Directory not found:** {path}\n\n"
                if suggestions:
                    error_msg += f"💡 **Did you mean:**\n"
                    for suggestion in suggestions[:3]:
                        error_msg += f"  • {suggestion}\n"
                else:
                    error_msg += f"💡 **Tip:** Use `ls` to see available directories"
                return error_msg
            
            if not os.path.isdir(new_path):
                return f"❌ **Not a directory:** {path} is a file, not a directory"
            
            # Check permissions
            if not os.access(new_path, os.R_OK):
                return f"❌ **Permission denied:** Cannot access directory {path}"
            
            # Update current directory
            old_directory = self.current_directory
            self.current_directory = new_path
            
            # Update working directory for the process
            os.chdir(new_path)
            
            # Track directory change in session
            if track_session:
                self.session_data.setdefault('directory_history', []).append({
                    'from': old_directory,
                    'to': new_path,
                    'timestamp': time.time()
                })
            
            # Build response
            response = f"📁 **Directory Changed Successfully**\n\n"
            response += f"📍 **Previous:** {old_directory}\n"
            response += f"📍 **Current:** {new_path}\n\n"
            project_info: Dict[str, Any] = {}
            
            # Directory analysis
            if analyze_context:
                context_analysis = self._analyze_directory_context(new_path)
                response += f"🔍 **Directory Analysis:**\n"
                for analysis in context_analysis:
                    response += f"  • {analysis}\n"
                response += "\n"
                
                # Project detection
                project_info = self._detect_project_info(new_path)
                if project_info:
                    response += f"🎯 **Project Information:**\n"
                    for key, value in project_info.items():
                        response += f"  • {key.replace('_', ' ').title()}: {value}\n"
                    response += "\n"
                
                # Directory contents preview
                contents_preview = self._get_directory_preview(new_path)
                if contents_preview:
                    response += f"📂 **Directory Contents Preview:**\n"
                    response += contents_preview
                    response += "\n"
            
            # Development environment detection
            dev_context = self._detect_directory_dev_context(new_path)
            if dev_context:
                response += f"🛠️ **Development Context:**\n"
                for context in dev_context:
                    response += f"  • {context}\n"
                response += "\n"
            
            # Smart suggestions based on directory
            suggestions = self._get_directory_suggestions(new_path, project_info if analyze_context else {})
            if suggestions:
                response += f"💡 **Smart Suggestions:**\n"
                for suggestion in suggestions:
                    response += f"  • {suggestion}\n"
                response += "\n"
            
            # Navigation history
            if track_session and len(self.session_data.get('directory_history', [])) > 1:
                recent_dirs = self.session_data['directory_history'][-5:]  # Last 5 changes
                response += f"🔄 **Recent Navigation:**\n"
                for i, nav in enumerate(reversed(recent_dirs), 1):
                    timestamp = datetime.fromtimestamp(nav['timestamp'])
                    time_ago = self._format_time_ago(timestamp)
                    response += f"  {i}. {nav['to']} ({time_ago})\n"
                response += "\n"
            
            # Quick actions for this directory
            response += f"🚀 **Quick Actions:**\n"
            response += f"  • Use bb7_terminal_run_command to execute commands here\n"
            response += f"  • Use bb7_list_directory to explore contents\n"
            response += f"  • Use bb7_terminal_cd .. to go up one level\n"
            if project_info:
                response += f"  • Use project-specific commands for this {project_info.get('type', 'project')}"
            
            self.logger.info(f"Changed directory: {old_directory} -> {new_path}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error changing directory to '{path}': {e}")
            return f"❌ **Directory Change Error:** {str(e)}\n\n💡 **Suggestions:**\n  • Check the path spelling\n  • Ensure you have access permissions\n  • Use absolute paths if relative paths aren't working"
    
    def bb7_terminal_which(self, arguments: Dict[str, Any]) -> str:
        """
        🔍 Locate executables and analyze command availability in VS Code terminal environment 
        with intelligent path analysis, version detection, and alternative suggestions. Perfect 
        for troubleshooting missing commands, verifying tool installations, and understanding 
        your development environment setup. Provides comprehensive tool availability analysis.
        """
        command = arguments.get('command', '')
        show_alternatives = arguments.get('show_alternatives', True)
        include_version = arguments.get('include_version', True)
        analyze_path = arguments.get('analyze_path', True)
        
        if not command.strip():
            return "❌ Please specify a command to locate. Example: 'python', 'git', or 'node'"
        
        try:
            # Find the command
            command_path = shutil.which(command)
            
            response = f"🔍 **Command Location Analysis: `{command}`**\n\n"
            
            if command_path:
                response += f"✅ **Found:** {command_path}\n\n"
                
                # File information
                if os.path.exists(command_path):
                    stat_info = os.stat(command_path)
                    response += f"📊 **File Information:**\n"
                    response += f"  • Full Path: {command_path}\n"
                    response += f"  • Size: {stat_info.st_size:,} bytes\n"
                    response += f"  • Permissions: {oct(stat_info.st_mode)[-3:]}\n"
                    
                    # Check if it's a symbolic link
                    if os.path.islink(command_path):
                        real_path = os.path.realpath(command_path)
                        response += f"  • Type: Symbolic link → {real_path}\n"
                    else:
                        response += f"  • Type: Regular executable\n"
                    
                    response += "\n"
                
                # Version detection
                if include_version:
                    version_info = self._get_command_version(command, command_path)
                    if version_info:
                        response += f"📋 **Version Information:**\n"
                        response += f"  • Version: {version_info['version']}\n"
                        if version_info.get('details'):
                            response += f"  • Details: {version_info['details']}\n"
                        response += "\n"
                
                # PATH analysis
                if analyze_path:
                    path_analysis = self._analyze_command_path_context(command, command_path)
                    if path_analysis:
                        response += f"🛤️ **PATH Context:**\n"
                        for item in path_analysis:
                            response += f"  • {item}\n"
                        response += "\n"
                
                # Alternative locations
                if show_alternatives:
                    alternatives = self._find_command_alternatives(command, command_path)
                    if alternatives:
                        response += f"🔄 **Alternative Locations:**\n"
                        for alt in alternatives:
                            response += f"  • {alt['path']}"
                            if alt.get('version'):
                                response += f" (version: {alt['version']})"
                            response += "\n"
                        response += "\n"
                
            else:
                response += f"❌ **Not Found:** Command `{command}` not found in PATH\n\n"
                
                # Search for partial matches
                similar_commands = self._find_similar_commands(command)
                if similar_commands:
                    response += f"🔍 **Similar Commands Found:**\n"
                    for sim_cmd in similar_commands[:5]:
                        sim_path = shutil.which(sim_cmd)
                        response += f"  • `{sim_cmd}`: {sim_path}\n"
                    response += "\n"
                
                # Installation suggestions
                install_suggestions = self._get_installation_suggestions(command)
                if install_suggestions:
                    response += f"💡 **Installation Suggestions:**\n"
                    for suggestion in install_suggestions:
                        response += f"  • {suggestion}\n"
                    response += "\n"
                
                # PATH troubleshooting
                response += f"🔧 **Troubleshooting Steps:**\n"
                response += f"  • Check if the tool is installed: Try package manager commands\n"
                response += f"  • Verify PATH variable: Use bb7_terminal_environment\n"
                response += f"  • Search for the executable: Try find / -name '{command}' 2>/dev/null\n"
                response += f"  • Check alternative names: Some tools have different executable names\n\n"
            
            # Command usage context
            usage_context = self._get_command_usage_context(command)
            if usage_context:
                response += f"🎯 **Usage Context:**\n"
                for context in usage_context:
                    response += f"  • {context}\n"
                response += "\n"
            
            # Related commands
            related_commands = self._get_related_commands(command)
            if related_commands:
                response += f"🔗 **Related Commands:**\n"
                for related in related_commands:
                    related_path = shutil.which(related)
                    status_emoji = "✅" if related_path else "❌"
                    response += f"  {status_emoji} `{related}`"
                    if related_path:
                        response += f": {related_path}"
                    response += "\n"
                response += "\n"
            
            # Environment specific notes
            env_notes = self._get_environment_specific_notes(command)
            if env_notes:
                response += f"📝 **Environment Notes:**\n"
                for note in env_notes:
                    response += f"  • {note}\n"
                response += "\n"
            
            # Quick actions
            response += f"🚀 **Quick Actions:**\n"
            if command_path:
                response += f"  • Run the command: bb7_terminal_run_command command='{command} --help'\n"
                response += f"  • Check version: bb7_terminal_run_command command='{command} --version'\n"
            else:
                response += f"  • Search for installation packages\n"
                response += f"  • Check environment setup: bb7_terminal_environment\n"
            response += f"  • Analyze PATH: Use bb7_terminal_environment include_paths=true"
            
            self.logger.info(f"Located command '{command}': {'found' if command_path else 'not found'}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error locating command '{command}': {e}")
            return f"❌ **Command Location Error:** {str(e)}\n\n💡 **Suggestion:** Check command spelling and try again"
    
    # Helper methods for comprehensive terminal analysis
    def _detect_workspace_path(self) -> Optional[str]:
        """Detect VS Code workspace path"""
        workspace_indicators = [
            os.environ.get('VSCODE_CWD'),
            os.getcwd()
        ]
        
        for path in workspace_indicators:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def _analyze_development_context(self) -> Dict[str, Any]:
        """Analyze current development context"""
        context = {}
        cwd = self.current_directory
        
        # Project type detection
        project_files = {
            'package.json': 'Node.js/JavaScript',
            'requirements.txt': 'Python',
            'pyproject.toml': 'Python (Modern)',
            'Cargo.toml': 'Rust',
            'pom.xml': 'Java (Maven)',
            'build.gradle': 'Java (Gradle)',
            'go.mod': 'Go',
            'composer.json': 'PHP'
        }
        
        for file, project_type in project_files.items():
            if os.path.exists(os.path.join(cwd, file)):
                context['project_type'] = project_type
                break
        
        # Version control
        if os.path.exists(os.path.join(cwd, '.git')):
            context['version_control'] = 'Git'
        
        # Virtual environment detection
        if os.environ.get('VIRTUAL_ENV'):
            context['virtual_environment'] = os.path.basename(os.environ['VIRTUAL_ENV'])
        elif os.environ.get('CONDA_DEFAULT_ENV'):
            context['virtual_environment'] = f"Conda ({os.environ['CONDA_DEFAULT_ENV']})"
        
        # Package managers
        package_managers = []
        if shutil.which('npm'):
            package_managers.append('npm')
        if shutil.which('yarn'):
            package_managers.append('yarn')
        if shutil.which('pip'):
            package_managers.append('pip')
        if shutil.which('conda'):
            package_managers.append('conda')
        
        if package_managers:
            context['package_managers'] = package_managers
        
        return context
    
    def _detect_terminal_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Detect available terminal integrations"""
        integrations = {}
        
        # Git integration
        if shutil.which('git'):
            integrations['Git'] = {
                'available': True,
                'description': 'Version control integration available'
            }
        
        # Docker integration
        if shutil.which('docker'):
            integrations['Docker'] = {
                'available': True,
                'description': 'Container management available'
            }
        
        # Package managers
        for pm in ['npm', 'pip', 'cargo', 'go']:
            if shutil.which(pm):
                integrations[pm.upper()] = {
                    'available': True,
                    'description': f'{pm} package manager available'
                }
        
        return integrations
    
    def _get_development_processes(self) -> List[Dict[str, Any]]:
        """Get development-related processes"""
        dev_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    name = proc_info['name'].lower()
                    
                    # Development-related process names
                    dev_indicators = [
                        'python', 'node', 'java', 'code', 'git', 'docker',
                        'npm', 'yarn', 'webpack', 'typescript', 'eslint'
                    ]
                    
                    if any(indicator in name for indicator in dev_indicators):
                        dev_processes.append(proc_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception:
            pass
        
        return sorted(dev_processes, key=lambda x: x['cpu_percent'], reverse=True)
    
    def _analyze_terminal_capabilities(self) -> Dict[str, bool]:
        """Analyze terminal capabilities"""
        capabilities = {
            'color_support': True,  # Assume modern terminal
            'unicode_support': True,  # Assume modern terminal
            'shell_integration': self.is_vscode_context,
            'command_history': len(self.terminal_history) > 0,
            'environment_tracking': True,
            'directory_tracking': True
        }
        
        # Check for specific features
        if os.environ.get('TERM'):
            term = os.environ['TERM']
            capabilities['advanced_terminal'] = 'xterm' in term or '256color' in term
        
        return capabilities
    
    def _generate_terminal_recommendations(self) -> List[str]:
        """Generate terminal optimization recommendations"""
        recommendations = []
        
        if not self.is_vscode_context:
            recommendations.append("Consider using VS Code's integrated terminal for better integration")
        
        if self.shell_type == 'cmd':
            recommendations.append("Consider upgrading to PowerShell for better scripting capabilities")
        
        if len(self.terminal_history) > 50:
            recommendations.append("High command usage detected - consider creating aliases for frequent commands")
        
        # Check for common development tools
        essential_tools = ['git', 'python', 'node', 'npm']
        missing_tools = [tool for tool in essential_tools if not shutil.which(tool)]
        
        if missing_tools:
            recommendations.append(f"Consider installing missing development tools: {', '.join(missing_tools)}")
        
        return recommendations
    
    def _analyze_command_intent(self, command: str) -> Dict[str, Any]:
        """Analyze command intent and categorize"""
        command_lower = command.lower().strip()
        
        intent_patterns = {
            'navigation': ['cd', 'ls', 'dir', 'pwd', 'find'],
            'version_control': ['git', 'svn', 'hg'],
            'package_management': ['npm', 'pip', 'yarn', 'cargo', 'go get'],
            'file_operations': ['cp', 'mv', 'rm', 'mkdir', 'touch'],
            'process_management': ['ps', 'kill', 'top', 'htop'],
            'network': ['curl', 'wget', 'ping', 'ssh'],
            'development': ['python', 'node', 'java', 'gcc', 'make'],
            'testing': ['pytest', 'jest', 'mocha', 'cargo test'],
            'build': ['build', 'compile', 'webpack', 'rollup']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in command_lower for pattern in patterns):
                return {'intent': intent}
        
        return {'intent': 'general'}
    
    def _update_current_directory(self, command: str, work_dir: str, result: subprocess.CompletedProcess) -> str:
        """Update current directory based on command execution"""
        if command.strip().startswith('cd ') and result.returncode == 0:
            # Extract target directory from cd command
            cd_target = command[3:].strip()
            if cd_target:
                if cd_target == '..':
                    return str(Path(work_dir).parent)
                elif cd_target.startswith('/'):
                    return cd_target
                else:
                    return str(Path(work_dir) / cd_target)
        
        return self.current_directory
    
    def _detect_environment_changes(self) -> List[str]:
        """Detect environment variable changes"""
        changes = []
        current_env = dict(os.environ)
        
        # Compare with snapshot
        for key, value in current_env.items():
            if key not in self.environment_snapshot:
                changes.append(f"Added: {key}={value[:50]}{'...' if len(value) > 50 else ''}")
            elif self.environment_snapshot[key] != value:
                changes.append(f"Changed: {key}")
        
        for key in self.environment_snapshot:
            if key not in current_env:
                changes.append(f"Removed: {key}")
        
        # Update snapshot
        self.environment_snapshot = current_env.copy()
        
        return changes
    
    def _analyze_command_output(self, command: str, output: str) -> Optional[str]:
        """Analyze command output for insights"""
        command_lower = command.lower()
        
        # Git command analysis
        if command_lower.startswith('git'):
            if 'status' in command_lower:
                if 'nothing to commit' in output:
                    return "Repository is clean - all changes committed"
                elif 'Changes not staged' in output:
                    return "Unstaged changes detected - use 'git add' to stage files"
                elif 'Changes to be committed' in output:
                    return "Staged changes ready for commit"
            elif 'log' in command_lower:
                commit_count = output.count('commit ')
                return f"Showing {commit_count} commits in history"
        
        # Directory listing analysis
        elif command_lower.startswith(('ls', 'dir')):
            lines = [line for line in output.split('\n') if line.strip()]
            return f"Directory contains {len(lines)} items"
        
        # Package manager analysis
        elif any(pm in command_lower for pm in ['npm', 'pip', 'yarn']):
            if 'install' in command_lower:
                if 'added' in output or 'Successfully installed' in output:
                    return "Package installation completed successfully"
                elif 'WARN' in output or 'WARNING' in output:
                    return "Installation completed with warnings"
        
        return None
    
    def _analyze_command_error(self, command: str, error: str, exit_code: int) -> Optional[Dict[str, Any]]:
        """Analyze command errors and provide solutions"""
        error_lower = error.lower()
        command_parts = command.split()
        base_cmd = command_parts[0] if command_parts else ""
        
        # Common error patterns
        if 'command not found' in error_lower or 'is not recognized' in error_lower:
            return {
                'diagnosis': f"Command '{base_cmd}' is not installed or not in PATH",
                'solution': f"Install {base_cmd} or check if it's properly added to your PATH",
                'alternative_commands': [f'which {base_cmd}', 'echo $PATH']
            }
        
        elif 'permission denied' in error_lower:
            return {
                'diagnosis': "Insufficient permissions to execute command",
                'solution': "Run with elevated privileges or check file permissions",
                'alternative_commands': [f'ls -la {command_parts[-1] if len(command_parts) > 1 else "."}']
            }
        
        elif 'no such file or directory' in error_lower:
            return {
                'diagnosis': "File or directory does not exist",
                'solution': "Check the path spelling and ensure the file/directory exists",
                'alternative_commands': ['ls -la', 'pwd']
            }
        
        # Git-specific errors
        elif base_cmd == 'git':
            if 'not a git repository' in error_lower:
                return {
                    'diagnosis': "Current directory is not a Git repository",
                    'solution': "Navigate to a Git repository or initialize one with 'git init'",
                    'alternative_commands': ['git init', 'git status']
                }
        
        return None
    
    def _get_command_suggestions(self, command: str, output: str, command_analysis: Dict[str, Any]) -> List[str]:
        """Get smart suggestions based on command and output"""
        suggestions = []
        intent = command_analysis.get('intent', '')
        
        # Intent-based suggestions
        if intent == 'version_control' and 'git' in command:
            if 'status' in command:
                suggestions.append("Use 'git add .' to stage all changes")
                suggestions.append("Use 'git commit -m \"message\"' to commit changes")
            elif 'log' in command:
                suggestions.append("Use 'git log --oneline' for compact history")
        
        elif intent == 'package_management':
            if 'install' in command:
                suggestions.append("Consider using a lockfile for reproducible installs")
                suggestions.append("Run security audit after installing packages")
        
        elif intent == 'navigation':
            if 'ls' in command or 'dir' in command:
                suggestions.append("Use 'ls -la' for detailed file information")
        
        return suggestions
    
    def _get_command_performance_insights(self, command: str, execution_time: float, result: subprocess.CompletedProcess) -> Optional[str]:
        """Get performance insights for command execution"""
        if execution_time < 0.1:
            return "Very fast execution"
        elif execution_time > 5:
            return f"Slow execution ({execution_time:.1f}s) - consider optimization"
        elif len(result.stdout) > 10000:
            return "Large output generated - consider filtering"
        
        return None
    
    def _suggest_next_steps(self, command: str, result: subprocess.CompletedProcess, command_analysis: Dict[str, Any]) -> List[str]:
        """Suggest intelligent next steps based on command execution"""
        next_steps = []
        intent = command_analysis.get('intent', '')
        
        if result.returncode == 0:
            # Success-based suggestions
            if intent == 'version_control' and 'git status' in command:
                if 'Changes not staged' in result.stdout:
                    next_steps.append("Stage changes with 'git add <file>' or 'git add .'")
                elif 'Changes to be committed' in result.stdout:
                    next_steps.append("Commit changes with 'git commit -m \"your message\"'")
            
            elif intent == 'package_management' and 'install' in command:
                next_steps.append("Test the installation by importing/using the package")
                next_steps.append("Update your project documentation with new dependencies")
        
        else:
            # Failure-based suggestions
            next_steps.append("Review the error message above for specific issues")
            next_steps.append("Check command syntax and required parameters")
        
        return next_steps
    
    def _detect_development_environment(self) -> Dict[str, Any]:
        """Detect comprehensive development environment"""
        env = {}
        
        # Python environment
        python_cmd = shutil.which('python') or shutil.which('python3')
        if python_cmd:
            try:
                result = subprocess.run([python_cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    env['python'] = {'version': result.stdout.strip()}
                    
                    # Virtual environment
                    if os.environ.get('VIRTUAL_ENV'):
                        env['python']['virtual_env'] = os.path.basename(os.environ['VIRTUAL_ENV'])
                    
                    # Check for common packages
                    try:
                        pip_result = subprocess.run([python_cmd, '-m', 'pip', 'list'], capture_output=True, text=True)
                        if pip_result.returncode == 0:
                            packages = pip_result.stdout.lower()
                            common_packages = ['django', 'flask', 'requests', 'numpy', 'pandas']
                            found_packages = [pkg for pkg in common_packages if pkg in packages]
                            env['python']['packages'] = found_packages
                    except:
                        pass
            except:
                pass
        
        # Node.js environment
        node_cmd = shutil.which('node')
        if node_cmd:
            try:
                result = subprocess.run([node_cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    env['node'] = {'version': result.stdout.strip()}
                    
                    # npm version
                    npm_result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
                    if npm_result.returncode == 0:
                        env['node']['npm_version'] = npm_result.stdout.strip()
            except:
                pass
        
        # Git environment
        git_cmd = shutil.which('git')
        if git_cmd:
            try:
                result = subprocess.run([git_cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    env['git'] = {'version': result.stdout.strip()}
                    
                    # Git user info
                    user_result = subprocess.run([git_cmd, 'config', 'user.name'], capture_output=True, text=True)
                    if user_result.returncode == 0:
                        env['git']['user_name'] = user_result.stdout.strip()
            except:
                pass
        
        return env
    
    def _analyze_path_environment(self) -> Dict[str, Any]:
        """Analyze PATH environment variable"""
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        analysis = {
            'total_dirs': len(path_dirs),
            'valid_dirs': 0,
            'dev_tools_count': 0,
            'important_paths': [],
            'issues': []
        }
        
        dev_tools = ['python', 'node', 'git', 'java', 'gcc', 'npm', 'pip']
        
        for raw_path_dir in path_dirs:
            path_dir = raw_path_dir.strip().strip('"')
            if not path_dir:
                continue

            if os.path.isdir(path_dir):
                analysis['valid_dirs'] += 1
                
                # Check for development tools in this directory
                tools_in_dir = []
                for tool in dev_tools:
                    tool_path = os.path.join(path_dir, tool)
                    if os.path.exists(tool_path) or os.path.exists(tool_path + '.exe'):
                        tools_in_dir.append(tool)
                        analysis['dev_tools_count'] += 1
                
                if tools_in_dir:
                    analysis['important_paths'].append({
                        'path': path_dir,
                        'tools': ', '.join(tools_in_dir)
                    })
            elif os.path.exists(path_dir):
                analysis['issues'].append(f"PATH entry is not a directory: {path_dir}")
            else:
                analysis['issues'].append(f"Invalid PATH directory: {path_dir}")
        
        return analysis
    
    def _check_development_tools(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Check availability of development tools"""
        tools_categories = {
            'version_control': {
                'git': {'install_hint': 'git'},
                'svn': {'install_hint': 'subversion'},
            },
            'python': {
                'python': {'install_hint': 'python3'},
                'pip': {'install_hint': 'python3-pip'},
                'virtualenv': {'install_hint': 'python3-virtualenv'},
            },
            'node': {
                'node': {'install_hint': 'nodejs'},
                'npm': {'install_hint': 'npm'},
                'yarn': {'install_hint': 'yarn'},
            },
            'build_tools': {
                'make': {'install_hint': 'build-essential'},
                'gcc': {'install_hint': 'gcc'},
                'cmake': {'install_hint': 'cmake'},
            }
        }
        
        for category, tools in tools_categories.items():
            for tool_name, tool_info in tools.items():
                tool_path = shutil.which(tool_name)
                tool_info['available'] = tool_path is not None
                
                if tool_path:
                    # Try to get version
                    try:
                        version_result = subprocess.run([tool_name, '--version'], 
                                                      capture_output=True, text=True, timeout=5)
                        if version_result.returncode == 0:
                            # Extract version from output
                            version_line = version_result.stdout.split('\n')[0]
                            tool_info['version'] = version_line[:50]  # Truncate long versions
                    except:
                        pass
        
        return tools_categories
    
    def _analyze_environment_variables(self) -> Dict[str, Any]:
        """Analyze environment variables"""
        env_vars = dict(os.environ)
        analysis = {
            'total_count': len(env_vars),
            'dev_related_count': 0,
            'important_missing': {},
            'potential_issues': []
        }
        
        # Count development-related variables
        dev_indicators = ['PATH', 'PYTHON', 'NODE', 'JAVA', 'GO', 'RUST', 'VIRTUAL_ENV', 'CONDA']
        for var in env_vars:
            if any(indicator in var.upper() for indicator in dev_indicators):
                analysis['dev_related_count'] += 1
        
        # Check for important missing variables
        important_vars = {
            'EDITOR': 'Default text editor',
            'BROWSER': 'Default web browser',
            'PAGER': 'Default pager for command output'
        }
        
        for var, description in important_vars.items():
            if var not in env_vars:
                analysis['important_missing'][var] = description
        
        # Check for potential issues
        if 'PATH' in env_vars:
            path_value = env_vars['PATH']
            if len(path_value) > 2000:
                analysis['potential_issues'].append("PATH variable is very long - may cause performance issues")
            
            # Check for duplicate entries
            path_dirs = path_value.split(os.pathsep)
            if len(path_dirs) != len(set(path_dirs)):
                analysis['potential_issues'].append("Duplicate entries found in PATH")
        
        return analysis
    
    def _analyze_shell_configuration(self) -> Dict[str, Any]:
        """Analyze shell configuration"""
        config = {}
        
        shell_configs = {
            'bash': ['.bashrc', '.bash_profile', '.profile'],
            'zsh': ['.zshrc', '.zprofile'],
            'fish': ['.config/fish/config.fish']
        }
        
        home_dir = os.path.expanduser('~')
        config_files = shell_configs.get(self.shell_type, [])
        
        for config_file in config_files:
            config_path = os.path.join(home_dir, config_file)
            if os.path.exists(config_path):
                config['config_file'] = config_file
                
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    # Count aliases and functions
                    config['aliases_count'] = content.count('alias ')
                    config['functions_count'] = content.count('function ') + content.count('() {')
                    
                    # Check for features
                    config['features'] = {
                        'aliases': 'alias ' in content,
                        'functions': 'function ' in content or '() {' in content,
                        'exports': 'export ' in content,
                        'path_modifications': 'PATH=' in content
                    }
                    
                except:
                    pass
                
                break
        
        return config
    
    def _generate_environment_suggestions(self, dev_env: Dict[str, Any], path_analysis: Dict[str, Any], 
                                        tools_status: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, List[str]]:
        """Generate environment optimization suggestions"""
        suggestions = {
            'performance': [],
            'tools': [],
            'configuration': [],
            'security': []
        }
        
        # Performance suggestions
        if path_analysis.get('total_dirs', 0) > 20:
            suggestions['performance'].append("Consider cleaning up PATH - many directories may slow command lookup")
        
        # Tools suggestions
        missing_essential = []
        for category, tools in tools_status.items():
            for tool, status in tools.items():
                if not status['available'] and tool in ['git', 'python', 'node']:
                    missing_essential.append(tool)
        
        if missing_essential:
            suggestions['tools'].append(f"Install essential development tools: {', '.join(missing_essential)}")
        
        # Configuration suggestions
        if not dev_env.get('python', {}).get('virtual_env'):
            suggestions['configuration'].append("Consider using Python virtual environments for project isolation")
        
        if self.shell_type == 'cmd':
            suggestions['configuration'].append("Upgrade to PowerShell for better development experience")
        
        return suggestions
    
    def _get_vscode_terminal_tips(self) -> List[str]:
        """Get VS Code specific terminal tips"""
        tips = [
            "Use Ctrl+` to toggle terminal visibility",
            "Use Ctrl+Shift+` to create new terminal instance",
            "Right-click in terminal for context menu with copy/paste options",
            "Use 'code .' to open current directory in VS Code",
            "Terminal inherits VS Code's color theme automatically"
        ]
        
        if self.system_info['platform'] == 'Windows':
            tips.append("Use Ctrl+Shift+P and search 'Terminal: Select Default Profile' to change shell")
        
        return tips
    
    def _run_environment_diagnostics(self) -> List[Dict[str, str]]:
        """Run quick environment diagnostics"""
        diagnostics = []
        
        # Check shell
        if self.shell_type != 'unknown':
            diagnostics.append({'status': 'ok', 'message': f'Shell detected: {self.shell_type}'})
        else:
            diagnostics.append({'status': 'warning', 'message': 'Shell type could not be determined'})
        
        # Check PATH
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        valid_dirs = sum(1 for d in path_dirs if os.path.exists(d))
        if valid_dirs / len(path_dirs) > 0.8:
            diagnostics.append({'status': 'ok', 'message': f'PATH is healthy ({valid_dirs}/{len(path_dirs)} valid directories)'})
        else:
            diagnostics.append({'status': 'warning', 'message': f'PATH has issues ({valid_dirs}/{len(path_dirs)} valid directories)'})
        
        # Check essential tools
        essential_tools = ['python', 'git']
        available_tools = [tool for tool in essential_tools if shutil.which(tool)]
        if len(available_tools) == len(essential_tools):
            diagnostics.append({'status': 'ok', 'message': 'Essential development tools available'})
        else:
            missing = set(essential_tools) - set(available_tools)
            diagnostics.append({'status': 'warning', 'message': f'Missing tools: {", ".join(missing)}'})
        
        return diagnostics
    
    def _analyze_command_history(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze command history for patterns and metrics"""
        if not history:
            return {}
        
        # Calculate metrics
        successful_commands = [cmd for cmd in history if cmd.get('success', False)]
        success_rate = len(successful_commands) / len(history) * 100
        
        execution_times = [cmd.get('execution_time', 0) for cmd in history]
        avg_execution_time = sum(execution_times) / len(execution_times)
        
        # Calculate session duration
        timestamps = [cmd.get('timestamp', 0) for cmd in history]
        if timestamps:
            session_duration = max(timestamps) - min(timestamps)
            if session_duration > 3600:
                session_duration_str = f"{session_duration / 3600:.1f} hours"
            elif session_duration > 60:
                session_duration_str = f"{session_duration / 60:.1f} minutes"
            else:
                session_duration_str = f"{session_duration:.1f} seconds"
        else:
            session_duration_str = "Unknown"
        
        # Find most used commands
        command_counts = {}
        for cmd in history:
            base_cmd = cmd.get('command', '').split()[0]
            command_counts[base_cmd] = command_counts.get(base_cmd, 0) + 1
        
        most_used = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'session_duration': session_duration_str,
            'most_used_commands': most_used
        }
    
    def _format_time_ago(self, timestamp) -> str:
        """Format timestamp as time ago"""
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
    
    def _analyze_performance_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends in command history"""
        analysis = {}
        
        # Find slowest commands
        slow_commands = []
        for cmd in history:
            exec_time = cmd.get('execution_time', 0)
            if exec_time > 1.0:  # Commands taking more than 1 second
                slow_commands.append({
                    'command': cmd.get('command', ''),
                    'time': exec_time
                })
        
        slow_commands.sort(key=lambda x: x['time'], reverse=True)
        analysis['slow_commands'] = slow_commands
        
        # Performance trends
        trends = []
        if len(history) >= 10:
            recent_times = [cmd.get('execution_time', 0) for cmd in history[-5:]]
            older_times = [cmd.get('execution_time', 0) for cmd in history[-10:-5]]
            
            recent_avg = sum(recent_times) / len(recent_times)
            older_avg = sum(older_times) / len(older_times)
            
            if recent_avg < older_avg * 0.8:
                trends.append("Performance improving over recent commands")
            elif recent_avg > older_avg * 1.2:
                trends.append("Performance declining - commands taking longer")
            else:
                trends.append("Performance stable across recent commands")
        
        analysis['trends'] = trends
        return analysis
    
    def _detect_command_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Detect patterns in command usage"""
        patterns = {}
        
        # Analyze command sequences
        commands = [cmd.get('command', '') for cmd in history]
        
        # Git workflow patterns
        git_commands = [cmd for cmd in commands if cmd.startswith('git')]
        if len(git_commands) > 2:
            patterns['git_workflow'] = {
                'count': len(git_commands),
                'example': git_commands[0],
                'suggestion': 'Consider creating git aliases for frequently used commands'
            }
        
        # Build patterns
        build_commands = [cmd for cmd in commands if any(word in cmd.lower() for word in ['build', 'compile', 'make', 'npm run'])]
        if len(build_commands) > 1:
            patterns['build_workflow'] = {
                'count': len(build_commands),
                'example': build_commands[0],
                'suggestion': 'Consider automating build processes with scripts'
            }
        
        # Navigation patterns
        cd_commands = [cmd for cmd in commands if cmd.startswith('cd ')]
        if len(cd_commands) > 3:
            patterns['navigation_heavy'] = {
                'count': len(cd_commands),
                'example': cd_commands[0],
                'suggestion': 'Consider using bookmarks or aliases for frequently accessed directories'
            }
        
        return patterns
    
    def _analyze_workflow_patterns(self, history: List[Dict[str, Any]]) -> List[str]:
        """Analyze workflow patterns"""
        insights = []
        commands = [cmd.get('command', '') for cmd in history]
        
        # Development workflow detection
        if any('git' in cmd for cmd in commands) and any('npm' in cmd or 'pip' in cmd for cmd in commands):
            insights.append("Active development workflow detected (version control + package management)")
        
        # Testing workflow
        if any('test' in cmd.lower() for cmd in commands):
            insights.append("Testing workflow identified - good development practices")
        
        # Deploy/build workflow
        if any(word in ' '.join(commands).lower() for word in ['build', 'deploy', 'docker', 'kubectl']):
            insights.append("Deployment/containerization workflow detected")
        
        return insights
    
    def _suggest_automation_opportunities(self, history: List[Dict[str, Any]]) -> List[str]:
        """Suggest automation opportunities based on command patterns"""
        suggestions = []
        commands = [cmd.get('command', '') for cmd in history]
        
        # Repetitive command detection
        from collections import Counter
        command_counts = Counter(commands)
        frequent_commands = [(cmd, count) for cmd, count in command_counts.items() if count > 2]
        
        if frequent_commands:
            suggestions.append(f"Create aliases for frequently used commands: {frequent_commands[0][0]}")
        
        # Sequential command patterns
        if len(commands) >= 3:
            for i in range(len(commands) - 2):
                sequence = commands[i:i+3]
                if len(set(sequence)) == 3:  # All different commands
                    suggestions.append(f"Consider scripting this sequence: {' && '.join(sequence)}")
                    break
        
        # Development workflow automation
        git_workflow = ['git add', 'git commit', 'git push']
        if all(any(step in cmd for cmd in commands) for step in git_workflow):
            suggestions.append("Create a script for your git workflow (add, commit, push)")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _analyze_directory_context(self, directory: str) -> List[str]:
        """Analyze directory context"""
        context = []
        
        try:
            items = os.listdir(directory)
            
            # Basic stats
            files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
            dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
            
            context.append(f"Contains {len(files)} files and {len(dirs)} directories")
            
            # Project indicators
            project_indicators = {
                'package.json': 'Node.js project',
                'requirements.txt': 'Python project',
                'Cargo.toml': 'Rust project',
                '.git': 'Git repository',
                'Dockerfile': 'Docker project'
            }
            
            for indicator, description in project_indicators.items():
                if indicator in items:
                    context.append(f"Detected: {description}")
            
            # File type analysis
            extensions = {}
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            if extensions:
                top_ext = max(extensions.items(), key=lambda x: x[1])
                context.append(f"Most common file type: {top_ext[0]} ({top_ext[1]} files)")
            
        except PermissionError:
            context.append("Permission denied - cannot analyze directory contents")
        except Exception:
            context.append("Unable to analyze directory contents")
        
        return context
    
    def _find_similar_directories(self, target: str, current_dir: str) -> List[str]:
        """Find directories similar to target"""
        suggestions = []
        
        try:
            # Check current directory for similar names
            items = os.listdir(current_dir)
            for item in items:
                if os.path.isdir(os.path.join(current_dir, item)):
                    if target.lower() in item.lower() or item.lower().startswith(target.lower()[:3]):
                        suggestions.append(item)
            
            # Check parent directory if no matches found
            if not suggestions:
                parent_dir = str(Path(current_dir).parent)
                try:
                    parent_items = os.listdir(parent_dir)
                    for item in parent_items:
                        if os.path.isdir(os.path.join(parent_dir, item)):
                            if target.lower() in item.lower():
                                suggestions.append(f"../{item}")
                except:
                    pass
        
        except:
            pass
        
        return suggestions[:5]
    
    def _detect_project_info(self, directory: str) -> Dict[str, Any]:
        """Detect project information"""
        info = {}
        
        try:
            items = os.listdir(directory)
            
            # Project type detection
            if 'package.json' in items:
                info['type'] = 'Node.js'
                info['config_file'] = 'package.json'
            elif 'requirements.txt' in items or 'pyproject.toml' in items:
                info['type'] = 'Python'
                info['config_file'] = 'requirements.txt' if 'requirements.txt' in items else 'pyproject.toml'
            elif 'Cargo.toml' in items:
                info['type'] = 'Rust'
                info['config_file'] = 'Cargo.toml'
            elif 'pom.xml' in items:
                info['type'] = 'Java (Maven)'
                info['config_file'] = 'pom.xml'
            
            # Version control
            if '.git' in items:
                info['version_control'] = 'Git'
            
            # Build tools
            build_files = ['Makefile', 'build.gradle', 'CMakeLists.txt']
            for build_file in build_files:
                if build_file in items:
                    info['build_system'] = build_file
                    break
        
        except:
            pass
        
        return info
    
    def _get_directory_preview(self, directory: str) -> str:
        """Get directory contents preview"""
        try:
            items = os.listdir(directory)
            
            # Show first few items
            preview_items = []
            for item in sorted(items)[:8]:  # Show max 8 items
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    preview_items.append(f"📁 {item}/")
                else:
                    preview_items.append(f"📄 {item}")
            
            if len(items) > 8:
                preview_items.append(f"... and {len(items) - 8} more items")
            
            return "\n".join(f"  {item}" for item in preview_items)
        
        except:
            return "  Unable to preview directory contents"
    
    def _detect_directory_dev_context(self, directory: str) -> List[str]:
        """Detect development context for directory"""
        context = []
        
        try:
            items = os.listdir(directory)
            
            # Development indicators
            if any(item.endswith('.py') for item in items):
                context.append("Python development environment")
            
            if any(item.endswith(('.js', '.ts')) for item in items):
                context.append("JavaScript/TypeScript development")
            
            if 'node_modules' in items:
                context.append("Node.js dependencies installed")
            
            if '.venv' in items or 'venv' in items:
                context.append("Python virtual environment present")
            
            if '.gitignore' in items:
                context.append("Git repository with ignore rules")
            
            if 'README.md' in items:
                context.append("Documented project (has README)")
        
        except:
            pass
        
        return context
    
    def _get_directory_suggestions(self, directory: str, project_info: Dict[str, Any]) -> List[str]:
        """Get smart suggestions for directory"""
        suggestions = []
        
        project_type = project_info.get('type', '')
        
        if project_type == 'Node.js':
            suggestions.append("Run 'npm install' to install dependencies")
            suggestions.append("Use 'npm start' or 'npm run dev' to start the project")
        
        elif project_type == 'Python':
            suggestions.append("Consider creating a virtual environment: python -m venv venv")
            suggestions.append("Install dependencies: pip install -r requirements.txt")
        
        elif project_type == 'Rust':
            suggestions.append("Use 'cargo build' to compile the project")
            suggestions.append("Use 'cargo run' to build and run")
        
        # General suggestions
        if project_info.get('version_control') == 'Git':
            suggestions.append("Check project status with 'git status'")
        
        return suggestions
    
    def _get_command_version(self, command: str, command_path: str) -> Optional[Dict[str, str]]:
        """Get version information for command"""
        version_flags = ['--version', '-version', '-V', '-v']
        
        for flag in version_flags:
            try:
                result = subprocess.run([command_path, flag], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    version_output = result.stdout.strip()
                    # Extract version number
                    version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', version_output)
                    
                    return {
                        'version': version_match.group(1) if version_match else version_output.split('\n')[0],
                        'details': version_output.split('\n')[0]
                    }
            except:
                continue
        
        return None
    
    def _analyze_command_path_context(self, command: str, command_path: str) -> List[str]:
        """Analyze PATH context for command"""
        context = []
        
        # Check if it's in a virtual environment
        if 'venv' in command_path or 'virtualenv' in command_path:
            context.append("Located in virtual environment")
        
        # Check if it's a system installation
        system_paths = ['/usr/bin', '/usr/local/bin', '/bin']
        if any(sys_path in command_path for sys_path in system_paths):
            context.append("System-wide installation")
        
        # Check if it's in user space
        if os.path.expanduser('~') in command_path:
            context.append("User-local installation")
        
        # Check directory context
        command_dir = os.path.dirname(command_path)
        if 'node_modules' in command_dir:
            context.append("Node.js package binary")
        
        return context
    
    def _find_command_alternatives(self, command: str, primary_path: str) -> List[Dict[str, str]]:
        """Find alternative locations for command"""
        alternatives: List[Dict[str, str]] = []
        normalized_primary = os.path.normcase(os.path.realpath(primary_path))
        seen_paths = {normalized_primary}

        search_paths: List[str] = []
        if primary_path:
            primary_dir = os.path.dirname(primary_path)
            if primary_dir:
                search_paths.append(primary_dir)

        search_paths.extend(self._iter_valid_path_directories())

        if self.system_info.get('platform') == 'Windows':
            system_root = os.environ.get('SystemRoot', r'C:\Windows')
            search_paths.extend([
                os.path.join(system_root, 'System32'),
                os.path.join(system_root, 'SysWOW64'),
            ])
        else:
            search_paths.extend([
                '/usr/bin', '/usr/local/bin', '/bin', '/opt/bin',
                os.path.expanduser('~/.local/bin'),
                os.path.expanduser('~/bin')
            ])

        candidate_names = [command]
        if self.system_info.get('platform') == 'Windows' and not os.path.splitext(command)[1]:
            pathext = os.environ.get('PATHEXT', '.EXE;.CMD;.BAT;.COM').split(';')
            candidate_names.extend([command + ext.lower() for ext in pathext if ext])
            candidate_names.extend([command + ext.upper() for ext in pathext if ext])

        dedup_paths = []
        seen_dirs = set()
        for path_dir in search_paths:
            normalized = os.path.normcase(os.path.realpath(path_dir)) if os.path.exists(path_dir) else ""
            if not path_dir or not os.path.isdir(path_dir):
                continue
            if normalized in seen_dirs:
                continue
            seen_dirs.add(normalized)
            dedup_paths.append(path_dir)

        for search_path in dedup_paths:
            for candidate in candidate_names:
                alt_path = os.path.join(search_path, candidate)
                if not os.path.isfile(alt_path):
                    continue
                normalized_alt = os.path.normcase(os.path.realpath(alt_path))
                if normalized_alt in seen_paths:
                    continue
                seen_paths.add(normalized_alt)
                alternatives.append({'path': alt_path})

        return alternatives[:10]
    
    def _find_similar_commands(self, command: str) -> List[str]:
        """Find commands with similar names"""
        similar = []

        for path_dir in self._iter_valid_path_directories():
            try:
                for item in os.listdir(path_dir):
                    if command.lower() in item.lower() and item != command:
                        similar.append(item)
            except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
                continue
        
        return list(set(similar))  # Remove duplicates

    def _iter_valid_path_directories(self) -> List[str]:
        """Return de-duplicated, existing PATH directory entries only."""
        raw_entries = os.environ.get('PATH', '').split(os.pathsep)
        valid_dirs: List[str] = []
        seen = set()
        for raw_entry in raw_entries:
            candidate = raw_entry.strip().strip('"')
            if not candidate:
                continue
            if not os.path.isdir(candidate):
                continue
            normalized = os.path.normcase(os.path.realpath(candidate))
            if normalized in seen:
                continue
            seen.add(normalized)
            valid_dirs.append(candidate)
        return valid_dirs
    
    def _get_installation_suggestions(self, command: str) -> List[str]:
        """Get installation suggestions for missing command"""
        suggestions = []
        
        # Common installation mappings
        install_map = {
            'python': ['sudo apt install python3', 'brew install python', 'winget install python'],
            'git': ['sudo apt install git', 'brew install git', 'winget install git'],
            'node': ['sudo apt install nodejs', 'brew install node', 'winget install nodejs'],
            'npm': ['sudo apt install npm', 'brew install npm', 'included with nodejs'],
            'docker': ['sudo apt install docker.io', 'brew install docker', 'Docker Desktop'],
            'code': ['Install VS Code from https://code.visualstudio.com/']
        }
        
        if command in install_map:
            suggestions.extend(install_map[command])
        else:
            # Generic suggestions
            suggestions.append(f'Try: sudo apt install {command}  # Ubuntu/Debian')
            suggestions.append(f'Try: brew install {command}  # macOS')
            suggestions.append(f'Try: winget install {command}  # Windows')
        
        return suggestions
    
    def _get_command_usage_context(self, command: str) -> List[str]:
        """Get usage context for command"""
        context_map = {
            'git': ['Version control operations', 'Repository management', 'Collaboration workflows'],
            'python': ['Python script execution', 'Package management', 'Virtual environments'],
            'node': ['JavaScript runtime', 'Server-side development', 'Build tools'],
            'npm': ['Node.js package management', 'Dependency installation', 'Script execution'],
            'docker': ['Container management', 'Application deployment', 'Development environments'],
            'code': ['VS Code editor', 'File and project management', 'Extension management']
        }
        
        return context_map.get(command, [])
    
    def _get_related_commands(self, command: str) -> List[str]:
        """Get related commands"""
        related_map = {
            'git': ['gh', 'git-lfs', 'gitk', 'tig'],
            'python': ['pip', 'python3', 'pipenv', 'virtualenv'],
            'node': ['npm', 'yarn', 'npx', 'nvm'],
            'npm': ['yarn', 'pnpm', 'npx'],
            'docker': ['docker-compose', 'kubectl', 'podman'],
            'code': ['codium', 'cursor', 'subl']
        }
        
        return related_map.get(command, [])
    
    def _get_environment_specific_notes(self, command: str) -> List[str]:
        """Get environment-specific notes"""
        notes = []
        
        if command == 'python':
            if self.system_info['platform'] == 'Windows':
                notes.append("On Windows, use 'py' launcher for Python version management")
            notes.append("Consider using virtual environments for project isolation")
        
        elif command == 'git':
            notes.append("Configure user.name and user.email for first-time setup")
            if self.is_vscode_context:
                notes.append("VS Code has built-in Git integration")
        
        elif command == 'node':
            notes.append("npm is included with Node.js installation")
            notes.append("Consider using nvm for Node.js version management")
        
        return notes
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all available VS Code terminal tools with proper MCP formatting"""
        return {
            'bb7_terminal_status': {
                'description': '🖥️ Get comprehensive VS Code terminal status including session information, environment variables, development context, and integration state. Perfect for understanding your current development environment, troubleshooting terminal issues, and optimizing your workflow setup. Provides actionable insights for terminal configuration and usage.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'include_environment': {
                            'type': 'boolean',
                            'description': 'Include environment variables analysis',
                            'default': True
                        },
                        'include_integrations': {
                            'type': 'boolean',
                            'description': 'Include terminal integrations information',
                            'default': True
                        },
                        'include_performance': {
                            'type': 'boolean',
                            'description': 'Include performance metrics',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_terminal_status
            },
            'bb7_terminal_run_command': {
                'description': '⚡ Execute commands in VS Code terminal context with intelligent output analysis, directory tracking, and environment awareness. Perfect for development workflows, build processes, testing, and automation. Maintains session continuity and provides smart error diagnosis with actionable solutions for common development scenarios.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'Command to execute in terminal'
                        },
                        'change_directory': {
                            'type': 'boolean',
                            'description': 'Whether to track directory changes',
                            'default': True
                        },
                        'timeout': {
                            'type': 'integer',
                            'description': 'Command timeout in seconds',
                            'default': 30
                        },
                        'capture_environment': {
                            'type': 'boolean',
                            'description': 'Whether to capture environment changes',
                            'default': True
                        }
                    },
                    'required': ['command']
                },
                'function': self.bb7_terminal_run_command
            },
            'bb7_terminal_environment': {
                'description': '🌍 Analyze and display VS Code terminal environment with intelligent insights about development setup, tool availability, and configuration optimization. Perfect for troubleshooting environment issues, setting up new projects, and ensuring proper development tool configuration. Provides actionable recommendations for environment improvement.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'include_paths': {
                            'type': 'boolean',
                            'description': 'Include PATH analysis',
                            'default': True
                        },
                        'include_tools': {
                            'type': 'boolean',
                            'description': 'Include development tools status',
                            'default': True
                        },
                        'include_suggestions': {
                            'type': 'boolean',
                            'description': 'Include optimization suggestions',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_terminal_environment
            },
            'bb7_terminal_history': {
                'description': '📜 Display and analyze terminal command history with intelligent insights, pattern detection, and usage analytics. Perfect for reviewing recent development activities, identifying workflow patterns, finding frequently used commands, and optimizing development processes. Provides smart suggestions for command automation and workflow improvement.',
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
                        'include_analytics': {
                            'type': 'boolean',
                            'description': 'Include usage analytics',
                            'default': True
                        },
                        'show_performance': {
                            'type': 'boolean',
                            'description': 'Include performance analysis',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_terminal_history
            },
            'bb7_terminal_cd': {
                'description': '📁 Navigate directories with intelligent context tracking, project detection, and workspace awareness. Perfect for development workflow navigation with automatic environment detection, project structure analysis, and smart suggestions for development tasks. Maintains directory context across VS Code terminal sessions with comprehensive path intelligence.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'Directory path to navigate to (relative or absolute)'
                        },
                        'analyze_context': {
                            'type': 'boolean',
                            'description': 'Whether to analyze directory context',
                            'default': True
                        },
                        'track_session': {
                            'type': 'boolean',
                            'description': 'Whether to track navigation in session',
                            'default': True
                        }
                    }
                },
                'function': self.bb7_terminal_cd
            },
            'bb7_terminal_which': {
                'description': '🔍 Locate executables and analyze command availability in VS Code terminal environment with intelligent path analysis, version detection, and alternative suggestions. Perfect for troubleshooting missing commands, verifying tool installations, and understanding your development environment setup. Provides comprehensive tool availability analysis.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'Command name to locate'
                        },
                        'show_alternatives': {
                            'type': 'boolean',
                            'description': 'Show alternative locations',
                            'default': True
                        },
                        'include_version': {
                            'type': 'boolean',
                            'description': 'Include version information',
                            'default': True
                        },
                        'analyze_path': {
                            'type': 'boolean',
                            'description': 'Analyze PATH context',
                            'default': True
                        }
                    },
                    'required': ['command']
                },
                'function': self.bb7_terminal_which
            }
        }


# For standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tool = VSCodeTerminalTool()

    print("=== Testing VS Code Terminal Tool ===")
    print(f"Terminal status:\n{tool.bb7_terminal_status({})}\n")
    print(
        "Command execution:\n"
        f"{tool.bb7_terminal_run_command({'command': 'echo \"Hello from VS Code terminal!\"'})}\n"
    )
    print(f"Environment analysis:\n{tool.bb7_terminal_environment({})}\n")
