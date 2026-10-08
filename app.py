import sqlite3
import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

# Configuration & Database Setup
DATABASE = "lostfound_auth.db"
IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        # Users registry table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            contact TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        # Items reporting table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            color TEXT,
            location TEXT NOT NULL,
            date_reported TEXT NOT NULL,
            description TEXT,
            contact TEXT,
            image_path TEXT,
            status TEXT DEFAULT 'Active',
            reported_by TEXT,
            created_at TEXT NOT NULL
        )
        """)
        self.conn.commit()

    # User Management functions
    def add_user(self, username, password, contact):
        try:
            self.conn.execute("""
            INSERT INTO users (username, password, contact, created_at)
            VALUES (?, ?, ?, ?)
            """, (username, password, contact, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        return self.conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    # Lost/Found Item functions
    def add_item(self, item_type, item_name, category, color, location, date_reported, description, contact, image_path, reported_by):
        self.conn.execute("""
        INSERT INTO items (item_type, item_name, category, color, location, date_reported, description, contact, image_path, status, reported_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_type, item_name, category, color, location, date_reported, description, contact, image_path, "Active", reported_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.conn.commit()

    def get_all_items(self):
        return self.conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()

    def search_items(self, keyword="", item_type="All", status="All"):
        query = "SELECT * FROM items WHERE 1=1"
        params = []
        if keyword:
            query += " AND (item_name LIKE ? OR category LIKE ? OR color LIKE ? OR location LIKE ? OR description LIKE ?)"
            keyword = f"%{keyword}%"
            params.extend([keyword, keyword, keyword, keyword, keyword])
        if item_type != "All":
            query += " AND item_type = ?"
            params.append(item_type)
        if status != "All":
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY id DESC"
        return self.conn.execute(query, params).fetchall()

    def get_item(self, item_id):
        return self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    def update_status(self, item_id, status):
        self.conn.execute("UPDATE items SET status = ? WHERE id = ?", (status, item_id))
        self.conn.commit()

    def delete_item(self, item_id):
        item = self.get_item(item_id)
        if item and item["image_path"] and os.path.exists(item["image_path"]):
            try:
                os.remove(item["image_path"])
            except:
                pass
        self.conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.conn.commit()

    def statistics(self):
        total = self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        lost = self.conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Lost'").fetchone()[0]
        found = self.conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Found'").fetchone()[0]
        resolved = self.conn.execute("SELECT COUNT(*) FROM items WHERE status='Resolved'").fetchone()[0]
        return total, lost, found, resolved

db = Database()

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")  

class LostFoundApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Lost & Found System")
        self.geometry("1100x750")
        self.minsize(950, 650)
        
        self.current_user = None
        self.lost_image_path = None
        self.found_image_path = None

        # Container Frame for handling full page transitions
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Show Auth Screen first
        self.show_auth_screen()

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- Authentication Screen ---
    def show_auth_screen(self):
        self.clear_container()
        
        auth_frame = ctk.CTkFrame(self.main_container, width=400, height=500)
        auth_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        title = ctk.CTkLabel(auth_frame, text="🔎 Smart Lost & Found", font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(pady=(30, 25))
        
        tab_view = ctk.CTkTabview(auth_frame, width=340, height=360)
        tab_view.pack(padx=20, pady=(0, 20))
        
        login_tab = tab_view.add("Sign In")
        register_tab = tab_view.add("Create Account")
        
        # --- Login UI Components ---
        ctk.CTkLabel(login_tab, text="Username").pack(anchor="w", padx=10, pady=(15, 2))
        login_user = ctk.CTkEntry(login_tab, width=280, placeholder_text="Enter User ID")
        login_user.pack(padx=10, pady=2)
        
        ctk.CTkLabel(login_tab, text="Password").pack(anchor="w", padx=10, pady=(10, 2))
        login_pass = ctk.CTkEntry(login_tab, width=280, show="*", placeholder_text="Enter Password")
        login_pass.pack(padx=10, pady=2)
        
        def handle_login():
            user = login_user.get().strip()
            password = login_pass.get().strip()
            if not user or not password:
                messagebox.showerror("Error", "Please fill in all details.")
                return
            
            user_record = db.get_user(user)
            if user_record and user_record["password"] == password:
                self.current_user = user
                self.show_home_page()
            else:
                messagebox.showerror("Error", "Invalid User ID or Password.")

        login_btn = ctk.CTkButton(login_tab, text="Login", command=handle_login, width=280, fg_color="#1f538d")
        login_btn.pack(padx=10, pady=30)
        
        # --- Registration UI Components ---
        ctk.CTkLabel(register_tab, text="Choose User ID *").pack(anchor="w", padx=10, pady=(10, 2))
        reg_user = ctk.CTkEntry(register_tab, width=280)
        reg_user.pack(padx=10, pady=2)
        
        ctk.CTkLabel(register_tab, text="Choose Password *").pack(anchor="w", padx=10, pady=(5, 2))
        reg_pass = ctk.CTkEntry(register_tab, width=280, show="*")
        reg_pass.pack(padx=10, pady=2)
        
        ctk.CTkLabel(register_tab, text="Contact Info (Email/Phone) *").pack(anchor="w", padx=10, pady=(5, 2))
        reg_contact = ctk.CTkEntry(register_tab, width=280, placeholder_text="e.g. +91 9876543210")
        reg_contact.pack(padx=10, pady=2)
        
        def handle_register():
            user = reg_user.get().strip()
            password = reg_pass.get().strip()
            contact = reg_contact.get().strip()
            
            if not user or not password or not contact:
                messagebox.showerror("Error", "All registration parameters are mandatory.")
                return
            
            if db.add_user(user, password, contact):
                messagebox.showinfo("Success", "Account created successfully! Please Sign In.")
                tab_view.set("Sign In")
                login_user.insert(0, user)
            else:
                messagebox.showerror("Error", "User ID already exists. Choose a unique one.")

        reg_btn = ctk.CTkButton(register_tab, text="Register Account", command=handle_register, width=280, fg_color="#22c55e", hover_color="#16a34a")
        reg_btn.pack(padx=10, pady=25)

    # --- Home Menu Page (Clean Navigation Dashboard Only) ---
    def show_home_page(self):
        self.clear_container()

        # Upper Profile Greeting Bar
        top_bar = ctk.CTkFrame(self.main_container, height=60, fg_color="transparent")
        top_bar.pack(fill="x", padx=30, pady=(20, 0))
        
        user_lbl = ctk.CTkLabel(top_bar, text=f"👤 Active Profile: {self.current_user}", font=ctk.CTkFont(size=14, weight="bold"))
        user_lbl.pack(side="left", pady=10)
        
        def logout():
            self.current_user = None
            self.show_auth_screen()
            
        logout_btn = ctk.CTkButton(top_bar, text="Logout", width=80, fg_color="#ef4444", hover_color="#dc2626", command=logout)
        logout_btn.pack(side="right", pady=10)

        # Header Presentation Title
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(pady=(10, 30))
        
        title_lbl = ctk.CTkLabel(header_frame, text="🔎 Smart Lost & Found System", font=ctk.CTkFont(size=26, weight="bold"))
        title_lbl.pack()
        subtitle_lbl = ctk.CTkLabel(header_frame, text="College Lost & Found Management Hub", font=ctk.CTkFont(size=14, slant="italic"))
        subtitle_lbl.pack(pady=5)

        # Core Navigation Routing Grid Layout Frame
        grid_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=60, pady=10)
        
        grid_frame.columnconfigure((0, 1), weight=1, uniform="equal")
        grid_frame.rowconfigure((0, 1, 2), weight=1, uniform="equal")

        # Visual Structural Routing Cards Setup
        self.create_nav_button(grid_frame, 0, 0, "🏠 Operational Dashboard", "#3b82f6", "#2563eb", lambda: self.show_page_frame("Dashboard"))
        self.create_nav_button(grid_frame, 0, 1, "🔴 Report Lost Item", "#ef4444", "#dc2626", lambda: self.show_page_frame("Report Lost"))
        self.create_nav_button(grid_frame, 1, 0, "🟢 Report Found Item", "#22c55e", "#16a34a", lambda: self.show_page_frame("Report Found"))
        self.create_nav_button(grid_frame, 1, 1, "🔎 Deep Search Records", "#4b5563", "#374151", lambda: self.show_page_frame("Search"))
        self.create_nav_button(grid_frame, 2, 0, "📋 All Database Entries", "#6b21a8", "#581c87", lambda: self.show_page_frame("All Reports"))
        self.create_nav_button(grid_frame, 2, 1, "⚙️ Administrative Actions", "#d97706", "#b45309", lambda: self.show_page_frame("Manage"))

    def create_nav_button(self, master, row, col, text, color, hover, command):
        btn = ctk.CTkButton(master, text=text, font=ctk.CTkFont(size=16, weight="bold"), fg_color=color, hover_color=hover, command=command)
        btn.grid(row=row, column=col, padx=25, pady=20, sticky="nsew")

    # --- Framework Route Controller for Inner Modules ---
    def show_page_frame(self, target_page):
        self.clear_container()

        # Re-attach Top Control Context Layer (Back Button & Profile View)
        nav_header = ctk.CTkFrame(self.main_container, height=50)
        nav_header.pack(fill="x", padx=20, pady=10)
        
        back_btn = ctk.CTkButton(nav_header, text="⬅️ Main Hub", width=100, command=self.show_home_page)
        back_btn.pack(side="left", padx=10, pady=10)
        
        ctx_title = ctk.CTkLabel(nav_header, text=f"Workspace » {target_page}", font=ctk.CTkFont(size=15, weight="bold"))
        ctx_title.pack(side="left", padx=20)
        
        user_lbl = ctk.CTkLabel(nav_header, text=f"User ID: {self.current_user}", font=ctk.CTkFont(size=13))
        user_lbl.pack(side="right", padx=15)

        # Dynamic Module Execution Routing
        work_area = ctk.CTkFrame(self.main_container)
        work_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if target_page == "Dashboard":
            self.render_dashboard(work_area)
        elif target_page == "Report Lost":
            self.render_report_form(work_area, "Lost")
        elif target_page == "Report Found":
            self.render_report_form(work_area, "Found")
        elif target_page == "Search":
            self.render_search(work_area)
        elif target_page == "All Reports":
            self.render_all_reports(work_area)
        elif target_page == "Manage":
            self.render_manage(work_area)

    # --- Workspace Render Engines ---
    def render_dashboard(self, master):
        self.stat_title = ctk.CTkLabel(master, text="Real-Time Analytics Dashboard", font=ctk.CTkFont(size=18, weight="bold"))
        self.stat_title.pack(pady=15)

        cards_container = ctk.CTkFrame(master, fg_color="transparent")
        cards_container.pack(pady=10, padx=20, fill="x")
        cards_container.columnconfigure((0, 1, 2, 3), weight=1, uniform="equal")

        self.card_total = self.create_stat_card(cards_container, 0, "📦 Total Reports", "0", "#3b82f6")
        self.card_lost = self.create_stat_card(cards_container, 1, "🔴 Lost Items", "0", "#ef4444")
        self.card_found = self.create_stat_card(cards_container, 2, "🟢 Found Items", "0", "#22c55e")
        self.card_resolved = self.create_stat_card(cards_container, 3, "✅ Resolved Cases", "0", "#a855f7")

        instr_frame = ctk.CTkFrame(master)
        instr_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        instr_text = "💡 Operational Roadmap Guide:\n\n"                      "• Track system metrics and items using real-time database records.\n"                      "• Active profiles can seamlessly view global system logs or manage custom updates.\n"                      "• Check specific data matching parameters directly from the Core Deep Search pane."
        
        self.instr_label = ctk.CTkLabel(instr_frame, text=instr_text, justify="left", font=ctk.CTkFont(size=13))
        self.instr_label.pack(pady=20, padx=20, anchor="w")

        refresh_dash_btn = ctk.CTkButton(master, text="🔄 Refresh Statistics", command=self.update_dashboard_stats)
        refresh_dash_btn.pack(pady=15)
        self.update_dashboard_stats()

    def create_stat_card(self, master, col, label, value, border_color):
        card = ctk.CTkFrame(master, border_width=2, border_color=border_color)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
        lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(pady=(12, 4))
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"))
        val_lbl.pack(pady=(0, 12))
        return val_lbl

    def update_dashboard_stats(self):
        total, lost, found, resolved = db.statistics()
        self.card_total.configure(text=str(total))
        self.card_lost.configure(text=str(lost))
        self.card_found.configure(text=str(found))
        self.card_resolved.configure(text=str(resolved))

    def render_report_form(self, master, item_type):
        container = ctk.CTkScrollableFrame(master)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(container, text=f"Registry Entry Matrix - {item_type} Item", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(container, text="Item Name *").grid(row=1, column=0, padx=15, pady=5, sticky="w")
        name_entry = ctk.CTkEntry(container, width=320, placeholder_text="e.g. Casio Calculator")
        name_entry.grid(row=1, column=1, padx=15, pady=5, sticky="w")

        categories = ["Electronics", "Documents", "Wallet", "Bag", "Clothing", "Keys", "Books", "Accessories", "Other"]
        ctk.CTkLabel(container, text="Category *").grid(row=2, column=0, padx=15, pady=5, sticky="w")
        cat_dropdown = ctk.CTkOptionMenu(container, values=categories, width=320)
        cat_dropdown.grid(row=2, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(container, text="Color").grid(row=3, column=0, padx=15, pady=5, sticky="w")
        color_entry = ctk.CTkEntry(container, width=320)
        color_entry.grid(row=3, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(container, text=f"Location Where {item_type} *").grid(row=4, column=0, padx=15, pady=5, sticky="w")
        loc_entry = ctk.CTkEntry(container, width=320)
        loc_entry.grid(row=4, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(container, text="Date").grid(row=5, column=0, padx=15, pady=5, sticky="w")
        date_entry = ctk.CTkEntry(container, width=320)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=5, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(container, text="Detailed Description").grid(row=6, column=0, padx=15, pady=5, sticky="nw")
        desc_textbox = ctk.CTkTextbox(container, width=320, height=80)
        desc_textbox.grid(row=6, column=1, padx=15, pady=5, sticky="w")

        # Automatically populating logged in user contact as alternative default
        user_info = db.get_user(self.current_user)
        user_contact = user_info["contact"] if user_info else ""

        ctk.CTkLabel(container, text="Contact Info").grid(row=7, column=0, padx=15, pady=5, sticky="w")
        contact_entry = ctk.CTkEntry(container, width=320)
        contact_entry.insert(0, user_contact)
        contact_entry.grid(row=7, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(container, text="Item Image").grid(row=8, column=0, padx=15, pady=5, sticky="w")
        img_lbl = ctk.CTkLabel(container, text="No image selected", text_color="gray")
        
        def file_picker():
            path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
            if path:
                img_lbl.configure(text=os.path.basename(path), text_color="green")
                if item_type == "Lost":
                    self.lost_image_path = path
                else:
                    self.found_image_path = path

        img_btn = ctk.CTkButton(container, text="📁 Browse...", width=120, fg_color="#4b5563", hover_color="#374151", command=file_picker)
        img_btn.grid(row=8, column=1, padx=15, pady=5, sticky="w")
        img_lbl.grid(row=8, column=1, padx=(145, 15), pady=5, sticky="w")

        def submit_report():
            name = name_entry.get().strip()
            category = cat_dropdown.get()
            color = color_entry.get().strip()
            location = loc_entry.get().strip()
            date = date_entry.get().strip()
            description = desc_textbox.get("1.0", "end-1c").strip()
            contact = contact_entry.get().strip()
            uploaded_img = self.lost_image_path if item_type == "Lost" else self.found_image_path

            if not name or not category or not location:
                messagebox.showerror("Validation Error", "Item Name, Category and Location fields are strict prerequisites.")
                return

            image_dest = None
            if uploaded_img and os.path.exists(uploaded_img):
                ext = os.path.splitext(uploaded_img)[1]
                filename = datetime.now().strftime("%Y%m%d%H%M%S%f") + ext
                image_dest = os.path.join(IMAGE_FOLDER, filename)
                try:
                    shutil.copy(uploaded_img, image_dest)
                except Exception:
                    image_dest = None

            db.add_item(item_type, name, category, color, location, date or datetime.now().strftime("%Y-%m-%d"), description, contact, image_dest, self.current_user)
            messagebox.showinfo("Success", f"Report entry for '{name}' successfully submitted!")
            
            # Reset form properties
            name_entry.delete(0, "end")
            color_entry.delete(0, "end")
            loc_entry.delete(0, "end")
            desc_textbox.delete("1.0", "end")
            img_lbl.configure(text="No image selected", text_color="gray")
            if item_type == "Lost":
                self.lost_image_path = None
            else:
                self.found_image_path = None

        btn_color = "#ef4444" if item_type == "Lost" else "#22c55e"
        btn_hover = "#dc2626" if item_type == "Lost" else "#16a34a"
        submit_btn = ctk.CTkButton(container, text=f"Submit {item_type} Report", fg_color=btn_color, hover_color=btn_hover, command=submit_report, width=320)
        submit_btn.grid(row=9, column=0, columnspan=2, pady=25)

    def render_search(self, master):
        top_frame = ctk.CTkFrame(master)
        top_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(top_frame, text="Keyword").grid(row=0, column=0, padx=10, pady=2, sticky="w")
        kw_entry = ctk.CTkEntry(top_frame, placeholder_text="Enter keyword...", width=220)
        kw_entry.grid(row=1, column=0, padx=10, pady=5)

        ctk.CTkLabel(top_frame, text="Type").grid(row=0, column=1, padx=10, pady=2, sticky="w")
        type_drop = ctk.CTkOptionMenu(top_frame, values=["All", "Lost", "Found"], width=130)
        type_drop.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(top_frame, text="Status").grid(row=0, column=2, padx=10, pady=2, sticky="w")
        status_drop = ctk.CTkOptionMenu(top_frame, values=["All", "Active", "Resolved"], width=130)
        status_drop.grid(row=1, column=2, padx=10, pady=5)

        table_frame = ctk.CTkFrame(master)
        table_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        search_tree = self.create_data_tree(table_frame)

        def perform_search():
            for row in search_tree.get_children():
                search_tree.delete(row)
            items = db.search_items(kw_entry.get().strip(), type_drop.get(), status_drop.get())
            for item in items:
                search_tree.insert("", "end", values=(item["id"], item["item_type"], item["item_name"], item["category"], item["color"], item["location"], item["date_reported"], item["status"]))

        search_btn = ctk.CTkButton(top_frame, text="🔎 Search", command=perform_search, width=130)
        search_btn.grid(row=1, column=3, padx=15, pady=5)
        perform_search()

    def render_all_reports(self, master):
        container = ctk.CTkFrame(master)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        self.all_tree = self.create_data_tree(container)

        def reload_records():
            for row in self.all_tree.get_children():
                self.all_tree.delete(row)
            for item in db.get_all_items():
                self.all_tree.insert("", "end", values=(item["id"], item["item_type"], item["item_name"], item["category"], item["color"], item["location"], item["date_reported"], item["status"]))

        refresh_btn = ctk.CTkButton(container, text="🔄 Reload Records Table", command=reload_records)
        refresh_btn.pack(pady=10)
        reload_records()

    def create_data_tree(self, master):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background="#3a3a3a", foreground="white", borderwidth=1)
        style.map("Treeview", background=[("selected", "#1f538d")])

        cols = ("ID", "Type", "Item", "Category", "Color", "Location", "Date", "Status")
        tree = ttk.Treeview(master, columns=cols, show="headings")
        
        widths = {"ID": 50, "Type": 80, "Item": 180, "Category": 110, "Color": 90, "Location": 140, "Date": 110, "Status": 90}
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 100), anchor="center")

        scrollbar = ttk.Scrollbar(master, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill="both", expand=True, side="left", padx=(10, 0), pady=10)
        scrollbar.pack(fill="y", side="right", padx=(0, 10), pady=10)
        return tree

    def render_manage(self, master):
        main_container = ctk.CTkFrame(master)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        ctrl_frame = ctk.CTkFrame(main_container)
        ctrl_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(ctrl_frame, text="Enter Item ID:").pack(side="left", padx=10, pady=10)
        id_entry = ctk.CTkEntry(ctrl_frame, width=120)
        id_entry.pack(side="left", padx=5, pady=10)

        output_box = ctk.CTkTextbox(main_container, wrap="word", font=ctk.CTkFont(family="Courier", size=13))
        output_box.pack(fill="both", expand=True, padx=15, pady=10)

        def fetch_target_id():
            raw_id = id_entry.get().strip()
            if not raw_id or not raw_id.isdigit():
                return None
            return int(raw_id)

        def display_details():
            output_box.delete("1.0", "end")
            target = fetch_target_id()
            if not target:
                output_box.insert("end", "❌ Invalid input. Please supply a valid item ID.")
                return
            item = db.get_item(target)
            if not item:
                output_box.insert("end", f"❌ Record #{target} could not be located.")
                return
            
            details = f"📋 ITEM LOG DOSSIER #{item['id']}\n"                       f"-----------------------------------------\n"                       f"Type          : {item['item_type']}\n"                       f"Name          : {item['item_name']}\n"                       f"Category      : {item['category']}\n"                       f"Color         : {item['color'] or 'N/A'}\n"                       f"Location      : {item['location']}\n"                       f"Report Date   : {item['date_reported']}\n"                       f"Status        : {item['status']}\n"                       f"Reported By   : {item['reported_by'] or 'Legacy User'}\n"                       f"Contact Point : {item['contact'] or 'Not provided'}\n"                       f"Stored Image  : {item['image_path'] or 'No image file mapped.'}\n\n"                       f"📝 Description:\n"                       f"{item['description'] or 'No supplemental description provided.'}"
            output_box.insert("end", details)

        def change_status(new_status):
            target = fetch_target_id()
            if not target or not db.get_item(target):
                messagebox.showerror("Error", "Target operational Item ID does not exist.")
                return
            db.update_status(target, new_status)
            messagebox.showinfo("Success", f"Item #{target} marked as {new_status}.")
            display_details()

        def drop_report():
            target = fetch_target_id()
            if not target or not db.get_item(target):
                messagebox.showerror("Error", "Target operational Item ID does not exist.")
                return
            if messagebox.askyesno("Confirm Delete", f"Permanently drop Report entry #{target}?"):
                db.delete_item(target)
                output_box.delete("1.0", "end")
                output_box.insert("end", f"🗑️ Report entry #{target} has been purged from the system.")
                id_entry.delete(0, "end")

        ctk.CTkButton(ctrl_frame, text="📋 Inspect Details", command=display_details, fg_color="#4b5563").pack(side="left", padx=10)
        ctk.CTkButton(ctrl_frame, text="✅ Resolve Case", command=lambda: change_status("Resolved"), fg_color="#a855f7").pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="🔄 Reset Active", command=lambda: change_status("Active"), fg_color="#3b82f6").pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="🗑️ Delete Entry", command=drop_report, fg_color="#ef4444").pack(side="left", padx=5)

if __name__ == "__main__":
    app = LostFoundApp()
    app.mainloop()

