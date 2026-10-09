__version__ = "1.0.0"

import os
import threading
import json
import urllib.request
import urllib.error
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserIconView

KV = r"""
#:import dp kivy.metrics.dp
<GeneratorRoot>:
    orientation: "vertical"
    padding: dp(14)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.055, 0.075, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "[b]OMNI FLASH[/b]  [color=66d9ef]VIDEO STUDIO[/color]"
        markup: True
        font_size: "23sp"
        size_hint_y: None
        height: dp(48)
        color: 0.94, 0.96, 1, 1
    Label:
        text: "Генератор видео по промпту и изображению"
        font_size: "13sp"
        size_hint_y: None
        height: dp(24)
        color: 0.70, 0.76, 0.86, 1
    TextInput:
        id: api_key
        hint_text: "Gemini API key"
        password: True
        multiline: False
        size_hint_y: None
        height: dp(48)
        background_color: 0.12, 0.15, 0.22, 1
        foreground_color: 1, 1, 1, 1
        cursor_color: 0.3, 0.8, 1, 1
        padding: dp(12), dp(12)
    TextInput:
        id: prompt
        hint_text: "Опиши видео: персонажи, действия, камера, стиль..."
        text: "Реалистичное кинематографичное видео: мопс смотрит в камеру, затем уверенно идет вперед. Плавное движение камеры, естественное освещение, высокая детализация."
        multiline: True
        size_hint_y: 0.38
        background_color: 0.12, 0.15, 0.22, 1
        foreground_color: 1, 1, 1, 1
        cursor_color: 0.3, 0.8, 1, 1
        padding: dp(12), dp(12)
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        Button:
            text: "Выбрать картинку"
            background_normal: ""
            background_color: 0.17, 0.36, 0.55, 1
            on_release: root.choose_image()
        Button:
            text: "Убрать картинку"
            background_normal: ""
            background_color: 0.25, 0.27, 0.33, 1
            on_release: root.clear_image()
    Label:
        id: image_label
        text: "Изображение не выбрано"
        size_hint_y: None
        height: dp(24)
        color: 0.72, 0.83, 0.95, 1
        text_size: self.width, None
        halign: "left"
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)
        Spinner:
            id: aspect
            text: "9:16"
            values: ["9:16", "16:9"]
            background_normal: ""
            background_color: 0.17, 0.2, 0.29, 1
        Spinner:
            id: resolution
            text: "720p"
            values: ["360p", "720p", "1080p"]
            background_normal: ""
            background_color: 0.17, 0.2, 0.29, 1
    Button:
        id: generate
        text: "СОЗДАТЬ ВИДЕО"
        size_hint_y: None
        height: dp(54)
        background_normal: ""
        background_color: 0.08, 0.62, 0.78, 1
        color: 1, 1, 1, 1
        bold: True
        on_release: root.generate_video()
    Label:
        id: status
        text: "Готово. Введите API-ключ и нажмите кнопку."
        size_hint_y: None
        height: dp(60)
        text_size: self.width, None
        halign: "left"
        valign: "top"
        color: 0.84, 0.88, 0.94, 1
"""

class GeneratorRoot(BoxLayout):
    image_path = None

    def choose_image(self):
        chooser = FileChooserIconView(filters=["*.png", "*.jpg", "*.jpeg", "*.webp"])
        layout = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        layout.add_widget(chooser)
        from kivy.uix.button import Button
        btn = Button(text="Выбрать", size_hint_y=None, height=dp(46))
        layout.add_widget(btn)
        popup = Popup(title="Выберите изображение", content=layout, size_hint=(0.95, 0.9))
        def select(*_):
            if chooser.selection:
                self.image_path = chooser.selection[0]
                self.ids.image_label.text = os.path.basename(self.image_path)
                popup.dismiss()
        btn.bind(on_release=select)
        popup.open()

    def clear_image(self):
        self.image_path = None
        self.ids.image_label.text = "Изображение не выбрано"

    def set_status(self, value):
        self.ids.status.text = value

    def generate_video(self):
        key = self.ids.api_key.text.strip()
        prompt = self.ids.prompt.text.strip()
        if not key:
            self.set_status("Введите Gemini API key из Google AI Studio.")
            return
        if not prompt:
            self.set_status("Введите описание видео.")
            return
        self.ids.generate.disabled = True
        self.set_status("Отправляю запрос. Генерация может занять некоторое время…")
        threading.Thread(
            target=self._worker,
            args=(key, prompt, self.image_path, self.ids.aspect.text, self.ids.resolution.text),
            daemon=True
        ).start()

    def _worker(self, key, prompt, image_path, aspect, resolution):
        try:
            # API integration is intentionally isolated; check current API schema/model access.
            import base64
            parts = []
            if image_path:
                import mimetypes
                mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
                with open(image_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode("ascii")
                parts.append({"type": "image", "data": data, "mime_type": mime})
            parts.append({"type": "text", "text": prompt})
            payload = {
                "model": "gemini-omni-1.1-flash",
                "input": parts if image_path else prompt,
                "generation_config": {
                    "video_config": {"task": "image_to_video" if image_path else "text_to_video"}
                },
                "response_format": {
                    "type": "video", "aspect_ratio": aspect, "resolution": resolution
                }
            }
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "x-goog-api-key": key},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=600) as response:
                result = json.loads(response.read().decode("utf-8"))
            video_data = None
            output_video = result.get("output_video") or {}
            if isinstance(output_video, dict):
                video_data = output_video.get("data")
            if not video_data:
                raise RuntimeError("API не вернул видео. Проверьте доступность модели и актуальный формат API.")
            video_bytes = base64.b64decode(video_data)
            # Save in app's private documents folder; user can share it via Android file manager.
            outdir = App.get_running_app().user_data_dir
            os.makedirs(outdir, exist_ok=True)
            outpath = os.path.join(outdir, "omni_video.mp4")
            with open(outpath, "wb") as f:
                f.write(video_bytes)
            Clock.schedule_once(lambda dt: self._done(outpath), 0)
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda dt, m=msg: self._error(m), 0)

    def _done(self, path):
        self.ids.generate.disabled = False
        self.set_status("Видео сохранено внутри приложения:\n" + path)

    def _error(self, msg):
        self.ids.generate.disabled = False
        self.set_status("Ошибка генерации:\n" + msg[:500])

class OmniApp(App):
    def build(self):
        Builder.load_string(KV)
        return GeneratorRoot()

if __name__ == "__main__":
    OmniApp().run()
