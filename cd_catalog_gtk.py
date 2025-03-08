#!/usr/bin/env python3

import json
import os
import warnings
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib

# Подавляем DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

class CDCatalogApp:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, "config.txt")
        self.tabs = self.load_config()
        self.app = Gtk.Application(application_id="com.example.CDCatalog")
        self.app.connect("activate", self.on_activate)

    def load_config(self):
        tabs = []
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if not lines:
                    raise ValueError("Файл config.txt пуст!")
                num_tabs = int(lines[0])
                if num_tabs < 1:
                    raise ValueError("Количество вкладок должно быть положительным!")
                if len(lines) - 1 < num_tabs:
                    raise ValueError(f"Указано {num_tabs} вкладок, но найдено только {len(lines) - 1} строк!")
                for line in lines[1:num_tabs + 1]:
                    parts = line.rsplit(maxsplit=1)
                    if len(parts) != 2:
                        raise ValueError(f"Неверный формат строки: '{line}'")
                    name, filename = parts
                    full_filename = os.path.join(self.base_dir, filename)
                    catalog = self.load_catalog(full_filename)
                    tabs.append({"name": name, "file": full_filename, "catalog": catalog})
            return tabs
        except FileNotFoundError:
            return [
                {"name": "Компакт-диски", "file": os.path.join(self.base_dir, "cd_catalog.json"), "catalog": {}},
                {"name": "Винил", "file": os.path.join(self.base_dir, "vinyl_catalog.json"), "catalog": {}},
                {"name": "Детские пластинки", "file": os.path.join(self.base_dir, "kids_catalog.json"), "catalog": {}}
            ]
        except Exception as e:
            print(f"Ошибка при чтении {self.config_file}: {e}")
            return [
                {"name": "Компакт-диски", "file": os.path.join(self.base_dir, "cd_catalog.json"), "catalog": {}},
                {"name": "Винил", "file": os.path.join(self.base_dir, "vinyl_catalog.json"), "catalog": {}},
                {"name": "Детские пластинки", "file": os.path.join(self.base_dir, "kids_catalog.json"), "catalog": {}}
            ]

    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("Каталог музыки")
        self.window.set_default_size(600, 1000)
                
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.set_child(main_box)

        # Верхняя панель с полями ввода
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_box.set_margin_top(10)
        input_box.set_margin_start(10)
        input_box.set_margin_end(10)

        band_box = Gtk.Box(spacing=6)
        band_label = Gtk.Label(label="Исполнитель:")
        self.band_entry = Gtk.Entry()
        self.band_entry.set_hexpand(True)
        self.band_entry.connect("changed", self.on_band_entry_changed)
        self.band_entry.connect("activate", self.on_band_entry_activate)

        # Popover для автодополнения
        self.popover = Gtk.Popover()
        self.popover.set_parent(self.band_entry)
        self.completion_listbox = Gtk.ListBox()
        self.completion_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.completion_listbox.connect("row-activated", self.on_completion_row_activated)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_width(300)
        scrolled.set_propagate_natural_height(True)
        scrolled.set_child(self.completion_listbox)
        self.popover.set_child(scrolled)

        band_box.append(band_label)
        band_box.append(self.band_entry)
        input_box.append(band_box)

        album_box = Gtk.Box(spacing=6)
        album_label = Gtk.Label(label="Альбом:")
        self.album_entry = Gtk.Entry()
        self.album_entry.set_hexpand(True)
        self.album_entry.connect("activate", self.on_band_entry_activate)
        album_box.append(album_label)
        album_box.append(self.album_entry)
        input_box.append(album_box)

        add_button = Gtk.Button(label="Добавить")
        add_button.connect("clicked", self.on_add_clicked)
        input_box.append(add_button)

        main_box.append(input_box)

        # Вкладки
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)
        self.notebook.connect("switch-page", self.on_page_switched)
        main_box.append(self.notebook)

        # Динамическое создание вкладок
        for tab in self.tabs:
            tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            tab_scrolled = Gtk.ScrolledWindow()
            tab_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            tab_scrolled.set_vexpand(True)
            tab["store"] = Gtk.ListStore(int, str, str)
            tab["treeview"] = Gtk.TreeView(model=tab["store"])
            tab["treeview"].set_headers_clickable(True)

            renderer = Gtk.CellRendererText()
            column_num = Gtk.TreeViewColumn("№", renderer, text=0)
            column_num.set_sort_column_id(0)
            tab["treeview"].append_column(column_num)
            
            column_band = Gtk.TreeViewColumn("Исполнитель", renderer, text=1)
            column_band.set_sort_column_id(1)
            tab["treeview"].append_column(column_band)
            
            column_album = Gtk.TreeViewColumn("Альбом", renderer, text=2)
            column_album.set_sort_column_id(2)
            tab["treeview"].append_column(column_album)

            tab_scrolled.set_child(tab["treeview"])
            tab_box.append(tab_scrolled)
            self.notebook.append_page(tab_box, Gtk.Label(label=tab["name"]))

        # Нижняя панель
        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_box.set_margin_bottom(10)
        save_box.set_margin_start(10)
        save_box.set_margin_end(10)

        sort_button = Gtk.Button(label="Сортировать")
        sort_button.connect("clicked", self.on_sort_clicked)
        save_box.append(sort_button)

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

        save_button = Gtk.Button(label="Сохранить каталоги")
        save_button.connect("clicked", self.on_save_clicked)
        save_box.append(save_button)

        save_box.set_halign(Gtk.Align.END)
        main_box.append(save_box)

        self.update_completion()
        self.window.present()
        GLib.idle_add(self.update_views)

    # Обновление TreeView
    def update_view(self, catalog, store):
        store.clear()
        index = 1
        for band in sorted(catalog.keys()):
            for album in catalog[band]:
                store.append([index, band, album])
                index += 1

    def update_views(self):
        for tab in self.tabs:
            if "store" in tab:
                self.update_view(tab["catalog"], tab["store"])
        GLib.idle_add(self.update_completion)
        return False

    # Обновление списка автодополнения в Popover
    def update_completion(self):
        current_page = self.notebook.get_current_page()
        catalog = self.tabs[current_page]["catalog"]
        
        # Очистка текущего списка
        while self.completion_listbox.get_first_child():
            self.completion_listbox.remove(self.completion_listbox.get_first_child())
        
        # Заполнение списка
        bands = sorted(catalog.keys())
        for band in bands:
            label = Gtk.Label(label=band)
            label.set_halign(Gtk.Align.START)
            self.completion_listbox.append(label)

        # Принудительно обновляем размер Popover
        if bands:
            self.completion_listbox.queue_resize()
            self.popover.queue_resize()

    # Реакция на ввод в поле исполнителя
    def on_band_entry_changed(self, entry):
        text = entry.get_text().strip().lower()
        if text:
            self.update_completion()
            child = self.completion_listbox.get_first_child()
            visible_count = 0
            while child:
                label = child.get_child()
                band = label.get_label().lower()
                is_visible = band.startswith(text)
                child.set_visible(is_visible)
                if is_visible:
                    visible_count += 1
                child = child.get_next_sibling()
            if visible_count > 0:
                self.popover.popup()
            else:
                self.popover.popdown()
        else:
            self.popover.popdown()

    # Выбор элемента из Popover
    def on_completion_row_activated(self, listbox, row):
        label = row.get_child()
        self.band_entry.set_text(label.get_label())
        self.popover.popdown()
        self.album_entry.grab_focus()

    # Нажатие Enter в любом поле ввода
    def on_band_entry_activate(self, entry):
        self.on_add_clicked(None)

    def add_cd(self, band, album, catalog, store):
        if not band or not album:
            self.show_message("Ошибка", "Введите название исполнителя и альбома!")
            return
        if band not in catalog:
            catalog[band] = []
        if album not in catalog[band]:
            catalog[band].append(album)
            self.update_view(catalog, store)
            GLib.idle_add(self.update_completion)

    def sort_catalog(self, catalog, store):
        sorted_catalog = dict(sorted(catalog.items()))
        catalog.clear()
        catalog.update(sorted_catalog)
        self.update_view(catalog, store)
        self.show_message("Успех", "Каталог отсортирован по исполнителям!")
        GLib.idle_add(self.update_completion)

    def remove_entry(self, catalog, store, entry):
        try:
            index = int(entry.get_text().strip()) - 1
            if index < 0:
                raise ValueError("Номер должен быть положительным!")
            flat_list = [(band, album) for band in catalog for album in catalog[band]]
            if index >= len(flat_list):
                raise ValueError("Номер превышает количество записей!")
            band, album = flat_list[index]
            catalog[band].remove(album)
            if not catalog[band]:
                del catalog[band]
            self.update_view(catalog, store)
            self.show_message("Успех", f"Удалено: {band} - {album}")
            entry.set_text("")
            GLib.idle_add(self.update_completion)
        except ValueError as e:
            self.show_message("Ошибка", str(e) if str(e) else "Введите корректный номер записи!")
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при удалении: {e}")

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
                    return json.load(f)
            except Exception as e:
                self.show_message("Ошибка", f"Ошибка при загрузке {filename}: {e}")
                return {}
        return {}

    def on_add_clicked(self, button):
        band = self.band_entry.get_text().strip()
        album = self.album_entry.get_text().strip()
        current_page = self.notebook.get_current_page()
        tab = self.tabs[current_page]
        self.add_cd(band, album, tab["catalog"], tab["store"])
        self.band_entry.set_text("")
        self.album_entry.set_text("")

    def on_sort_clicked(self, button):
        current_page = self.notebook.get_current_page()
        tab = self.tabs[current_page]
        self.sort_catalog(tab["catalog"], tab["store"])

    def on_delete_clicked(self, button):
        current_page = self.notebook.get_current_page()
        tab = self.tabs[current_page]
        self.remove_entry(tab["catalog"], tab["store"], self.delete_entry)

    def on_save_clicked(self, button):
        all_saved = True
        for tab in self.tabs:
            if not self.save_catalog(tab["catalog"], tab["file"]):
                all_saved = False
        if all_saved:
            self.show_message("Успех", "Все каталоги успешно сохранены!")

    def on_page_switched(self, notebook, page, page_num):
        GLib.idle_add(self.update_completion)
        self.popover.popdown()

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
    # Создаём config.txt, если его нет
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.txt")
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("3\n")
            f.write("Компакт-диски cd_catalog.json\n")
            f.write("Винил vinyl_catalog.json\n")
            f.write("Детские пластинки kids_catalog.json\n")
    app = CDCatalogApp()
    app.run()
