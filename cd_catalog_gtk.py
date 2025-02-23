#!/usr/bin/env python3

import json
import os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib

class CDCatalogApp:
    def __init__(self):
        # Инициализация путей к файлам каталогов
        self.cd_filename = "cd_catalog.json"  # Файл для хранения каталога компакт-дисков
        self.vinyl_filename = "vinyl_catalog.json"  # Файл для хранения каталога виниловых пластинок
        self.cd_catalog = self.load_catalog(self.cd_filename)  # Загружаем каталог CD
        self.vinyl_catalog = self.load_catalog(self.vinyl_filename)  # Загружаем каталог Vinyl

        # Создание приложения GTK с уникальным идентификатором
        self.app = Gtk.Application(application_id="org.example.cdcatalog")
        self.app.connect("activate", self.on_activate)  # Подключаем обработчик активации окна

    def on_activate(self, app):
        # Создание главного окна приложения
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("Каталог музыки")  # Устанавливаем заголовок окна
        self.window.set_default_size(600, 1000)  # Задаём начальный размер окна
        self.window.set_icon_name("icon.png")

        # Основной контейнер с вертикальной ориентацией
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.set_child(main_box)  # Устанавливаем main_box как содержимое окна

        # Верхняя панель с полями ввода и кнопкой "Добавить"
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_box.set_margin_top(10)  # Отступ сверху
        input_box.set_margin_start(10)  # Отступ слева
        input_box.set_margin_end(10)  # Отступ справа

        # Контейнер для поля ввода группы
        band_box = Gtk.Box(spacing=6)
        band_label = Gtk.Label(label="Группа:")  # Метка "Группа:"
        self.band_store = Gtk.StringList.new([])  # Базовая модель для списка групп
        self.band_filter = Gtk.StringFilter.new(Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
        self.band_filter.set_match_mode(Gtk.StringFilterMatchMode.PREFIX)  # Фильтр по началу строки
        self.band_filtered_model = Gtk.FilterListModel.new(self.band_store, self.band_filter)  # Фильтрованная модель
        self.band_dropdown = Gtk.DropDown(model=self.band_filtered_model)  # Выпадающий список групп
        self.band_dropdown.set_hexpand(True)  # Растягиваем по горизонтали
        self.band_dropdown.set_show_arrow(True)  # Показываем стрелку
        self.band_dropdown.connect("notify::selected", self.on_band_selected)  # Подключаем обработчик выбора
        self.band_entry = Gtk.Entry()  # Поле ввода для группы
        self.band_entry.set_hexpand(True)  # Растягиваем по горизонтали
        self.band_entry_handler = self.band_entry.connect("changed", self.on_band_entry_changed)  # Обработчик ввода текста
        band_box.append(band_label)
        band_box.append(self.band_dropdown)
        band_box.append(self.band_entry)
        input_box.append(band_box)

        # Контейнер для поля ввода альбома
        album_box = Gtk.Box(spacing=6)
        album_label = Gtk.Label(label="Альбом:")  # Метка "Альбом:"
        self.album_entry = Gtk.Entry()  # Поле ввода для альбома
        self.album_entry.set_hexpand(True)  # Растягиваем по горизонтали
        album_box.append(album_label)
        album_box.append(self.album_entry)
        input_box.append(album_box)

        # Кнопка "Добавить"
        add_button = Gtk.Button(label="Добавить")
        add_button.connect("clicked", self.on_add_clicked)  # Подключаем обработчик добавления записи
        input_box.append(add_button)

        main_box.append(input_box)  # Добавляем верхнюю панель в основной контейнер

        # Вкладки для отображения записей
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)  # Растягиваем по вертикали для заполнения пространства
        self.notebook.connect("switch-page", self.on_page_switched)  # Обработчик смены вкладок
        main_box.append(self.notebook)

        # Вкладка "Компакт-диски"
        cd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cd_scrolled = Gtk.ScrolledWindow()
        cd_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)  # Автоматическая прокрутка
        cd_scrolled.set_vexpand(True)  # Растягиваем по вертикали
        self.cd_view = Gtk.TextView()  # Текстовое поле для отображения записей CD
        self.cd_view.set_editable(False)  # Запрещаем редактирование
        self.cd_view.set_wrap_mode(Gtk.WrapMode.WORD)  # Перенос по словам
        cd_scrolled.set_child(self.cd_view)
        cd_box.append(cd_scrolled)
        self.notebook.append_page(cd_box, Gtk.Label(label="Компакт-диски"))  # Добавляем вкладку

        # Вкладка "Винил"
        vinyl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vinyl_scrolled = Gtk.ScrolledWindow()
        vinyl_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)  # Автоматическая прокрутка
        vinyl_scrolled.set_vexpand(True)  # Растягиваем по вертикали
        self.vinyl_view = Gtk.TextView()  # Текстовое поле для отображения записей Vinyl
        self.vinyl_view.set_editable(False)  # Запрещаем редактирование
        self.vinyl_view.set_wrap_mode(Gtk.WrapMode.WORD)  # Перенос по словам
        vinyl_scrolled.set_child(self.vinyl_view)
        vinyl_box.append(vinyl_scrolled)
        self.notebook.append_page(vinyl_box, Gtk.Label(label="Винил"))  # Добавляем вкладку

        # Нижняя панель с кнопками управления
        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_box.set_margin_bottom(10)  # Отступ снизу
        save_box.set_margin_start(10)  # Отступ слева
        save_box.set_margin_end(10)  # Отступ справа

        # Кнопка "Сортировать"
        sort_button = Gtk.Button(label="Сортировать")
        sort_button.connect("clicked", self.on_sort_clicked)  # Подключаем обработчик сортировки
        save_box.append(sort_button)

        # Контейнер для удаления записи
        delete_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        delete_label = Gtk.Label(label="Удалить №:")  # Метка для поля номера записи
        self.delete_entry = Gtk.Entry()  # Поле ввода номера записи для удаления
        self.delete_entry.set_width_chars(5)  # Ограничиваем ширину поля
        delete_button = Gtk.Button(label="Удалить")
        delete_button.connect("clicked", self.on_delete_clicked)  # Подключаем обработчик удаления
        delete_box.append(delete_label)
        delete_box.append(self.delete_entry)
        delete_box.append(delete_button)
        save_box.append(delete_box)

        # Кнопка "Экспорт в TXT"
        export_button = Gtk.Button(label="Экспорт в TXT")
        export_button.connect("clicked", self.on_export_clicked)  # Подключаем обработчик экспорта
        save_box.append(export_button)

        # Кнопка "Сохранить каталоги"
        save_button = Gtk.Button(label="Сохранить каталоги")
        save_button.connect("clicked", self.on_save_clicked)  # Подключаем обработчик сохранения
        save_box.append(save_button)

        save_box.set_halign(Gtk.Align.END)  # Выравниваем кнопки вправо
        main_box.append(save_box)  # Добавляем нижнюю панель в основной контейнер

        self.update_dropdown()  # Обновляем выпадающий список групп
        self.window.present()  # Показываем окно
        GLib.idle_add(self.update_views)  # Асинхронно обновляем отображение записей

    # Обновление списка групп в DropDown
    def update_dropdown(self):
        current_page = self.notebook.get_current_page()  # Получаем номер текущей вкладки
        catalog = self.cd_catalog if current_page == 0 else self.vinyl_catalog  # Выбираем каталог
        bands = sorted(catalog.keys())  # Получаем отсортированный список групп
        GLib.idle_add(self._update_dropdown_model, bands or [""])  # Асинхронно обновляем модель
        print(f"Updated dropdown for page {current_page}: {bands}")

    # Асинхронное обновление модели DropDown
    def _update_dropdown_model(self, bands):
        self.band_store.splice(0, self.band_store.get_n_items(), bands)  # Заменяем содержимое модели
        self.band_filter.set_search("")  # Сбрасываем фильтр

    # Обработчик изменения текста в поле ввода группы
    def on_band_entry_changed(self, entry):
        text = entry.get_text().strip()  # Получаем введённый текст
        GLib.idle_add(self._apply_filter, text)  # Асинхронно применяем фильтр
        print(f"Filter set to: {text}")

    # Асинхронное применение фильтра к списку групп
    def _apply_filter(self, text):
        self.band_filter.set_search(text)  # Устанавливаем фильтр по введённому тексту

    # Обработчик выбора группы из DropDown
    def on_band_selected(self, dropdown, pspec):
        selected = dropdown.get_selected()  # Получаем индекс выбранного элемента
        print(f"Selected index: {selected}")
        if selected != Gtk.INVALID_LIST_POSITION:  # Если выбор валиден
            band = dropdown.get_model().get_item(selected).get_string()  # Получаем название группы
            print(f"Selected band: {band}")
            if band and band != "":
                GLib.idle_add(self._set_band_entry_text, band)  # Асинхронно устанавливаем текст

    # Асинхронная установка текста в поле ввода группы
    def _set_band_entry_text(self, band):
        self.band_entry.handler_block(self.band_entry_handler)  # Блокируем сигнал changed
        self.band_entry.set_text(band)  # Устанавливаем текст
        self.band_entry.handler_unblock(self.band_entry_handler)  # Разблокируем сигнал

    # Добавление записи в каталог
    def add_cd(self, band, album, catalog, view):
        if not band or not album:  # Проверка на пустые поля
            self.show_message("Ошибка", "Введите название группы и альбома!")
            return
        
        if band not in catalog:  # Если группы нет, создаём новый список
            catalog[band] = []
        
        if album not in catalog[band]:  # Если альбом не существует, добавляем его
            catalog[band].append(album)
            self.update_view(catalog, view)  # Обновляем отображение
            GLib.idle_add(self.update_dropdown)  # Асинхронно обновляем DropDown

    # Сортировка каталога по группам
    def sort_catalog(self, catalog, view):
        sorted_catalog = dict(sorted(catalog.items()))  # Сортируем группы
        catalog.clear()  # Очищаем текущий каталог
        catalog.update(sorted_catalog)  # Обновляем отсортированным
        self.update_view(catalog, view)  # Обновляем отображение
        self.show_message("Успех", "Каталог отсортирован по группам!")
        GLib.idle_add(self.update_dropdown)  # Асинхронно обновляем DropDown

    # Удаление записи из каталога
    def remove_entry(self, catalog, view, entry):
        try:
            index = int(entry.get_text().strip()) - 1  # Получаем индекс записи (нумерация с 1)
            if index < 0:
                raise ValueError("Номер должен быть положительным!")
            flat_list = [(band, album) for band in catalog for album in catalog[band]]  # Преобразуем каталог в плоский список
            if index >= len(flat_list):
                raise ValueError("Номер превышает количество записей!")
            band, album = flat_list[index]  # Получаем группу и альбом по индексу
            catalog[band].remove(album)  # Удаляем альбом
            if not catalog[band]:  # Если группа осталась без альбомов, удаляем её
                del catalog[band]
            self.update_view(catalog, view)  # Обновляем отображение
            self.show_message("Успех", f"Удалено: {band} - {album}")
            entry.set_text("")  # Очищаем поле ввода номера
            GLib.idle_add(self.update_dropdown)  # Асинхронно обновляем DropDown
        except ValueError as e:
            self.show_message("Ошибка", str(e) if str(e) else "Введите корректный номер записи!")
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при удалении: {e}")

    # Экспорт каталога в текстовый файл
    def export_to_txt(self, catalog, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:  # Открываем файл для записи
                if not catalog:
                    f.write("Каталог пуст!\n")
                else:
                    f.write("Каталог:\n" + "-" * 40 + "\n")
                    index = 1
                    for band in catalog:
                        for album in catalog[band]:
                            f.write(f"{index}. {band} - {album}\n")  # Записываем номер, группу и альбом
                            index += 1
                    f.write("-" * 40 + "\n")
            self.show_message("Успех", f"Каталог экспортирован в {filename}")
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при экспорте: {e}")

    # Обновление текстового отображения каталога
    def update_view(self, catalog, view):
        buffer = view.get_buffer()  # Получаем буфер текста
        if not catalog:
            buffer.set_text("Каталог пуст!")  # Если каталог пуст, показываем сообщение
            return
        
        text = "Каталог:\n" + "-" * 40 + "\n"
        index = 1
        for band in catalog:
            for album in catalog[band]:
                text += f"\n{index}. {band} - {album}\n"  # Формируем список записей с номерами
                index += 1
        text += "-" * 40
        buffer.set_text(text)  # Устанавливаем текст в буфер
        view.queue_draw()  # Перерисовываем виджет

    # Асинхронное обновление отображения обеих вкладок
    def update_views(self):
        if hasattr(self, 'cd_view') and hasattr(self, 'vinyl_view'):
            self.update_view(self.cd_catalog, self.cd_view)  # Обновляем CD
            self.update_view(self.vinyl_catalog, self.vinyl_view)  # Обновляем Vinyl
        GLib.idle_add(self.update_dropdown)  # Асинхронно обновляем DropDown
        return False  # Возвращаем False для завершения idle_add

    # Сохранение каталога в JSON-файл
    def save_catalog(self, catalog, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:  # Открываем файл для записи
                json.dump(catalog, f, ensure_ascii=False, indent=4)  # Сохраняем каталог в JSON
            return True
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при сохранении {filename}: {e}")
            return False

    # Загрузка каталога из JSON-файла
    def load_catalog(self, filename):
        if os.path.exists(filename):  # Проверяем, существует ли файл
            try:
                with open(filename, 'r', encoding='utf-8') as f:  # Открываем файл для чтения
                    data = json.load(f)  # Загружаем данные
                    return data
            except Exception as e:
                self.show_message("Ошибка", f"Ошибка при загрузке {filename}: {e}")
                return {}
        return {}  # Возвращаем пустой словарь, если файла нет

    # Обработчик нажатия кнопки "Добавить"
    def on_add_clicked(self, button):
        band = self.band_entry.get_text().strip()  # Получаем название группы
        album = self.album_entry.get_text().strip()  # Получаем название альбома
        current_page = self.notebook.get_current_page()  # Получаем текущую вкладку
        
        if current_page == 0:
            self.add_cd(band, album, self.cd_catalog, self.cd_view)  # Добавляем в CD
        else:
            self.add_cd(band, album, self.vinyl_catalog, self.vinyl_view)  # Добавляем в Vinyl
        
        self.band_entry.set_text("")  # Очищаем поле группы
        self.album_entry.set_text("")  # Очищаем поле альбома

    # Обработчик нажатия кнопки "Сортировать"
    def on_sort_clicked(self, button):
        current_page = self.notebook.get_current_page()
        if current_page == 0:
            self.sort_catalog(self.cd_catalog, self.cd_view)  # Сортируем CD
        else:
            self.sort_catalog(self.vinyl_catalog, self.vinyl_view)  # Сортируем Vinyl

    # Обработчик нажатия кнопки "Удалить"
    def on_delete_clicked(self, button):
        current_page = self.notebook.get_current_page()
        if current_page == 0:
            self.remove_entry(self.cd_catalog, self.cd_view, self.delete_entry)  # Удаляем из CD
        else:
            self.remove_entry(self.vinyl_catalog, self.vinyl_view, self.delete_entry)  # Удаляем из Vinyl

    # Обработчик нажатия кнопки "Экспорт в TXT"
    def on_export_clicked(self, button):
        current_page = self.notebook.get_current_page()
        if current_page == 0:
            self.export_to_txt(self.cd_catalog, "cd_catalog.txt")  # Экспортируем CD
        else:
            self.export_to_txt(self.vinyl_catalog, "vinyl_catalog.txt")  # Экспортируем Vinyl

    # Обработчик нажатия кнопки "Сохранить каталоги"
    def on_save_clicked(self, button):
        cd_saved = self.save_catalog(self.cd_catalog, self.cd_filename)  # Сохраняем CD
        vinyl_saved = self.save_catalog(self.vinyl_catalog, self.vinyl_filename)  # Сохраняем Vinyl
        if cd_saved and vinyl_saved:
            self.show_message("Успех", "Оба каталога успешно сохранены!")

    # Обработчик переключения вкладок
    def on_page_switched(self, notebook, page, page_num):
        GLib.idle_add(self.update_dropdown)  # Асинхронно обновляем DropDown при смене вкладки

    # Отображение диалогового окна с сообщением
    def show_message(self, title, message):
        dialog = Gtk.AlertDialog()
        dialog.set_buttons(["OK"])  # Устанавливаем кнопку "OK"
        dialog.set_default_button(0)  # Делаем "OK" кнопкой по умолчанию
        dialog.set_cancel_button(0)  # Назначаем "OK" как кнопку отмены
        dialog.set_message(title)  # Заголовок сообщения
        dialog.set_detail(message)  # Текст сообщения
        dialog.show(self.window)  # Показываем диалог

    # Запуск приложения
    def run(self):
        self.app.run()

if __name__ == "__main__":
    app = CDCatalogApp()
    app.run()  # Запускаем приложение
