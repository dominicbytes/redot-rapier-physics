"""Capture native x64 Windows stacks, including a console launcher's children."""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import sys

K = C.WinDLL("kernel32", use_last_error=True)
D = C.WinDLL("dbghelp", use_last_error=True)
INVALID_HANDLE = C.c_void_p(-1).value


class ThreadEntry(C.Structure):
    _fields_ = [("size", W.DWORD), ("usage", W.DWORD), ("tid", W.DWORD),
                ("pid", W.DWORD), ("base", W.LONG), ("delta", W.LONG), ("flags", W.DWORD)]


class ModuleEntry(C.Structure):
    _fields_ = [("size", W.DWORD), ("mid", W.DWORD), ("pid", W.DWORD),
                ("global_count", W.DWORD), ("process_count", W.DWORD), ("base", C.c_void_p),
                ("length", W.DWORD), ("handle", W.HMODULE), ("name", W.WCHAR * 256),
                ("path", W.WCHAR * 260)]


class ProcessEntry(C.Structure):
    _fields_ = [("size", W.DWORD), ("usage", W.DWORD), ("pid", W.DWORD),
                ("heap", C.c_size_t), ("module", W.DWORD), ("threads", W.DWORD),
                ("parent", W.DWORD), ("priority", W.LONG), ("flags", W.DWORD),
                ("name", W.WCHAR * 260)]


for name, arguments, result in [
    ("OpenProcess", [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
    ("OpenThread", [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
    ("CreateToolhelp32Snapshot", [W.DWORD, W.DWORD], W.HANDLE),
    ("CloseHandle", [W.HANDLE], W.BOOL),
    ("SuspendThread", [W.HANDLE], W.DWORD),
    ("ResumeThread", [W.HANDLE], W.DWORD),
    ("GetThreadContext", [W.HANDLE, C.c_void_p], W.BOOL),
]:
    function = getattr(K, name)
    function.argtypes, function.restype = arguments, result
for name, structure in [("Thread32First", ThreadEntry), ("Thread32Next", ThreadEntry),
                        ("Module32FirstW", ModuleEntry), ("Module32NextW", ModuleEntry),
                        ("Process32FirstW", ProcessEntry), ("Process32NextW", ProcessEntry)]:
    function = getattr(K, name)
    function.argtypes, function.restype = [W.HANDLE, C.POINTER(structure)], W.BOOL
D.SymInitialize.argtypes = [W.HANDLE, C.c_char_p, W.BOOL]
D.SymInitialize.restype = W.BOOL
D.SymCleanup.argtypes = [W.HANDLE]
D.SymSetOptions.argtypes = [W.DWORD]
D.StackWalk64.argtypes = [W.DWORD, W.HANDLE, W.HANDLE] + [C.c_void_p] * 6
D.StackWalk64.restype = W.BOOL
D.SymFromAddr.argtypes = [W.HANDLE, C.c_uint64, C.POINTER(C.c_uint64), C.c_void_p]
D.SymFromAddr.restype = W.BOOL


def process_tree(pid: int) -> list[int]:
    snapshot = K.CreateToolhelp32Snapshot(2, 0)
    if snapshot == INVALID_HANDLE:
        raise OSError(C.get_last_error(), "process snapshot failed")
    entry = ProcessEntry()
    entry.size = C.sizeof(entry)
    parents = {}
    try:
        ok = K.Process32FirstW(snapshot, C.byref(entry))
        while ok:
            parents[entry.pid] = entry.parent
            ok = K.Process32NextW(snapshot, C.byref(entry))
    finally:
        K.CloseHandle(snapshot)
    result = [pid]
    for parent in result:
        result.extend(child for child, owner in parents.items() if owner == parent and child not in result)
    return list(reversed(result))  # Capture the engine before its console launcher.


def stacks(pid: int) -> str:
    process = K.OpenProcess(0x410, False, pid)  # QUERY_INFORMATION | VM_READ
    if not process:
        raise OSError(C.get_last_error(), "OpenProcess failed")
    initialized = False
    try:
        modules = []
        snapshot = K.CreateToolhelp32Snapshot(0x18, pid)  # MODULE | MODULE32
        if snapshot == INVALID_HANDLE:
            raise OSError(C.get_last_error(), "module snapshot failed")
        module = ModuleEntry()
        module.size = C.sizeof(module)
        try:
            ok = K.Module32FirstW(snapshot, C.byref(module))
            while ok:
                modules.append((module.base, module.base + module.length, module.name))
                ok = K.Module32NextW(snapshot, C.byref(module))
        finally:
            K.CloseHandle(snapshot)
        snapshot = K.CreateToolhelp32Snapshot(4, 0)  # THREAD
        if snapshot == INVALID_HANDLE:
            raise OSError(C.get_last_error(), "thread snapshot failed")
        entry = ThreadEntry()
        entry.size = C.sizeof(entry)
        tids = []
        try:
            ok = K.Thread32First(snapshot, C.byref(entry))
            while ok:
                if entry.pid == pid:
                    tids.append(entry.tid)
                ok = K.Thread32Next(snapshot, C.byref(entry))
        finally:
            K.CloseHandle(snapshot)
        D.SymSetOptions(0x4 | 0x10 | 0x200 | 0x80000)  # Deferred, lines, no error dialogs.
        target = Path(os.environ.get("CARGO_TARGET_DIR", Path(__file__).resolve().parents[1] / "target"))
        search = os.pathsep.join(str(target / folder) for folder in ("debug", "debug/deps"))
        initialized = D.SymInitialize(process, search.encode("utf-8"), True)
        lines = [f"Threads: {len(tids)}; symbols initialized: {bool(initialized)}"]
        for tid in tids:
            lines.append(f"Thread {tid}")
            thread = K.OpenThread(0x2 | 0x8 | 0x40, False, tid)  # Suspend, context, query.
            if not thread:
                lines.append("  OpenThread failed")
                continue
            suspended = False
            try:
                if K.SuspendThread(thread) == 0xffffffff:
                    lines.append("  SuspendThread failed")
                    continue
                suspended = True
                # AMD64 CONTEXT is 1232 bytes, aligned to 16; request CONTROL, INTEGER, FLOATING_POINT.
                raw = C.create_string_buffer(1232 + 16)
                context = (C.addressof(raw) + 15) & ~15
                C.c_uint32.from_address(context + 48).value = 0x10000b
                if not K.GetThreadContext(thread, context):
                    lines.append("  GetThreadContext failed")
                    continue
                # STACKFRAME64's ADDRESS64 fields: PC, frame and stack; mode 3 is flat addressing.
                frame = C.create_string_buffer(512)
                for offset, register in [(0, 248), (32, 160), (48, 152)]:
                    C.c_uint64.from_buffer(frame, offset).value = C.c_uint64.from_address(context + register).value
                    C.c_uint32.from_buffer(frame, offset + 12).value = 3
                previous = None
                for index in range(80):
                    pc = C.c_uint64.from_buffer(frame, 0).value
                    sp = C.c_uint64.from_buffer(frame, 48).value
                    if not pc or (index > 1 and (pc, sp) == previous):
                        break
                    if (pc, sp) != previous:  # StackWalk64 initially returns the current frame again.
                        location = f"0x{pc:x}"
                        for low, high, name in modules:
                            if low <= pc < high:
                                location = f"{name}+0x{pc-low:x}"
                                break
                        symbol = C.create_string_buffer(4096)
                        C.c_uint32.from_buffer(symbol, 0).value = 88  # sizeof(SYMBOL_INFO)
                        C.c_uint32.from_buffer(symbol, 80).value = 4000
                        displacement = C.c_uint64()
                        if (initialized and D.SymFromAddr(process, pc, C.byref(displacement), symbol)
                                and displacement.value < 0x100000):
                            name = C.string_at(C.addressof(symbol) + 84).decode("utf-8", "replace")
                            location += f" {name}+0x{displacement.value:x}"
                        lines.append("  " + location)
                    previous = pc, sp
                    if not D.StackWalk64(0x8664, process, thread, frame, context, None,
                                         C.cast(D.SymFunctionTableAccess64, C.c_void_p),
                                         C.cast(D.SymGetModuleBase64, C.c_void_p), None):
                        break
            finally:
                if suspended:
                    K.ResumeThread(thread)
                K.CloseHandle(thread)
        return "\n".join(lines) + "\n"
    finally:
        if initialized:
            D.SymCleanup(process)
        K.CloseHandle(process)


if __name__ == "__main__":
    if C.sizeof(C.c_void_p) != 8:
        raise SystemExit("Native stack capture requires x64 Python.")
    for pid in process_tree(int(sys.argv[1])):
        print(f"Process {pid}", flush=True)
        try:
            print(stacks(pid), flush=True)
        except OSError as error:
            print(f"Native stack capture failed (error {error.errno}).", flush=True)
