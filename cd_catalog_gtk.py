#!/usr/bin/env python3

import json
import os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib

class CDCatalogApp:
    def __init__(self):
        self.cd_filename = "cd_catalog.json"
        self.vinyl_filename = "vinyl_catalog.json"
        self.cd_catalog = self.load_catalog(self.cd_filename)
        self.vinyl_catalog = self.load_catalog(self.vinyl_filename)

        self.app = Gtk.Application(application_id="org.example.cdcatalog")
        self.app.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("Каталог музыки")
        self.window.set_default_size(600, 1000)
        self.window.set_icon_name("icon.png")

        # Основной контейнер
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.set_child(main_box)

        # Поля ввода и кнопка добавления в одной строке
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_box.set_margin_top(10)
        input_box.set_margin_start(10)
        input_box.set_margin_end(10)

        # Поле "Группа"
        band_box = Gtk.Box(spacing=6)
        band_label = Gtk.Label(label="Группа:")
        self.band_entry = Gtk.Entry()
        self.band_entry.set_hexpand(True)
        band_box.append(band_label)
        band_box.append(self.band_entry)
        input_box.append(band_box)

        # Поле "Альбом"
        album_box = Gtk.Box(spacing=6)
        album_label = Gtk.Label(label="Альбом:")
        self.album_entry = Gtk.Entry()
        self.album_entry.set_hexpand(True)
        album_box.append(album_label)
        album_box.append(self.album_entry)
        input_box.append(album_box)

        # Кнопка "Добавить"
        add_button = Gtk.Button(label="Добавить")
        add_button.connect("clicked", self.on_add_clicked)
        input_box.append(add_button)

        main_box.append(input_box)

        # Вкладки
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)
        main_box.append(self.notebook)

        # Вкладка CD
        cd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cd_scrolled = Gtk.ScrolledWindow()
        cd_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        cd_scrolled.set_min_content_height(200)
        self.cd_view = Gtk.TextView()
        self.cd_view.set_editable(False)
        self.cd_view.set_wrap_mode(Gtk.WrapMode.WORD)
        cd_scrolled.set_child(self.cd_view)
        cd_box.append(cd_scrolled)
        self.notebook.append_page(cd_box, Gtk.Label(label="Компакт-диски"))

        # Вкладка Vinyl
        vinyl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vinyl_scrolled = Gtk.ScrolledWindow()
        vinyl_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vinyl_scrolled.set_min_content_height(200)
        self.vinyl_view = Gtk.TextView()
        self.vinyl_view.set_editable(False)
        self.vinyl_view.set_wrap_mode(Gtk.WrapMode.WORD)
        vinyl_scrolled.set_child(self.vinyl_view)
        vinyl_box.append(vinyl_scrolled)
        self.notebook.append_page(vinyl_box, Gtk.Label(label="Винил"))

        # Нижняя панель с кнопками
        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_box.set_margin_bottom(10)
        save_box.set_margin_start(10)
        save_box.set_margin_end(10)

        # Кнопка сортировки
        sort_button = Gtk.Button(label="Сортировать")
        sort_button.connect("clicked", self.on_sort_clicked)
        save_box.append(sort_button)

        # Удаление
        delete_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        delete_label = Gtk.Label(label="Удалить №:")
        self.delete_entry = Gtk.Entry()
        self.delete_entry.set_width_chars(5)
        delete_button = Gtk.Button(label="Удалить")
        delete_button.connect("clicked", self.on_delete_clicked)
        delete_box.append(delete_label)
        delete_box.append(self.delete_entry)
        delete_box.append(delete_button)
        save_box.append(delete_box)

        # Кнопка сохранения
        save_button = Gtk.Button(label="Сохранить каталоги")
        save_button.connect("clicked", self.on_save_clicked)
        save_box.append(save_button)

        save_box.set_halign(Gtk.Align.END)
        main_box.append(save_box)

        self.window.present()
        GLib.idle_add(self.update_views)

    def add_cd(self, band, album, catalog, view):
        if not band or not album:
            self.show_message("Ошибка", "Введите название группы и альбома!")
            return
        
        if band not in catalog:
            catalog[band] = []
        
        if album not in catalog[band]:
            catalog[band].append(album)
            self.update_view(catalog, view)
        else:
            self.show_message("Предупреждение", "Этот альбом уже есть в каталоге!")

    def sort_catalog(self, catalog, view):
        sorted_catalog = dict(sorted(catalog.items()))
        catalog.clear()
        catalog.update(sorted_catalog)
        self.update_view(catalog, view)
        self.show_message("Успех", "Каталог отсортирован по группам!")

    def delete_entry(self, catalog, view, entry):
        try:
            index = int(entry.get_text().strip()) - 1  # Нумерация с 1
            if index < 0:
                raise ValueError("Номер должен быть положительным!")
            flat_list = [(band, album) for band in catalog for album in catalog[band]]
            if index >= len(flat_list):
                raise ValueError("Номер превышает количество записей!")
            band, album = flat_list[index]
            catalog[band].remove(album)
            if not catalog[band]:
                del catalog[band]
            self.update_view(catalog, view)
            self.show_message("Успех", f"Удалено: {band} - {album}")
            entry.set_text("")
        except ValueError as e:
            self.show_message("Ошибка", str(e) if str(e) else "Введите корректный номер записи!")
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при удалении: {e}")

    def update_view(self, catalog, view):
        buffer = view.get_buffer()
        if not catalog:
            buffer.set_text("Каталог пуст!")
            return
        
        text = "Каталог:\n" + "-" * 40 + "\n"
        index = 1
        for band in catalog:
            for album in catalog[band]:
                text += f"\n{index}. {band} - {album}\n"
                index += 1
        text += "-" * 40
        buffer.set_text(text)
        view.queue_draw()

    def update_views(self):
        if hasattr(self, 'cd_view') and hasattr(self, 'vinyl_view'):
            self.update_view(self.cd_catalog, self.cd_view)
            self.update_view(self.vinyl_catalog, self.vinyl_view)
        return False

    def save_catalog(self, catalog, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(catalog, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при сохранении {filename}: {e}")
            return False

    def load_catalog(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                self.show_message("Ошибка", f"Ошибка при загрузке {filename}: {e}")
                return {}
        return {}

    def on_add_clicked(self, button):
        band = self.band_entry.get_text().strip()
        album = self.album_entry.get_text().strip()
        current_page = self.notebook.get_current_page()
        
        if current_page == 0:  # CD вкладка
            self.add_cd(band, album, self.cd_catalog, self.cd_view)
        else:  # Vinyl вкладка
            self.add_cd(band, album, self.vinyl_catalog, self.vinyl_view)
        
        self.band_entry.set_text("")
        self.album_entry.set_text("")

    def on_sort_clicked(self, button):
        current_page = self.notebook.get_current_page()
        if current_page == 0:  # CD вкладка
            self.sort_catalog(self.cd_catalog, self.cd_view)
        else:  # Vinyl вкладка
            self.sort_catalog(self.vinyl_catalog, self.vinyl_view)

    def on_delete_clicked(self, button):
        current_page = self.notebook.get_current_page()
        if current_page == 0:  # CD вкладка
            self.delete_entry(self.cd_catalog, self.cd_view, self.delete_entry)
        else:  # Vinyl вкладка
            self.delete_entry(self.vinyl_catalog, self.vinyl_view, self.delete_entry)

    def on_save_clicked(self, button):
        cd_saved = self.save_catalog(self.cd_catalog, self.cd_filename)
        vinyl_saved = self.save_catalog(self.vinyl_catalog, self.vinyl_filename)
        if cd_saved and vinyl_saved:
            self.show_message("Успех", "Оба каталога успешно сохранены!")

    def show_message(self, title, message):
        dialog = Gtk.AlertDialog()
        dialog.set_buttons(["OK"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        dialog.set_message(title)
        dialog.set_detail(message)
        dialog.show(self.window)

    def run(self):
        self.app.run()

if __name__ == "__main__":
    app = CDCatalogApp()
    app.run()
