"""
formatter.py — Intelligent Auto-Formatter untuk nomor telepon WhatsApp.

Membersihkan, menormalisasi prefix, dan memvalidasi panjang nomor.
Mengubah input berantakan menjadi format standar internasional WhatsApp (JID).
"""

import re


def clean_number(raw: str) -> str:
    """
    Hapus karakter non-digit dari string nomor.
    Menghapus: spasi, +, (, ), -, titik, dan karakter lainnya.
    """
    return re.sub(r"[^\d]", "", raw.strip())


def normalize_prefix(number: str) -> str:
    """
    Normalisasi prefix nomor Indonesia ke format internasional.
    
    Rules:
        - 08... → 628...
        - 8...  → 628...
        - 628.. → 628.. (sudah benar)
        - Nomor lain dibiarkan apa adanya
    """
    if number.startswith("08"):
        return "62" + number[1:]
    elif number.startswith("8"):
        return "62" + number
    elif number.startswith("628"):
        return number
    # Untuk nomor internasional lain, biarkan
    return number


def is_valid_length(number: str) -> bool:
    """
    Validasi panjang nomor setelah dibersihkan.
    Sangat permisif untuk mendukung kebutuhan user (minimal 3 digit).
    """
    return len(number) >= 3


def format_numbers(raw_list: list[str]) -> list[str]:
    """
    Pipeline lengkap: clean → normalize → validate → deduplicate.
    
    Args:
        raw_list: Daftar nomor mentah dari berbagai sumber input
        
    Returns:
        List nomor yang sudah bersih, unik, dan valid
    """
    seen = set()
    result = []
    
    for raw in raw_list:
        if not raw or not raw.strip():
            continue
            
        cleaned = clean_number(raw)
        
        if not cleaned:
            continue
            
        normalized = normalize_prefix(cleaned)
        
        # Cek duplikat adalah prioritas utama sesuai permintaan user
        if normalized in seen:
            continue
            
        # Tetap minimal 3 digit agar tidak memproses sampah/kosong
        if len(normalized) < 3:
            continue
            
        seen.add(normalized)
        result.append(normalized)
    
    return result
