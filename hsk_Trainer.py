
import tkinter as tk
from tkinter import filedialog
from bs4 import BeautifulSoup
import random
import unidecode
import webbrowser
# import pyttsx3
import platform

def load_dictionary(filename, hsk_levels=None):
    with open(filename, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    words = []
    for row in soup.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 5:
            chinese = cols[2].text.strip()
            pinyin = cols[3].text.strip()
            french = cols[4].text.strip()
            try:
                hsk = int(cols[1].text.strip())
            except:
                hsk = None
            if hsk_levels is None or hsk in hsk_levels:
                words.append((chinese, pinyin, french))

    return words

def parse_hsk_levels(expr):
    levels = set()
    for part in expr.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            levels.update(range(start, end + 1))
        else:
            levels.add(int(part))
    return levels

default_dict_file = "vocabulaire.html"
hsk_filter_default = "2" #  "1-6"
dictionary = load_dictionary(default_dict_file)


class PinyinTrainer:
    def log_progress(self, chinese, correct_pinyin, user_input, success):
        import csv
        from datetime import datetime
        with open("rapport_progression.csv", mode="a", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                chinese,
                correct_pinyin,
                user_input,
                "✔️" if success else "❌"
            ])

    def __init__(self, root):
        self.root = root
        self.dict_file = tk.StringVar(value=default_dict_file);
        self.old_hsk_filter = ""
        self.hsk_filter = tk.StringVar(value=hsk_filter_default)
        self.correct_count = 0
        self.total_count = 0
        self.words = dictionary.copy()
        self.translation_labels = []
        self.first_good_result = []
        self.entries = []
        self.word_info = []

        self.generate_new_set()
        # init lecture par pyttsx3
        # self.engine = pyttsx3.init()
        # self.engine.setProperty('rate', 150)

    def reset_hsk(self):
        self.correct_count = 0  # Réinitialiser le score uniquement lors du changement de HSK
        self.total_count = 0
        self.generate_new_set()

    def generate_new_set(self):
        self.translation_labels.clear()
        self.first_good_result.clear()
        self.entries.clear()
        self.word_info.clear()
        # self.words = dictionary.copy()
        # self.words = [w for w in dictionary if w[0] == self.hsk_level.get()]
        if self.hsk_filter.get() != self.old_hsk_filter:
            self.correct_count = 0  # Réinitialiser le score uniquement lors du changement de HSK
            self.total_count = 0
            self.old_hsk_filter = self.hsk_filter.get()
        hsk_levels = parse_hsk_levels(self.hsk_filter.get())
        global dictionary
        dictionary = load_dictionary(self.dict_file.get(), hsk_levels)
        self.words = [w for w in dictionary]
        random.shuffle(self.words)
        self.selected_words = self.words[:20]
        self.total_count += 20
        self.create_ui()

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
        if filepath:
            self.dict_file.set(filepath)
            self.correct_count = 0
            self.total_count = 0
            self.generate_new_set()

    def play_google_tts(self, word):
        # Lecture par google translate
        # url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={word}&tl=zh-CN&client=tw-ob"
        # webbrowser.open(url)
        from gtts import gTTS
        import os
        import tempfile
        from playsound import playsound


        try:
            tts = gTTS(word, lang='zh-cn')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_file = fp.name
                tts.save(temp_file)

            # Supprimer après lecture (optionnel sur Windows, attention au timing)
            # time.sleep(2)  # attendre avant suppression ?
            # os.remove(temp_file)

            if platform.system() == "Windows":
                os.startfile(temp_file)
            else:
                playsound(temp_file)

        except Exception as e:
            print(f"Erreur lors de la lecture vocale : {e}")

    def play_pygame_pronunciation(self, event, character):
        import requests
        import tempfile
        import os
        import pygame
        import time

        try:
            url = f"https://dict.youdao.com/dictvoice?type=1&audio={character}"
            response = requests.get(url)

            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name

                pygame.mixer.init()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    time.sleep(0.5)

                os.remove(tmp_path)
            else:
                print("Échec de la récupération du son.")
        except Exception as e:
            print(f"Erreur lecture audio: {e}")

    def create_ui(self):
        tabHeader = 5
        for widget in self.root.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self.root)
        y_scroll = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        x_scroll = tk.Scrollbar(self.root, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        canvas.grid(row=0, column=0, sticky="nsew", columnspan=4, rowspan=30)
        y_scroll.grid(row=0, column=4, sticky="ns", rowspan=30)
        x_scroll.grid(row=30, column=0, sticky="ew", columnspan=4)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        frame.bind("<Configure>", on_frame_configure)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        pos_Dico = 0
        tk.Label(frame, text="Dictionnaire :", font=("Arial", 12)).grid(row=pos_Dico, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.dict_file, font=("Arial", 12), width=15).grid(row=pos_Dico, column=1)
        tk.Button(frame, text="Choisir fichier", command=self.select_file).grid(row=pos_Dico, column=2)

        pos_Chap = 1
        tk.Label(frame, text="Chap (ex: 1-3,5):", font=("Arial", 12)).grid(row=pos_Chap, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.hsk_filter, font=("Arial", 12), width=10).grid(row=pos_Chap,
                                                                                         column=1, sticky="w")
        tk.Button(frame, text="change Selection/Nouveau", command=self.generate_new_set).grid(row=pos_Chap,
                                                                                                 column=2)

        pos_Score = 2
        self.accuracy_label_1 = tk.Label(frame, text=f"Score: {self.correct_count}/{self.total_count}",
                                       font=("Arial", 14, "bold"))
        self.accuracy_label_1.grid(row=pos_Score, column=0, sticky="w")

        pos_entete_table = 3
        tk.Label(frame, text="Caractère", font=("Arial", 14, "bold")).grid(row=pos_entete_table, column=0)
        tk.Label(frame, text="Saisir le Pinyin", font=("Arial", 14, "bold")).grid(row=pos_entete_table, column=1)
        tk.Label(frame, text="Traduction", font=("Arial", 14, "bold")).grid(row=pos_entete_table, column=2, sticky='w')

        for i, (chinese, pinyin, french) in enumerate(self.selected_words):
            char_label = tk.Label(frame, text=chinese, font=("NSimSun", 20), cursor="hand2")
            char_label.grid(row=i + tabHeader, column=0)
            char_label.bind("<Button-1>", lambda e, ch=chinese: self.play_pronunciation(ch))

            entry = tk.Entry(frame, font=("Arial", 14))
            entry.grid(row=i + tabHeader, column=1)
            entry.bind("<KeyRelease>", lambda e, idx=i, p=pinyin, f=french, c=chinese: (
                self.handle_special_input(e, idx, p, f, c ),
                self.check_pinyin(e, idx, p)
            ))
            entry.bind("<Button-3>", lambda e, idx=i, f=french: self.show_french(idx, f))
            entry.bind("<Double-Button-3>", lambda e, idx=i, p=pinyin: self.show_pinyin(idx, p))

            self.entries.append(entry)
            self.word_info.append((pinyin, french))

            lbl = tk.Label(frame, text="", font=("Arial", 12), fg="blue")
            lbl.grid(row=i + tabHeader, column=2, sticky='w')
            self.translation_labels.append(lbl)
            self.first_good_result.append(False)

        Pos_Last = 20+tabHeader

        tk.Button(frame, text="Vérifier", command=self.show_results,font=("Arial", 14)).grid(row=Pos_Last, column=0)
        tk.Button(frame, text="Nouveau", command=self.generate_new_set,font=("Arial", 14)).grid(row=Pos_Last, column=1)

        self.accuracy_label_2 = tk.Label(frame, text=f"Score: {self.correct_count}/{self.total_count}",
                                       font=("Arial", 14, "bold"))
        self.accuracy_label_2.grid(column=0, sticky="w")


    def handle_special_input(self, event, idx, pinyin, french, chinese ):
        entry = self.entries[idx]
        text = entry.get().strip()
        if  "," in text:
            entry.delete(0, tk.END)
            entry.insert(0, pinyin)
            entry.config(bg="yellow")
            self.first_good_result[idx]=True
        elif  "." in text:
            entry.delete(0, tk.END)
            entry.config(bg="white")
            self.translation_labels[idx].config(text=self.word_info[idx][1])
        elif  "'" in text :
            print(chinese)
            self.play_pygame_pronunciation(event, chinese)
            #self.play_google_tts(chinese)
        elif "?"  in text:
             # Comparer mots incorrects
             user_words = unidecode.unidecode(text).split()
             correct_words = unidecode.unidecode(pinyin).split()
             # print (correct_words.reverse(), user_words.reverse())
             self.entries[idx].delete(0, tk.END)
             entry.config(bg="lightblue")
             self.first_good_result[idx]=True
             firstWord = True
             for i, (uw, cw) in enumerate(zip(user_words, correct_words)):
                 print (uw,cw)
                 if uw != cw and firstWord:
                     # Affiche la traduction du mot incorrect (si disponible)
                     self.entries[idx].insert('end', cw+" ")
                     firstWord = False
                 else:
                     self.entries[idx].insert('end', uw+" ")


    def check_pinyin(self, event, idx, correct_pinyin):

        entry = self.entries[idx]
        if entry.cget("bg") == "lightblue" :
            return

        user_input_raw = entry.get().strip()
        user_input = unidecode.unidecode(user_input_raw)
        if len(user_input)==0:
            entry.delete(0, tk.END)
            entry.config(bg="white")
            return
        # Détection de l'apostrophe pour lecture vocale
        # if user_input_raw == "'":
        #     self.engine.say(correct_pinyin)
        #     self.engine.runAndWait()
        #     entry.delete(0, tk.END)
        #     return

        correct = unidecode.unidecode(correct_pinyin)

        if user_input == correct:
            if entry.cget("bg") != "lightgreen" and not(self.first_good_result[idx]):
                self.correct_count += 1
                entry.config(bg="lightgreen")
            self.translation_labels[idx].config(text=self.word_info[idx][1])  # Affiche la traduction
            self.first_good_result[idx]=True
        else:
            user_words = user_input.split()
            correct_words = correct.split()
            if self.first_good_result[idx] :
                  entry.delete(0, tk.END)
                  entry.insert(0, correct_pinyin)
                  entry.config(bg="lightgreen")
            else:
                if correct.startswith(user_input):
                    entry.config(bg="#ccffcc")  # Vert pâle
                # if len(user_words) != len(correct_words):
                #   entry.config(bg="salmon")
                else:
                   exact_matches = sum(1 for u, c in zip(user_words, correct_words) if u == c)
                   common_words = set(user_words) & set(correct_words)
                   if exact_matches > 0:
                       entry.config(bg="#d0a3ff")  # violet
                   elif common_words:
                       entry.config(bg="#ffd580")  # orange
                   else:
                       entry.config(bg="salmon")

        self.accuracy_label_1.config(text=f"Score: {self.correct_count}/{self.total_count}")
        self.accuracy_label_2.config(text=f"Score: {self.correct_count}/{self.total_count}")


    def show_french(self, idx, french):
        self.entries[idx].delete(0, tk.END)
        self.entries[idx].insert(0, french)

    def show_pinyin(self, idx, pinyin):
        self.entries[idx].delete(0, tk.END)
        self.entries[idx].insert(0, pinyin)

    def play_pronunciation(self, character):
        url = f"https://www.frdic.com/dicts/en/{character}"
        webbrowser.open(url)

    def show_results(self):
        result_window = tk.Toplevel(self.root)
        result_window.title("Correction")

        canvas = tk.Canvas(result_window)
        y_scrollbar = tk.Scrollbar(result_window, orient="vertical", command=canvas.yview)
        x_scrollbar = tk.Scrollbar(result_window, orient="horizontal", command=canvas.xview)

        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        result_window.grid_rowconfigure(0, weight=1)
        result_window.grid_columnconfigure(0, weight=1)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # === CONTENU SCROLLABLE ===
        tk.Label(scrollable_frame, text="Caractère", font=("Arial", 14, "bold")).grid(row=0, column=0)
        tk.Label(scrollable_frame, text="Pinyin", font=("Arial", 14, "bold")).grid(row=0, column=1)
        tk.Label(scrollable_frame, text="Français", font=("Arial", 14, "bold")).grid(row=0, column=2, sticky='w')

        for i, (chinese, pinyin, french) in enumerate(self.selected_words):
            tk.Label(scrollable_frame, text=chinese, font=("NSimSun", 20)).grid(row=i + 1, column=0)
            tk.Label(scrollable_frame, text=pinyin, font=("Arial", 14)).grid(row=i + 1, column=1, sticky='w')
            tk.Label(scrollable_frame, text=french, font=("Arial", 10)).grid(row=i + 1, column=2, sticky='w')

        tk.Button(scrollable_frame, text="Fermer", command=result_window.destroy, font=("Arial", 14)).grid(row=21,column=1)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Entraînement au Pinyin")
    app = PinyinTrainer(root)
    root.mainloop()

