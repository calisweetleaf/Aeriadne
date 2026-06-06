
# *This file contains the outputs of research code being run inside the claude application in order to get capabilities list so that a **claude_tool_pack.md** could be shown to claude and used in order to fully access its capabilities and tools not just boring chats.*

```bash
==============================================
   SOMNUS SOVEREIGN INTEL: SYSTEM PROBE v1    
==============================================
[04:12:42] DETECTING HOST ENVIRONMENT...
System: Linux 4.4.0
Distro: PRETTY_NAME="Ubuntu 24.04.3 LTS"
Kernel Version: #1 SMP Sun Jan 10 15:06:54 PST 2016
Architecture: x86_64
Uptime: up 0 minutes
[04:12:42] CHECKING HARDWARE LIMITS...
CPU Cores (Logical): 4
Memory Total: 9.0 GB
Memory Available: 8.98 GB
[04:12:42] MAPPING MOUNT POINTS...
Filesystem      Size  Used Avail Use% Mounted on
none            9.8G  2.3M  9.8G   1% /
none            252G     0  252G   0% /dev
none            252G     0  252G   0% /dev/shm
none            252G     0  252G   0% /sys/fs/cgroup
none            1.0P     0  1.0P   0% /mnt/transcripts
none            1.0P     0  1.0P   0% /mnt/skills/public
none            9.8G  2.3M  9.8G   1% /container_info.json
none            1.0P     0  1.0P   0% /mnt/skills/examples
none            1.0P     0  1.0P   0% /mnt/user-data/outputs
none            1.0P     0  1.0P   0% /mnt/user-data/uploads
none            1.0P     0  1.0P   0% /mnt/user-data/tool_results
[04:12:43] --- Exploring: /mnt/skills ---
skills/
    user/
    public/
        docx.skill
        frontend-design.skill
        pdf.skill
        pptx.skill
        product-self-knowledge.skill
        ... (1 more)
    examples/
        algorithmic-art.skill
        brand-guidelines.skill
        canvas-design.skill
        doc-coauthoring.skill
        internal-comms.skill
        ... (5 more)
[04:12:43] --- Exploring: /mnt/user-data ---
user-data/
[04:12:44] CHECKING EGRESS RULES...
HTTP_PROXY: http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--awful-winged-both-rushes:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAxODM1NSwiZXhwIjoxNzY4MDMyNzU1LCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1hd2Z1bC13aW5nZWQtYm90aC1ydXNoZXMifQ.HOkQpQDhh4Wp5pYhpqA5hRP1ykyenUvH0IqiJHLL-cbF6jQgIdpYj5N1clsLT6UW87InbEuom51IAyFICscj7A@21.0.0.45:15004
HTTPS_PROXY: http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--awful-winged-both-rushes:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAxODM1NSwiZXhwIjoxNzY4MDMyNzU1LCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1hd2Z1bC13aW5nZWQtYm90aC1ydXNoZXMifQ.HOkQpQDhh4Wp5pYhpqA5hRP1ykyenUvH0IqiJHLL-cbF6jQgIdpYj5N1clsLT6UW87InbEuom51IAyFICscj7A@21.0.0.45:15004
NO_PROXY: localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com
[04:12:44] CHECKING PYTHON ENVIRONMENT...
Python Location: /usr/bin/python
Key Packages:
numpy                      2.3.5
pandas                     2.3.3
[04:12:45] WHO AM I?
User: root
Groups: root
Write Access to /home/claude? True
==============================================
             PROBE COMPLETE                   
=============================================
```
---

# *process archeology *

```bash
[96m══════════════════════════════════════════════════════════════════════ 🔬 PROCESS ARCHAEOLOGY v1.0 🔬 ══════════════════════════════════════════════════════════════════════[0m [92mExcavation started: 2026-01-10 07:14:59[0m [1m[94m>>> System Overview[0m [4mProcess Count:[0m Total processes: 3 Unique executables: 3 [4mCommon Binaries:[0m - dash - process_api - python3.12 [1m[94m>>> Building Process Tree[0m [1m[94m>>> Complete Process Tree[0m [96m[1] process_api[0m (ppid:0, threads:6, state:S (sleeping)) └─ [96mcmd:[0m /process_api --addr 0.0.0.0:2024 --max-ws-buffer-size 32768 --cpu-shares 1024 --... └─ [96m[17] sh[0m (ppid:1, threads:1, state:S (sleeping)) └─ └─ [96mcmd:[0m /bin/sh -c cd /home/claude && python3 process_archaeology.py └─ [93m[18] python3[0m (ppid:17, threads:1, state:R (running)) └─ └─ [96mcmd:[0m python3 process_archaeology.py [1m[94m>>> Parent Process Chain[0m ↑ [93m[18][0m python3 [96mpython3 process_archaeology.py[0m ↑ [93m[17][0m sh [96m/bin/sh -c cd /home/claude && python3 process_archaeology.py[0m [93m[1][0m process_api [96m/process_api --addr 0.0.0.0:2024 --max-ws-buffer-size 32768 --cpu-shar...[0m [1m[94m>>> Current Process Deep Dive[0m [1mCurrent PID:[0m 18 [4mProcess Status:[0m Name : python3 State : R (running) Tgid : 18 Pid : 18 PPid : 17 TracerPid : 0 Uid : 0 0 0 0 Gid : 0 0 0 0 FDSize : 512 Threads : 1 VmSize : 25524 kB VmRSS : 17720 kB [4mCommand Line:[0m python3 process_archaeology.py [4mEnvironment Variables:[0m DEBIAN_FRONTEND=noninteractive ELECTRON_GET_USE_PROXY=1 GLOBAL_AGENT_HTTPS_PROXY=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 GLOBAL_AGENT_HTTP_PROXY=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 GLOBAL_AGENT_NO_PROXY=localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com HOME=/root HTTPS_PROXY=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 HTTP_PROXY=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 IS_SANDBOX=yes JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt NODE_PATH=/usr/local/lib/node_modules_global NO_PROXY=localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com OLDPWD=/ PATH=/home/claude/.npm-global/bin:/home/claude/.local/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin PIP_CACHE_DIR=/home/claude/.cache/pip PIP_ROOT_USER_ACTION=ignore PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers PWD=/home/claude PYTHONUNBUFFERED=1 REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt RUST_BACKTRACE=1 SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt YARN_HTTPS_PROXY=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 YARN_HTTP_PROXY=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 http_proxy=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 https_proxy=http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 no_proxy=localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com [4mOpen File Descriptors:[0m 0 -> pipe:[8] 1 -> pipe:[9] 2 -> pipe:[10] [4mMemory Maps (first 20 lines):[0m 00400000-00420000 r--p 00000000 00:11 69 /usr/bin/python3.12 00420000-00703000 r-xp 00020000 00:11 69 /usr/bin/python3.12 00703000-00a28000 r--p 00303000 00:11 69 /usr/bin/python3.12 00a28000-00a29000 r--p 00627000 00:11 69 /usr/bin/python3.12 00a29000-00ba7000 rw-p 00628000 00:11 69 /usr/bin/python3.12 00ba7000-00bab000 rw-p 00000000 00:00 0 00bab000-00d96000 rw-p 00000000 00:00 0 [heap] 7edac6e86000-7edac71a7000 rw-p 00000000 00:00 0 7edac71a7000-7edac7200000 r--p 00000000 00:11 78 /usr/lib/locale/C.utf8/LC_CTYPE 7edac7200000-7edac7228000 r--p 00000000 00:11 37 /usr/lib/x86_64-linux-gnu/libc.so.6 7edac7228000-7edac73b0000 r-xp 00028000 00:11 37 /usr/lib/x86_64-linux-gnu/libc.so.6 7edac73b0000-7edac73ff000 r--p 001b0000 00:11 37 /usr/lib/x86_64-linux-gnu/libc.so.6 7edac73ff000-7edac7403000 r--p 001fe000 00:11 37 /usr/lib/x86_64-linux-gnu/libc.so.6 7edac7403000-7edac7405000 rw-p 00202000 00:11 37 /usr/lib/x86_64-linux-gnu/libc.so.6 7edac7405000-7edac7412000 rw-p 00000000 00:00 0 7edac741a000-7edac741c000 r--p 00000000 00:11 796 /usr/lib/python3.12/lib-dynload/_json.cpython-312-x86_64-linux-gnu.so 7edac741c000-7edac7423000 r-xp 00002000 00:11 796 /usr/lib/python3.12/lib-dynload/_json.cpython-312-x86_64-linux-gnu.so 7edac7423000-7edac7425000 r--p 00009000 00:11 796 /usr/lib/python3.12/lib-dynload/_json.cpython-312-x86_64-linux-gnu.so 7edac7425000-7edac7426000 r--p 0000a000 00:11 796 /usr/lib/python3.12/lib-dynload/_json.cpython-312-x86_64-linux-gnu.so 7edac7426000-7edac7427000 rw-p 0000b000 00:11 796 /usr/lib/python3.12/lib-dynload/_json.cpython-312-x86_64-linux-gnu.so [4mResource Limits:[0m Limit Soft Limit Hard Limit Units Max cpu time unlimited unlimited seconds Max file size unlimited unlimited bytes Max data size unlimited unlimited bytes Max stack size 8388608 unlimited bytes Max core file size unlimited unlimited bytes Max resident set unlimited unlimited bytes Max processes unlimited unlimited processes Max open files 20000 20000 files Max locked memory 65536 65536 bytes Max address space unlimited unlimited bytes Max file locks unlimited unlimited locks Max pending signals 0 0 signals Max msgqueue size 819200 819200 bytes Max nice priority 0 0 [1m[94m>>> Namespace Isolation[0m [4mActive Namespaces:[0m ipc -> ipc:[2] mnt -> mnt:[5] net -> net:[1] pid -> pid:[4] user -> user:[625] uts -> uts:[3] [1m[94m>>> Cgroup Hierarchy[0m [4mCgroup Memberships:[0m 7:pids:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn 6:memory:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn/process_api/02f68559b5d199630c89f55c39ada221 5:job:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn 4:devices:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn 3:cpuset:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn 2:cpuacct:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn 1:cpu:/container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn [1m[94m>>> Security Context[0m [4mCapabilities:[0m CapInh : 00000000a82c35fb CapPrm : 00000000a82c35fb CapEff : 00000000a82c35fb CapBnd : 00000000a82c35fb [4mSeccomp:[0m Mode: Disabled [96m══════════════════════════════════════════════════════════════════════ 🏆 EXCAVATION COMPLETE 🏆 ══════════════════════════════════════════════════════════════════════[0m [92mArtifacts preserved: 2026-01-10 07:14:59[0m
```

### Python Excavator Capabilities

### PID explanations

```bash
process_api (PID 1) 
  └─ sh (PID 17)
      └─ python3 (PID 18) ← user are here
```


### Test 2: Python Process Excavator

```bash
ipc:[2]    → Inter-process communication isolated
mnt:[5]    → Filesystem mounts isolated
net:[1]    → Network stack isolated
pid:[4]    → Process IDs isolated
user:[625] → User namespace isolated
uts:[3]    → Hostname isolated
```

### Test 3 Python Process Excavator

```bash
[96m══════════════════════════════════════════════════════════════════════ 🐍 PYTHON MODULE ARCHAEOLOGY v1.0 🐍 ══════════════════════════════════════════════════════════════════════[0m [92mExcavation started: 2026-01-10 07:19:27[0m [1m[94m>>> Python Environment Summary[0m [1mPython Version:[0m 3.12.3 (main, Aug 14 2025, 17:47:21) [GCC 13.3.0] [1mExecutable:[0m /usr/bin/python3 [1mPrefix:[0m /usr [1mPlatform:[0m linux [1mMax Int:[0m 9223372036854775807 [1mRecursion Limit:[0m 1000 [4mPip Package Count:[0m Total packages via pip: [93m142[0m [4mSample of installed packages:[0m • Deprecated [96m1.3.1[0m • Flask [96m3.1.2[0m • ImageIO [96m2.37.2[0m • Jinja2 [96m3.1.6[0m • Markdown [96m3.10[0m • MarkupSafe [96m3.0.3[0m • PyGObject [96m3.48.2[0m • PyJWT [96m2.7.0[0m • PyYAML [96m6.0.3[0m • Pygments [96m2.19.2[0m • Wand [96m0.6.13[0m • Werkzeug [96m3.1.3[0m • absl-py [96m2.3.1[0m • argcomplete [96m3.1.4[0m • attrs [96m25.4.0[0m • babel [96m2.17.0[0m • backrefs [96m6.1[0m • beautifulsoup4 [96m4.14.2[0m • blinker [96m1.9.0[0m • camelot-py [96m1.0.9[0m ... and 122 more [1m[94m>>> sys.path Analysis[0m [4mPython Search Paths:[0m [92m✓[0m [0] /home/claude (10 items: 3 .py files, 5 directories) [91m✗[0m [1] /usr/lib/python312.zip [92m✓[0m [2] /usr/lib/python3.12 (201 items: 167 .py files, 32 directories) [92m✓[0m [3] /usr/lib/python3.12/lib-dynload (46 items: 0 .py files, 0 directories) [92m✓[0m [4] /usr/local/lib/python3.12/dist-packages (271 items: 12 .py files, 256 directories) [92m✓[0m [5] /usr/lib/python3/dist-packages (66 items: 3 .py files, 56 directories) [1m[94m>>> Standard Library Discovery[0m [4mTotal Standard Library Modules Found:[0m 196 [4mModules by Category:[0m [93m_:[0m 21 modules [93mA:[0m 6 modules abc, aifc, antigravity, argparse, ast, asyncio [93mB:[0m 4 modules base64, bdb, bisect, bz2 [93mC:[0m 22 modules [93mD:[0m 7 modules dataclasses, datetime, dbm, decimal, difflib, dis, doctest [93mE:[0m 4 modules email, encodings, ensurepip, enum [93mF:[0m 6 modules filecmp, fileinput, fnmatch, fractions, ftplib, functools [93mG:[0m 7 modules genericpath, getopt, getpass, gettext, glob, graphlib, gzip [93mH:[0m 5 modules hashlib, heapq, hmac, html, http [93mI:[0m 6 modules imaplib, imghdr, importlib, inspect, io, ipaddress [93mJ:[0m 1 modules json [93mK:[0m 1 modules keyword [93mL:[0m 4 modules linecache, locale, logging, lzma [93mM:[0m 5 modules mailbox, mailcap, mimetypes, modulefinder, multiprocessing [93mN:[0m 5 modules netrc, nntplib, ntpath, nturl2path, numbers [93mO:[0m 4 modules opcode, operator, optparse, os [93mP:[0m 18 modules [93mQ:[0m 2 modules queue, quopri [93mR:[0m 5 modules random, re, reprlib, rlcompleter, runpy [93mS:[0m 27 modules [93mT:[0m 19 modules [93mU:[0m 4 modules unittest, urllib, uu, uuid [93mV:[0m 1 modules venv [93mW:[0m 5 modules warnings, wave, weakref, webbrowser, wsgiref [93mX:[0m 3 modules xdrlib, xml, xmlrpc [93mZ:[0m 4 modules zipapp, zipfile, zipimport, zoneinfo [1m[94m>>> Installed Package Discovery[0m [96mScanning sys.path for packages...[0m Found 400 importable modules/packages [4mAttempting to import and version check...[0m Progress: 50/400 /home/claude/python_archaeology.py:44: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in Click 9.1. Use feature detection or 'importlib.metadata.version("click")' instead. if hasattr(module, attr): /home/claude/python_archaeology.py:45: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in Click 9.1. Use feature detection or 'importlib.metadata.version("click")' instead. ver = getattr(module, attr) Progress: 100/400 ============================================== SOMNUS SOVEREIGN INTEL: SYSTEM PROBE v1 ============================================== [07:19:32] DETECTING HOST ENVIRONMENT... System: Linux 4.4.0 Distro: PRETTY_NAME="Ubuntu 24.04.3 LTS" Kernel Version: #1 SMP Sun Jan 10 15:06:54 PST 2016 Architecture: x86_64 Uptime: up 4 minutes [07:19:32] CHECKING HARDWARE LIMITS... CPU Cores (Logical): 4 Memory Total: 9.0 GB Memory Available: 8.64 GB [07:19:32] MAPPING MOUNT POINTS... Filesystem Size Used Avail Use% Mounted on none 9.8G 2.4M 9.8G 1% / none 252G 0 252G 0% /dev none 252G 0 252G 0% /dev/shm none 252G 0 252G 0% /sys/fs/cgroup none 1.0P 0 1.0P 0% /mnt/transcripts none 1.0P 0 1.0P 0% /mnt/skills/public none 9.8G 2.4M 9.8G 1% /container_info.json none 1.0P 0 1.0P 0% /mnt/skills/examples none 1.0P 0 1.0P 0% /mnt/user-data/outputs none 1.0P 0 1.0P 0% /mnt/user-data/uploads none 1.0P 0 1.0P 0% /mnt/user-data/tool_results [07:19:32] --- Exploring: /mnt/skills --- skills/ public/ docx.skill frontend-design.skill pdf.skill pptx.skill product-self-knowledge.skill ... (1 more) examples/ algorithmic-art.skill brand-guidelines.skill canvas-design.skill doc-coauthoring.skill internal-comms.skill ... (5 more) user/ [07:19:33] --- Exploring: /mnt/user-data --- user-data/ [07:19:33] CHECKING EGRESS RULES... HTTP_PROXY: http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 HTTPS_PROXY: http://container_container_01XBf9w6z3B1yeDEhRmsvFTD--wiggle--kindly-feisty-few-conn:jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6IjgxMDhlNjk4LWU5ZDAtNDNlZC1hNTc0LWM5MmRiZjNjOGE3MyIsImlhdCI6MTc2ODAyOTI5MiwiZXhwIjoxNzY4MDQzNjkyLCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6ImZhbHNlIiwiY29udGFpbmVyX2lkIjoiY29udGFpbmVyXzAxWEJmOXc2ejNCMXllREVoUm1zdkZURC0td2lnZ2xlLS1raW5kbHktZmVpc3R5LWZldy1jb25uIn0.bCRkAQJMcXZgrKOqQsQ3hfgURCXJr7FAHGndWz74yNI1evd4rse_RGmIYPvlkuQYVnLj4fPd3gR-bvoowRHbGg@21.0.0.133:15004 NO_PROXY: localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com [07:19:33] CHECKING PYTHON ENVIRONMENT... Python Location: /usr/bin/python3 Key Packages: numpy 2.3.5 pandas 2.3.3 [07:19:35] WHO AM I? User: root Groups: root Write Access to /home/claude? True ============================================== PROBE COMPLETE ============================================== /home/claude/python_archaeology.py:44: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in Flask 3.2. Use feature detection or 'importlib.metadata.version("flask")' instead. if hasattr(module, attr): /home/claude/python_archaeology.py:45: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in Flask 3.2. Use feature detection or 'importlib.metadata.version("flask")' instead. ver = getattr(module, attr) Progress: 150/400 /home/claude/python_archaeology.py:44: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in ItsDangerous 2.3. Use feature detection or 'importlib.metadata.version("itsdangerous")' instead. if hasattr(module, attr): /home/claude/python_archaeology.py:45: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in ItsDangerous 2.3. Use feature detection or 'importlib.metadata.version("itsdangerous")' instead. ver = getattr(module, attr) Progress: 200/400 /home/claude/python_archaeology.py:44: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in MarkupSafe 3.1. Use feature detection, or `importlib.metadata.version("markupsafe")`, instead. if hasattr(module, attr): /home/claude/python_archaeology.py:45: DeprecationWarning: The '__version__' attribute is deprecated and will be removed in MarkupSafe 3.1. Use feature detection, or `importlib.metadata.version("markupsafe")`, instead. ver = getattr(module, attr) Progress: 250/400 Progress: 300/400 /home/claude/python_archaeology.py:44: DeprecationWarning: version is deprecated and will be removed in Python 3.14 if hasattr(module, attr): /home/claude/python_archaeology.py:45: DeprecationWarning: version is deprecated and will be removed in Python 3.14 ver = getattr(module, attr) The Zen of Python, by Tim Peters Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex. Complex is better than complicated. Flat is better than nested. Sparse is better than dense. Readability counts. Special cases aren't special enough to break the rules. Although practicality beats purity. Errors should never pass silently. Unless explicitly silenced. In the face of ambiguity, refuse the temptation to guess. There should be one-- and preferably only one --obvious way to do it. Although that way may not be obvious at first unless you're Dutch. Now is better than never. Although never is often better than *right* now. If the implementation is hard to explain, it's a bad idea. If the implementation is easy to explain, it may be a good idea. Namespaces are one honking great idea -- let's do more of those! Progress: 350/400 [92mSuccessfully imported: 398[0m [91mFailed imports: 2[0m [1m[94m>>> Package Categorization[0m [93mDATA SCIENCE:[0m 5 modules • matplotlib[96m (3.10.7)[0m • numpy[96m (2.3.5)[0m • pandas[96m (2.3.3)[0m • scipy[96m (1.16.3)[0m • sklearn[96m (1.7.2)[0m [93mWEB:[0m 6 modules • flask[96m (3.1.2)[0m • http[96m[0m • httplib2[96m (0.20.4)[0m • requests[96m (2.32.5)[0m • urllib[96m[0m • urllib3[96m (2.5.0)[0m [93mCRYPTO:[0m 6 modules • _hashlib[96m[0m • _ssl[96m[0m • cryptography[96m (46.0.3)[0m • hashlib[96m[0m • secrets[96m[0m • ssl[96m[0m [93mSYSTEM:[0m 18 modules • _distutils_system_mod[96m[0m • _multiprocessing[96m[0m • _osx_support[96m[0m • _posixshmem[96m[0m • _sysconfigdata__linux_x86_64-linux-gnu[96m[0m • _sysconfigdata__x86_64-linux-gnu[96m[0m • _threading_local[96m[0m • colorsys[96m[0m • multiprocessing[96m[0m • os[96m[0m ... and 8 more [93mDEV TOOLS:[0m 3 modules • logging[96m (0.5.1.2)[0m • pdb[96m[0m • unittest[96m[0m [93mOTHER:[0m 360 modules • PIL[96m (12.0.0)[0m • __future__[96m[0m • __hello__[96m[0m • __phello__[96m[0m • _aix_support[96m[0m • _asyncio[96m[0m • _bz2[96m[0m • _cffi_backend[96m (2.0.0)[0m • _codecs_cn[96m[0m • _codecs_hk[96m[0m ... and 350 more [1m[94m>>> Key Package Deep Dive[0m [92m✓[0m [1mnumpy[0m Version: [96m2.3.5[0m Location: /usr/local/lib/python3.12/dist-packages/numpy/__init__.py Exports: 501 public names [92m✓[0m [1mpandas[0m Version: [96m2.3.3[0m Location: /usr/local/lib/python3.12/dist-packages/pandas/__init__.py Exports: 114 public names [92m✓[0m [1mscipy[0m Version: [96m1.16.3[0m Location: /usr/local/lib/python3.12/dist-packages/scipy/__init__.py Exports: 22 public names [92m✓[0m [1mmatplotlib[0m Version: [96m3.10.7[0m Location: /usr/local/lib/python3.12/dist-packages/matplotlib/__init__.py Exports: 30 public names [92m✓[0m [1mrequests[0m Version: [96m2.32.5[0m Location: /usr/local/lib/python3.12/dist-packages/requests/__init__.py [92m✓[0m [1mPIL[0m Version: [96m12.0.0[0m Location: /usr/local/lib/python3.12/dist-packages/PIL/__init__.py [92m✓[0m [1mcv2[0m Version: [96m4.11.0[0m Location: /usr/local/lib/python3.12/dist-packages/cv2/__init__.py Exports: 0 public names [91m✗[0m torch - [91mNot installed[0m [91m✗[0m tensorflow - [91mNot installed[0m [92m✓[0m [1msklearn[0m Version: [96m1.7.2[0m Location: /usr/local/lib/python3.12/dist-packages/sklearn/__init__.py Exports: 43 public names [91m✗[0m transformers - [91mNot installed[0m [91m✗[0m openai - [91mNot installed[0m [91m✗[0m anthropic - [91mNot installed[0m [91m✗[0m boto3 - [91mNot installed[0m [92m✓[0m [1mgoogle[0m Location: None [91m✗[0m azure - [91mNot installed[0m [1mSummary:[0m 9/16 key packages available [1m[94m>>> Compiled Extension Discovery[0m Found 1009 compiled extensions (.so files) [4mExtensions by Library (top 15):[0m [1m[94m>>> Hidden/Interesting Module Check[0m [4mChecking for interesting modules:[0m ✓ [1mctypes [0m [[96mmodule[0m] ✓ [1mcffi [0m [[96mmodule[0m] ✓ [1m_ctypes [0m [[96mmodule[0m] ✓ [1msocket [0m [[96mmodule[0m] ✓ [1mssl [0m [[96mmodule[0m] ✓ [1m_ssl [0m [[96mmodule[0m] ✓ [1mzlib [0m [[92mbuiltin[0m] ✓ [1mgzip [0m [[96mmodule[0m] ✓ [1mbz2 [0m [[96mmodule[0m] ✓ [1mlzma [0m [[96mmodule[0m] ✓ [1mstruct [0m [[96mmodule[0m] ✓ [1marray [0m [[92mbuiltin[0m] ✓ [1mmmap [0m [[96mmodule[0m] ✓ [1mmultiprocessing [0m [[96mmodule[0m] ✓ [1m_multiprocessing [0m [[96mmodule[0m] ✓ [1mpdb [0m [[96mmodule[0m] ✓ [1mtrace [0m [[96mmodule[0m] ✓ [1mtraceback [0m [[96mmodule[0m] ✓ [1mdis [0m [[96mmodule[0m] ✓ [1mast [0m [[96mmodule[0m] ✓ [1mtokenize [0m [[96mmodule[0m] ✗ parser [missing] ✓ [1m_thread [0m [[92mbuiltin[0m] ✓ [1m_socket [0m [[92mbuiltin[0m] ✓ [1m_io [0m [[92mbuiltin[0m] ✓ [1m_json [0m [[96mmodule[0m] [1m[94m>>> Final Statistics[0m Total stdlib modules: [93m196[0m Successfully imported: [92m398[0m Failed imports: [91m2[0m [4mSample import errors:[0m [91msounddevice[0m: PortAudio library not found [91mturtle[0m: No module named 'tkinter' [96m══════════════════════════════════════════════════════════════════════ 🏆 EXCAVATION COMPLETE 🏆 ══════════════════════════════════════════════════════════════════════[0m [92mArtifacts preserved: 2026-01-10 07:19:46[0m
```

### Final Quick Package Run: 

```markdown
Top 20 libraries by compiled extension 
sklearn 69 extensions 
skimage 54 extensions 
pandas 44 extensions 
jaxlib 29 extensions 
numpy 19 extensions 
matplotlib 8 extensions 
PIL 8 extensions 
lxml 7 extensions 
fontTools 6 extensions 
greenlet 3 extensions 
mediapipe 3 extensions _cffi_backend.cpython-312-x86_64-linux-gnu.so 2 extensions 
charset_normalizer 2 extensions 
cv2 2 extensions 
onnxruntime 2 extensions 
cryptography 2 extensions 
yaml 1 extensions 
pypdfium2_raw 1 extensions 
kiwisolver 1 extensions
✓ numpy 2.3.5          (501 exports, 19 C extensions)
✓ pandas 2.3.3         (114 exports, 44 C extensions)  
✓ scipy 1.16.3         (22 exports, 114 C extensions!)
✓ matplotlib 3.10.7    (30 exports, 8 C extensions)
✓ sklearn 1.7.2        (43 exports, 69 C extensions)
✓ cv2 4.11.0           (OpenCV!)
✓ PIL 12.0.0           (Pillow for image processing)
✓ skimage              (54 C extensions - full scikit-image)

---

## **Web/Network:**
✓ Flask 3.1.2
✓ requests 2.32.5
✓ urllib3 2.5.0
✓ httplib2 0.20.4

---

## **Other Goodies**

✓ jaxlib               (29 C extensions - Googles JAX!)
✓ mediapipe            (3 C extensions - Google ML)
✓ onnxruntime          (2 C extensions - Microsoft ML)
✓ lxml                 (7 C extensions - XML/HTML parsing)
✓ cryptography 46.0.3
✓ beautifulsoup4 4.14.2
✓ PyYAML 6.0.3
✓ Wand 0.6.13          (ImageMagick bindings)
✓ camelot-py 1.0.9     (PDF table extraction)

---

## **Must Install/Missing**
✗ torch/pytorch
✗ tensorflow
✗ transformers
✗ anthropic/openai SDKs
✗ boto3/AWS
✗ azure

---

## **Lowest Level Capabilities**
✓ ctypes, cffi         - Foreign function interfaces
✓ socket, ssl          - Full network stack
✓ multiprocessing      - Parallel processing
✓ zlib, gzip, bz2, lzma - All compression
✓ struct, array, mmap  - Binary data manipulation
✓ ast, tokenize, dis   - Code introspection


