import tkinter as tk


def scrivi(parent, testo):
    parent.text.insert(tk.END, testo + '\n')
    parent.text.see(tk.END)
    parent.text.update()


def accoda(parent, testo):
    parent.text.insert(tk.END, testo)

    parent.text.update()


def svuota(parent):
    parent.text.delete('0.0', tk.END)
    parent.text.update()


def avanzamento(parent, value):
    parent.progress["value"] = value
    parent.progress.update()
