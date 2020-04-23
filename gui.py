import tkinter as tk
import traceback
from tkinter import filedialog, ttk
import utility
from datamanager import carica_dati, carica_cpm
import appdirs
import os
import configparser

WIDTH = 450
HEIGHT = 520


class Application2(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # carica configurazione
        directory = appdirs.user_data_dir("Inquinanti", "Vale")
        self.inclusivo = tk.IntVar(value=1)
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.configuration_filename = os.path.join(directory, "configurazione.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.configuration_filename)
        with open(self.configuration_filename, "w") as configfile:
            self.config.write(configfile)
        try:
            filename_cpm = self.config["DEFAULT"]["classed_post_map"]
        except KeyError:
            filename_cpm = ""
        try:
            esportazione_cpm = self.config["DEFAULT"]["esportazione_cpm"]
        except KeyError:
            esportazione_cpm = ""
        try:
            diametro_min = self.config["DEFAULT"]["diametro_min_cpm"]
        except KeyError:
            diametro_min = 7
        try:
            step_cpm = self.config["DEFAULT"]["step_cpm"]
        except KeyError:
            step_cpm = 1
        try:
            self.inclusivo.set(int(self.config["DEFAULT"]["inclusivo"]))
        except KeyError:
            self.inclusivo.set(1)
        s = ttk.Style()
        s.theme_use("classic")
        s.configure("red.Horizontal.TProgressbar", foreground="blue", background="blue")

        tk.Grid.columnconfigure(self, 1, weight=1)
        tk.Grid.rowconfigure(self, 10, weight=1)

        tk.Label(self, text="File con i dati").grid(row=1, column=0, sticky=tk.W)
        tk.Label(self, text="Destinazione elaborazioni").grid(
            row=2, column=0, sticky=tk.W
        )
        tk.Label(self, text="Diametro minimo cerchi").grid(row=3, column=0, sticky=tk.W)
        tk.Label(self, text="Step incremento cerchi").grid(row=4, column=0, sticky=tk.W)
        tk.Label(self, text="Messaggi", anchor="ne").grid(
            row=10, column=0, sticky="nsw"
        )

        tk.Button(self, text="...", command=self.seleziona_file).grid(
            row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=5
        )
        tk.Button(self, text="...", command=self.esportazione_file).grid(
            row=2, column=2, columnspan=2, sticky="ew", padx=5, pady=5
        )

        self.radiobutton1 = tk.Radiobutton(
            self,
            text="superamenti inclusivi (>= valore soglia)",
            padx=20,
            variable=self.inclusivo,
            value=1,
            justify=tk.LEFT,
            command=self.impostaInclusivo(1),
        )
        self.radiobutton1.grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5
        )
        self.radiobutton2 = tk.Radiobutton(
            self,
            text="superamenti non inclusivi* (> valore soglia)",
            padx=20,
            variable=self.inclusivo,
            value=2,
            justify=tk.LEFT,
            command=self.impostaInclusivo(2),
        )
        self.radiobutton2.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=5
        )

        tk.Button(
            self, width=100, text="Inizia elaborazione", command=self.elabora_tracciati
        ).grid(row=7, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        tk.Button(self, text="esci", fg="red", command=root.destroy).grid(
            row=11, columnspan=4, sticky="ew", padx=5, pady=5
        )

        self.file_text = tk.Text(self, height=1, width=100, wrap="word", fg="blue")
        self.file_text.delete("0.0", tk.END)
        self.file_text.insert(tk.END, filename_cpm)
        self.file_text.grid(row=1, column=1, sticky="ew", pady=5)

        self.esportazione_text = tk.Text(
            self, height=1, width=100, wrap="word", fg="blue"
        )
        self.esportazione_text.delete("0.0", tk.END)
        self.esportazione_text.insert(tk.END, esportazione_cpm)
        self.esportazione_text.grid(row=2, column=1, sticky="ew", pady=5)

        self.diametro_text = tk.Text(self, height=1, width=100, wrap="word", fg="blue")
        self.diametro_text.delete("0.0", tk.END)
        self.diametro_text.insert(tk.END, diametro_min)
        self.diametro_text.grid(row=3, column=1, sticky="ew", pady=5)

        self.step_cpm_text = tk.Text(self, height=1, width=100, wrap="word", fg="blue")
        self.step_cpm_text.delete("0.0", tk.END)
        self.step_cpm_text.insert(tk.END, step_cpm)
        self.step_cpm_text.grid(row=4, column=1, sticky="ew", pady=5)

        self.progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            mode="determinate",
            style="red.Horizontal.TProgressbar",
        )
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.progress.grid(row=9, columnspan=4, sticky="ew", padx=5, pady=5)

        self.text = tk.Text(self, height=10, wrap="word", fg="blue")
        self.text.grid(row=10, column=1, columnspan=2, sticky="nsew", pady=5)

        self.scrollb = tk.Scrollbar(self, command=self.text.yview)
        self.scrollb.grid(row=10, column=3, pady=5, sticky="ns")
        self.text["yscrollcommand"] = self.scrollb.set
        self.text.see(tk.END)

    def seleziona_file(self):
        filename = filedialog.askopenfile(
            defaultextension="xlsx",
            filetypes=(("File excel 2010", "*.xlsx"),),
            title="Scegli il file excel con le informazioni da elaborare",
        )
        if filename:
            self.config["DEFAULT"]["classed_post_map"] = filename.name
            with open(self.configuration_filename, "w") as configfile:
                self.config.write(configfile)
            self.file_text.delete("0.0", tk.END)
            self.file_text.insert("0.0", filename.name)
            self.progress["value"] = 0
        else:
            self.file_text.insert("0.0", "")

    def esportazione_file(self):
        esportazione = filedialog.askdirectory(
            title="Scegli la cartella dove desideri salvare le esportazioni"
        )
        if esportazione:
            self.config["DEFAULT"]["esportazione_cpm"] = esportazione
            with open(self.configuration_filename, "w") as configfile:
                self.config.write(configfile)
            self.esportazione_text.delete("0.0", tk.END)
            self.esportazione_text.insert("0.0", esportazione)
            self.progress["value"] = 0
        else:
            self.esportazione_text.insert("0.0", "")

    def impostaInclusivo(self, value):
        self.config["DEFAULT"]["inclusivo"] = str(value)
        with open(self.configuration_filename, "w") as configfile:
            self.config.write(configfile)

    def elabora_tracciati(self):
        try:
            carica_cpm(self)
        except Exception:
            utility.scrivi(self, "*** ERRORE ***")
            utility.scrivi(self, traceback.format_exc())
            self.text.see(tk.END)


class Application(tk.Frame):
    # Pie Chart maps
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # carica configurazione
        directory = appdirs.user_data_dir("Inquinanti", "Vale")
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.configuration_filename = os.path.join(directory, "configurazione.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.configuration_filename)
        self.inclusivo = tk.IntVar(value=1)
        with open(self.configuration_filename, "w") as configfile:
            self.config.write(configfile)
        try:
            filename = self.config["DEFAULT"]["last_parsed"]
        except KeyError:
            filename = ""
        try:
            configurazione = self.config["DEFAULT"]["raggruppamenti"]
        except KeyError:
            configurazione = ""
        try:
            esportazione = self.config["DEFAULT"]["esportazione"]
        except KeyError:
            esportazione = ""
        try:
            diametro = self.config["DEFAULT"]["diametro"]
        except KeyError:
            diametro = 7
        try:
            self.inclusivo.set(int(self.config["DEFAULT"]["inclusivo"]))
        except KeyError:
            self.inclusivo.set(1)

        s = ttk.Style()
        s.theme_use("classic")
        s.configure("red.Horizontal.TProgressbar", foreground="blue", background="blue")

        tk.Grid.columnconfigure(self, 1, weight=1)
        tk.Grid.rowconfigure(self, 10, weight=1)

        tk.Label(self, text="File con i dati").grid(row=1, column=0, sticky=tk.W)
        tk.Label(self, text="File di configurazione").grid(row=2, column=0, sticky=tk.W)
        tk.Label(self, text="Destinazione elaborazioni").grid(
            row=3, column=0, sticky=tk.W
        )
        tk.Label(self, text="Diametro cerchi").grid(row=4, column=0, sticky=tk.W)
        tk.Label(self, text="Messaggi", anchor="ne").grid(
            row=10, column=0, sticky="nsw"
        )

        tk.Button(self, text="...", command=self.seleziona_file).grid(
            row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=5
        )
        tk.Button(self, text="...", command=self.configurazione_file).grid(
            row=2, column=2, columnspan=2, sticky="ew", padx=5, pady=5
        )
        tk.Button(self, text="...", command=self.esportazione_file).grid(
            row=3, column=2, columnspan=2, sticky="ew", padx=5, pady=5
        )
        self.radiobutton1 = tk.Radiobutton(
            self,
            text="superamenti inclusivi (>= valore soglia)",
            padx=20,
            variable=self.inclusivo,
            value=1,
            justify=tk.LEFT,
            command=self.impostaInclusivo(1),
        )
        self.radiobutton1.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=5
        )
        self.radiobutton2 = tk.Radiobutton(
            self,
            text="superamenti non inclusivi (> valore soglia)",
            padx=20,
            variable=self.inclusivo,
            value=2,
            justify=tk.LEFT,
            command=self.impostaInclusivo(2),
        )
        self.radiobutton2.grid(
            row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=5
        )
        tk.Button(
            self, width=100, text="Inizia elaborazione", command=self.elabora_tracciati
        ).grid(row=8, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        tk.Button(self, text="esci", fg="red", command=root.destroy).grid(
            row=11, columnspan=4, sticky="ew", padx=5, pady=5
        )

        self.file_text = tk.Text(self, height=1, width=100, wrap="word", fg="blue")
        self.file_text.delete("0.0", tk.END)
        self.file_text.insert(tk.END, filename)
        self.file_text.grid(row=1, column=1, sticky="ew", pady=5)

        self.configurazione_text = tk.Text(
            self, height=1, width=100, wrap="word", fg="blue"
        )
        self.configurazione_text.delete("0.0", tk.END)
        self.configurazione_text.insert(tk.END, configurazione)
        self.configurazione_text.grid(row=2, column=1, sticky="ew", pady=5)

        self.esportazione_text = tk.Text(
            self, height=1, width=100, wrap="word", fg="blue"
        )
        self.esportazione_text.delete("0.0", tk.END)
        self.esportazione_text.insert(tk.END, esportazione)
        self.esportazione_text.grid(row=3, column=1, sticky="ew", pady=5)

        self.diametro_text = tk.Text(self, height=1, width=100, wrap="word", fg="blue")
        self.diametro_text.delete("0.0", tk.END)
        self.diametro_text.insert(tk.END, diametro)
        self.diametro_text.grid(row=4, column=1, sticky="ew", pady=5)

        self.progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            mode="determinate",
            style="red.Horizontal.TProgressbar",
        )
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.progress.grid(row=9, columnspan=4, sticky="ew", padx=5, pady=5)

        self.text = tk.Text(self, height=10, wrap="word", fg="blue")
        self.text.grid(row=10, column=1, columnspan=2, sticky="nsew", pady=5)

        self.scrollb = tk.Scrollbar(self, command=self.text.yview)
        self.scrollb.grid(row=10, column=3, pady=5, sticky="ns")
        self.text["yscrollcommand"] = self.scrollb.set
        self.text.see(tk.END)

    def configurazione_file(self):
        filename = filedialog.askopenfile(
            defaultextension="xlsx",
            filetypes=(("File excel 2010", "*.xlsx"),),
            title="Scegli il file excel con i raggruppamenti degli inquinanti",
        )

        if filename:
            self.config["DEFAULT"]["raggruppamenti"] = filename.name
            with open(self.configuration_filename, "w") as configfile:
                self.config.write(configfile)
            self.configurazione_text.delete("0.0", tk.END)
            self.configurazione_text.insert("0.0", filename.name)
            self.progress["value"] = 0
        else:
            self.configurazione_text.insert("0.0", "")

    def seleziona_file(self):
        filename = filedialog.askopenfile(
            defaultextension="xlsx",
            filetypes=(("File excel 2010", "*.xlsx"),),
            title="Scegli il file excel con le informazioni da elaborare",
        )
        if filename:
            self.config["DEFAULT"]["last_parsed"] = filename.name
            with open(self.configuration_filename, "w") as configfile:
                self.config.write(configfile)
            self.file_text.delete("0.0", tk.END)
            self.file_text.insert("0.0", filename.name)
            self.progress["value"] = 0
        else:
            self.file_text.insert("0.0", "")

    def impostaInclusivo(self, value):
        self.config["DEFAULT"]["inclusivo"] = str(value)
        with open(self.configuration_filename, "w") as configfile:
            self.config.write(configfile)

    def esportazione_file(self):
        esportazione = filedialog.askdirectory(
            title="Scegli la cartella dove desideri salvare le esportazioni"
        )
        if esportazione:
            self.config["DEFAULT"]["esportazione"] = esportazione
            with open(self.configuration_filename, "w") as configfile:
                self.config.write(configfile)
            self.esportazione_text.delete("0.0", tk.END)
            self.esportazione_text.insert("0.0", esportazione)
            self.progress["value"] = 0
        else:
            self.esportazione_text.insert("0.0", "")

    def elabora_tracciati(self):
        try:
            carica_dati(self)
        except Exception:
            utility.scrivi(self, "*** ERRORE ***")
            utility.scrivi(self, traceback.format_exc())
            self.text.see(tk.END)


root = tk.Tk()
root.geometry(f"{WIDTH}x{HEIGHT}")

nb = ttk.Notebook(root)
page1 = Application(nb, width=WIDTH, height=HEIGHT)
nb.add(page1, text="Pie chart maps")

# second page
page2 = Application2(nb, width=WIDTH, height=HEIGHT)
nb.add(page2, text="Classed post map")

nb.pack(fill="both", expand="yes")

root.title("Generazione grafici per inquinanti")
root.mainloop()
