import csv
from datetime import datetime
import os
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import minimalmodbus
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
READERS = (("run.py", "data", 27, 1, 4), ("run_meter.py", "data_meter", 70, 2, 3))


class StopPolling(Exception):
    pass


class ReaderStartupTests(unittest.TestCase):
    def check_reader(self, reader, folder, count, slave, function, port=None, retry=False):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / reader
            shutil.copyfile(ROOT / reader, script)
            instrument = MagicMock()
            values = list(range(count))
            instrument.read_registers.side_effect = (
                [minimalmodbus.NoResponseError("test timeout"), values] if retry else [values]
            )
            environment = dict(os.environ)
            environment.pop("SERIAL_PORT", None)
            if port is not None:
                environment["SERIAL_PORT"] = port
            sleeps = [None, StopPolling()] if retry else [StopPolling()]
            with patch.dict(os.environ, environment, clear=True), patch(
                "minimalmodbus.Instrument", return_value=instrument
            ) as constructor, patch("time.sleep", side_effect=sleeps):
                with self.assertRaises(StopPolling):
                    runpy.run_path(str(script), run_name="__main__")
            constructor.assert_called_once_with(port or "/dev/ttyUSB0", slave)
            instrument.read_registers.assert_called_with(0, count, function)
            files = list((Path(directory) / folder).glob("*.csv"))
            self.assertEqual(len(files), 1)
            self.assertEqual(pd.read_csv(files[0]).shape, (1, count + 1))
            with files[0].open(newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0], [str(i) for i in range(count + 1)])
            self.assertEqual(rows[1][:-1], [str(i) for i in range(count)])
            self.assertEqual(len(rows), 2)
            self.assertGreater(float(rows[1][-1]), 0)

    def test_fresh_checkout_creates_output_and_keeps_csv_format(self):
        for reader in READERS:
            with self.subTest(reader=reader[0]):
                self.check_reader(*reader)

    def test_serial_port_can_be_configured(self):
        for reader in READERS:
            with self.subTest(reader=reader[0]):
                self.check_reader(*reader, port="/dev/serial/by-id/test-adapter")

    def test_timeout_is_followed_by_a_successful_sample(self):
        for reader in READERS:
            with self.subTest(reader=reader[0]):
                self.check_reader(*reader, retry=True)

    def run_dashboard(self, contents="sample", sample_age=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "dashboard").mkdir()
            (root / "data").mkdir()
            script = root / "dashboard" / "app.py"
            shutil.copyfile(ROOT / "dashboard" / "app.py", script)
            if contents is not None:
                filepath = root / "data" / f"results_{datetime.now().date()}.csv"
                if contents == "sample":
                    with filepath.open("w", newline="") as handle:
                        writer = csv.writer(handle)
                        writer.writerow(range(28))
                        writer.writerow(list(range(27)) + [datetime.now().timestamp() - sample_age])
                else:
                    filepath.write_text(contents)
            streamlit = MagicMock()
            streamlit.columns.return_value = [MagicMock() for _ in range(5)]
            modules = {name: MagicMock() for name in ("altair", "pytz", "scipy", "scipy.signal")}
            modules["streamlit"] = streamlit
            with patch.dict("sys.modules", modules), patch("time.sleep", side_effect=StopPolling()) as sleep:
                with self.assertRaises(StopPolling):
                    runpy.run_path(str(script), run_name="__main__")
            sleep.assert_called_once_with(2)
            return streamlit

    def test_dashboard_waits_between_refreshes(self):
        streamlit = self.run_dashboard()
        streamlit.columns.assert_called_once_with(5)

    def test_dashboard_waits_for_missing_empty_or_incomplete_data(self):
        for contents in (None, "", "0,1\n1,2\n", ",".join(str(i) for i in range(28)) + "\n0,1\n"):
            with self.subTest(contents=contents):
                streamlit = self.run_dashboard(contents=contents)
                streamlit.info.assert_called_once()
                streamlit.columns.assert_not_called()

    def test_dashboard_marks_old_samples_as_stale(self):
        streamlit = self.run_dashboard(sample_age=60)
        streamlit.warning.assert_called_once()
        self.assertIn("stale", streamlit.warning.call_args.args[0])

    def test_dashboard_marks_future_samples(self):
        streamlit = self.run_dashboard(sample_age=-120)
        streamlit.warning.assert_called_once()
        self.assertIn("future", streamlit.warning.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
