"""
reader.py — Universal file reader untuk nomor telepon.

Mendukung: .xlsx, .csv, .txt, .log, dan input manual dari terminal.
Menggunakan regex untuk mengekstrak nomor dari file teks biasa.
"""

import os
import re

import pandas as pd
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def read_excel(path: str) -> list[str]:
    """
    Baca nomor telepon dari file Excel (.xlsx).
    Menggunakan dtype=str agar nomor tidak berubah jadi format ilmiah (6.2E+12).
    """
    try:
        df = pd.read_excel(path, dtype=str, engine="openpyxl")
    except Exception as e:
        console.print(f"[red]❌ Gagal membaca file Excel: {e}[/red]")
        return []

    numbers = []
    # Cari kolom yang berisi nomor telepon
    for col in df.columns:
        col_data = df[col].dropna().astype(str).tolist()
        # Cek apakah kolom ini berisi angka (minimal 50% isinya digit)
        digit_count = sum(1 for val in col_data if re.match(r"^[\d\s\+\-\(\)\.]+$", val.strip()))
        if digit_count > len(col_data) * 0.5:
            numbers.extend(col_data)
            console.print(f"[green]  ✓ Kolom '{col}' terdeteksi ({len(col_data)} nomor)[/green]")

    if not numbers:
        # Fallback: ambil kolom pertama
        first_col = df.iloc[:, 0].dropna().astype(str).tolist()
        numbers.extend(first_col)
        console.print(f"[yellow]  ⚠ Menggunakan kolom pertama sebagai fallback ({len(first_col)} baris)[/yellow]")

    return numbers


def read_csv(path: str) -> list[str]:
    """
    Baca nomor telepon dari file CSV.
    Logika deteksi kolom sama dengan Excel.
    """
    try:
        # Coba berbagai delimiter
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(path, dtype=str, sep=sep)
                if len(df.columns) >= 1:
                    break
            except Exception:
                continue
        else:
            console.print("[red]❌ Gagal mendeteksi format CSV[/red]")
            return []
    except Exception as e:
        console.print(f"[red]❌ Gagal membaca file CSV: {e}[/red]")
        return []

    numbers = []
    for col in df.columns:
        col_data = df[col].dropna().astype(str).tolist()
        digit_count = sum(1 for val in col_data if re.match(r"^[\d\s\+\-\(\)\.]+$", val.strip()))
        if digit_count > len(col_data) * 0.5:
            numbers.extend(col_data)
            console.print(f"[green]  ✓ Kolom '{col}' terdeteksi ({len(col_data)} nomor)[/green]")

    if not numbers:
        first_col = df.iloc[:, 0].dropna().astype(str).tolist()
        numbers.extend(first_col)
        console.print(f"[yellow]  ⚠ Menggunakan kolom pertama sebagai fallback ({len(first_col)} baris)[/yellow]")

    return numbers


def read_text(path: str) -> list[str]:
    """
    Baca dan ekstrak nomor telepon dari file teks (.txt, .log, dll).
    Menggunakan regex untuk menangkap deretan 9-15 digit dari setiap baris.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        console.print(f"[red]❌ Gagal membaca file: {e}[/red]")
        return []

    # Ekstrak semua deretan angka 9-15 digit (termasuk yang ada prefix +, spasi, strip)
    raw_numbers = re.findall(r"[\+]?[\d\s\-\(\)\.]{9,20}", content)
    numbers = [n.strip() for n in raw_numbers if n.strip()]

    console.print(f"[green]  ✓ {len(numbers)} nomor diekstrak dari file teks[/green]")
    return numbers


def read_manual() -> list[str]:
    """
    Input interaktif dari terminal.
    User bisa memasukkan nomor dipisah koma, spasi, atau satu per baris.
    Ketik 'done' atau baris kosong untuk selesai.
    """
    console.print("\n[bold cyan]📱 Input Manual[/bold cyan]")
    console.print("[dim]Masukkan nomor telepon (pisahkan dengan koma, spasi, atau enter).[/dim]")
    console.print("[dim]Ketik 'done' atau tekan Enter 2x untuk selesai.[/dim]\n")

    numbers = []
    empty_count = 0

    while True:
        try:
            line = input("  → ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if line.lower() == "done":
            break

        if not line:
            empty_count += 1
            if empty_count >= 2:
                break
            continue
        else:
            empty_count = 0

        # Split by koma, spasi, semicolon, atau tab
        parts = re.split(r"[,;\s\t]+", line)
        for part in parts:
            part = part.strip()
            if part:
                numbers.append(part)

    console.print(f"[green]  ✓ {len(numbers)} nomor diinput secara manual[/green]")
    return numbers


def detect_and_read(path: str) -> list[str]:
    """
    Auto-detect format file berdasarkan ekstensi dan baca nomor.
    
    Args:
        path: Path ke file input
        
    Returns:
        List nomor mentah (belum diformat)
    """
    if not os.path.exists(path):
        console.print(f"[red]❌ File tidak ditemukan: {path}[/red]")
        return []

    ext = os.path.splitext(path)[1].lower()

    if ext == ".xlsx" or ext == ".xls":
        console.print(f"[cyan]📊 Membaca file Excel: {os.path.basename(path)}[/cyan]")
        return read_excel(path)
    elif ext == ".csv":
        console.print(f"[cyan]📋 Membaca file CSV: {os.path.basename(path)}[/cyan]")
        return read_csv(path)
    elif ext in (".txt", ".log", ".text", ".dat"):
        console.print(f"[cyan]📄 Membaca file teks: {os.path.basename(path)}[/cyan]")
        return read_text(path)
    else:
        # Fallback: coba baca sebagai teks biasa
        console.print(f"[yellow]⚠ Format '{ext}' tidak dikenal, mencoba baca sebagai teks...[/yellow]")
        return read_text(path)
