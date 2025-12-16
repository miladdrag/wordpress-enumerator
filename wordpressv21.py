import threading
import time
import re
import csv
from urllib.parse import urlparse
import requests
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# تنظیمات
TIMEOUT = 8
USER_AGENT = "WP-Enum/1.0"
KEYWORDS = ["yoast", "jetpack", "woocommerce", "elementor", "contact-form-7"]

class WordPressEnumerator:
    def __init__(self, root):
        self.root = root
        root.title("WordPress User Enumerator")
        root.geometry("1180x820")

        # Session و State
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.stop_flag = threading.Event()
        self.results = []
        self.start_time = None

        # رنگ‌های تم تیره
        self.colors = {
            "bg": "#000000",
            "panel": "#0a0a0a",
            "text": "#ffffff",
            "muted": "#121212",
            "accept": "#16f085",
            "error": "#ff6b6b"
        }

        # UI variables
        self.filter_var = tk.StringVar()
        self.status_var = tk.StringVar(value="آماده")

        self._build_ui()
        self._apply_theme()

        # کلیدهای میانبر
        root.bind_all("<Control-s>", lambda e: self.export_csv())
        root.bind_all("<Control-l>", lambda e: self.export_log())
        root.bind_all("<Control-r>", lambda e: self.reset())
        root.bind_all("<Control-e>" , lambda e: self.start_scan())

    def _build_ui(self):
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # هدر
        header = tk.Frame(container, pady=8)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12)
        tk.Label(header, text="WordPress Enumerator", font=("Arial", 14, "bold")).pack(anchor="w")

        # نوار ابزار
        toolbar = tk.Frame(container, pady=6)
        toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12)

        self.btn_start = tk.Button(toolbar, text="▶ شروع", command=self.start_scan, relief="flat", padx=10, pady=6)
        self.btn_start.pack(side="left", padx=4)
        
        self.btn_stop = tk.Button(toolbar, text="⏹ توقف", command=self.stop_scan, relief="flat", padx=10, pady=6, state="disabled")
        self.btn_stop.pack(side="left", padx=4)
        
        tk.Button(toolbar, text="↺ ریست", command=self.reset, relief="flat", padx=10, pady=6).pack(side="left", padx=4)
        tk.Button(toolbar, text="⇩ CSV", command=self.export_csv, relief="flat", padx=10, pady=6).pack(side="left", padx=4)
        tk.Button(toolbar, text="⇩ Log", command=self.export_log, relief="flat", padx=10, pady=6).pack(side="left", padx=4)

        # ستون چپ: تنظیمات و لاگ
        left_panel = tk.Frame(container)
        left_panel.grid(row=2, column=0, sticky="ns", padx=(12, 6))

        settings = tk.Frame(left_panel, padx=8, pady=8)
        settings.pack(fill="x")
        
        tk.Label(settings, text="URL هدف:").grid(row=0, column=0, sticky="w", pady=4)
        self.url_entry = tk.Entry(settings, width=36)
        self.url_entry.grid(row=0, column=1, pady=4)
        self.url_entry.insert(0, "https://example.com")

        tk.Label(settings, text="حداکثر ID:").grid(row=1, column=0, sticky="w", pady=4)
        self.max_id_entry = tk.Entry(settings, width=12)
        self.max_id_entry.grid(row=1, column=1, pady=4, sticky="w")
        self.max_id_entry.insert(0, "20")

        tk.Label(settings, text="تاخیر (ثانیه):").grid(row=2, column=0, sticky="w", pady=4)
        self.delay_entry = tk.Entry(settings, width=12)
        self.delay_entry.grid(row=2, column=1, pady=4, sticky="w")
        self.delay_entry.insert(0, "1.0")

        # لاگ
        log_frame = tk.Frame(left_panel, padx=6, pady=6)
        log_frame.pack(fill="both", expand=True, pady=(12, 0))
        tk.Label(log_frame, text="لاگ").pack(anchor="w")
        
        self.log_text = tk.Text(log_frame, height=16, wrap="none", padx=6, pady=6)
        self.log_text.pack(fill="both", expand=True, side="left")
        
        log_scroll = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.tag_config("INFO", foreground=self.colors["text"])
        self.log_text.tag_config("FOUND", foreground=self.colors["accept"])
        self.log_text.tag_config("ERROR", foreground=self.colors["error"])

        # ستون راست: نتایج
        right_panel = tk.Frame(container)
        right_panel.grid(row=2, column=1, sticky="nsew", padx=(6, 12))
        
        top_bar = tk.Frame(right_panel)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="نتایج", font=("Arial", 11, "bold")).pack(side="left")
        tk.Label(top_bar, text="فیلتر:").pack(side="left", padx=(12, 4))
        tk.Entry(top_bar, textvariable=self.filter_var).pack(side="left", padx=(0, 8))
        self.filter_var.trace("w", lambda *args: self.apply_filter())

        # جدول نتایج
        columns = ("id", "username", "name", "link", "source")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", selectmode="browse")
        
        for col, title in zip(columns, ("ID", "نام کاربری", "نام نمایشی", "لینک", "منبع")):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=140 if col != "id" else 60)

        self.tree.pack(fill="both", expand=True)
        tree_scroll = tk.Scrollbar(right_panel, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.bind("<Double-1>", lambda e: self.open_link())
        self.tree.bind("<Button-3>", self.show_context_menu)

        # نوار وضعیت
        status_bar = tk.Frame(self.root)
        status_bar.pack(fill="x", padx=12, pady=(6, 10))
        
        tk.Label(status_bar, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(status_bar, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=8)
        
        self.percent_label = tk.Label(status_bar, text="", width=6)
        self.percent_label.grid(row=0, column=2)
        
        self.elapsed_label = tk.Label(status_bar, text="زمان: 0s", width=14)
        self.elapsed_label.grid(row=0, column=3)
        
        self.count_label = tk.Label(status_bar, text="کاربران: 0", width=12)
        self.count_label.grid(row=0, column=4)

    def _apply_theme(self):
        c = self.colors
        style = ttk.Style(self.root)
        
        try:
            style.theme_use("clam")
        except:
            pass

        style.configure("Treeview", background=c["panel"], fieldbackground=c["panel"], 
                       foreground=c["text"], rowheight=24)
        style.configure("Treeview.Heading", background=c["panel"], foreground=c["text"])
        style.configure("Horizontal.TProgressbar", troughcolor=c["muted"], background=c["accept"])

        try:
            style.map("Treeview", background=[("selected", c["muted"])], 
                     foreground=[("selected", c["text"])])
        except:
            pass

        for widget in (self.url_entry, self.max_id_entry, self.delay_entry, self.log_text):
            try:
                widget.configure(bg=c["panel"], fg=c["text"], insertbackground=c["accept"], relief="flat")
            except:
                pass

    def log(self, message, tag="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        try:
            self.root.after(0, lambda: self.log_text.insert("end", line, tag))
            self.root.after(0, lambda: self.log_text.see("end"))
        except:
            pass
        print(line.strip())

    def normalize_url(self, url):
        url = url.strip()
        if not url:
            return None
        
        if not re.match(r"^https?://", url, re.I):
            url = "https://" + url
        
        try:
            parsed = urlparse(url)
        except:
            return None
        
        if not parsed.netloc:
            return None
        
        path = parsed.path or ""
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""
        
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]
        
        return f"{parsed.scheme}://{parsed.netloc}{path}{query}{fragment}"

    def apply_filter(self):
        query = self.filter_var.get().lower().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for result in self.results:
            if not query or any(query in str(result.get(k, "")).lower() 
                              for k in ("username", "name", "link", "id")):
                self.tree.insert("", "end", values=(
                    result.get("id"), result.get("username"), 
                    result.get("name"), result.get("link"), result.get("source")
                ))

    def reset(self):
        self.log_text.delete("1.0", "end")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results.clear()
        self.progress_bar["value"] = 0
        self.percent_label.config(text="")
        self.status_var.set("آماده")
        self.elapsed_label.config(text="زمان: 0s")
        self.count_label.config(text="کاربران: 0")
        self.log("ریست انجام شد")

    def export_csv(self):
        if not self.results:
            messagebox.showinfo("داده ای وجود ندارد", "نتیجه ای برای ذخیره وجود ندارد")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "username", "name", "link", "source"])
                writer.writeheader()
                writer.writerows(self.results)
            self.log(f"CSV ذخیره شد: {path}")
        except Exception as e:
            self.log(f"خطا در ذخیره CSV: {e}", "ERROR")

    def export_log(self):
        content = self.log_text.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("لاگ خالی", "لاگی برای ذخیره وجود ندارد")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"لاگ ذخیره شد: {path}")
        except Exception as e:
            self.log(f"خطا در ذخیره لاگ: {e}", "ERROR")

    def start_scan(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("ورودی نامعتبر", "لطفا URL هدف را وارد کنید")
            return
        
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.stop_flag.clear()
        self.results.clear()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        threading.Thread(target=self.scan_worker, args=(url,), daemon=True).start()

    def stop_scan(self):
        self.stop_flag.set()
        self.status_var.set("در حال توقف...")
        self.log("درخواست توقف ارسال شد")

    def scan_worker(self, raw_url):
        self.start_time = time.time()
        self.update_timer()
        
        base_url = self.normalize_url(raw_url)
        if not base_url:
            self.log("URL نامعتبر است", "ERROR")
            self.finish_scan()
            return
        
        try:
            max_id = int(self.max_id_entry.get())
            delay = float(self.delay_entry.get())
            if max_id < 1 or delay < 0:
                raise ValueError
        except:
            messagebox.showwarning("ورودی نامعتبر", "مقادیر معتبر وارد کنید")
            self.finish_scan()
            return

        # استخراج path برای ترکیب صحیح URLها
        parsed_base = urlparse(base_url)
        base_path = parsed_base.path.rstrip('/') if parsed_base.path else ''

        def build_url(endpoint):
            if endpoint.startswith('?'):
                return base_url + endpoint
            return f"{parsed_base.scheme}://{parsed_base.netloc}{base_path}{endpoint}"

        self.log(f"شروع اسکن: {base_url}")
        
        try:
            response = self.session.get(base_url, timeout=TIMEOUT)
            page_content = response.text
            self.log(f"HTTP {response.status_code}")
        except Exception as e:
            self.log(f"خطا در دریافت صفحه: {e}", "ERROR")
            self.finish_scan()
            return

        # تحلیل HTML
        version_match = re.search(r'<meta[^>]*name=[\'"]generator[\'"][^>]*content=[\'"]WordPress\s*([\d\.]+)[\'"]', 
                                  page_content, re.I)
        if version_match:
            self.log(f"نسخه WordPress: {version_match.group(1)}")
        
        plugins = sorted(set(re.findall(r'/wp-content/plugins/([\w\-]+)/', page_content)))
        if plugins:
            self.log(f"افزونه‌ها: {', '.join(plugins[:10])}")
        
        themes = sorted(set(re.findall(r'/wp-content/themes/([\w\-]+)/', page_content)))
        if themes:
            self.log(f"قالب‌ها: {', '.join(themes)}")

        for keyword in KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', page_content, re.I):
                self.log(f"[کلیدواژه] {keyword}")

        # تست REST API
        endpoints = ['/wp-json/wp/v2/users', '?rest_route=/wp/v2/users']
        for endpoint in endpoints:
            if self.stop_flag.is_set():
                break
            
            url = build_url(endpoint)
            self.log(f"تست {url}")
            
            try:
                resp = self.session.get(url, timeout=TIMEOUT)
                self.log(f"→ {resp.status_code}")
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, list) and data:
                            for user in data:
                                self.add_result(user, endpoint)
                            self.log("کاربران از REST یافت شدند", "FOUND")
                            break
                    except:
                        pass
            except Exception as e:
                self.log(f"خطا: {e}", "ERROR")

        # شمارش IDها
        self.log(f"شمارش IDها از 1 تا {max_id}")
        self.progress_bar["maximum"] = max_id
        
        times = []
        for user_id in range(1, max_id + 1):
            if self.stop_flag.is_set():
                break
            
            start = time.time()
            self.status_var.set(f"در حال اسکن {user_id}/{max_id}")
            
            for endpoint in (f"/wp-json/wp/v2/users/{user_id}", f"/?rest_route=/wp/v2/users/{user_id}"):
                if self.stop_flag.is_set():
                    break
                
                try:
                    url = build_url(endpoint)
                    self.log(f"تست {url}")
                    
                    resp = self.session.get(url, timeout=TIMEOUT)
                    self.log(f"→ {resp.status_code}")
                    
                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                            if isinstance(data, dict) and data.get("id"):
                                self.add_result(data, endpoint)
                                self.log(f"ID {user_id} یافت شد", "FOUND")
                                break
                        except:
                            pass
                except Exception as e:
                    self.log(f"خطا در ID {user_id}: {e}", "ERROR")
            
            elapsed = time.time() - start
            times.append(elapsed)
            
            self.progress_bar["value"] = user_id
            self.percent_label.config(text=f"{int((user_id / max_id) * 100)}%")
            self.count_label.config(text=f"کاربران: {len(self.results)}")
            
            if user_id != max_id and delay > 0:
                time.sleep(delay)

        self.log(f"پایان. {len(self.results)} کاربر یافت شد")
        self.finish_scan()

    def update_timer(self):
        if not self.start_time:
            return
        
        elapsed = int(time.time() - self.start_time)
        self.elapsed_label.config(text=f"زمان: {elapsed}s")
        
        if self.btn_stop["state"] == "normal":
            self.root.after(1000, self.update_timer)

    def finish_scan(self):
        def finish():
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.status_var.set("آماده")
            self.progress_bar["value"] = 0
            self.percent_label.config(text="")
        
        self.root.after(0, finish)
        self.start_time = None

    def add_result(self, user_data, source=""):
        try:
            user_id = user_data.get("id")
            username = user_data.get("slug") or user_data.get("username") or ""
            name = user_data.get("name") or ""
            link = user_data.get("link") or ""
        except:
            return
        
        result = {"id": user_id, "username": username, "name": name, "link": link, "source": source}
        
        if not any(r.get("id") == result["id"] for r in self.results):
            self.results.append(result)
            
            query = self.filter_var.get().lower().strip()
            if not query or any(query in str(result.get(k, "")).lower() 
                              for k in ("id", "username", "name", "link")):
                self.root.after(0, lambda: self.tree.insert("", "end", values=(
                    result["id"], result["username"], result["name"], result["link"], result["source"]
                )))
            
            self.root.after(0, lambda: self.count_label.config(text=f"کاربران: {len(self.results)}"))

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="کپی نام کاربری", command=lambda: self.copy_field("username"))
            menu.add_command(label="کپی لینک", command=lambda: self.copy_field("link"))
            menu.add_separator()
            menu.add_command(label="باز کردن لینک", command=self.open_link)
            menu.tk_popup(event.x_root, event.y_root)

    def copy_field(self, field):
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0], "values")
        field_map = {"id": 0, "username": 1, "name": 2, "link": 3, "source": 4}
        value = values[field_map[field]]
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(value))
            self.log(f"کپی شد: {value}")
        except:
            pass

    def open_link(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        link = self.tree.item(selection[0], "values")[3]
        if link:
            try:
                webbrowser.open(link)
                self.log(f"لینک باز شد: {link}")
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    WordPressEnumerator(root)
    root.mainloop()
