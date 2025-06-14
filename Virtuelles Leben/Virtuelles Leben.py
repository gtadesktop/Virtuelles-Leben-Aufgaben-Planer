import sys
import json
import os
import random
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QLineEdit, QTextEdit, QMessageBox, QListWidget, QInputDialog, QMenu,
    QHBoxLayout, QComboBox, QDateEdit, QFileDialog, QDialog
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QPoint, QDate

# Für Diagramme
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import time

print("
Virtuelles Leben - Aufgaben Planer

Copyright (c) 2025 gtadesktop

Dieses Projekt ist unter der MIT Lizenz lizenziert.
")

time.sleep(10)

DATA_DIR = "data"
THOUGHTS_FILE = os.path.join(DATA_DIR, "thoughts.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
LEVEL_FILE = os.path.join(DATA_DIR, "level.json")
GOAL_FILE = os.path.join(DATA_DIR, "goal.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def set_modern_style(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(40, 40, 40))
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

DEFAULT_CATEGORIES = ["Allgemein", "Schule", "Arbeit", "Privat", "Sonstiges"]

MOTIVATION_QUOTES = [
    "Du schaffst das!",
    "Jeder Tag ist eine neue Chance.",
    "Bleib dran, es lohnt sich!",
    "Große Dinge beginnen klein.",
    "Gib niemals auf!",
    "Dein Einsatz zahlt sich aus.",
    "Heute ist dein Tag!",
    "Mach weiter so!"
]

class StatsDialog(QDialog):
    def __init__(self, tasks, thoughts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Statistiken & Diagramme")
        self.setGeometry(200, 200, 500, 400)
        layout = QVBoxLayout()
        # Statistiken
        total_tasks = len(tasks)
        total_thoughts = len(thoughts)
        per_cat = {}
        for t in tasks:
            cat = t.get("category", "Allgemein")
            per_cat[cat] = per_cat.get(cat, 0) + 1
        stats_label = QLabel(
            f"Aufgaben gesamt: {total_tasks}\n"
            f"Gedanken gesamt: {total_thoughts}\n"
            + "\n".join([f"{cat}: {count} Aufgaben" for cat, count in per_cat.items()])
        )
        layout.addWidget(stats_label)
        # Diagramm
        if per_cat:
            fig = Figure(figsize=(4,2.5))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.bar(per_cat.keys(), per_cat.values(), color="#2a82da")
            ax.set_title("Aufgaben pro Kategorie")
            ax.set_ylabel("Anzahl")
            fig.tight_layout()
            layout.addWidget(canvas)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Virtuelles Leben")
        self.setGeometry(100, 100, 750, 650)
        self.tasks = load_json(TASKS_FILE, [])
        self.thoughts = load_json(THOUGHTS_FILE, [])
        self.level = load_json(LEVEL_FILE, {"xp": 0, "level": 1})
        self.goal = load_json(GOAL_FILE, {"date": "", "goal": "", "done": False})
        self.init_ui()
        self.refresh_labels()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)

        font = QFont("Segoe UI", 12)
        headline_font = QFont("Segoe UI", 14, QFont.Bold)

        self.todo_label = QLabel("To-Dos:")
        self.todo_label.setFont(headline_font)
        self.mood_label = QLabel()
        self.mood_label.setFont(headline_font)
        self.xp_label = QLabel()
        self.xp_label.setFont(headline_font)

        # Motivation
        self.motivation_label = QLabel(random.choice(MOTIVATION_QUOTES))
        self.motivation_label.setFont(QFont("Segoe UI", 11, QFont.StyleItalic))
        self.motivation_label.setStyleSheet("color: #2a82da;")
        self.motivation_btn = QPushButton("Neuer Motivationsspruch")
        self.motivation_btn.setFont(font)
        self.motivation_btn.clicked.connect(self.show_new_motivation)

        # Tagesziel
        goal_layout = QHBoxLayout()
        self.goal_input = QLineEdit()
        self.goal_input.setFont(font)
        self.goal_input.setPlaceholderText("Tagesziel eingeben...")
        self.goal_btn = QPushButton("Tagesziel speichern")
        self.goal_btn.setFont(font)
        self.goal_btn.clicked.connect(self.save_goal)
        self.goal_done_btn = QPushButton("Tagesziel erledigt!")
        self.goal_done_btn.setFont(font)
        self.goal_done_btn.clicked.connect(self.finish_goal)
        goal_layout.addWidget(self.goal_input)
        goal_layout.addWidget(self.goal_btn)
        goal_layout.addWidget(self.goal_done_btn)
        self.goal_status_label = QLabel()
        self.goal_status_label.setFont(font)

        # Filter
        filter_layout = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItem("Alle Kategorien")
        self.category_filter.addItems(DEFAULT_CATEGORIES)
        self.category_filter.currentIndexChanged.connect(self.refresh_labels)
        self.deadline_filter = QDateEdit()
        self.deadline_filter.setCalendarPopup(True)
        self.deadline_filter.setDisplayFormat("yyyy-MM-dd")
        self.deadline_filter.setDateRange(QDate(2000, 1, 1), QDate(2100, 12, 31))
        self.deadline_filter.setDate(QDate(2000, 1, 1))
        self.deadline_filter.setSpecialValueText("Kein Filter")
        self.deadline_filter.dateChanged.connect(self.refresh_labels)
        filter_layout.addWidget(QLabel("Kategorie:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("Fällig bis:"))
        filter_layout.addWidget(self.deadline_filter)

        self.task_list = QListWidget()
        self.task_list.setFont(font)
        self.task_list.setStyleSheet("padding: 8px; border-radius: 6px; background-color: #232629; color: white;")
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_task_context_menu)

        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setFont(font)
        self.task_input.setPlaceholderText("Neue Aufgabe eingeben...")
        self.category_input = QComboBox()
        self.category_input.addItems(DEFAULT_CATEGORIES)
        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDisplayFormat("yyyy-MM-dd")
        self.deadline_input.setDate(QDate.currentDate())
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.category_input)
        input_layout.addWidget(self.deadline_input)

        self.add_task_btn = QPushButton("Aufgabe hinzufügen")
        self.add_task_btn.setFont(font)
        self.add_task_btn.clicked.connect(self.add_task)

        self.thought_input = QTextEdit()
        self.thought_input.setFont(font)
        self.thought_input.setPlaceholderText("Gedanken/Stimmung eintragen...")
        self.add_thought_btn = QPushButton("Gedanke speichern")
        self.add_thought_btn.setFont(font)
        self.add_thought_btn.clicked.connect(self.add_thought)

        self.save_btn = QPushButton("Sichern (Backup)")
        self.save_btn.setFont(font)
        self.save_btn.clicked.connect(self.save_backup)
        self.status_btn = QPushButton("Status anzeigen")
        self.status_btn.setFont(font)
        self.status_btn.clicked.connect(self.show_status)

        # Neue Buttons für Statistik, Export
        self.stats_btn = QPushButton("Statistiken & Diagramme")
        self.stats_btn.setFont(font)
        self.stats_btn.clicked.connect(self.show_stats)
        self.export_btn = QPushButton("Export (CSV)")
        self.export_btn.setFont(font)
        self.export_btn.clicked.connect(self.export_csv)

        layout.addWidget(self.todo_label)
        layout.addLayout(filter_layout)
        layout.addWidget(self.task_list)
        layout.addLayout(input_layout)
        layout.addWidget(self.add_task_btn)
        layout.addWidget(self.mood_label)
        layout.addWidget(self.thought_input)
        layout.addWidget(self.add_thought_btn)
        layout.addWidget(self.xp_label)
        layout.addWidget(self.motivation_label)
        layout.addWidget(self.motivation_btn)
        layout.addLayout(goal_layout)
        layout.addWidget(self.goal_status_label)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.status_btn)
        layout.addWidget(self.stats_btn)
        layout.addWidget(self.export_btn)

        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet("background-color: #232629; color: white;")
        self.setCentralWidget(container)

    def get_filtered_tasks(self):
        cat = self.category_filter.currentText()
        date = self.deadline_filter.date()
        filtered = []
        for t in self.tasks:
            if cat != "Alle Kategorien" and t.get("category", "Allgemein") != cat:
                continue
            if date != QDate(2000, 1, 1):
                if not t.get("deadline"):
                    continue
                tdate = QDate.fromString(t["deadline"], "yyyy-MM-dd")
                if tdate > date:
                    continue
            filtered.append(t)
        return filtered

    def refresh_labels(self):
        self.task_list.clear()
        filtered = self.get_filtered_tasks()
        if filtered:
            for t in filtered:
                cat = t.get("category", "Allgemein")
                deadline = t.get("deadline", "")
                self.task_list.addItem(f"{t['text']} [Kategorie: {cat}" + (f" | Fällig: {deadline}]" if deadline else "]"))
            self.task_list.setEnabled(True)
        else:
            self.task_list.addItem("(keine Aufgaben)")
            self.task_list.setEnabled(False)
        self.mood_label.setText("Letzter Gedanke:\n" + (self.thoughts[-1]["text"] if self.thoughts else "(keine Einträge)"))
        self.xp_label.setText(f"Level: {self.level['level']} | XP: {self.level['xp']}")
        # Tagesziel-Anzeige
        today = QDate.currentDate().toString("yyyy-MM-dd")
        if self.goal.get("date") == today:
            status = "Erledigt!" if self.goal.get("done") else "Offen"
            self.goal_status_label.setText(f"Tagesziel: {self.goal.get('goal','')} [{status}]")
        else:
            self.goal_status_label.setText("Kein Tagesziel gesetzt.")

    def add_task(self):
        text = self.task_input.text().strip()
        category = self.category_input.currentText()
        deadline = self.deadline_input.date().toString("yyyy-MM-dd")
        if text:
            task = {"text": text, "category": category}
            if deadline:
                task["deadline"] = deadline
            self.tasks.append(task)
            save_json(TASKS_FILE, self.tasks)
            self.task_input.clear()
            self.level["xp"] += 5
            self.check_level_up()
            save_json(LEVEL_FILE, self.level)
            self.refresh_labels()

    def edit_task(self, idx):
        filtered = self.get_filtered_tasks()
        if idx >= len(filtered):
            return
        task = filtered[idx]
        orig_idx = self.tasks.index(task)
        old_text = task["text"]
        old_cat = task.get("category", "Allgemein")
        old_deadline = task.get("deadline", "")
        new_text, ok = QInputDialog.getText(self, "Aufgabe bearbeiten", "Neue Beschreibung:", QLineEdit.Normal, old_text)
        if not (ok and new_text.strip()):
            return
        new_cat, ok = QInputDialog.getItem(self, "Kategorie wählen", "Kategorie:", DEFAULT_CATEGORIES, DEFAULT_CATEGORIES.index(old_cat), False)
        if not ok:
            return
        new_deadline, ok = QInputDialog.getText(self, "Deadline ändern", "Fällig bis (yyyy-MM-dd, leer = keine):", QLineEdit.Normal, old_deadline)
        if not ok:
            return
        self.tasks[orig_idx] = {
            "text": new_text.strip(),
            "category": new_cat,
            **({"deadline": new_deadline.strip()} if new_deadline.strip() else {})
        }
        save_json(TASKS_FILE, self.tasks)
        self.refresh_labels()

    def delete_task(self, idx):
        filtered = self.get_filtered_tasks()
        if idx >= len(filtered):
            return
        task = filtered[idx]
        orig_idx = self.tasks.index(task)
        reply = QMessageBox.question(self, "Aufgabe löschen", f"Aufgabe wirklich löschen?\n\n{task['text']}", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.tasks[orig_idx]
            save_json(TASKS_FILE, self.tasks)
            self.refresh_labels()

    def show_task_context_menu(self, pos: QPoint):
        filtered = self.get_filtered_tasks()
        if not filtered:
            return
        item = self.task_list.itemAt(pos)
        if not item:
            return
        idx = self.task_list.row(item)
        menu = QMenu(self)
        edit = menu.addAction("Bearbeiten")
        delete = menu.addAction("Löschen")
        action = menu.exec_(self.task_list.mapToGlobal(pos))
        if action == edit:
            self.edit_task(idx)
        elif action == delete:
            self.delete_task(idx)

    def add_thought(self):
        text = self.thought_input.toPlainText().strip()
        if text:
            self.thoughts.append({"text": text})
            save_json(THOUGHTS_FILE, self.thoughts)
            self.thought_input.clear()
            self.level["xp"] += 2
            self.check_level_up()
            save_json(LEVEL_FILE, self.level)
            self.refresh_labels()

    def check_level_up(self):
        while self.level["xp"] >= self.level["level"] * 20:
            self.level["xp"] -= self.level["level"] * 20
            self.level["level"] += 1

    def save_backup(self):
        backup_dir = os.path.join(DATA_DIR, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        for file in [TASKS_FILE, THOUGHTS_FILE, LEVEL_FILE, GOAL_FILE]:
            if os.path.exists(file):
                with open(file, "r", encoding="utf-8") as src, open(os.path.join(backup_dir, os.path.basename(file)), "w", encoding="utf-8") as dst:
                    dst.write(src.read())
        QMessageBox.information(self, "Backup", "Backup wurde gespeichert.")

    def show_status(self):
        QMessageBox.information(self, "Status", f"Level: {self.level['level']}\nXP: {self.level['xp']}\nAufgaben: {len(self.tasks)}\nGedanken: {len(self.thoughts)}")

    def show_stats(self):
        dlg = StatsDialog(self.tasks, self.thoughts, self)
        dlg.exec_()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportiere als CSV", "", "CSV Dateien (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Typ", "Text", "Kategorie", "Deadline"])
                for t in self.tasks:
                    writer.writerow(["Aufgabe", t.get("text", ""), t.get("category", ""), t.get("deadline", "")])
                for th in self.thoughts:
                    writer.writerow(["Gedanke", th.get("text", ""), "", ""])
            QMessageBox.information(self, "Export", "Export erfolgreich!")
        except Exception as e:
            QMessageBox.warning(self, "Export", f"Fehler beim Export: {e}")

    def show_new_motivation(self):
        self.motivation_label.setText(random.choice(MOTIVATION_QUOTES))

    def save_goal(self):
        goal = self.goal_input.text().strip()
        if goal:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            self.goal = {"date": today, "goal": goal, "done": False}
            save_json(GOAL_FILE, self.goal)
            self.goal_input.clear()
            self.refresh_labels()

    def finish_goal(self):
        today = QDate.currentDate().toString("yyyy-MM-dd")
        if self.goal.get("date") == today and not self.goal.get("done"):
            self.goal["done"] = True
            save_json(GOAL_FILE, self.goal)
            self.level["xp"] += 10
            self.check_level_up()
            save_json(LEVEL_FILE, self.level)
            QMessageBox.information(self, "Tagesziel", "Super! XP für das Tagesziel erhalten.")
            self.refresh_labels()
        else:
            QMessageBox.information(self, "Tagesziel", "Kein Tagesziel gesetzt oder schon erledigt.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_modern_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
