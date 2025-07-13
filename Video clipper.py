import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import subprocess
import zipfile
from datetime import datetime

class VideoClipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Clipper Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.video_path = tk.StringVar()
        self.clip_length = tk.StringVar(value="30")
        self.segments = []
        self.selected_segments = []
        self.output_folder = ""
        self.video_duration = 0.0  # <- Neu
        self.duration_label = None # <- Neu
        
        # Style configuration
        self.setup_styles()
        
        # Create main layout
        self.create_layout()
        
        # Check for ffmpeg
        self.check_ffmpeg()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TButton', background='#4CAF50', foreground='white', borderwidth=0, focuscolor='none', padding=(20, 10))
        style.configure('Secondary.TButton', background='#2196F3', foreground='white', borderwidth=0, focuscolor='none', padding=(15, 8))
        style.configure('Danger.TButton', background='#f44336', foreground='white', borderwidth=0, focuscolor='none', padding=(15, 8))
        style.configure('Modern.TEntry', borderwidth=1, relief='solid', padding=(10, 8))
        style.configure('Card.TFrame', background='#2d2d2d', relief='flat', borderwidth=1)
    
    def create_layout(self):
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.create_sidebar(main_frame)
        self.create_main_area(main_frame)
    
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg='#2d2d2d', width=350)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)
        title = tk.Label(sidebar, text="🎬 Video Clipper Pro", font=('Arial', 18, 'bold'), bg='#2d2d2d', fg='#ffffff')
        title.pack(pady=(20, 30))
        video_frame = tk.Frame(sidebar, bg='#2d2d2d')
        video_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(video_frame, text="📁 Video auswählen", font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#ffffff').pack(anchor=tk.W)
        self.video_label = tk.Label(video_frame, text="Kein Video ausgewählt", bg='#404040', fg='#cccccc', relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 9))
        self.video_label.pack(fill=tk.X, pady=(5, 10), ipady=8, ipadx=10)
        # Videolänge-Label (NEU)
        self.duration_label = tk.Label(video_frame, text="", bg='#2d2d2d', fg='#FFC107', font=('Arial', 10, 'italic'))
        self.duration_label.pack(anchor=tk.W, pady=(0,5))
        select_btn = tk.Button(video_frame, text="Video auswählen", command=self.select_video, bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'), relief=tk.FLAT, cursor='hand2')
        select_btn.pack(fill=tk.X, pady=5)
        drop_frame = tk.Frame(video_frame, bg='#404040', relief=tk.GROOVE, bd=2)
        drop_frame.pack(fill=tk.X, pady=10)
        drop_label = tk.Label(drop_frame, text="Oder Video hier hineinziehen\n(Drag & Drop)", bg='#404040', fg='#888888', font=('Arial', 9), justify=tk.CENTER)
        drop_label.pack(pady=20)
        length_frame = tk.Frame(sidebar, bg='#2d2d2d')
        length_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Label(length_frame, text="⏱️ Clip-Länge (Sekunden)", font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#ffffff').pack(anchor=tk.W)
        length_entry = tk.Entry(length_frame, textvariable=self.clip_length, font=('Arial', 12), justify=tk.CENTER, bg='#404040', fg='white', insertbackground='white')
        length_entry.pack(fill=tk.X, pady=(5, 10), ipady=8)
        self.start_btn = tk.Button(sidebar, text="🚀 Schneiden starten", command=self.start_cutting, bg='#2196F3', fg='white', font=('Arial', 14, 'bold'), relief=tk.FLAT, cursor='hand2', state=tk.DISABLED)
        self.start_btn.pack(fill=tk.X, padx=20, pady=20, ipady=10)
        self.progress = ttk.Progressbar(sidebar, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=10)
        self.status_label = tk.Label(sidebar, text="Bereit", bg='#2d2d2d', fg='#888888', font=('Arial', 10))
        self.status_label.pack(pady=10)
        download_frame = tk.Frame(sidebar, bg='#2d2d2d')
        download_frame.pack(fill=tk.X, padx=20, pady=20)
        self.download_selected_btn = tk.Button(download_frame, text="📥 Ausgewählte downloaden", command=self.download_selected, bg='#FF9800', fg='white', font=('Arial', 11, 'bold'), relief=tk.FLAT, cursor='hand2', state=tk.DISABLED)
        self.download_selected_btn.pack(fill=tk.X, pady=5)
        self.download_all_btn = tk.Button(download_frame, text="📦 Alle als ZIP downloaden", command=self.download_all, bg='#9C27B0', fg='white', font=('Arial', 11, 'bold'), relief=tk.FLAT, cursor='hand2', state=tk.DISABLED)
        self.download_all_btn.pack(fill=tk.X, pady=5)
    
    def create_main_area(self, parent):
        main_area = tk.Frame(parent, bg='#1a1a1a')
        main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        header = tk.Frame(main_area, bg='#2d2d2d', height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        tk.Label(header, text="📹 Video-Segmente", font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='#ffffff').pack(side=tk.LEFT, pady=15, padx=20)
        self.create_segments_area(main_area)
        info_frame = tk.Frame(main_area, bg='#2d2d2d')
        info_frame.pack(fill=tk.X, pady=10)
        tk.Label(info_frame, text="ℹ️ TikTok-Upload: Automatischer Upload ist aktuell nicht möglich.\nDu kannst die Clips aber downloaden und manuell hochladen.", bg='#2d2d2d', fg='#FFC107', font=('Arial', 10), justify=tk.LEFT).pack(padx=20, pady=10)
    
    def create_segments_area(self, parent):
        scroll_frame = tk.Frame(parent, bg='#1a1a1a')
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = tk.Canvas(scroll_frame, bg='#1a1a1a', highlightthickness=0, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        self.segments_frame = tk.Frame(self.canvas, bg='#1a1a1a')
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.segments_frame, anchor=tk.NW)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.segments_frame.bind('<Configure>', self.on_frame_configure)
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def select_video(self):
        file_path = filedialog.askopenfilename(
            title="Video auswählen",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.video_path.set(file_path)
            filename = os.path.basename(file_path)
            self.video_label.config(text=filename, fg='#4CAF50')
            # Videolänge ermitteln und anzeigen (NEU)
            duration = self.get_video_duration(file_path)
            self.video_duration = duration
            if duration:
                min_ = int(duration // 60)
                sec_ = int(duration % 60)
                self.duration_label.config(text=f"Länge: {min_} min {sec_:02d} sec")
            else:
                self.duration_label.config(text="Länge: unbekannt")
            self.start_btn.config(state=tk.NORMAL)
    
    def get_video_duration(self, filepath):
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries',
                'format=duration', '-of', 'csv=p=0', filepath
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception:
            return None
    
    def check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            messagebox.showerror("FFmpeg fehlt", "FFmpeg ist nicht installiert oder nicht im PATH.\n\nBitte installiere FFmpeg von https://ffmpeg.org/")
            return False
    
    def start_cutting(self):
        if not self.video_path.get():
            messagebox.showerror("Fehler", "Bitte wähle zuerst ein Video aus!")
            return
        try:
            clip_length = int(self.clip_length.get())
            if clip_length <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gib eine gültige Clip-Länge ein!")
            return
        self.start_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Schneide Video...", fg='#4CAF50')
        thread = threading.Thread(target=self.cut_video)
        thread.daemon = True
        thread.start()
    
    def cut_video(self):
        try:
            video_path = self.video_path.get()
            clip_length = int(self.clip_length.get())
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_folder = os.path.join(os.path.dirname(video_path), f"{video_name}_segments_{timestamp}")
            os.makedirs(self.output_folder, exist_ok=True)
            duration_cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries',
                'format=duration', '-of', 'csv=p=0', video_path
            ]
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            num_segments = int(duration / clip_length) + (1 if duration % clip_length > 0 else 0)
            self.segments = []
            for i in range(num_segments):
                start_time = i * clip_length
                output_path = os.path.join(self.output_folder, f"segment_{i+1:03d}.mp4")
                self.root.after(0, lambda i=i: self.status_label.config(text=f"Segment {i+1}/{num_segments}..."))
                cmd = [
                    'ffmpeg', '-i', video_path, '-ss', str(start_time),
                    '-t', str(clip_length), '-c', 'copy', '-y', output_path
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(output_path):
                    self.segments.append({
                        'name': f"Segment {i+1}",
                        'path': output_path,
                        'duration': min(clip_length, duration - start_time)
                    })
            self.root.after(0, self.cutting_complete)
        except Exception as e:
            self.root.after(0, lambda: self.cutting_error(str(e)))
    
    def cutting_complete(self):
        self.progress.stop()
        self.status_label.config(text=f"{len(self.segments)} Segmente erstellt!", fg='#4CAF50')
        self.start_btn.config(state=tk.NORMAL)
        self.download_selected_btn.config(state=tk.NORMAL)
        self.download_all_btn.config(state=tk.NORMAL)
        self.display_segments()
        messagebox.showinfo("Erfolgreich", f"{len(self.segments)} Video-Segmente wurden erstellt!")
    
    def cutting_error(self, error_msg):
        self.progress.stop()
        self.status_label.config(text="Fehler beim Schneiden", fg='#f44336')
        self.start_btn.config(state=tk.NORMAL)
        messagebox.showerror("Fehler", f"Fehler beim Schneiden: {error_msg}")
    
    def display_segments(self):
        for widget in self.segments_frame.winfo_children():
            widget.destroy()
        self.selected_segments = []
        for i, segment in enumerate(self.segments):
            self.create_segment_card(i, segment)
    
    def create_segment_card(self, index, segment):
        card = tk.Frame(self.segments_frame, bg='#2d2d2d', relief=tk.RAISED, bd=1)
        card.pack(fill=tk.X, padx=20, pady=10)
        header = tk.Frame(card, bg='#2d2d2d')
        header.pack(fill=tk.X, padx=15, pady=10)
        var = tk.BooleanVar()
        self.selected_segments.append(var)
        checkbox = tk.Checkbutton(header, variable=var, bg='#2d2d2d', activebackground='#2d2d2d', selectcolor='#4CAF50')
        checkbox.pack(side=tk.LEFT)
        info_frame = tk.Frame(header, bg='#2d2d2d')
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        tk.Label(info_frame, text=segment['name'], font=('Arial', 12, 'bold'), bg='#2d2d2d', fg='#ffffff').pack(anchor=tk.W)
        tk.Label(info_frame, text=f"Dauer: {segment['duration']:.1f}s", font=('Arial', 10), bg='#2d2d2d', fg='#888888').pack(anchor=tk.W)
        btn_frame = tk.Frame(header, bg='#2d2d2d')
        btn_frame.pack(side=tk.RIGHT)
        download_btn = tk.Button(btn_frame, text="📥", command=lambda idx=index: self.download_single(idx), bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'), relief=tk.FLAT, cursor='hand2', width=3)
        download_btn.pack(side=tk.LEFT, padx=2)
        tiktok_btn = tk.Button(btn_frame, text="📱", bg='#888888', fg='white', font=('Arial', 10, 'bold'), relief=tk.FLAT, width=3, state=tk.DISABLED)
        tiktok_btn.pack(side=tk.LEFT, padx=2)
        preview_frame = tk.Frame(card, bg='#404040', height=60)
        preview_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        preview_frame.pack_propagate(False)
        tk.Label(preview_frame, text="🎬 Video-Preview", bg='#404040', fg='#888888', font=('Arial', 10)).pack(expand=True)
    
    def download_single(self, index):
        segment = self.segments[index]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4")],
            initialfile=f"{segment['name']}.mp4"
        )
        if save_path:
            try:
                import shutil
                shutil.copy2(segment['path'], save_path)
                messagebox.showinfo("Erfolgreich", f"Segment wurde gespeichert: {save_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def download_selected(self):
        selected_indices = [i for i, var in enumerate(self.selected_segments) if var.get()]
        if not selected_indices:
            messagebox.showwarning("Warnung", "Bitte wähle mindestens ein Segment aus!")
            return
        folder = filedialog.askdirectory(title="Ordner für Download auswählen")
        if folder:
            try:
                for i in selected_indices:
                    segment = self.segments[i]
                    dest_path = os.path.join(folder, f"{segment['name']}.mp4")
                    import shutil
                    shutil.copy2(segment['path'], dest_path)
                messagebox.showinfo("Erfolgreich", f"{len(selected_indices)} Segmente wurden heruntergeladen!")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Download: {str(e)}")
    
    def download_all(self):
        if not self.segments:
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile="video_segments.zip"
        )
        if save_path:
            try:
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for segment in self.segments:
                        zipf.write(segment['path'], f"{segment['name']}.mp4")
                messagebox.showinfo("Erfolgreich", f"Alle Segmente wurden als ZIP gespeichert: {save_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Erstellen der ZIP: {str(e)}")

def main():
    root = tk.Tk()
    app = VideoClipperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
