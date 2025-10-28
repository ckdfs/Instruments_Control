#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tektronix AFG1062 USB helper with verification diagnostics.

- 自动发现 Tektronix USBTMC 仪器 (厂商 ID 0x0699)
- 可选地配置 CH1，并逐项回读确认指令是否生效
- 遇到 VISA I/O 异常时给出具体的 SCPI 命令上下文，便于排查
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import pyvisa
from pyvisa.errors import VisaIOError

TEK_VENDOR_HEX = ("0699",)
MODEL_HINTS = ("AFG1062", "AFG1000", "AFG1", "AFG")


class VisaCommandError(RuntimeError):
    """Wrap a VisaIOError with the command that triggered it."""

    def __init__(self, operation: str, command: str, original: Exception):
        super().__init__(f"{operation} {command!r} failed: {original}")
        self.operation = operation
        self.command = command
        self.original = original


class InstrumentIO:
    """Thin wrapper around a VISA instrument that logs commands and preserves context."""

    def __init__(self, inst, debug: bool = False):
        self.inst = inst
        self.debug = debug

    def write(self, command: str) -> None:
        if self.debug:
            print(f">> {command}")
        try:
            self.inst.write(command)
        except VisaIOError as exc:
            raise VisaCommandError("write", command, exc) from exc

    def query(self, command: str) -> str:
        if self.debug:
            print(f">> {command}")
        try:
            response = self.inst.query(command).strip()
        except VisaIOError as exc:
            raise VisaCommandError("query", command, exc) from exc
        if self.debug:
            print(f"<< {response}")
        return response


@dataclass
class ChannelConfig:
    function: str = "SIN"
    frequency_hz: float = 1_000.0
    voltage_vpp: float = 2.0
    offset_v: float = 0.0
    load: str = "50"  # Tektronix accepts 50 or INF


def find_tektronix_usb(rm: pyvisa.ResourceManager) -> Optional[str]:
    """Return the first USB resource that looks like a Tektronix generator."""
    usb_resources = [r for r in rm.list_resources() if r.upper().startswith("USB")]
    tek_candidates: List[str] = []

    for resource in usb_resources:
        vendor_matches = re.findall(r"0x([0-9A-Fa-f]{4})", resource)
        if vendor_matches and vendor_matches[0].lower() in TEK_VENDOR_HEX:
            tek_candidates.append(resource)

    probe_list = tek_candidates or usb_resources
    for resource in probe_list:
        try:
            inst = rm.open_resource(resource, write_termination="\n", read_termination="\n", timeout=5000)
            try:
                idn = inst.query("*IDN?").strip()
            finally:
                inst.close()
        except Exception:
            continue
        idn_upper = idn.upper()
        if any(hint in idn_upper for hint in MODEL_HINTS) or "TEKTRONIX" in idn_upper:
            return resource
    return None


def open_instrument(resource: str):
    """Open the VISA resource with sensible defaults for USBTMC."""
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(resource, write_termination="\n", read_termination="\n", timeout=30000)
    return rm, inst


def configure_channel_one(io: InstrumentIO, cfg: ChannelConfig, reset: bool = False) -> None:
    """Send the SCPI commands that set up CH1."""
    io.write("*CLS")
    if reset:
        io.write("*RST")
        time.sleep(1.0)  # give the instrument time to finish reset

    io.write(f"SOUR1:FUNC {cfg.function}")
    io.write(f"SOUR1:FREQ {cfg.frequency_hz}")
    io.write(f"SOUR1:VOLT {cfg.voltage_vpp}")
    io.write(f"SOUR1:VOLT:OFFS {cfg.offset_v}")
    io.write(f"OUTP1:LOAD {cfg.load}")
    io.write("OUTP1 ON")


def check_numeric(actual: str, expected: float, tolerance: float) -> Tuple[bool, float]:
    """Compare a numeric VISA response with a tolerance."""
    value = float(actual)
    return abs(value - expected) <= tolerance, value


def verify_channel_one(io: InstrumentIO, cfg: ChannelConfig) -> Tuple[bool, List[str]]:
    """Query the instrument to confirm that CH1 is configured as expected."""
    diagnostics: List[str] = []
    ok = True

    def add_diag(label: str, status: str) -> None:
        diagnostics.append(f"{label}: {status}")

    try:
        func = io.query("SOUR1:FUNC?").upper()
        expected_func = cfg.function.upper()
        passed = func == expected_func
        add_diag("功能形状", f"当前 {func}, 期望 {expected_func} -> {'OK' if passed else 'NG'}")
        ok &= passed
    except Exception as exc:
        add_diag("功能形状", f"查询失败 ({exc})")
        ok = False

    try:
        passed, value = check_numeric(io.query("SOUR1:FREQ?"), cfg.frequency_hz, tolerance=0.5)
        add_diag("频率", f"当前 {value:.6g} Hz, 期望 {cfg.frequency_hz:.6g} Hz -> {'OK' if passed else 'NG'}")
        ok &= passed
    except Exception as exc:
        add_diag("频率", f"查询失败 ({exc})")
        ok = False

    try:
        passed, value = check_numeric(io.query("SOUR1:VOLT?"), cfg.voltage_vpp, tolerance=0.05)
        add_diag("幅度(Vpp)", f"当前 {value:.6g}, 期望 {cfg.voltage_vpp:.6g} -> {'OK' if passed else 'NG'}")
        ok &= passed
    except Exception as exc:
        add_diag("幅度(Vpp)", f"查询失败 ({exc})")
        ok = False

    try:
        passed, value = check_numeric(io.query("SOUR1:VOLT:OFFS?"), cfg.offset_v, tolerance=0.01)
        add_diag("偏置(Vdc)", f"当前 {value:.6g}, 期望 {cfg.offset_v:.6g} -> {'OK' if passed else 'NG'}")
        ok &= passed
    except Exception as exc:
        add_diag("偏置(Vdc)", f"查询失败 ({exc})")
        ok = False

    try:
        load = io.query("OUTP1:LOAD?").upper()
        expected_load = cfg.load.upper()
        passed = load == expected_load
        add_diag("负载", f"当前 {load}, 期望 {expected_load} -> {'OK' if passed else 'NG'}")
        ok &= passed
    except Exception as exc:
        add_diag("负载", f"查询失败 ({exc})")
        ok = False

    try:
        state = io.query("OUTP1:STAT?")
        passed = state == "1"
        add_diag("输出状态", f"当前 {state}, 期望 1(打开) -> {'OK' if passed else 'NG'}")
        ok &= passed
    except Exception as exc:
        add_diag("输出状态", f"查询失败 ({exc})")
        ok = False

    try:
        err = io.query("SYST:ERR?")
        add_diag("SYST:ERR?", err)
        if not err.startswith("0"):
            ok = False
    except Exception as exc:
        add_diag("SYST:ERR?", f"查询失败 ({exc})")
        ok = False

    return ok, diagnostics


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="控制并验证 Tektronix AFG1062 CH1 输出。")
    parser.add_argument("--freq", type=float, default=1_000.0, help="CH1 频率 (Hz)")
    parser.add_argument("--volt", type=float, default=2.0, help="CH1 幅度 (Vpp)")
    parser.add_argument("--offset", type=float, default=0.0, help="CH1 偏置 (Vdc)")
    parser.add_argument("--load", default="50", help="输出负载 (50 或 INF)")
    parser.add_argument("--check-only", action="store_true", help="只检测当前状态，不修改设置。")
    parser.add_argument("--reset", action="store_true", help="在配置前执行 *RST。")
    parser.add_argument(
        "--monitor",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="持续监控，每隔指定秒数重新查询一次（0 表示不循环）。",
    )
    parser.add_argument("--debug", action="store_true", help="打印每条 SCPI 命令及响应。")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    cfg = ChannelConfig(
        function="SIN",
        frequency_hz=args.freq,
        voltage_vpp=args.volt,
        offset_v=args.offset,
        load=args.load,
    )

    try:
        rm = pyvisa.ResourceManager()
    except Exception as exc:
        print(f"无法创建 VISA 资源管理器: {exc}", file=sys.stderr)
        return 2

    resource = find_tektronix_usb(rm)
    if not resource:
        print(
            "未自动找到 Tektronix AFG USB 设备，请检查：\n"
            "1) 是否已安装 NI-VISA 或 TekVisa；\n"
            "2) USB 线缆与端口是否正常；\n"
            "3) 可在 Python 中运行 `pyvisa.ResourceManager().list_resources()` 查看可用资源。",
            file=sys.stderr,
        )
        rm.close()
        return 1

    print(f"发现设备资源: {resource}")
    try:
        rm.close()  # close the probe ResourceManager; open_instrument will create a fresh one
    except Exception:
        pass

    rm, inst = open_instrument(resource)
    io = InstrumentIO(inst, debug=args.debug)

    try:
        idn = io.query("*IDN?")
        print(f"*IDN? -> {idn}")

        if not args.check_only:
            configure_channel_one(io, cfg, reset=args.reset)
            time.sleep(0.2)  # Allow a brief settling time before readback
            print("配置命令已发送，正在进行回读确认...")
        else:
            print("跳过配置，仅检查当前状态。")

        ok, diagnostics = verify_channel_one(io, cfg)
        for line in diagnostics:
            print("  " + line)

        if ok:
            print("结果: 控制正常，仪器已响应并匹配设定值。")
        else:
            print("结果: 未能确认仪器完全匹配设定，请检查上方诊断信息。", file=sys.stderr)

        if args.monitor > 0:
            try:
                print(f"进入监控模式，每 {args.monitor}s 回读一次 (Ctrl+C 退出)...")
                while True:
                    time.sleep(args.monitor)
                    ok, diagnostics = verify_channel_one(io, cfg)
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] 回读结果 -> {'OK' if ok else 'NG'}")
                    for line in diagnostics:
                        print("  " + line)
            except KeyboardInterrupt:
                print("\n收到中断指令，准备关闭输出并断开。")

    except VisaCommandError as exc:
        print(f"VISA 命令异常: {exc}", file=sys.stderr)
        try:
            err = io.query("SYST:ERR?")
            print(f"附加信息 SYST:ERR? -> {err}", file=sys.stderr)
        except Exception:
            pass
        return 4
    except VisaIOError as exc:
        print(f"VISA 通讯异常: {exc}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("\n收到中断指令，准备关闭输出并断开。")
    finally:
        try:
            if not args.check_only:
                io.write("OUTPut1:STATe OFF")
            io.write("OUTPut2:STATe OFF")
        except Exception:
            pass
        try:
            inst.close()
        finally:
            rm.close()
        print("已断开与仪器的连接。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
