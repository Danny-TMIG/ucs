// count.c — an eBPF program (source form).
// Compiled with: clang -O2 -target bpf -c count.c -o count.o
// Loaded with bpftool or a Python loader.
#include <linux/bpf.h>
#include <linux/ptrace.h>

#define SEC(NAME) __attribute__((section(NAME), used))

// Map: 64-bit counter keyed by uint32
struct bpf_map_def SEC("maps") counts = {
    .type = BPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(__u32),
    .value_size = sizeof(__u64),
    .max_entries = 256,
};

// Tracepoint: count sys_enter calls per syscall number
SEC("tracepoint/raw_syscalls/sys_enter")
int count_syscalls(void *ctx) {
    __u32 key = 0;
    __u64 *val = bpf_map_lookup_elem(&counts, &key);
    if (val) __sync_fetch_and_add(val, 1);
    return 0;
}

char _license[] SEC("license") = "GPL";
