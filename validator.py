"""
validator.py — WhatsApp Number Validator Engine menggunakan neonize.

Menangani:
- Pairing Code Authentication
- Batch number checking via is_on_whatsapp()
- Smart delay untuk menghindari rate limit
- Menyimpan hasil ke folder results/
"""

import json
import os
import random
import time
import threading
import logging
from datetime import datetime

# Agresif mematikan SEMUA log dari neonize dan whatsmeow
for logger_name in ["neonize", "whatsmeow", "Whatsmeow"]:
    l = logging.getLogger(logger_name)
    l.setLevel(logging.CRITICAL)
    l.propagate = False
    for handler in l.handlers[:]:
        l.removeHandler(handler)
    l.addHandler(logging.NullHandler())

# Reset root logger yang sering di-override neonize
root = logging.getLogger()
for handler in root.handlers[:]:
    root.removeHandler(handler)
root.addHandler(logging.NullHandler())
root.setLevel(logging.CRITICAL)

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

# Batch size untuk pengecekan nomor
BATCH_SIZE = 20
# Delay range antar batch (detik)
DELAY_MIN = 0.2
DELAY_MAX = 0.5


class WhatsAppValidator:
    """
    Engine untuk memvalidasi nomor WhatsApp menggunakan neonize.
    Zero-message policy: hanya menggunakan is_on_whatsapp(), tanpa send_message().
    """

    def __init__(self, session_name: str = "wa_filter"):
        """
        Inisialisasi client neonize.
        
        Args:
            session_name: Nama sesi untuk menyimpan login
        """
        from neonize.client import NewClient
        
        self.session_name = session_name
        self.client = NewClient(session_name)
        self._connected = threading.Event()
        self._paired = threading.Event()
        self._setup_events()

    def _setup_events(self):
        """Setup event handlers untuk koneksi dan pairing."""
        from neonize.events import ConnectedEv, PairStatusEv

        @self.client.event(ConnectedEv)
        def on_connected(client, event):
            console.print("[bold green]✅ Terhubung ke WhatsApp![/bold green]")
            self._connected.set()

        @self.client.event(PairStatusEv)
        def on_pair_status(client, event):
            if event.ID.User:
                console.print(f"[bold green]✅ Login berhasil sebagai: {event.ID.User}[/bold green]")
                self._paired.set()

    def has_session(self) -> bool:
        """Cek apakah sudah ada sesi login tersimpan."""
        db_file = f"{self.session_name}.db"
        return os.path.exists(db_file) and os.path.getsize(db_file) > 0

    def authenticate(self, phone_number: str) -> str:
        """
        Autentikasi menggunakan Pairing Code dengan retry logic.
        """
        # Pastikan format nomor benar untuk pairing
        phone_number = "".join(filter(str.isdigit, phone_number))
        if phone_number.startswith("08"):
            phone_number = "62" + phone_number[1:]
        elif phone_number.startswith("8"):
            phone_number = "62" + phone_number

        console.print(f"\n[cyan]🔐 Meminta pairing code untuk: {phone_number}...[/cyan]")

        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Beri waktu tambahan supaya socket stabil di setiap attempt
                time.sleep(3)
                pairing_code = self.client.PairPhone(phone_number, True)
                return pairing_code
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]  ⚠ Gagal (Attempt {attempt+1}/{max_retries}), mencoba lagi...[/yellow]")
                    time.sleep(2)
                else:
                    raise e

    def connect_and_wait(self):
        """Mulai koneksi client dan tunggu sampai terhubung."""
        # Jalankan connect di thread terpisah karena blocking
        connect_thread = threading.Thread(target=self._run_client, daemon=True)
        connect_thread.start()

    def _run_client(self):
        """Jalankan client neonize (blocking call)."""
        try:
            self.client.connect()
            self.client.event.wait()
        except Exception as e:
            console.print(f"[red]❌ Error koneksi: {e}[/red]")

    def wait_for_connection(self, timeout: int = 120) -> bool:
        """
        Tunggu sampai client terhubung.
        
        Args:
            timeout: Waktu tunggu maksimal dalam detik
            
        Returns:
            True jika berhasil terhubung
        """
        return self._connected.wait(timeout=timeout)

    def check_numbers(self, numbers: list[str]) -> tuple[list[str], list[str]]:
        """
        Cek daftar nomor apakah terdaftar di WhatsApp.
        
        Menggunakan batch processing dengan smart delay untuk menghindari rate limit.
        
        Args:
            numbers: List nomor dalam format internasional (e.g., "628123456789")
            
        Returns:
            Tuple (active_numbers, invalid_numbers)
        """
        active = []
        invalid = []
        total = len(numbers)

        console.print(f"\n[bold cyan]🔍 Memulai validasi {total} nomor...[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Memfilter nomor", total=total)

            # Proses per batch
            for i in range(0, total, BATCH_SIZE):
                batch = numbers[i : i + BATCH_SIZE]

                try:
                    results = self.client.is_on_whatsapp(*batch)

                    for result in results:
                        if result.IsIn:
                            # Ambil nomor dari JID
                            jid_number = result.JID.User if result.JID and result.JID.User else result.Query
                            active.append(jid_number)
                        else:
                            invalid.append(result.Query)

                except Exception as e:
                    console.print(f"\n[red]  ⚠ Error pada batch {i // BATCH_SIZE + 1}: {e}[/red]")
                    # Tambahkan semua nomor di batch ini ke invalid
                    invalid.extend(batch)

                progress.update(task, advance=len(batch))

                # Smart delay antar batch (kecuali batch terakhir)
                if i + BATCH_SIZE < total:
                    delay = random.uniform(DELAY_MIN, DELAY_MAX)
                    time.sleep(delay)

        return active, invalid

    def display_results(self, active: list[str], invalid: list[str], elapsed: float):
        """
        Tampilkan ringkasan hasil di terminal menggunakan rich Table.
        """
        total = len(active) + len(invalid)

        console.print("\n")
        
        # Tabel ringkasan
        table = Table(
            title="📊 Hasil Validasi WhatsApp",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
        )
        table.add_column("Metrik", style="bold")
        table.add_column("Nilai", justify="right")

        table.add_row("Total Input", str(total))
        table.add_row("✅ Aktif WhatsApp", f"[green]{len(active)}[/green]")
        table.add_row("❌ Tidak Terdaftar", f"[red]{len(invalid)}[/red]")
        table.add_row(
            "📈 Persentase Aktif",
            f"[cyan]{len(active) / total * 100:.1f}%[/cyan]" if total > 0 else "0%",
        )
        table.add_row("⏱ Waktu Proses", f"{elapsed:.2f} detik")

        console.print(table)

    def save_results(
        self, active: list[str], invalid: list[str], elapsed: float, output_dir: str = "results"
    ):
        """
        Simpan hasil filter ke folder output.
        
        Files yang dibuat:
        - active_wa.txt: Nomor yang aktif di WhatsApp
        - invalid_wa.txt: Nomor yang tidak terdaftar
        - summary.json: Statistik lengkap
        """
        os.makedirs(output_dir, exist_ok=True)
        total = len(active) + len(invalid)

        # active_wa.txt
        active_path = os.path.join(output_dir, "active_wa.txt")
        with open(active_path, "w", encoding="utf-8") as f:
            f.write("\n".join(active))

        # invalid_wa.txt
        invalid_path = os.path.join(output_dir, "invalid_wa.txt")
        with open(invalid_path, "w", encoding="utf-8") as f:
            f.write("\n".join(invalid))

        # summary.json
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_input": total,
            "total_active": len(active),
            "total_invalid": len(invalid),
            "percentage_active": round(len(active) / total * 100, 2) if total > 0 else 0,
            "processing_time_seconds": round(elapsed, 2),
        }
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        console.print(f"\n[bold green]💾 Hasil disimpan di folder '{output_dir}/':[/bold green]")
        console.print(f"   📗 {active_path}  ({len(active)} nomor)")
        console.print(f"   📕 {invalid_path}  ({len(invalid)} nomor)")
        console.print(f"   📊 {summary_path}")
