from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .domain import MAX_AGE, MIN_AGE, PulseMeasurements, assess


BG = "#F5F4F8"
SURFACE = "#FFFFFF"
TEXT = "#201A29"
MUTED = "#6E6878"
BORDER = "#DDD8E5"
PURPLE = "#6F30D0"
PURPLE_DARK = "#5720B4"
YELLOW = "#FFD43B"


class RuffierApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Тест Руфье")
        self.geometry("860x680")
        self.minsize(760, 600)
        self.configure(bg=BG)

        self._timer_job: str | None = None
        self._timer_generation = 0
        self._name = ""
        self._age = 0
        self._measurements: dict[str, int] = {}

        self._configure_styles()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build_shell()
        self.show_intro()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Primary.TButton",
            background=PURPLE,
            foreground="white",
            bordercolor=PURPLE,
            focusthickness=2,
            focuscolor=PURPLE,
            font=("Segoe UI", 11, "bold"),
            padding=(18, 11),
        )
        style.map(
            "Primary.TButton",
            background=[("active", PURPLE_DARK), ("disabled", "#B9A7D6")],
            bordercolor=[("active", PURPLE_DARK), ("disabled", "#B9A7D6")],
        )
        style.configure(
            "Secondary.TButton",
            background=SURFACE,
            foreground=TEXT,
            bordercolor=BORDER,
            font=("Segoe UI", 10, "bold"),
            padding=(14, 9),
        )
        style.map("Secondary.TButton", background=[("active", "#EEEAF3")])
        style.configure(
            "Timer.Horizontal.TProgressbar",
            troughcolor="#E9E4EF",
            background=PURPLE,
            bordercolor="#E9E4EF",
            lightcolor=PURPLE,
            darkcolor=PURPLE,
            thickness=14,
        )
        style.configure(
            "TEntry",
            fieldbackground=SURFACE,
            foreground=TEXT,
            bordercolor=BORDER,
            padding=9,
            font=("Segoe UI", 11),
        )

    def _build_shell(self) -> None:
        header = tk.Frame(self, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x")
        header.columnconfigure(0, weight=1)

        title = tk.Label(
            header,
            text="Тест Руфье",
            bg=SURFACE,
            fg=TEXT,
            font=("Segoe UI", 18, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=28, pady=18)
        self._reset_button = ttk.Button(
            header,
            text="Начать заново",
            style="Secondary.TButton",
            command=self.show_intro,
        )
        self._reset_button.grid(row=0, column=1, padx=28, pady=12)

        self._content = tk.Frame(self, bg=BG)
        self._content.pack(fill="both", expand=True, padx=28, pady=24)

    def _clear_content(self) -> None:
        self._cancel_timer()
        for child in self._content.winfo_children():
            child.destroy()

    def _card(self) -> tk.Frame:
        card = tk.Frame(
            self._content,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        return card

    @staticmethod
    def _label(
        parent: tk.Misc,
        text: str,
        *,
        size: int = 11,
        weight: str = "normal",
        color: str = TEXT,
        justify: str = "left",
    ) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=color,
            font=("Segoe UI", size, weight),
            justify=justify,
            wraplength=690,
        )

    def show_intro(self) -> None:
        self._clear_content()
        self._measurements.clear()
        self._reset_button.grid_remove()
        card = self._card()

        self._label(card, "Оценка реакции организма на нагрузку", size=24, weight="bold").grid(
            row=0, column=0, sticky="w", padx=42, pady=(38, 10)
        )
        self._label(
            card,
            "Три измерения пульса и 30 приседаний помогут рассчитать индекс Руфье. "
            "Приложение проведёт по каждому этапу и выдержит нужные интервалы.",
            size=12,
            color=MUTED,
        ).grid(row=1, column=0, sticky="w", padx=42, pady=(0, 26))

        form = tk.Frame(card, bg=SURFACE)
        form.grid(row=2, column=0, sticky="ew", padx=42)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        self._label(form, "Имя", size=10, weight="bold").grid(row=0, column=0, sticky="w")
        self._label(form, "Возраст", size=10, weight="bold").grid(
            row=0, column=1, sticky="w", padx=(18, 0)
        )
        name_var = tk.StringVar(value=self._name)
        age_var = tk.StringVar(value=str(self._age) if self._age else "")
        name_entry = ttk.Entry(form, textvariable=name_var)
        age_entry = ttk.Entry(form, textvariable=age_var)
        name_entry.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        age_entry.grid(row=1, column=1, sticky="ew", padx=(18, 0), pady=(6, 0))

        steps = tk.Frame(card, bg="#F8F5FC", highlightbackground="#E5D9F6", highlightthickness=1)
        steps.grid(row=3, column=0, sticky="ew", padx=42, pady=28)
        self._label(
            steps,
            "1. Пульс в покое     2. 30 приседаний     3. Пульс после нагрузки     "
            "4. Восстановление     5. Контрольный пульс",
            size=10,
            weight="bold",
            color=PURPLE_DARK,
            justify="center",
        ).pack(fill="x", padx=20, pady=18)

        def begin() -> None:
            name = name_var.get().strip()
            try:
                age = int(age_var.get().strip())
            except ValueError:
                messagebox.showerror("Проверьте возраст", "Введите возраст целым числом.")
                return
            if not name:
                messagebox.showerror("Проверьте имя", "Введите имя участника.")
                return
            if not MIN_AGE <= age <= MAX_AGE:
                messagebox.showerror(
                    "Проверьте возраст",
                    f"Допустимый возраст: от {MIN_AGE} до {MAX_AGE} лет.",
                )
                return
            self._name = name
            self._age = age
            self._reset_button.grid()
            self._show_measurement(
                key="rest",
                step="Этап 1 из 5",
                title="Пульс в покое",
                description=(
                    "Сядьте удобно и успокойте дыхание. Нажмите кнопку и считайте "
                    "удары пульса ровно 15 секунд."
                ),
                next_action=self._show_squats,
            )

        ttk.Button(card, text="Начать тест", style="Primary.TButton", command=begin).grid(
            row=4, column=0, sticky="ew", padx=42, pady=(0, 20)
        )
        self._label(
            card,
            "Тест носит справочный характер и не заменяет медицинское обследование. "
            "При плохом самочувствии прекратите нагрузку.",
            size=9,
            color=MUTED,
            justify="center",
        ).grid(row=5, column=0, padx=42, pady=(0, 30))
        name_entry.focus_set()

    def _show_measurement(
        self,
        *,
        key: str,
        step: str,
        title: str,
        description: str,
        next_action: Callable[[], None],
    ) -> None:
        self._clear_content()
        card = self._card()
        self._label(card, step.upper(), size=9, weight="bold", color=PURPLE).grid(
            row=0, column=0, pady=(38, 8)
        )
        self._label(card, title, size=25, weight="bold", justify="center").grid(
            row=1, column=0, padx=42
        )
        self._label(card, description, size=12, color=MUTED, justify="center").grid(
            row=2, column=0, padx=58, pady=(12, 24)
        )

        timer_value = tk.StringVar(value="15")
        timer_label = self._label(card, "15", size=54, weight="bold", color=PURPLE, justify="center")
        timer_label.configure(textvariable=timer_value)
        timer_label.grid(row=3, column=0)
        self._label(card, "секунд", size=10, color=MUTED, justify="center").grid(row=4, column=0)

        progress = ttk.Progressbar(
            card,
            style="Timer.Horizontal.TProgressbar",
            maximum=15,
            value=0,
        )
        progress.grid(row=5, column=0, sticky="ew", padx=90, pady=20)

        pulse_var = tk.StringVar()
        input_frame = tk.Frame(card, bg=SURFACE)
        input_frame.grid(row=6, column=0, pady=(2, 18))
        self._label(input_frame, "Насчитано ударов:", size=10, weight="bold").pack(side="left", padx=(0, 10))
        pulse_entry = ttk.Entry(input_frame, textvariable=pulse_var, width=9, state="disabled")
        pulse_entry.pack(side="left")

        action_button = ttk.Button(card, text="Начать отсчёт", style="Primary.TButton")
        action_button.grid(row=7, column=0, padx=90, sticky="ew", pady=(0, 32))

        def save_and_continue() -> None:
            try:
                value = int(pulse_var.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Проверьте результат",
                    "Введите количество ударов, насчитанных за 15 секунд.",
                )
                return
            if not 1 <= value <= 100:
                messagebox.showerror(
                    "Проверьте результат",
                    "Количество ударов за 15 секунд должно быть от 1 до 100.",
                )
                return
            self._measurements[key] = value
            next_action()

        def finish_timer() -> None:
            timer_value.set("0")
            pulse_entry.configure(state="normal")
            pulse_entry.focus_set()
            action_button.configure(text="Сохранить и продолжить", command=save_and_continue)

        def start_timer() -> None:
            action_button.configure(state="disabled")
            self._run_timer(
                seconds=15,
                label_var=timer_value,
                progress=progress,
                on_finish=finish_timer,
            )

        action_button.configure(command=start_timer)

    def _show_squats(self) -> None:
        self._clear_content()
        card = self._card()
        self._label(card, "ЭТАП 2 ИЗ 5", size=9, weight="bold", color=PURPLE).grid(
            row=0, column=0, pady=(38, 8)
        )
        self._label(card, "30 приседаний", size=25, weight="bold", justify="center").grid(
            row=1, column=0
        )
        self._label(
            card,
            "Выполните 30 спокойных приседаний за 45 секунд. Держите спину ровно, "
            "двигайтесь без рывков и прекратите упражнение при плохом самочувствии.",
            size=12,
            color=MUTED,
            justify="center",
        ).grid(row=2, column=0, padx=58, pady=(12, 24))

        timer_value = tk.StringVar(value="45")
        timer_label = self._label(card, "45", size=54, weight="bold", color=PURPLE, justify="center")
        timer_label.configure(textvariable=timer_value)
        timer_label.grid(row=3, column=0)
        self._label(card, "секунд", size=10, color=MUTED, justify="center").grid(row=4, column=0)
        progress = ttk.Progressbar(card, style="Timer.Horizontal.TProgressbar", maximum=45)
        progress.grid(row=5, column=0, sticky="ew", padx=90, pady=20)
        action_button = ttk.Button(card, text="Начать упражнение", style="Primary.TButton")
        action_button.grid(row=6, column=0, sticky="ew", padx=90, pady=(4, 32))

        def go_to_pulse() -> None:
            self._show_measurement(
                key="after_load",
                step="Этап 3 из 5",
                title="Пульс после нагрузки",
                description=(
                    "Начните измерение сразу после приседаний. Считайте удары пульса "
                    "в течение первых 15 секунд восстановления."
                ),
                next_action=self._show_recovery,
            )

        def finish_timer() -> None:
            timer_value.set("0")
            action_button.configure(
                state="normal",
                text="Перейти к измерению пульса",
                command=go_to_pulse,
            )

        def start_timer() -> None:
            action_button.configure(state="disabled")
            self._run_timer(
                seconds=45,
                label_var=timer_value,
                progress=progress,
                on_finish=finish_timer,
            )

        action_button.configure(command=start_timer)

    def _show_recovery(self) -> None:
        self._clear_content()
        card = self._card()
        self._label(card, "ЭТАП 4 ИЗ 5", size=9, weight="bold", color=PURPLE).grid(
            row=0, column=0, pady=(42, 8)
        )
        self._label(card, "Восстановление", size=25, weight="bold", justify="center").grid(
            row=1, column=0
        )
        self._label(
            card,
            "Оставайтесь в покое 30 секунд. Следующий замер начнётся на последней "
            "четверти первой минуты восстановления.",
            size=12,
            color=MUTED,
            justify="center",
        ).grid(row=2, column=0, padx=58, pady=(12, 30))

        timer_value = tk.StringVar(value="30")
        timer_label = self._label(card, "30", size=58, weight="bold", color=PURPLE, justify="center")
        timer_label.configure(textvariable=timer_value)
        timer_label.grid(row=3, column=0)
        self._label(card, "секунд", size=10, color=MUTED, justify="center").grid(row=4, column=0)
        progress = ttk.Progressbar(card, style="Timer.Horizontal.TProgressbar", maximum=30)
        progress.grid(row=5, column=0, sticky="ew", padx=90, pady=24)

        self._run_timer(
            seconds=30,
            label_var=timer_value,
            progress=progress,
            on_finish=lambda: self._show_measurement(
                key="after_recovery",
                step="Этап 5 из 5",
                title="Контрольный пульс",
                description=(
                    "Считайте удары пульса в течение последних 15 секунд первой "
                    "минуты восстановления."
                ),
                next_action=self._show_result,
            ),
        )

    def _show_result(self) -> None:
        self._clear_content()
        measurements = PulseMeasurements(
            rest=self._measurements["rest"],
            after_load=self._measurements["after_load"],
            after_recovery=self._measurements["after_recovery"],
        )
        result = assess(measurements, self._age)
        card = self._card()
        self._label(card, f"РЕЗУЛЬТАТ ДЛЯ {self._name.upper()}", size=9, weight="bold", color=PURPLE).grid(
            row=0, column=0, pady=(34, 8)
        )
        self._label(card, f"{result.index:g}", size=52, weight="bold", color=result.color, justify="center").grid(
            row=1, column=0
        )
        self._label(card, "индекс Руфье", size=10, color=MUTED, justify="center").grid(row=2, column=0)
        self._label(card, result.title, size=20, weight="bold", color=result.color, justify="center").grid(
            row=3, column=0, padx=42, pady=(16, 8)
        )
        self._label(card, result.explanation, size=11, color=MUTED, justify="center").grid(
            row=4, column=0, padx=70
        )

        metrics = tk.Frame(card, bg="#F8F7FA", highlightbackground=BORDER, highlightthickness=1)
        metrics.grid(row=5, column=0, sticky="ew", padx=42, pady=24)
        for column in range(3):
            metrics.columnconfigure(column, weight=1)
        metric_values = (
            ("В покое", result.rest_bpm),
            ("После нагрузки", result.after_load_bpm),
            ("После восстановления", result.after_recovery_bpm),
        )
        for column, (caption, bpm) in enumerate(metric_values):
            self._label(metrics, f"{bpm}", size=19, weight="bold", justify="center").grid(
                row=0, column=column, pady=(16, 2)
            )
            self._label(metrics, "уд/мин", size=9, color=MUTED, justify="center").grid(
                row=1, column=column
            )
            self._label(metrics, caption, size=9, color=MUTED, justify="center").grid(
                row=2, column=column, padx=8, pady=(4, 16)
            )

        ttk.Button(card, text="Пройти тест ещё раз", style="Primary.TButton", command=self.show_intro).grid(
            row=6, column=0, sticky="ew", padx=42, pady=(0, 14)
        )
        self._label(
            card,
            "Результат является ориентировочным. При жалобах на самочувствие обратитесь к врачу.",
            size=9,
            color=MUTED,
            justify="center",
        ).grid(row=7, column=0, padx=42, pady=(0, 26))

    def _run_timer(
        self,
        *,
        seconds: int,
        label_var: tk.StringVar,
        progress: ttk.Progressbar,
        on_finish: Callable[[], None],
    ) -> None:
        self._cancel_timer()
        self._timer_generation += 1
        generation = self._timer_generation
        started_at = time.monotonic()
        progress.configure(maximum=seconds, value=0)

        def tick() -> None:
            if generation != self._timer_generation:
                return
            elapsed = time.monotonic() - started_at
            remaining = max(0.0, seconds - elapsed)
            label_var.set(str(int(remaining + 0.999)))
            progress.configure(value=min(seconds, elapsed))
            if remaining <= 0:
                self._timer_job = None
                on_finish()
                return
            self._timer_job = self.after(50, tick)

        tick()

    def _cancel_timer(self) -> None:
        self._timer_generation += 1
        if self._timer_job is not None:
            self.after_cancel(self._timer_job)
            self._timer_job = None

    def _close(self) -> None:
        self._cancel_timer()
        self.destroy()


def main() -> None:
    app = RuffierApp()
    app.mainloop()


if __name__ == "__main__":
    main()
