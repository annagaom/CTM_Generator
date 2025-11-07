import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
from CTM_Generator import generate

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CTM Generator")
        self.geometry("500x240")
        self.files = []

        tk.Label(self, text="CTM Generator", font=("Arial", 15, "bold")).pack(pady=10)

        form = tk.Frame(self); form.pack()
        tk.Label(form, text="Sessios:").grid(row=0, column=0)
        tk.Label(form, text="Per sessio:").grid(row=0, column=2)

        self.sessions = tk.IntVar(value=1)
        self.per_session = tk.IntVar(value=10)

        tk.Entry(form, textvariable=self.sessions, width=5).grid(row=0, column=1, padx=5)
        tk.Entry(form, textvariable=self.per_session, width=5).grid(row=0, column=3, padx=5)

        tk.Button(self, text="Load files", command=self.load).pack(pady=5)
        self.btn_gen = tk.Button(self, text="Generate", command=self.start)
        self.btn_gen.pack()

        self.pb = ttk.Progressbar(self, length=450)
        self.pb.pack(pady=10)

        self.status = tk.Label(self, text="Ei valintaa.")
        self.status.pack()

    def load(self):
        d = filedialog.askdirectory()
        if not d:
            return

        self.files = [p for p in Path(d).rglob("*") if p.suffix.lower() == ".ctm"]

        if self.files:
            self.status.config(text=f"Löydetty {len(self.files)} CTM-tiedostoa.")
            self.btn_gen.config(state="normal")
        else:
            self.status.config(text="Ei CTM-tiedostoja kansiossa.")
            self.btn_gen.config(state="disabled")

    def start(self):
        self.btn_gen.config(state="disabled")
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        total = self.sessions.get() * self.per_session.get()
        self.pb["maximum"] = total
        callback = lambda done, name: self.after(0, self.update_ui, done, name)
        count = generate(self.files, self.sessions.get(), self.per_session.get(), callback)
        self.after(0, lambda: self.finish(count))

    def update_ui(self, done, name):
        self.pb["value"] = done
        self.status.config(text=name)

    def finish(self, count):
        self.btn_gen.config(state="normal")
        messagebox.showinfo("Valmis", f"Luotu {count} tiedostoa.")

if __name__ == "__main__":
    App().mainloop()
