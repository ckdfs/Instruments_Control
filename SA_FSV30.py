"""
Configure an R&S FSV30 spectrum analyzer over LAN using RsInstrument.
The script applies the requested measurement settings and periodically
reads back marker amplitudes.
"""

import time
from datetime import datetime
from typing import List, Tuple

from RsInstrument import RsInstrument

FSV_IP = "192.168.99.209"
RESOURCE = f"TCPIP::{FSV_IP}::INSTR"
CENTER_FREQ_HZ = 10.5e6
SPAN_HZ = 8e6
RBW_HZ = 1_000
VBW_HZ = 10
MARKERS: List[Tuple[str, float]] = [
    ("CALC:MARK1", 10e6),
    ("CALC:MARK2", 12e6),
]
POLL_INTERVAL_SEC = 2.0


def main() -> None:
    instr = None
    try:
        instr = RsInstrument(RESOURCE, reset=False, id_query=True)
        instr.visa_timeout = 10_000
        instr.opc_timeout = 10_000
        instr.instrument_status_checking = True

        identity = instr.query_str("*IDN?").strip()
        print(f"Connected to {identity}")

        instr.write_str("*CLS")
        instr.write_str("INIT:CONT OFF")
        instr.write_str("ABOR")
        instr.write_str("SYST:DISP:UPD ON")

        instr.write_str_with_opc(f"SENS:FREQ:CENT {CENTER_FREQ_HZ}")
        instr.write_str_with_opc(f"SENS:FREQ:SPAN {SPAN_HZ}")
        instr.write_str_with_opc(f"SENS:BAND:RES {RBW_HZ}")
        instr.write_str_with_opc(f"SENS:BAND:VID {VBW_HZ}")
        instr.write_str_with_opc("SENS:SWE:TYPE AUTO")

        for marker_cmd, freq_hz in MARKERS:
            instr.write_str(f"{marker_cmd}:STAT ON")
            instr.write_str(f"{marker_cmd}:X {freq_hz}")

        print("Starting acquisition loop, press Ctrl+C to stop.")

        while True:
            instr.write_str("INIT:IMM")
            instr.query_str("*OPC?")

            readings = []
            for marker_cmd, _ in MARKERS:
                freq = float(instr.query_str(f"{marker_cmd}:X?"))
                level = float(instr.query_str(f"{marker_cmd}:Y?"))
                readings.append((marker_cmd[-1], freq, level))

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted = " | ".join(
                f"{name}: {freq / 1e6:.6f} MHz, {level:.2f} dBm"
                for name, freq, level in readings
            )
            print(f"{timestamp} | {formatted}")

            time.sleep(POLL_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("Acquisition stopped by user.")
    except Exception as exc:
        print(f"Error: {exc}")
    finally:
        if instr:
            instr.close()
            print("Session closed.")


if __name__ == "__main__":
    main()
