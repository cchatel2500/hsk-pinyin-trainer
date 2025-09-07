
import tkinter as tk
from tkinter import filedialog
from bs4 import BeautifulSoup
import random
import unidecode
import webbrowser
# import pyttsx3
import platform

def load_dictionary(filename):
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
            words.append((chinese, pinyin, french, hsk))

    return words


def filter_words_by_hsk(words, hsk_levels=None):
    if hsk_levels is None:
        return [(ch, py, fr) for (ch, py, fr, _) in words]
    else:
        return [
            (ch, py, fr) for (ch, py, fr, hsk) in words if hsk in hsk_levels
        ]


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
dictionary = load_dictionary(default_dict_file)
hsk_filter_default = "2" #  "1-6"


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
        self.translation_labels = []
        self.first_good_result = []
        self.entries = []
        self.word_info = []
        self.char_labels = []  #

        self.generate_new_set()
        # init lecture par pyttsx3
        # self.engine = pyttsx3.init()
        # self.engine.setProperty('rate', 150)


    def generate_new_set(self):
        self.translation_labels.clear()
        self.first_good_result.clear()
        self.entries.clear()
        self.word_info.clear()
        self.char_labels.clear()

        if self.hsk_filter.get() != self.old_hsk_filter:
            self.correct_count = 0  # Réinitialiser le score uniquement lors du changement de HSK
            self.total_count = 0
            self.old_hsk_filter = self.hsk_filter.get()
            hsk_levels = parse_hsk_levels(self.hsk_filter.get())
            newSet = filter_words_by_hsk(dictionary, hsk_levels)
            self.words = [w for w in newSet]

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
            self.old_hsk_filter = ""
            global dictionary
            dictionary = load_dictionary(self.dict_file.get())
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
            # char_label.bind("<Button-1>", lambda e, ch=chinese: self.play_pronunciation(ch))
            char_label.bind("<Button-1>", lambda e, lbl=char_label: self.play_pronunciation(lbl.cget("text")))

            self.char_labels.append(char_label)

            entry = tk.Entry(frame, font=("Arial", 14))
            entry.grid(row=i + tabHeader, column=1)
            entry.bind("<KeyRelease>", lambda e, idx=i: (
                self.handle_special_input(e, idx),
                self.check_pinyin(e, idx)
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

    def handle_special_input(self, event, idx ):
        entry = self.entries[idx]
        raw = entry.get()
        text = raw.strip()
        # pinyin/trad courants (dynamiques)
        current_pinyin, current_french = self.word_info[idx]

        # Pas de caractère spécial -> on ne fait rien
        if not any(s in raw for s in (",", ".", "'", "?", "!")):
            return

        if  "," in text:
            entry.delete(0, tk.END)
            entry.insert(0, self.word_info[idx][0]) # pinyin actuel
            entry.config(bg="yellow")
            self.first_good_result[idx]=True
            return
        if  "." in text:
            entry.delete(0, tk.END)
            entry.config(bg="white")
            self.translation_labels[idx].config(text=self.word_info[idx][1]) # trad actuelle
            return
        if  "'" in text :
            chinese = self.char_labels[idx].cget("text")
            print(chinese)
            self.play_pygame_pronunciation(event, chinese)
            #self.play_google_tts(chinese)
            return
        if "!!" in text:
            if entry.cget("bg") == "salmon":  # Seulement si la zone est rouge
                # Nettoyer la chaîne (enlever ? ! , . ' etc.)
                user_pinyin = text.strip("?!,.' ").strip()
                self.popup_opening = False
                return
        if "!" in text:
            if entry.cget("bg") == "salmon":  # Seulement si la zone est rouge
                # Nettoyer la chaîne (enlever ? ! , . ' etc.)
                user_pinyin = text.strip("?!,.' ").strip()
                self.show_related_characters(user_pinyin, self.selected_words[idx][0])
                # On garde la couleur jaune sur le caractère correct
                self.char_labels[idx].config(bg="orange")
                return

        if "?" in text and entry.cget("bg") == "salmon":
            # extraire éventuel index (ex: "2?")
            numeric_part = ''.join(c for c in text if c.isdigit())
            user_pinyin = text.replace("?", "").replace(numeric_part, "").strip()

            # candidats (char, fr) pour ce pinyin
            candidates = self.get_candidates_from_pinyin(user_pinyin)

            if candidates:
                if numeric_part.isdigit():
                    choice = int(numeric_part) - 1
                    if not (0 <= choice < len(candidates)):
                        choice = 0
                else:
                    choice = 0

                chosen_char, chosen_fr = candidates[choice]

                # mise à jour affichage
                self.char_labels[idx].config(text=chosen_char, bg="yellow")
                self.translation_labels[idx].config(text=chosen_fr)

                # *** très important : mettre à jour la "vérité" utilisée partout ***
                # désormais, pour cette ligne, le pinyin de référence est celui que l’utilisateur a demandé
                self.word_info[idx] = (user_pinyin, chosen_fr)
            return
        # '?' : remplacement par un caractère correspondant au pinyin saisi
        if "?" in text and entry.cget("bg") != "salmon":
            # Comparer mots incorrects
            user_words = unidecode.unidecode(text).split()
            correct_words = unidecode.unidecode(current_pinyin).split()
            #print ("correct: ",correct_words, user_words, text)
            self.entries[idx].delete(0, tk.END)
            entry.config(bg="lightblue")
            self.first_good_result[idx] = True
            firstWord = True
            for i, (uw, cw) in enumerate(zip(user_words, correct_words)):
                #print("uw: ",uw, cw)
                if uw != cw and firstWord:
                    # Affiche la traduction du mot incorrect (si disponible)
                    self.entries[idx].insert('end', cw + " ")
                    firstWord = False
                else:
                    self.entries[idx].insert('end', uw + " ")

    def get_candidates_from_pinyin(self, pinyin_search):
        """
        Retourne la liste (caractère chinois, traduction FR)
        pour un pinyin donné (sans accents).
        """
        return [
            (ch, py, fr)
            for ch, py, fr, _ in dictionary
            if unidecode.unidecode(py) == unidecode.unidecode(pinyin_search)
        ]

    def show_related_characters(self, pinyin_search, correct_char):
        if getattr(self, "popup_opening", False):
            return
        self.popup_opening = True

        popup = tk.Toplevel(self.root)
        popup.title(f"Caractères avec pinyin '{pinyin_search}'")
        popup.geometry("500x150")

        def on_close():
            self.popup_opening = False
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_close)

        # --- Zone scrollable ---
        canvas = tk.Canvas(popup)
        scrollbar_y = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollbar_x = tk.Scrollbar(popup, orient="horizontal", command=canvas.xview)

        frame = tk.Frame(canvas)
        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all"),
                xscrollcommand=scrollbar_x.set,
                yscrollcommand=scrollbar_y.set,
            )
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        # --- En-têtes ---
        tk.Label(frame, text="Caractère", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(frame, text="Pinyin", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame, text="Français", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)

        # --- Données ---
        matches = [(ch, py, fr) for ch, py, fr, _ in dictionary
                   if unidecode.unidecode(py) == unidecode.unidecode(pinyin_search)]

        if not matches:
            tk.Label(frame, text="Aucun caractère trouvé", font=("Arial", 14)).grid(row=1, column=0, columnspan=3,
                                                                                    pady=20)
        else:
            for i, (ch, py, fr) in enumerate(matches, start=1):
                lbl_ch = tk.Label(frame, text=ch, font=("NSimSun", 20), cursor="hand2")
                lbl_ch.grid(row=i, column=0, padx=5, pady=2, sticky="w")
                lbl_ch.bind("<Button-1>", lambda e, c=ch: self.play_pronunciation(c))

                lbl_py = tk.Label(frame, text=py, font=("Arial", 12), anchor="w")
                lbl_py.grid(row=i, column=1, padx=5, pady=2, sticky="w")

                lbl_fr = tk.Label(frame, text=fr, font=("Arial", 12), anchor="w")
                lbl_fr.grid(row=i, column=2, padx=5, pady=2, sticky="w")

                if ch == correct_char:
                    lbl_ch.config(bg="yellow")

    def check_pinyin(self, event, idx):

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

        #
        correct_pinyin = self.word_info[idx][0]  # pinyin actuel
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

