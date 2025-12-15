#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把当前目录下所有 pdf 每 6 页拼成 1 页，再按 ~20 MB 一份合并
python pdf_6in1_merge.py
"""
import os
import math
import tempfile
import shutil
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

COLS = 4  # 列数
ROWS = 5  # 行数
PAGES_PER_SHEET = COLS * ROWS  # 15，自动对齐
# ----------------------- 参数可改 -----------------------
SRC_DIR = Path('./pdf')  # 源 PDF 所在目录
OUT_DIR = Path(f'./{PAGES_PER_SHEET}in1_out')  # 拼图后的单文件输出目录
MERGE_DIR = Path('./merged')  # 最终合并大文件目录
DPI = 300  # 拆页分辨率，越大越清晰但越慢
TARGET_MB = 20  # 每份合并文件的目标大小（MB）
# ------------------------------------------------------

A4_W, A4_H = 2480, 3508  # 300 dpi 下纵向 A4 的宽高（PIL 像素）


def pdf_to_images(pdf_path: Path, dpi: int = DPI):
    """返回 list[PIL.Image] 每一页"""
    doc = fitz.open(pdf_path)
    imgs = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        imgs.append(img)
    doc.close()
    return imgs


def build_grid_sheet(images, cols: int = COLS, rows: int = ROWS):
    """cols×rows 张图 → 整张 A4 纵向铺满，无白边"""
    if len(images) != cols * rows:
        raise ValueError(f"need exact {cols * rows} images")
    cell_w = A4_W // cols
    cell_h = A4_H // rows

    sheet = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
    for idx, img in enumerate(images):
        img.thumbnail((cell_w, cell_h), Image.LANCZOS)
        col = idx % cols
        row = idx // cols
        x = col * cell_w
        y = row * cell_h
        offset_x = (cell_w - img.width) // 2
        offset_y = (cell_h - img.height) // 2
        sheet.paste(img, (x + offset_x, y + offset_y))
    return sheet


def images_to_pdf(images, output_pdf: Path):
    """PIL 图像列表直接写 PDF"""
    images[0].save(
        output_pdf,
        "PDF",
        quality=95,
        optimize=True,
        save_all=True,
        append_images=images[1:]
    )


def process_single_pdf(pdf_path: Path, out_dir: Path, pages_per_sheet: int = PAGES_PER_SHEET):
    """
    把单个 PDF 每 <pages_per_sheet> 页拼成 1 页 3×4 宫格 A4 纵向版图
    返回生成的小 PDF 路径
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    imgs = pdf_to_images(pdf_path)  # 列表[PIL.Image]
    n = len(imgs)
    sheets = []  # 拼好的版图

    for i in range(0, n, pages_per_sheet):
        chunk = imgs[i:i + pages_per_sheet]
        # 不足 pages_per_sheet 张时补空白页
        blank = Image.new('RGB', (A4_W, A4_H), (255, 255, 255))
        while len(chunk) < pages_per_sheet:
            chunk.append(blank)

        # 每 COLS*ROWS 张拼一张版图
        grid = COLS * ROWS
        for j in range(0, pages_per_sheet, grid):
            group = chunk[j:j + grid]  # 用 grid 代替 12
            while len(group) < grid:  # 不足 grid 张补空白
                group.append(blank)
            sheets.append(build_grid_sheet(group, COLS, ROWS))

    # 所有版图 → 一个 PDF
    out_pdf = out_dir / f"{pdf_path.stem}_{COLS}x{ROWS}.pdf"
    images_to_pdf(sheets, out_pdf)
    return out_pdf


def merge_by_size(pdf_paths, merge_dir: Path, target_mb: int):
    """按目标大小合并，返回生成的大文件路径列表"""
    merge_dir.mkdir(parents=True, exist_ok=True)
    target_bytes = target_mb * 1024 * 1024
    out_list = []
    current_size = 0
    current_docs = []
    idx = 0

    for p in pdf_paths:
        sz = p.stat().st_size
        # 如果加入后超限，且已有文件，则先合并一份
        if current_size + sz > target_bytes and current_docs:
            out_file = merge_dir / f"merged_part{idx:03d}.pdf"
            merge_pdfs(current_docs, out_file)
            out_list.append(out_file)
            idx += 1
            current_docs = []
            current_size = 0
        current_docs.append(p)
        current_size += sz

    # 末尾剩余
    if current_docs:
        out_file = merge_dir / f"merged_part{idx:03d}.pdf"
        merge_pdfs(current_docs, out_file)
        out_list.append(out_file)
    return out_list


def merge_pdfs(pdf_paths, output: Path):
    """简单合并"""
    writer = fitz.open()
    for p in pdf_paths:
        reader = fitz.open(p)
        writer.insert_pdf(reader)
        reader.close()
    writer.save(str(output))
    writer.close()


def main():
    # 1. 列出所有 pdf
    from itertools import chain
    src_pdfs = sorted(
        p for p in SRC_DIR.iterdir()
        if p.is_file() and p.suffix.lower() == '.pdf'
    )
    if not src_pdfs:
        print("当前目录未找到 pdf 文件")
        return
    print(f"共发现 {len(src_pdfs)} 个 PDF，开始拼图…")

    # 2. 逐个处理
    small_pdfs = []
    for pdf in src_pdfs:
        print(f"[{PAGES_PER_SHEET}→1]", pdf.name)
        small_pdfs.append(process_single_pdf(pdf, OUT_DIR, PAGES_PER_SHEET))

    print("拼图完成，开始按 ~20 MB 合并…")
    # 3. 按大小合并
    merged_list = merge_by_size(small_pdfs, MERGE_DIR, TARGET_MB)
    print("全部完成！生成文件：")
    for m in merged_list:
        mb = m.stat().st_size / 1024 / 1024
        print(f"  {m.name}  {mb:.1f} MB")


if __name__ == "__main__":
    main()
