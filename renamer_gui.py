import os
import re
import pdfplumber
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Папки
OUTPUT_DIR = 'renamed_docs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize(s: str) -> str:
    return re.sub(r'[\/\\\:\*\?\"<>\|]', '', s).strip()

def normalize_amount(a: str) -> str:
    return a.replace(' ','').replace(',','.')

def extract_info(path: str) -> dict:
    """Извлекаем номер, организацию и сумму из платежки."""
    info = {}
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[0].extract_text() or ''
    # номер
    m = re.search(r'ПЛАТЕЖНОЕ\s*ПОРУЧЕНИЕ\s*№\s*(\d+)', text)
    if m: info['number'] = m.group(1)
    # организация
    m = re.search(r'(?:Бенефициар|Получатель)[:\s]+([^\n\r]+)', text)
    if m: info['entity'] = sanitize(m.group(1))
    # сумма
    m = re.search(r'Сумма[:\s]+([\d\s\.,]+)', text)
    if m: info['amount'] = normalize_amount(m.group(1))
    return info

def build_name(info: dict) -> str:
    if all(k in info for k in ('number','entity','amount')):
        return f"платежка{info['number']}_{info['entity']}_{info['amount']}.pdf"
    return None

def process_files(paths, log_widget):
    for path in paths:
        fname = os.path.basename(path)
        try:
            info = extract_info(path)
            new_name = build_name(info)
            if not new_name:
                log_widget.insert(tk.END, f"[SKIP] не все поля: {fname}\n")
                continue
            dst = os.path.join(OUTPUT_DIR, new_name)
            if os.path.exists(dst):
                log_widget.insert(tk.END, f"[!] уже есть: {new_name}\n")
                continue
            os.rename(path, dst)
            log_widget.insert(tk.END, f"[OK] {fname} → {new_name}\n")
        except Exception as e:
            log_widget.insert(tk.END, f"[ERR] {fname}: {e}\n")
    log_widget.see(tk.END)

def on_select():
    paths = filedialog.askopenfilenames(
        title="Выберите PDF для переименования",
        filetypes=[("PDF files","*.pdf")])
    if paths:
        process_files(paths, log)

def on_drop(event):
    # обработка перетаскивания (Windows)
    files = root.tk.splitlist(event.data)
    pdfs = [f for f in files if f.lower().endswith('.pdf')]
    process_files(pdfs, log)

# GUI
root = tk.Tk()
root.title("Репеймер платежек")
root.geometry("600x400")

btn = tk.Button(root, text="Выбрать PDF...", command=on_select)
btn.pack(pady=10)

log = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20)
log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Поддержка drag & drop (только на Windows по умолчанию)
try:
    import tkinterdnd2 as dnd
    root = dnd.TkinterDnD.Tk()
    log.drop_target_register(dnd.DND_FILES)
    log.dnd_bind('<<Drop>>', on_drop)
except ImportError:
    # без drag&drop будет просто кнопка
    pass

root.mainloop()
