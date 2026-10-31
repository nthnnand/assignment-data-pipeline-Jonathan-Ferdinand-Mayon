import os
import pandas as pd
import numpy as np

def load_data(filepath):
    """Fungsi untuk membaca dataset CSV dari folder raw."""
    print("=== 1. EXTRACT: Membaca Dataset ===")
    df = pd.read_csv(filepath)
    print(f"Dataset berhasil dimuat dengan {df.shape[0]} baris dan {df.shape[1]} kolom.\n")
    return df

def inspect_data(df):
    """Fungsi untuk memeriksa kondisi awal dataset (Data Inspection)."""
    print("=== 2. INSPECTION: Pemeriksaan Awal Dataset ===")
    
    # Lima baris pertama dataset
    print("--- Lima Baris Pertama Dataset ---")
    print(df.head())
    print()
    
    # Jumlah baris dan kolom
    print(f"Jumlah baris: {df.shape[0]}")
    print(f"Jumlah kolom: {df.shape[1]}")
    print()
    
    # Nama setiap kolom
    print("--- Nama Kolom ---")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    print()
    
    # Tipe data setiap kolom
    print("--- Tipe Data Setiap Kolom ---")
    print(df.dtypes)
    print()
    
    # Jumlah missing values pada setiap kolom
    missing = df.isnull().sum()
    missing_only = missing[missing > 0]
    print(f"--- Missing Values (Total: {missing_only.sum()}) ---")
    if len(missing_only) > 0:
        print(missing_only)
    else:
        print("  Tidak ada missing values.")
    print()
    
    # Jumlah duplicate records
    print(f"Jumlah baris duplikat: {df.duplicated().sum()}")
    print()
    
    # Nilai unik pada kolom kategorikal yang relevan
    print("--- Nilai Unik pada Kolom Kategorikal ---")
    cat_cols = df.select_dtypes(include=['object', 'str']).columns
    for col in cat_cols:
        unique_vals = df[col].nunique()
        print(f"  {col} ({unique_vals} unik): {df[col].unique()[:10].tolist()}"
              + (" ..." if df[col].nunique() > 10 else ""))
    print()

    # Kolom dengan tipe data yang belum sesuai
    print("--- Kolom dengan Tipe Data Belum Sesuai ---")
    if 'transaction_date' in df.columns and df['transaction_date'].dtype != 'datetime64[ns]':
        print(f"  - 'transaction_date' bertipe '{df['transaction_date'].dtype}', seharusnya datetime.")
    if 'normalized-losses' in df.columns and df['normalized-losses'].dtype == 'int64':
        print(f"  - 'normalized-losses' bertipe 'int64', sebaiknya float64 karena mengandung potensi missing values.")
    print()

    # Penulisan kategori yang belum konsisten
    print("--- Penulisan Kategori Tidak Konsisten ---")
    for col in cat_cols:
        lower_unique = df[col].dropna().str.lower().str.strip().nunique()
        raw_unique = df[col].dropna().nunique()
        if lower_unique < raw_unique:
            contoh = df[col].dropna().unique()[:5].tolist()
            print(f"  - Kolom '{col}': {raw_unique} nilai unik, tapi hanya {lower_unique} "
                  f"setelah di-lowercase & strip. Contoh: {contoh}")
    print()

    # Permasalahan lain yang ditemukan
    print("--- Permasalahan Lain ---")
    if 'transaction_date' in df.columns:
        sample_dates = df['transaction_date'].dropna().unique()[:5].tolist()
        print(f"  - Format tanggal tidak konsisten pada 'transaction_date'. "
              f"Contoh: {sample_dates}")
    # Cek spasi berlebih pada kolom kategorikal
    for col in cat_cols:
        has_extra_space = df[col].dropna().apply(lambda x: x != x.strip()).any()
        if has_extra_space:
            print(f"  - Kolom '{col}' memiliki spasi berlebih (leading/trailing spaces).")
    print()

    return df

def clean_data(df):
    """Fungsi untuk melakukan data cleaning berdasarkan temuan."""
    print("=== 3. TRANSFORM: Data Cleaning ===")
    initial_rows = len(df)
    missing_before = df.isnull().sum().sum()
    duplicates_count = df.duplicated().sum()
    changed_columns = []

    # 1. Menghapus baris duplikat
    df = df.drop_duplicates()
    if duplicates_count > 0:
        changed_columns.append('(seluruh baris duplikat)')

    # 2. Menyeragamkan teks kategori & menghapus spasi berlebih pada kolom kategorikal
    cat_cols_to_normalize = ['make', 'body-style', 'drive-wheels', 'fuel-system']
    for col in cat_cols_to_normalize:
        if col in df.columns:
            before_unique = df[col].dropna().nunique()
            df[col] = df[col].str.lower().str.strip()
            after_unique = df[col].dropna().nunique()
            if before_unique != after_unique:
                changed_columns.append(col)

    # 3. Memperbaiki tipe data — menyeragamkan format tanggal pada 'transaction_date'
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
        changed_columns.append('transaction_date')

    # 4. Menangani missing values pada kolom numerik penting dengan median
    num_cols_to_fill = ['price', 'horsepower', 'stroke', 'normalized-losses']
    for col in num_cols_to_fill:
        if col in df.columns and df[col].dtype in ['float64', 'int64']:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())
                changed_columns.append(col)

    # 5. Menangani missing values pada kolom kategorikal dengan modus
    cat_cols_to_fill = ['transaction_date', 'make', 'num-of-doors', 'horsepower-binned']
    for col in cat_cols_to_fill:
        if col in df.columns:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "unknown")
                if col not in changed_columns:
                    changed_columns.append(col)

    missing_after = df.isnull().sum().sum()

    # --- Output terminal sesuai ketentuan ---
    print(f"Jumlah data sebelum cleaning   : {initial_rows} baris")
    print(f"Jumlah data sesudah cleaning    : {len(df)} baris")
    print(f"Jumlah baris duplikat dihapus   : {duplicates_count}")
    print(f"Missing values sebelum cleaning : {missing_before}")
    print(f"Missing values sesudah cleaning : {missing_after}")
    print(f"Kolom yang mengalami perubahan  : {', '.join(changed_columns)}")
    print()

    return df

def transform_data(df):
    """Fungsi untuk melakukan transformasi data (Normalisasi & Encoding)."""
    print("=== 3. TRANSFORM: Data Transformation ===")
    
    # 1. Normalisasi Min-Max Scaling pada kolom numerik 'engine-size'
    if 'engine-size' in df.columns:
        min_val = df['engine-size'].min()
        max_val = df['engine-size'].max()
        df['engine-size_normalized'] = (df['engine-size'] - min_val) / (max_val - min_val)
        print("Kolom 'engine-size' berhasil dinormalisasi menjadi 'engine-size_normalized'.")
        
    # 2. Encoding pada kolom kategorikal 'aspiration' menggunakan One-Hot Encoding
    # Kolom asli tetap dipertahankan agar nilai sebelum dan sesudah dapat dibandingkan di processed dataset
    if 'aspiration' in df.columns:
        df['aspiration'] = df['aspiration'].astype(str).str.lower().str.strip()
        encoded_asp = pd.get_dummies(df['aspiration'], prefix='asp', dtype=int)
        df = pd.concat([df, encoded_asp], axis=1)
        print("Kolom 'aspiration' berhasil di-encode menjadi kolom baru: 'asp_std', 'asp_turbo'.")
        
    print("\nContoh Perbandingan Nilai Sebelum dan Sesudah Transformasi:")
    cols_preview = ['engine-size', 'engine-size_normalized', 'aspiration', 'asp_std', 'asp_turbo']
    valid_cols = [c for c in cols_preview if c in df.columns]
    print(df[valid_cols].head(5).to_string(index=False))
    print("\nTransformasi data selesai.\n")
    return df

def save_data(df, output_filepath):
    """Fungsi untuk menyimpan processed dataset ke folder processed (Load)."""
    print("=== 4. LOAD: Menyimpan Processed Dataset ===")
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    df.to_csv(output_filepath, index=False)
    print(f"Processed dataset berhasil disimpan ke: {output_filepath}\n")

def run_pipeline(raw_path, processed_path):
    """
    Menggabungkan seluruh proses ETL (Extract, Transform, Load)
    menjadi satu pipeline yang dijalankan dari awal sampai akhir dalam satu kali eksekusi.
    """
    print("==================================================")
    print("        MEMULAI AUTOMOTIVE DATA PIPELINE          ")
    print("==================================================\n")
    
    # 1. EXTRACT: Membaca dataset CSV dari data/raw/
    df = load_data(raw_path)
    
    # 2. TRANSFORM: Memeriksa, membersihkan, dan mentransformasi data
    df = inspect_data(df)
    df = clean_data(df)
    df = transform_data(df)
    
    # 3. LOAD: Menyimpan processed dataset ke data/processed/
    save_data(df, processed_path)

if __name__ == "__main__":
    raw_path = "data/raw/automobileEDA_dirty_training.csv"
    processed_path = "data/processed/automobileEDA_processed.csv"
    
    if os.path.exists(raw_path):
        run_pipeline(raw_path, processed_path)
    else:
        print(f"File mentah tidak ditemukan di {raw_path}.")