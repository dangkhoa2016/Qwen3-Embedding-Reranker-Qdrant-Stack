#!/usr/bin/env bash
set -Eeuo pipefail
PID="${1:?server pid}"
OUT="${2:?csv output}"
STOP_FILE="${3:?stop sentinel}"
printf '%s\n' 'timestamp_utc,pid,rss_kib,mem_available_kib,cgroup_current_bytes,cgroup_peak_bytes,max_events,oom,oom_kill' > "$OUT"
while kill -0 "$PID" 2>/dev/null && [[ ! -e "$STOP_FILE" ]]; do
  rss="$(awk '/VmRSS:/{print $2}' "/proc/$PID/status" 2>/dev/null || echo 0)"
  avail="$(awk '/MemAvailable:/{print $2}' /proc/meminfo 2>/dev/null || echo 0)"
  cur="$(cat /sys/fs/cgroup/memory.current 2>/dev/null || echo 0)"
  peak="$(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo 0)"
  maxe="$(awk '$1=="max"{print $2}' /sys/fs/cgroup/memory.events 2>/dev/null || echo 0)"
  oom="$(awk '$1=="oom"{print $2}' /sys/fs/cgroup/memory.events 2>/dev/null || echo 0)"
  killc="$(awk '$1=="oom_kill"{print $2}' /sys/fs/cgroup/memory.events 2>/dev/null || echo 0)"
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$PID" "$rss" "$avail" "$cur" "$peak" "$maxe" "$oom" "$killc" >> "$OUT"
  sleep 1
done
