import sys
import csv
import os

# Python 2/3 compatibility
if sys.version_info[0] < 3:
    import Tkinter as tk
    from Tkinter import ttk
    from ScrolledText import ScrolledText
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    CSV_OPEN_KWARGS = {}
else:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
    CSV_OPEN_KWARGS = {"newline": "", "encoding": "utf-8-sig"}


class CSVToTXTConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV to TXT Converter")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)

        self.csv_file = ""
        self.txt_file = ""
        self.rows = []
        self.selected = set()
        self.existing_blocks = []
        self.preview_text = ""

        self.create_widgets()

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # File selection
        file_frame = ttk.LabelFrame(main, text="Files", padding=10)
        file_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        self.csv_entry = ttk.Entry(file_frame)
        self.csv_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_csv).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(file_frame, text="TXT File:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=5)
        self.txt_entry = ttk.Entry(file_frame)
        self.txt_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(file_frame, text="Open Existing...", command=self.browse_txt).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(file_frame, text="New TXT...", command=self.new_txt).grid(row=1, column=3, padx=5, pady=5)
        file_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(button_frame, text="Select All", command=self.select_all).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Select None", command=self.select_none).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Preview", command=self.preview).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save / Update TXT", command=self.save_txt).pack(side="right", padx=5)

        # Active rows (Treeview)
        rows_frame = ttk.LabelFrame(main, text="Active CSV Records", padding=5)
        rows_frame.pack(fill="both", expand=True)

        columns = ("selected", "region", "area", "freq", "sig", "sytem", "latlong")
        self.tree = ttk.Treeview(rows_frame, columns=columns, show="headings", selectmode="none")

        for col in columns:
            self.tree.heading(col, text=col.title())
        
        self.tree.column("selected", width=55, anchor="center")
        self.tree.column("region", width=130)
        self.tree.column("area", width=130)
        self.tree.column("freq", width=100)
        self.tree.column("sig", width=150)
        self.tree.column("sytem", width=150)
        self.tree.column("latlong", width=180)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(rows_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Button-1>", self.tree_click)
        self.tree.bind("<Double-1>", self.show_row_details)

        # Status
        self.status_var = tk.StringVar(value="Ready - load a CSV file.")
        status_frame = ttk.Frame(main)
        status_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")

    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filename:
            return

        self.csv_file = filename
        self.csv_entry.delete(0, tk.END)
        self.csv_entry.insert(0, filename)

        base = os.path.splitext(filename)[0]
        if not self.txt_file:
            self.txt_entry.delete(0, tk.END)
            self.txt_entry.insert(0, base + ".txt")

        self.load_csv()

    def load_csv(self):
        if not self.csv_file:
            return

        try:
            with open(self.csv_file, "r", **CSV_OPEN_KWARGS) as file:
                reader = csv.DictReader(file)

                if reader.fieldnames is None:
                    messagebox.showerror("CSV Error", "The CSV file does not contain headings.")
                    return

                headings = [h.strip().lower() if h else "" for h in reader.fieldnames]
                required = ["status", "region", "area", "freq", "sig", "sytem", "latlong"]
                missing = [h for h in required if h not in headings]

                if missing:
                    messagebox.showerror("CSV Error", "Missing required headings:\n\n" + "\n".join(missing))
                    return

                heading_map = {original: original.strip().lower() for original in reader.fieldnames if original}
                rows = []

                for line_number, raw_row in enumerate(reader, start=2):
                    row = {}
                    for original, value in raw_row.items():
                        if original is None:
                            continue
                        normalised = heading_map.get(original, original.strip().lower())
                        row[normalised] = value.strip() if value is not None else ""

                    if row.get("status", "").lower() != "active":
                        continue

                    clean_row = {
                        "status": row.get("status", ""),
                        "region": row.get("region", ""),
                        "area": row.get("area", ""),
                        "freq": row.get("freq", ""),
                        "sig": row.get("sig", ""),
                        "sytem": row.get("sytem", ""),
                        "latlong": row.get("latlong", ""),
                        "_line": line_number
                    }
                    rows.append(clean_row)

                self.rows = rows
                self.selected = set(range(len(rows)))
                self.populate_tree()
                self.check_duplicates()
                self.status_var.set(f"Loaded {len(rows)} active record(s). Inactive records were ignored.")

        except Exception as exc:
            messagebox.showerror("CSV Error", "Could not read the CSV file.\n\n" + str(exc))

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, row in enumerate(self.rows):
            checkbox = u"\u2611" if index in self.selected else u"\u2610"
            self.tree.insert("", "end", iid=str(index), values=(
                checkbox, row["region"], row["area"], row["freq"], row["sig"], row["sytem"], row["latlong"]
            ))

    def tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)

        if not item or column != "#1":
            return

        index = int(item)
        if index in self.selected:
            self.selected.remove(index)
        else:
            self.selected.add(index)

        self.update_checkbox(index)

    def update_checkbox(self, index):
        if not self.tree.exists(str(index)):
            return

        values = list(self.tree.item(str(index), "values"))
        values[0] = u"\u2611" if index in self.selected else u"\u2610"
        self.tree.item(str(index), values=values)

    def select_all(self):
        self.selected = set(range(len(self.rows)))
        self.populate_tree()
        self.status_var.set(f"All {len(self.rows)} active records selected.")

    def select_none(self):
        self.selected.clear()
        self.populate_tree()
        self.status_var.set("No records selected.")

    def show_row_details(self, event):
        item = self.tree.identify_row(event.y)
        if not item or int(item) >= len(self.rows):
            return

        row = self.rows[int(item)]
        details = (
            f"CSV line: {row['_line']}\n\n"
            f"Status:   {row['status']}\n"
            f"Region:   {row['region']}\n"
            f"Area:     {row['area']}\n"
            f"Freq:     {row['freq']}\n"
            f"Sig:      {row['sig']}\n"
            f"System:   {row['sytem']}\n"
            f"Lat/Long: {row['latlong']}"
        )
        messagebox.showinfo("Record Details", details)

    def make_key(self, row):
        """Create identifier from sig + latlong (case-insensitive)"""
        return (row["sig"] + "|" + row["latlong"]).strip().lower()

    def check_duplicates(self):
        duplicates = {}
        for index, row in enumerate(self.rows):
            key = self.make_key(row)
            if key not in duplicates:
                duplicates[key] = []
            duplicates[key].append(index)

        duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}
        if not duplicate_groups:
            return True

        lines = []
        for key, indexes in duplicate_groups.items():
            first = self.rows[indexes[0]]
            lines.append(
                f"SIG: {first['sig']}\nLat/Long: {first['latlong']}\n"
                f"CSV rows: " + ", ".join(str(self.rows[i]["_line"]) for i in indexes)
            )

        messagebox.showwarning(
            "Duplicate Records",
            "Duplicate active records detected.\n\n"
            "Record identifier is SIG + Lat/Long.\n\n"
            "Please review before converting:\n\n" + "\n\n".join(lines)
        )
        return False

    def browse_txt(self):
        filename = filedialog.askopenfilename(
            title="Open Existing TXT File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return

        self.txt_file = filename
        self.txt_entry.delete(0, tk.END)
        self.txt_entry.insert(0, filename)
        self.load_existing_txt()

    def new_txt(self):
        filename = filedialog.asksaveasfilename(
            title="Create TXT File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return

        self.txt_file = filename
        self.txt_entry.delete(0, tk.END)
        self.txt_entry.insert(0, filename)
        self.existing_blocks = []
        self.status_var.set("New TXT file selected.")

    def load_existing_txt(self):
        if not self.txt_file or not os.path.exists(self.txt_file):
            self.existing_blocks = []
            return

        try:
            with open(self.txt_file, "r", encoding="utf-8") as file:
                self.existing_blocks = self.parse_blocks(file.read())
            self.status_var.set(f"Loaded TXT containing {len(self.existing_blocks)} block(s).")
        except Exception as exc:
            messagebox.showerror("TXT Error", "Could not read the TXT file.\n\n" + str(exc))

    def parse_blocks(self, content):
        """Split TXT into blocks separated by blank lines"""
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        blocks = [block.strip() for block in content.split("\n\n") if block.strip()]
        return blocks

    def get_block_key(self, block):
        """Extract NAME and Location from a TXT block"""
        name = None
        location = None

        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("NAME"):
                parts = stripped.split("=", 1)
                if len(parts) == 2:
                    name = parts[1].strip().lower()
            elif stripped.startswith("Location"):
                parts = stripped.split("=", 1)
                if len(parts) == 2:
                    location = parts[1].strip().lower()

        return (name + "|" + location).lower() if name and location else None

    def make_block(self, row):
        """Create TXT block from CSV row"""
        return (
            "[SYMBOL]\n"
            "colour = tbc\n"
            "SYMTYPE = APT\n"
            f"NAME = {row['sig']}\n"
            f"Comment = {row['sytem']}\n"
            f"comment = {row['freq']}\n"
            f"comment = {row['area']}\n"
            f"comment = {row['region']}\n"
            f"Location = {row['latlong']}"
        )

    def generate_output(self):
        """Generate updated TXT from existing blocks and selected rows"""
        if self.txt_file and os.path.exists(self.txt_file):
            self.load_existing_txt()

        blocks = list(self.existing_blocks)
        block_lookup = {}

        for index, block in enumerate(blocks):
            key = self.get_block_key(block)
            if key is not None and key not in block_lookup:
                block_lookup[key] = index

        for index in sorted(self.selected):
            row = self.rows[index]
            key = self.make_key(row)
            new_block = self.make_block(row)

            if key in block_lookup:
                blocks[block_lookup[key]] = new_block
            else:
                block_lookup[key] = len(blocks)
                blocks.append(new_block)

        return "\n\n".join(blocks) + ("\n" if blocks else "")

    def preview(self):
        if not self.rows:
            messagebox.showwarning("Nothing to Convert", "Load a CSV containing active records first.")
            return

        if not self.selected:
            messagebox.showwarning("Nothing Selected", "Please select at least one record.")
            return

        if not self.check_duplicates():
            if not messagebox.askyesno("Continue?", "Duplicates detected.\n\nContinue with preview?"):
                return

        try:
            self.preview_text = self.generate_output()
        except Exception as exc:
            messagebox.showerror("Preview Error", str(exc))
            return

        self.show_preview_window()

    def show_preview_window(self):
        preview_window = tk.Toplevel(self.root)
        preview_window.title("TXT Preview")
        preview_window.geometry("900x650")

        frame = ttk.Frame(preview_window, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Preview of resulting TXT file:").pack(anchor="w", pady=(0, 5))

        text = ScrolledText(frame, wrap="none", font=("TkFixedFont", 10))
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.preview_text)
        text.configure(state="disabled")

        ttk.Button(frame, text="Close", command=preview_window.destroy).pack(anchor="e", pady=(10, 0))

    def save_txt(self):
        if not self.rows:
            messagebox.showwarning("Nothing to Convert", "Load a CSV containing active records first.")
            return

        if not self.selected:
            messagebox.showwarning("Nothing Selected", "Please select at least one record.")
            return

        if not self.check_duplicates():
            if not messagebox.askyesno("Continue?", "Duplicates detected.\n\nAre you sure you want to continue?"):
                return

        if not self.txt_file:
            filename = filedialog.asksaveasfilename(
                title="Save TXT File",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if not filename:
                return

            self.txt_file = filename
            self.txt_entry.delete(0, tk.END)
            self.txt_entry.insert(0, filename)

        try:
            output = self.generate_output()

            # Create backup if file exists
            if os.path.exists(self.txt_file):
                backup_file = self.txt_file + ".bak"
                try:
                    with open(self.txt_file, "r", encoding="utf-8") as source:
                        with open(backup_file, "w", encoding="utf-8") as backup:
                            backup.write(source.read())
                except Exception:
                    messagebox.showwarning(
                        "Backup Warning",
                        "Backup could not be created.\n\nProgram will still attempt to save."
                    )

            with open(self.txt_file, "w", encoding="utf-8") as file:
                file.write(output)

            self.existing_blocks = self.parse_blocks(output)
            self.status_var.set(f"Saved successfully. {len(self.selected)} record(s) processed.")

            messagebox.showinfo(
                "Saved",
                f"TXT file updated successfully.\n\n{self.txt_file}\n\n"
                f"Backup: {self.txt_file}.bak"
            )

        except Exception as exc:
            messagebox.showerror("Save Error", "Could not save the TXT file.\n\n" + str(exc))


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except tk.TclError:
        pass

    app = CSVToTXTConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
