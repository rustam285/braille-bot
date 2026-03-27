import pyttsx3
import json
import datetime
import pygame
from dictionaries import letters_for_dictations, dictations, letter_code_map, sounds, play_sound
from resources import words_for_dict, letters
import random
from collections import OrderedDict

DB_FILE = "students_db.json"

class DictationModule:
    def __init__(self, student_id, braille_app):
        self.student_id = student_id
        self.braille_app = braille_app
        self.today = datetime.date.today().strftime("%d-%m-%Y")
        self.load_student_progress()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 120)
        self.engine.setProperty("voice", "russian")
        self.current_letter = None
        self.current_word = None
        self.dictation_queue = self.get_today_dictations()
        self.is_first_dictation = True  # Флаг для первого диктанта
        self.word_queue = None
        self.words_history = []

    def get_words_for_dictation(self, current_letter):
        main_words = dictations[current_letter].copy()

        # Для начального диктанта берем ровно 10 слов
        if current_letter == "Начальный диктант":
            self.words_history.extend(main_words)
            self.words_history = list(OrderedDict.fromkeys(self.words_history))
            return main_words[:10]

        # Для остальных диктантов дополняем из предыдущих
        needed_words = 10 - len(main_words)
        if needed_words > 0:
            # Собираем все предыдущие диктанты
            current_index = letters_for_dictations.index(current_letter)
            previous_letters = letters_for_dictations[:current_index]
            previous_words = []
            for letter in previous_letters:
                previous_words.extend(dictations[letter])
            # Убираем повторы и слова, уже присутствующие в текущем диктанте
            previous_words = list(OrderedDict.fromkeys(previous_words))
            available_words = [w for w in previous_words if w not in main_words]
            additional_words = random.sample(available_words, min(needed_words, len(available_words)))
            main_words.extend(additional_words)

        # Обновляем историю
        self.words_history.extend(main_words)
        self.words_history = list(OrderedDict.fromkeys(self.words_history))

        return main_words[:10]

    def load_student_progress(self):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.student_data = json.load(f)
        except FileNotFoundError:
            self.student_data = {}

        if self.student_id not in self.student_data:
            self.student_data[self.student_id] = {}

        if self.today not in self.student_data[self.student_id]:
            self.student_data[self.student_id][self.today] = {}

    def save_progress(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.student_data, f, ensure_ascii=False, indent=4)

    def say_phrase(self, phrase):
        self.engine.say(phrase)
        self.engine.runAndWait()

    def get_today_dictations(self):
        completed = self.student_data[self.student_id][self.today].keys()
        available = []

        if "Начальный диктант" not in completed:
            available.append("Начальный диктант")

        available.extend([letter for letter in letters_for_dictations 
                        if letter != "Начальный диктант" and letter not in completed])

        return iter(available)

    def clear_win(self):
        self.braille_app.clear_win()
        self.braille_app.s_word.clear()
        self.braille_app.pin = 0

    def next_letter(self):
        try:
            self.current_letter = next(self.dictation_queue)

            words = self.get_words_for_dictation(self.current_letter)

            if self.current_letter == "Начальный диктант":
                play_sound(sounds[8])
                pygame.time.delay(5500)
            else:
                play_sound(sounds[6])
                pygame.time.delay(4500)
                letters[letter_code_map[self.current_letter.lower()]].play_sound()

            self.word_queue = iter(words)
            self.next_word()

        except StopIteration:
            self.clear_win()
            play_sound(sounds[0])
            self.current_letter = None
            self.current_word = None

    def next_word(self):
        if not hasattr(self, 'word_queue') or self.word_queue is None:
            self.next_letter()
            return
        try:
            self.current_word = next(self.word_queue)
            pygame.time.delay(2500)
            play_sound(sounds[2])
            pygame.time.delay(2500)
            play_sound(words_for_dict[self.current_word])
        except StopIteration:
            self.next_letter()

    def check_word(self, user_word):
        if user_word.lower() == "стоп":
            play_sound(sounds[0])
            self.braille_app.clear_win()
            self.braille_app.s_word.clear()
            self.braille_app.pin = 0
            self.current_letter = None
            self.current_word = None
            return

        if not self.current_word:
            return

        if user_word == self.current_word:
            play_sound(sounds[5])
            self.update_student_progress(self.current_word, correct=True)
            self.next_word()
        else:
            play_sound(sounds[4])
            self.next_word()

        self.braille_app.clear_win()
        self.braille_app.s_word.clear()
        self.braille_app.pin = 0

    def update_student_progress(self, word, correct, mistake=None):
        dictation_key = "Начальный диктант" if self.current_letter == "Начальный диктант" else self.current_letter

        if dictation_key not in self.student_data[self.student_id][self.today]:
            self.student_data[self.student_id][self.today][dictation_key] = {
                "errors": 0,
                "mistakes": [],
                "grade": 10
            }

        if not correct:
            self.student_data[self.student_id][self.today][dictation_key]["errors"] += 1
            self.student_data[self.student_id][self.today][dictation_key]["mistakes"].append(mistake)
            self.student_data[self.student_id][self.today][dictation_key]["grade"] = max(
                1, self.student_data[self.student_id][self.today][dictation_key]["grade"] - 1
            )

        self.save_progress()
