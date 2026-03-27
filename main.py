"""
main.py — WhatsApp Universal Number Validator
Entry point CLI dengan Rich terminal UI.

Jalankan: python main.py
"""

import os
import sys
import time
import logging

# Agresif mematikan SEMUA log agar tidak mengganggu UI
for logger_name in ["neonize", "whatsmeow", "Whatsmeow"]:
    l = logging.getLogger(logger_name)
    l.setLevel(logging.CRITICAL)
    l.propagate = False
    for handler in l.handlers[:]:
        l.removeHandler(handler)
    l.addHandler(logging.NullHandler())

logging.getLogger().setLevel(logging.CRITICAL)

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.rule import Rule

from formatter import format_numbers
from reader import detect_and_read, read_manual
from validator import WhatsAppValidator

console = Console()

# ─── BANNER ────────────────────────────────────────────────────────────────────

BANNER = """
[bold cyan]
 ██╗    ██╗ █████╗     ███████╗██╗██╗  ████████╗███████╗██████╗ 
 ██║    ██║██╔══██╗    ██╔════╝██║██║  ╚══██╔══╝██╔════╝██╔══██╗
 ██║ █╗ ██║███████║    █████╗  ██║██║     ██║   █████╗  ██████╔╝
 ██║███╗██║██╔══██║    ██╔══╝  ██║██║     ██║   ██╔══╝  ██╔══██╗
 ╚███╔███╔╝██║  ██║    ██║     ██║███████╗██║   ███████╗██║  ██║
  ╚══╝╚══╝ ╚═╝  ╚═╝    ╚═╝     ╚═╝╚══════╝╚═╝   ╚══════╝╚═╝  ╚═╝
[/bold cyan]"""


def show_banner():
    """Tampilkan banner dan informasi tool."""
    console.print(BANNER)
    console.print(
        Panel(
            "[bold white]WhatsApp Universal Number Validator[/bold white]\n"
            "[dim]Validasi nomor WhatsApp dengan kecepatan tinggi[/dim]\n"
            "[dim]Tanpa kirim pesan • Aman untuk akun Anda[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def step_auth(validator: WhatsAppValidator):
    """
    Step 1: Autentikasi WhatsApp.
    Cek sesi yang sudah ada, atau minta pairing code baru.
    """
    console.print(Rule("[bold yellow]Step 1: Autentikasi WhatsApp[/bold yellow]", style="yellow"))
    console.print()

    if validator.has_session():
        console.print("[green]📱 Sesi login ditemukan! Mencoba koneksi...[/green]")
    else:
        console.print("[yellow]🔐 Belum ada sesi login. Perlu pairing code.[/yellow]")
        console.print()
        
        phone = Prompt.ask(
            "[bold cyan]Masukkan nomor HP untuk pairing[/bold cyan]\n"
            "[dim](contoh: 08123456789 atau 628123456789)[/dim]"
        )

        if not phone.strip():
            console.print("[red]❌ Nomor tidak boleh kosong![/red]")
            sys.exit(1)

        # Mulai koneksi (non-blocking)
        validator.connect_and_wait()
        
        # Tunggu sebentar agar client siap
        time.sleep(2)

        # Minta pairing code
        try:
            code = validator.authenticate(phone.strip())
            console.print()
            console.print(
                Panel(
                    f"[bold green]🔑 Pairing Code: [bold white on blue] {code} [/bold white on blue][/bold green]\n\n"
                    "[white]Buka WhatsApp di HP Anda:[/white]\n"
                    "[dim]  1. Buka Settings / Pengaturan[/dim]\n"
                    "[dim]  2. Pilih 'Linked Devices' / 'Perangkat Tertaut'[/dim]\n"
                    "[dim]  3. Pilih 'Link a Device' / 'Tautkan Perangkat'[/dim]\n"
                    "[dim]  4. Pilih 'Link with phone number'[/dim]\n"
                    "[dim]  5. Masukkan kode di atas[/dim]",
                    title="[bold]Pairing Code[/bold]",
                    border_style="green",
                    padding=(1, 3),
                )
            )
        except Exception as e:
            console.print(f"[red]❌ Gagal mendapatkan pairing code: {e}[/red]")
            sys.exit(1)

        # Tunggu pairing berhasil
        console.print("\n[yellow]⏳ Menunggu pairing... (maksimal 120 detik)[/yellow]")
        if not validator.wait_for_connection(timeout=120):
            console.print("[red]❌ Timeout! Pairing tidak berhasil dalam waktu yang ditentukan.[/red]")
            sys.exit(1)

        console.print()
        return

    # Jika sudah ada sesi, langsung connect
    validator.connect_and_wait()
    console.print("[yellow]⏳ Menghubungkan ke WhatsApp...[/yellow]")
    
    if not validator.wait_for_connection(timeout=60):
        console.print("[red]❌ Gagal terhubung! Coba hapus file sesi dan pairing ulang.[/red]")
        if Confirm.ask("[yellow]Hapus sesi dan coba lagi?[/yellow]"):
            try:
                for db_file in [validator.session_name, f"{validator.session_name}.db"]:
                    if os.path.exists(db_file):
                        os.remove(db_file)
                console.print("[green]✓ Sesi dihapus. Silakan jalankan ulang script.[/green]")
            except Exception:
                pass
        sys.exit(1)

    console.print()


def step_input() -> list[str]:
    """
    Step 2: Pilih sumber data dan baca nomor.
    """
    console.print(Rule("[bold yellow]Step 2: Sumber Data[/bold yellow]", style="yellow"))
    console.print()

    console.print("[bold]Pilih sumber input nomor:[/bold]")
    console.print("  [cyan]1.[/cyan] Ketik manual di terminal")
    console.print("  [cyan]2.[/cyan] Baca dari file (Excel/CSV/TXT)")
    console.print()

    choice = Prompt.ask(
        "[bold cyan]Pilihan Anda[/bold cyan]",
        choices=["1", "2"],
        default="2",
    )

    raw_numbers = []

    if choice == "1":
        raw_numbers = read_manual()
    else:
        file_path = Prompt.ask(
            "[bold cyan]Masukkan path file[/bold cyan]\n"
            "[dim](contoh: data/nomor.xlsx, contacts.csv, list.txt)[/dim]"
        )

        if not file_path.strip():
            console.print("[red]❌ Path file tidak boleh kosong![/red]")
            sys.exit(1)

        raw_numbers = detect_and_read(file_path.strip())

    if not raw_numbers:
        console.print("[red]❌ Tidak ada nomor yang berhasil dibaca![/red]")
        sys.exit(1)

    # Format & normalize
    console.print(f"\n[cyan]🔄 Memformat {len(raw_numbers)} nomor mentah...[/cyan]")
    formatted = format_numbers(raw_numbers)

    console.print(f"[green]✅ {len(formatted)} nomor valid & unik siap divalidasi[/green]")

    if len(raw_numbers) != len(formatted):
        diff = len(raw_numbers) - len(formatted)
        console.print(f"[dim]   ({diff} nomor dihapus: hanya membuang duplikat)[/dim]")

    console.print()
    return formatted


def step_validate(validator: WhatsAppValidator, numbers: list[str]):
    """
    Step 3: Jalankan validasi dan simpan hasil.
    """
    console.print(Rule("[bold yellow]Step 3: Validasi WhatsApp[/bold yellow]", style="yellow"))
    console.print()

    # Konfirmasi sebelum mulai
    if not Confirm.ask(
        f"[bold]Mulai validasi [cyan]{len(numbers)}[/cyan] nomor?[/bold]",
        default=True,
    ):
        console.print("[yellow]Dibatalkan oleh user.[/yellow]")
        sys.exit(0)

    start_time = time.time()
    active, invalid = validator.check_numbers(numbers)
    elapsed = time.time() - start_time

    # Tampilkan hasil
    validator.display_results(active, invalid, elapsed)

    # Simpan ke file
    validator.save_results(active, invalid, elapsed)

    console.print()
    console.print(
        Panel(
            "[bold green]🎉 Validasi selesai![/bold green]\n"
            "[dim]Cek folder results/ untuk hasil lengkap.[/dim]",
            border_style="green",
            padding=(1, 2),
        )
    )


def main():
    """Entry point utama."""
    try:
        show_banner()

        # Inisialisasi validator
        validator = WhatsAppValidator()

        # Step 1: Auth
        step_auth(validator)

        while True:
            # Step 2: Input
            numbers = step_input()

            # Step 3: Validate & Save
            step_validate(validator, numbers)

            console.print(Rule(style="dim"))
            if not Confirm.ask(
                "\n[bold yellow]Ingin memvalidasi nomor lain?[/bold yellow]",
                default=True,
            ):
                console.print("\n[yellow]👋 Terima kasih telah menggunakan Ghost Validator. Sampai jumpa![/yellow]")
                break

    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Dibatalkan oleh user. Sampai jumpa![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Error tidak terduga: {e}[/red]")
        console.print("[dim]Pastikan semua dependencies terinstall: pip install -r requirements.txt[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
