#!/usr/bin/env python3
"""cmdmap.py - map every command on this machine to its category.

Scans:
  /usr/bin, /usr/local/bin, /opt/homebrew/bin, /opt/homebrew/sbin,
  /bin, /sbin, /usr/sbin, plus every dir in $PATH.

For each binary, classify into a category by name pattern:
  vcs, container, k8s, cloud, build, test, package, editor, shell,
  network, security, monitoring, database, ml, filesystem, other.

Writes ~/ucs/cmdmap.json and prints the histogram.
"""

from __future__ import annotations
import json, os, re, shutil, sys, time
from pathlib import Path

HOME = Path.home()
OUT = HOME / "ucs" / "cmdmap.json"

CATEGORIES = [
    ("vcs", r"^(git|svn|hg|bzr|fossil|jj|git-.*)$"),
    (
        "container",
        r"^(docker|podman|buildah|skopeo|nerdctl|containerd|ctr|crictl|runc|crun)$",
    ),
    (
        "k8s",
        r"^(kubectl|k9s|kubectx|kubens|helm|kustomize|istioctl|linkerd|argo|flux|kind|minikube|k3s|k3d|talosctl)$",
    ),
    (
        "cloud",
        r"^(aws|gcloud|az|doctl|linode-cli|hcloud|oci|ibmcloud|fly|flyctl|vercel|netlify|heroku|wrangler|supabase|firebase|s3cmd|mc|rclone)$",
    ),
    (
        "build",
        r"^(make|cmake|ninja|bazel|buck|pants|gradle|mvn|ant|sbt|meson|autoconf|automake|libtool|cargo|go|zig|nim|dub|stack|cabal|ghc|clang|clang\+\+|gcc|g\+\+|cc|c\+\+|rustc|ld|ar|as|nasm|yasm|tsc|swc|esbuild|rollup|webpack|vite|parcel|babel)$",
    ),
    (
        "test",
        r"^(pytest|tox|nose|unittest|mypy|pyright|ruff|flake8|black|isort|pylint|eslint|prettier|jest|mocha|vitest|ava|tape|cargo-nextest|gotestsum|go-junit-report|junit|ctest|google-test)$",
    ),
    (
        "package",
        r"^(pip|pip3|pipx|poetry|pdm|uv|conda|mamba|npm|npx|pnpm|yarn|bun|deno|cargo|rustup|gem|bundle|composer|brew|apt|apt-get|dnf|yum|pacman|snap|flatpak|port|nix|nix-env|guix)$",
    ),
    (
        "editor",
        r"^(vim|nvim|vi|nano|emacs|helix|hx|kak|micro|code|codium|subl|atom|zed|mate|bbedit|textmate)$",
    ),
    (
        "shell",
        r"^(bash|zsh|sh|dash|fish|ksh|tcsh|csh|elvish|xonsh|nu|nushell|pwsh|powershell|cmd|elv|oil)$",
    ),
    (
        "network",
        r"^(curl|wget|http|httpie|xh|aria2|scp|sftp|ssh|ssh-keygen|ssh-add|ssh-agent|telnet|nc|netcat|ncat|socat|nmap|ping|traceroute|dig|nslookup|host|whois|tcpdump|tshark|wireshark|mtr|iperf|iperf3|tftp|ftp|rsync)$",
    ),
    (
        "security",
        r"^(openssl|gpg|gpg2|age|sops|vault|consul|ssh-vault|keybase|pass|step|cfssl|cfssljson|mkcert|mitmproxy|burp|zap|nuclei|nikto|sqlmap|hydra|john|hashcat|aircrack-ng|reaver|ettercap|bettercap|metasploit|msfconsole|msfvenom)$",
    ),
    (
        "monitoring",
        r"^(prometheus|promtool|grafana|alertmanager|node_exporter|blackbox_exporter|loki|promtail|jaeger|otelcol|opentelemetry|fluentd|fluent-bit|filebeat|logstash|metricbeat|heartbeat|packetbeat|telegraf|statsd|riemann|nagios|zabbix|sensu|datadog-agent|newrelic-infra)$",
    ),
    (
        "database",
        r"^(psql|pg_dump|pg_restore|pg_basebackup|createdb|dropdb|mysql|mysqldump|mysqladmin|mongo|mongosh|mongodump|mongorestore|redis-cli|redis-server|sqlite3|cqlsh|cassandra|influx|influxd|clickhouse-client|clickhouse-server|etcd|etcdctl|zkCli|zookeeper-server|minio|mc)$",
    ),
    (
        "ml",
        r"^(python|python3|jupyter|jupyter-lab|ipython|conda|mamba|pip|pip3|pipx|poetry|pdm|uv|torchrun|deepspeed|accelerate|ray|mlflow|dvc|wandb|bentoml|bentoml-cmd|bentoml-server|triton|tritonserver|ollama|llama|llama-cpp|vllm|hf|huggingface-cli|transformers-cli|sentence-transformers)$",
    ),
    (
        "filesystem",
        r"^(ls|cp|mv|rm|mkdir|rmdir|touch|chmod|chown|chgrp|ln|find|locate|updatedb|du|df|mount|umount|stat|file|tar|gzip|gunzip|bzip2|bunzip2|xz|unxz|zstd|unzstd|zip|unzip|7z|7za|rar|unrar|dd|rsync|scp|truncate|fallocate|mkfs|fsck)$",
    ),
    (
        "proc",
        r"^(ps|top|htop|btop|atop|iotop|pgrep|pkill|kill|killall|nice|renice|nohup|screen|tmux|byobu|time|timeout|watch|strace|ltrace|gdb|lldb|valgrind|perf|bpftrace|bpftool|dtrace|dtruss|fswatch|inotifywait|lsof|fuser|pgrep|pidof)$",
    ),
    (
        "text",
        r"^(grep|egrep|fgrep|rg|ag|ack|sed|awk|gawk|mawk|sort|uniq|cut|tr|wc|head|tail|less|more|cat|tee|paste|join|split|csplit|comm|diff|patch|xxd|od|hexdump|base64|md5|sha1sum|sha256sum|sha512sum|b2sum|cksum|cmp)$",
    ),
    ("json", r"^(jq|yq|jql|jp|fx|gron|json_pp|python3 -m json.tool|dasel|tomlq|gron)$"),
    (
        "editor_cli",
        r"^(sed|awk|perl|ruby|python|python3|node|deno|bun|lua|php|tclsh|wish|Rscript|julia|swift|kotlin|scala|clojure|clj|guile|sbcl|ocaml|ocamlfind|ocamlopt|ghc|ghci|runghc|stack|cabal|erl|erlc|escript|iex|elixir|mix|rebar3)$",
    ),
]


def scan_path():
    """Return {command_name: full_path} for every binary on PATH."""
    found = {}
    seen = set()
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d or d in seen:
            continue
        seen.add(d)
        p = Path(d)
        if not p.is_dir():
            continue
        try:
            for f in p.iterdir():
                if f.is_file() and os.access(f, os.X_OK):
                    name = f.name
                    if name not in found:
                        found[name] = str(f)
        except OSError:
            pass
    return found


def categorize(name):
    for cat, pat in CATEGORIES:
        if re.match(pat, name):
            return cat
    return "other"


def main():
    print("[scan] walking PATH ...")
    cmds = scan_path()
    print("  binaries: " + str(len(cmds)))

    by_cat = {}
    by_cmd = {}
    for name, path in sorted(cmds.items()):
        cat = categorize(name)
        by_cat.setdefault(cat, []).append(name)
        by_cmd[name] = {"path": path, "category": cat}

    print()
    print("[categories]")
    for cat in sorted(by_cat, key=lambda c: -len(by_cat[c])):
        names = by_cat[cat]
        print("  " + cat.ljust(14) + " " + str(len(names)).rjust(5))

    print()
    print("[devsecops subset]")
    devsecops = [
        "vcs",
        "container",
        "k8s",
        "cloud",
        "build",
        "test",
        "package",
        "security",
        "monitoring",
        "database",
        "ml",
    ]
    total = 0
    for cat in devsecops:
        n = len(by_cat.get(cat, []))
        total += n
        print("  " + cat.ljust(14) + " " + str(n).rjust(5))
    print("  " + "TOTAL".ljust(14) + " " + str(total).rjust(5))

    out = Path(HOME) / "ucs" / "cmdmap.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total": len(cmds),
                "by_category": {c: len(ns) for c, ns in by_cat.items()},
                "commands": by_cmd,
            },
            indent=2,
        )
    )
    print()
    print("  report: " + str(out))


if __name__ == "__main__":
    main()
