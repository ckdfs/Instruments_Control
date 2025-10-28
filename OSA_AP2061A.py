import argparse
import queue
import sys
import threading
import time
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import PyApex
from PyApex.Errors import ApexError

DEFAULT_IP = "192.168.99.198"
DEFAULT_CENTER_NM = 1550.0
DEFAULT_SPAN_NM = 0.250
DEFAULT_CHANNEL = "1"
DEFAULT_TRACE = 1
DEFAULT_SCALE_X = "nm"
DEFAULT_SCALE_Y = "log"
DEFAULT_INTERVAL = 0.5  # seconds between acquisitions


class OSA_AP2061A:
    """Convenience wrapper around the PyApex AP2XXX OSA interface."""

    _CHANNEL_ALIASES: Dict[str, str] = {
        "sum": "1+2",
        "total": "1+2",
        "0": "1+2",
        "both": "1&2",
        "1&2": "1&2",
        "dual": "1&2",
        "1": "1",
        "ch1": "1",
        "channel1": "1",
        "2": "2",
        "ch2": "2",
        "channel2": "2",
    }

    def __init__(
        self,
        ip: str,
        port: int = 5900,
        simulation: bool = False,
        timeout: Optional[float] = 30.0,
    ) -> None:
        self._ip = ip
        self._port = port
        self._ap2xxx = PyApex.AP2XXX(ip, PortNumber=port, Simulation=simulation)
        if not self._ap2xxx.IsConnected():
            raise ConnectionError(f"Failed to connect to AP2061A ({ip}:{port})")
        if timeout is not None:
            try:
                self._ap2xxx.SetTimeOut(timeout)
            except Exception:
                pass
        self._osa = self._ap2xxx.OSA()
        try:
            self._identity = self._ap2xxx.GetID().strip()
        except Exception:
            self._identity = "Unknown ID"

    def __enter__(self) -> "OSA_AP2061A":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def identity(self) -> str:
        return self._identity

    def close(self) -> None:
        try:
            self._ap2xxx.Close()
        except Exception:
            pass

    def configure(
        self,
        center_nm: float,
        span_nm: float,
        channel: str = DEFAULT_CHANNEL,
    ) -> None:
        """Apply wavelength settings and set the active input channel."""
        channel_key = self._CHANNEL_ALIASES.get(channel.lower(), channel)
        try:
            self._osa.SetPolarizationMode(channel_key)
        except ApexError as exc:
            raise ValueError(f"Invalid channel selection {channel!r}: {exc}") from exc

        self._osa.SetCenter(center_nm)
        self._osa.SetSpan(span_nm)

    def acquire_once(
        self,
        scale_x: str = DEFAULT_SCALE_X,
        scale_y: str = DEFAULT_SCALE_Y,
        trace: int = DEFAULT_TRACE,
        sweep_mode: str = "single",
    ) -> Tuple[int, List[float], List[float]]:
        """Trigger one sweep and return (trace number, y data, x data)."""
        trace_num = self._osa.Run(sweep_mode)
        if trace_num <= 0:
            raise RuntimeError("OSA did not return a valid trace number; measurement may have been interrupted")
        y_data, x_data = self._osa.GetData(scale_x, scale_y, trace)
        return trace_num, list(y_data), list(x_data)

    def scan_loop(
        self,
        interval_s: float = DEFAULT_INTERVAL,
        scale_x: str = DEFAULT_SCALE_X,
        scale_y: str = DEFAULT_SCALE_Y,
        trace: int = DEFAULT_TRACE,
        sweep_mode: str = "single",
    ) -> Iterator[Tuple[int, List[float], List[float]]]:
        """Continuously trigger sweeps and yield the acquired spectra."""
        while True:
            trace_num, y_data, x_data = self.acquire_once(
                scale_x=scale_x,
                scale_y=scale_y,
                trace=trace,
                sweep_mode=sweep_mode,
            )
            yield trace_num, y_data, x_data
            if interval_s > 0:
                time.sleep(interval_s)


class LivePlotter:
    """Lightweight matplotlib-based live plot helper."""

    def __init__(self, scale_x: str, scale_y: str, refresh_interval: float) -> None:
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise ImportError(
                "matplotlib is required for plotting; install it with `pip install matplotlib`"
            ) from exc

        self._plt = plt
        self._plt.ion()
        self._fig, self._ax = plt.subplots()
        (self._line,) = self._ax.plot([], [], lw=1.2)
        x_label = "Wavelength (nm)" if scale_x.lower() == "nm" else "Frequency (GHz)"
        y_label = "Power (dBm)" if scale_y.lower() == "log" else "Power (mW)"
        self._ax.set_xlabel(x_label)
        self._ax.set_ylabel(y_label)
        self._ax.set_title("AP2061A Spectrum")
        self._ax.grid(True, which="both", alpha=0.3)
        self._refresh_interval = max(refresh_interval, 0.01)
        self._last_draw = 0.0
        self._active = True
        self._fig.canvas.mpl_connect("close_event", self._handle_close)
        try:
            self._plt.show(block=False)
        except TypeError:
            self._plt.show()

    def update(self, x: List[float], y: List[float]) -> None:
        if not self._active:
            return
        now = time.perf_counter()
        if now - self._last_draw < self._refresh_interval:
            return
        self._last_draw = now
        self._line.set_data(x, y)
        self._ax.relim()
        self._ax.autoscale_view()
        self._fig.canvas.draw_idle()
        self._flush_events()

    def process_events(self) -> None:
        if not self._active:
            return
        self._flush_events()

    def close(self) -> None:
        self._active = False
        self._plt.ioff()
        try:
            self._plt.show(block=False)
        except TypeError:
            self._plt.show()

    def _flush_events(self) -> None:
        canvas = self._fig.canvas
        if hasattr(canvas, "flush_events"):
            canvas.flush_events()
        else:
            self._plt.pause(0.001)

    def _handle_close(self, _event) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active


def _scan_worker(
    osa: OSA_AP2061A,
    interval_s: float,
    scale_x: str,
    scale_y: str,
    trace: int,
    sweep_mode: str,
    data_queue: "queue.Queue[Tuple[str, object]]",
    stop_event: threading.Event,
) -> None:
    """Background acquisition loop pushing spectra into a queue."""
    wait_interval = max(interval_s, 0.0)
    try:
        while not stop_event.is_set():
            trace_num, y_data, x_data = osa.acquire_once(
                scale_x=scale_x,
                scale_y=scale_y,
                trace=trace,
                sweep_mode=sweep_mode,
            )
            data_queue.put(("data", trace_num, y_data, x_data))
            if stop_event.wait(wait_interval):
                break
    except Exception as exc:
        data_queue.put(("error", exc))
    finally:
        stop_event.set()

def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control an Apex AP2061A OSA via PyApex and run continuous scans"
    )
    parser.add_argument("--ip", default=DEFAULT_IP, help="Instrument IP address")
    parser.add_argument("--port", type=int, default=5900, help="Control port (default 5900)")
    parser.add_argument(
        "--channel", default=DEFAULT_CHANNEL, help="Polarization channel (e.g. 1, 2, 1&2)"
    )
    parser.add_argument("--center", type=float, default=DEFAULT_CENTER_NM, help="Center wavelength (nm)")
    parser.add_argument("--span", type=float, default=DEFAULT_SPAN_NM, help="Scan span (nm)")
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL, help="Delay between consecutive scans (s)"
    )
    parser.add_argument(
        "--mode",
        default="single",
        choices=["single", "repeat", "auto"],
        help="Sweep mode passed to PyApex",
    )
    parser.add_argument(
        "--scale-x",
        default=DEFAULT_SCALE_X,
        choices=["nm", "GHz"],
        help="X-axis unit for fetched data",
    )
    parser.add_argument(
        "--scale-y",
        default=DEFAULT_SCALE_Y,
        choices=["log", "lin"],
        help="Y-axis unit for fetched data",
    )
    parser.add_argument("--trace", type=int, default=DEFAULT_TRACE, help="Trace number to read (1-6)")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the peak summary (skip data length info)",
    )
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="Enable PyApex simulation mode",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Enable live spectrum plotting (requires matplotlib)",
    )
    parser.add_argument(
        "--plot-refresh-ms",
        type=float,
        default=100.0,
        help="Plot refresh interval in milliseconds",
    )
    return parser.parse_args(argv)



def _format_summary(y_data: List[float], x_data: List[float], scale_x: str) -> str:
    if not y_data:
        return "No valid data"
    peak_value = max(y_data)
    peak_index = y_data.index(peak_value)
    peak_x = x_data[peak_index] if peak_index < len(x_data) else float("nan")
    return f"Peak {peak_value:.2f} dBm @ {peak_x:.3f} {scale_x}"



def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)

    try:
        with OSA_AP2061A(
            args.ip,
            port=args.port,
            simulation=args.simulation,
        ) as osa:
            print(f"Connected: {osa.identity}")
            osa.configure(center_nm=args.center, span_nm=args.span, channel=args.channel)
            print(
                f"Configured -> channel {args.channel}, center {args.center} nm, "
                f"span {args.span} nm"
            )

            plotter: Optional[LivePlotter] = None
            if args.plot:
                try:
                    plotter = LivePlotter(
                        args.scale_x,
                        args.scale_y,
                        refresh_interval=max(args.plot_refresh_ms, 10.0) / 1000.0,
                    )
                except ImportError as exc:
                    print(exc, file=sys.stderr)
                    return 3

            data_queue: "queue.Queue[Tuple[str, object]]" = queue.Queue()
            stop_event = threading.Event()
            worker = threading.Thread(
                target=_scan_worker,
                args=(
                    osa,
                    args.interval,
                    args.scale_x,
                    args.scale_y,
                    args.trace,
                    args.mode,
                    data_queue,
                    stop_event,
                ),
                daemon=True,
            )
            worker.start()

            scan_idx = 0
            worker_error: Optional[BaseException] = None

            try:
                while not stop_event.is_set() or not data_queue.empty():
                    try:
                        item = data_queue.get(timeout=0.1)
                    except queue.Empty:
                        if plotter:
                            plotter.process_events()
                            if not plotter.active:
                                stop_event.set()
                        continue

                    kind = item[0]
                    if kind == "data":
                        _, trace_num, y_data, x_data = item
                        scan_idx += 1
                        timestamp = time.strftime("%H:%M:%S")
                        summary = _format_summary(y_data, x_data, args.scale_x)
                        print(f"[{timestamp}] #{scan_idx} Trace {trace_num}: {summary}")
                        if not args.summary_only:
                            print(f"  X({len(x_data)}) = ...")
                            print(f"  Y({len(y_data)}) = ...")
                        if plotter and plotter.active:
                            plotter.update(x_data, y_data)
                    elif kind == "error":
                        _, err = item
                        worker_error = err
                        stop_event.set()
                        continue

                    if plotter and plotter.active:
                        plotter.process_events()
            finally:
                stop_event.set()
                worker.join(timeout=5.0)
                if plotter:
                    plotter.close()

            if worker_error:
                raise worker_error

    except KeyboardInterrupt:
        print("\nStopped continuous scanning.")
        return 0
    except (ConnectionError, ApexError, RuntimeError) as exc:
        print(f"Operation failed: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

