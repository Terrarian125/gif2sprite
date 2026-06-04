import os
import math
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageSequence

# ==========================================
# 1. ロジック部分（各機能のクラス）
# ==========================================

class SpriteSheetCreator:
    """1. 複数の画像からスプライトシートを作成"""
    @staticmethod
    def create(image_paths, cols, rows, output_path):
        if not image_paths:
            raise ValueError("画像が選択されていません。")
        first_img = Image.open(image_paths[0])
        cell_w, cell_h = first_img.size
        spritesheet = Image.new("RGBA", (cell_w * cols, cell_h * rows), (0, 0, 0, 0))
        
        for idx, path in enumerate(image_paths):
            if idx >= cols * rows:
                break
            c, r = idx % cols, idx // cols
            with Image.open(path) as img:
                if img.size != (cell_w, cell_h):
                    img = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
                spritesheet.paste(img, (c * cell_w, r * cell_h))
        spritesheet.save(output_path)

class SpriteSheetSplitter:
    """2. スプライトシートを個別の画像に分解"""
    @staticmethod
    def split(sheet_path, cols, rows, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        with Image.open(sheet_path) as sheet:
            cell_w = sheet.size[0] // cols
            cell_h = sheet.size[1] // rows
            idx = 0
            for r in range(rows):
                for c in range(cols):
                    cropped_img = sheet.crop((c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h))
                    if cropped_img.getbbox(): 
                        cropped_img.save(os.path.join(output_dir, f"sprite_{idx:03d}.png"))
                        idx += 1
        return idx

class GifToSpriteConverter:
    """4. GIFアニメーションをスプライトシートに変換"""
    @staticmethod
    def get_frame_count(gif_path):
        try:
            with Image.open(gif_path) as gif:
                gif.seek(gif.n_frames - 1)
                return gif.n_frames
        except Exception:
            return 0

    @staticmethod
    def calculate_best_grid(frame_count):
        if frame_count <= 0:
            return 4, 4
        cols = math.ceil(math.sqrt(frame_count))
        rows = math.ceil(frame_count / cols)
        return cols, rows

    @staticmethod
    def convert(gif_path, cols, rows, output_path):
        with Image.open(gif_path) as gif:
            frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(gif)]
        if not frames:
            return
        cell_w, cell_h = frames[0].size
        spritesheet = Image.new("RGBA", (cell_w * cols, cell_h * rows), (0, 0, 0, 0))
        for idx, frame in enumerate(frames):
            if idx >= cols * rows:
                break
            spritesheet.paste(frame, ((idx % cols) * cell_w, (idx // cols) * cell_h))
        spritesheet.save(output_path)


# ==========================================
# 2. 画面部分（GUIアプリケーション）
# ==========================================

class SpriteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("スプライトシート・ツールボックス Pro")
        self.geometry("640x480")
        ctk.set_appearance_mode("dark")
        
        # 変数保持用
        self.selected_files = []
        self.selected_sheet_for_split = ""
        self.selected_gif_file = ""

        # タブの作成
        self.tabview = ctk.CTkTabview(self, width=600, height=440)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_create = self.tabview.add("画像 ➔ シート")
        self.tab_split = self.tabview.add("シート ➔ 画像")
        self.tab_togif = self.tabview.add("シート ➔ GIF")
        self.tab_fromgif = self.tabview.add("GIF ➔ シート")
        
        self.setup_create_tab()
        self.setup_split_tab()
        self.setup_togif_tab() # 予告タブ
        self.setup_fromgif_tab()

    def create_grid_inputs(self, parent):
        """共通の縦横グリッド入力フォーム"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=10)
        ctk.CTkLabel(frame, text="横のコマ数 (列):").grid(row=0, column=0, padx=5)
        cols_entry = ctk.CTkEntry(frame, width=60)
        cols_entry.insert(0, "4")
        cols_entry.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(frame, text="縦のコマ数 (row):").grid(row=0, column=2, padx=5)
        rows_entry = ctk.CTkEntry(frame, width=60)
        rows_entry.insert(0, "4")
        rows_entry.grid(row=0, column=3, padx=5)
        return cols_entry, rows_entry

    # --- 1. 画像 ➔ シート ---
    def setup_create_tab(self):
        lbl = ctk.CTkLabel(self.tab_create, text="複数の画像を選択してスプライトシートを作成します")
        lbl.pack(pady=10)
        
        self.lbl_create_status = ctk.CTkLabel(self.tab_create, text="選択されたファイル: 0枚", text_color="gray")
        btn_select = ctk.CTkButton(self.tab_create, text="画像ファイルを選択", command=self.select_multiple_files)
        btn_select.pack(pady=10)
        self.lbl_create_status.pack()
        
        self.c_entry_c, self.r_entry_c = self.create_grid_inputs(self.tab_create)
        
        btn_run = ctk.CTkButton(self.tab_create, text="スプライトシートを生成して保存", fg_color="green", hover_color="darkgreen", command=self.run_create)
        btn_run.pack(pady=20)

    def select_multiple_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if files:
            self.selected_files = list(files)
            self.lbl_create_status.configure(text=f"選択されたファイル: {len(self.selected_files)}枚", text_color="white")
            cols, rows = GifToSpriteConverter.calculate_best_grid(len(self.selected_files))
            self.c_entry_c.delete(0, tk.END)
            self.c_entry_c.insert(0, str(cols))
            self.r_entry_c.delete(0, tk.END)
            self.r_entry_c.insert(0, str(rows))

    def run_create(self):
        try:
            cols, rows = int(self.c_entry_c.get()), int(self.r_entry_c.get())
            out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
            if out_path:
                SpriteSheetCreator.create(self.selected_files, cols, rows, out_path)
                messagebox.showinfo("成功", "スプライトシートを保存しました！")
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    # --- 2. シート ➔ 画像 ---
    def setup_split_tab(self):
        lbl = ctk.CTkLabel(self.tab_split, text="スプライトシートを個別の画像（連番）に分解します")
        lbl.pack(pady=10)
        
        self.lbl_split_file = ctk.CTkLabel(self.tab_split, text="ファイルが選択されていません", text_color="gray")
        btn_select = ctk.CTkButton(self.tab_split, text="スプライトシートを選択", command=self.select_sheet_for_split)
        btn_select.pack(pady=10)
        self.lbl_split_file.pack()
        
        self.c_entry_s, self.r_entry_s = self.create_grid_inputs(self.tab_split)
        
        btn_run = ctk.CTkButton(self.tab_split, text="分解してフォルダに保存", fg_color="green", hover_color="darkgreen", command=self.run_split)
        btn_run.pack(pady=20)

    def select_sheet_for_split(self):
        file = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file:
            self.selected_sheet_for_split = file
            with Image.open(file) as img:
                w, h = img.size
            self.lbl_split_file.configure(text=f"{os.path.basename(file)} ({w}x{h} px)", text_color="white")

    def run_split(self):
        try:
            cols, rows = int(self.c_entry_s.get()), int(self.r_entry_s.get())
            out_dir = filedialog.askdirectory(title="保存先フォルダを選択")
            if out_dir:
                count = SpriteSheetSplitter.split(self.selected_sheet_for_split, cols, rows, out_dir)
                messagebox.showinfo("成功", f"分解が完了しました！\n{count}枚の画像を保存しました。")
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    # --- 3. シート ➔ GIF (アップデート予告版) ---
    def setup_togif_tab(self):
        # 案内文
        lbl_info = ctk.CTkLabel(self.tab_togif, text="シートからGIFへの変換機能は現在開発中です！", font=("🚀", 16, "bold"))
        lbl_info.pack(pady=30)
        
        lbl_expect = ctk.CTkLabel(self.tab_togif, text="アップデートにこうご期待！", font=("🎨", 20, "bold"), text_color="cyan")
        lbl_expect.pack(pady=10)
        
        lbl_sub = ctk.CTkLabel(self.tab_togif, text="最新の開発状況やソースコードはGitHubでチェックできます。", text_color="gray")
        lbl_sub.pack(pady=20)
        
        # GitHubへのリンクボタン
        btn_github = ctk.CTkButton(
            self.tab_togif, 
            text="GitHubでリポジトリを見る", 
            fg_color="#24292e", # GitHubっぽいダークグレー
            hover_color="#2f363d",
            command=self.open_github
        )
        btn_github.pack(pady=10)

    def open_github(self):
        webbrowser.open("https://github.com/Terrarian125/gif2sprite")

    # --- 4. GIF ➔ シート ---
    def setup_fromgif_tab(self):
        lbl = ctk.CTkLabel(self.tab_fromgif, text="アニメーションGIFを1枚のスプライトシートに結合します")
        lbl.pack(pady=10)
        
        self.lbl_fromgif_file = ctk.CTkLabel(self.tab_fromgif, text="ファイルが選択されていません", text_color="gray")
        self.lbl_frame_count = ctk.CTkLabel(self.tab_fromgif, text="", text_color="cyan")
        
        btn_select = ctk.CTkButton(self.tab_fromgif, text="GIFファイルを選択", command=self.select_gif_and_detect)
        btn_select.pack(pady=10)
        self.lbl_fromgif_file.pack()
        self.lbl_frame_count.pack()
        
        self.c_entry_fg, self.r_entry_fg = self.create_grid_inputs(self.tab_fromgif)
        
        btn_run = ctk.CTkButton(self.tab_fromgif, text="スプライトシートを生成して保存", fg_color="green", hover_color="darkgreen", command=self.run_fromgif)
        btn_run.pack(pady=20)

    def select_gif_and_detect(self):
        file = filedialog.askopenfilename(filetypes=[("GIF Files", "*.gif")])
        if file:
            self.selected_gif_file = file
            self.lbl_fromgif_file.configure(text=os.path.basename(file), text_color="white")
            
            frames = GifToSpriteConverter.get_frame_count(file)
            self.lbl_frame_count.configure(text=f"検出された総コマ数: {frames} コマ", text_color="cyan")
            
            cols, rows = GifToSpriteConverter.calculate_best_grid(frames)
            self.c_entry_fg.delete(0, tk.END)
            self.c_entry_fg.insert(0, str(cols))
            self.r_entry_fg.delete(0, tk.END)
            self.r_entry_fg.insert(0, str(rows))

    def run_fromgif(self):
        try:
            cols, rows = int(self.c_entry_fg.get()), int(self.r_entry_fg.get())
            out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
            if out_path:
                GifToSpriteConverter.convert(self.selected_gif_file, cols, rows, out_path)
                messagebox.showinfo("成功", "GIFからスプライトシートを作成しました！")
        except Exception as e:
            messagebox.showerror("エラー", str(e))


if __name__ == "__main__":
    app = SpriteApp()
    app.mainloop()