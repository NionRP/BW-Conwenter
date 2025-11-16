import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import sys

class PNGToBWConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер PNG в черно-белое")
        self.root.geometry("700x600")
        
        # Хранилище для выбранных элементов
        self.selected_items = {}  # {item_id: {'path': path, 'type': 'folder'/'file', 'parent': parent_id}}
        self.item_counter = 0
        
        # Проверяем наличие Pillow
        if not self.check_dependencies():
            return
            
        self.create_widgets()
        
    def check_dependencies(self):
        try:
            from PIL import Image
            return True
        except ImportError:
            self.show_install_instructions()
            return False
            
    def show_install_instructions(self):
        instructions = """
Для работы программы необходимо установить библиотеку Pillow.

Как установить:

1. Откройте командную строку (Win+R, введите cmd)
2. Введите команду: pip install Pillow
3. Нажмите Enter и дождитесь установки
4. Перезапустите программу

Или установите через PyCharm/VSCode:
- PyCharm: File → Settings → Python Interpreter → + → Pillow
- VSCode: Откройте терминал → pip install Pillow
        """
        
        text = tk.Text(self.root, height=20, width=70, wrap=tk.WORD)
        text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        text.insert(tk.END, instructions)
        text.config(state=tk.DISABLED)
        
    def create_widgets(self):
        # Фрейм для выбора папки
        frame_select = ttk.Frame(self.root)
        frame_select.pack(pady=10, padx=10, fill=tk.X)
        
        self.btn_select = ttk.Button(
            frame_select, 
            text="Выбрать папку", 
            command=self.select_folder
        )
        self.btn_select.pack(side=tk.LEFT, padx=(0, 10))
        
        self.label_path = ttk.Label(frame_select, text="Папка не выбрана")
        self.label_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Фрейм для списка конвертации
        frame_list = ttk.LabelFrame(self.root, text="Список для конвертации")
        frame_list.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # Создаем Treeview для отображения древовидной структуры
        self.tree = ttk.Treeview(frame_list, columns=('type',), show='tree')
        self.tree.heading('#0', text='Файлы и папки')
        self.tree.column('#0', width=400)
        self.tree.heading('type', text='Тип')
        self.tree.column('type', width=100)
        
        # Scrollbar для Treeview
        tree_scroll = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем двойной клик для удаления
        self.tree.bind('<Double-1>', self.remove_item)
        
        # Фрейм для прогрессбара
        frame_progress = ttk.Frame(self.root)
        frame_progress.pack(pady=5, padx=10, fill=tk.X)
        
        self.progress = ttk.Progressbar(
            frame_progress, 
            mode='determinate'
        )
        self.progress.pack(fill=tk.X)
        
        # Текстовое поле для логов
        frame_log = ttk.LabelFrame(self.root, text="Логи выполнения")
        frame_log.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        self.text_log = tk.Text(frame_log, height=10, width=70)
        log_scroll = ttk.Scrollbar(frame_log, orient="vertical", command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=log_scroll.set)
        
        self.text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Фрейм для кнопок
        frame_buttons = ttk.Frame(self.root)
        frame_buttons.pack(pady=5, padx=10, fill=tk.X)
        
        self.btn_convert = ttk.Button(
            frame_buttons, 
            text="Начать конвертацию", 
            command=self.start_conversion,
            state=tk.DISABLED
        )
        self.btn_convert.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_clear_all = ttk.Button(
            frame_buttons,
            text="Очистить все",
            command=self.clear_all,
            state=tk.DISABLED
        )
        self.btn_clear_all.pack(side=tk.LEFT)
        
    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.add_folder_to_list(folder_selected)
            
    def add_folder_to_list(self, folder_path):
        """Добавляет папку и все PNG файлы в древовидный список"""
        folder_name = os.path.basename(folder_path)
        
        # Добавляем папку в дерево
        folder_id = self.tree.insert('', 'end', text=folder_name, values=('Папка',))
        self.item_counter += 1
        self.selected_items[folder_id] = {
            'path': folder_path,
            'type': 'folder',
            'parent': None
        }
        
        # Рекурсивно добавляем все PNG файлы
        self.add_png_files_recursive(folder_path, folder_id)
        
        # Обновляем состояние кнопок
        self.update_buttons_state()
        
    def add_png_files_recursive(self, folder_path, parent_id):
        """Рекурсивно добавляет PNG файлы из папки и подпапок"""
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                
                if os.path.isdir(item_path):
                    # Если это папка, добавляем её и рекурсивно её содержимое
                    subfolder_id = self.tree.insert(parent_id, 'end', text=item, values=('Папка',))
                    self.item_counter += 1
                    self.selected_items[subfolder_id] = {
                        'path': item_path,
                        'type': 'folder',
                        'parent': parent_id
                    }
                    self.add_png_files_recursive(item_path, subfolder_id)
                    
                elif item.lower().endswith('.png'):
                    # Если это PNG файл, добавляем его
                    file_id = self.tree.insert(parent_id, 'end', text=item, values=('Файл',))
                    self.item_counter += 1
                    self.selected_items[file_id] = {
                        'path': item_path,
                        'type': 'file',
                        'parent': parent_id
                    }
                    
        except PermissionError:
            self.log(f"Ошибка доступа к папке: {folder_path}")
            
    def remove_item(self, event):
        """Удаляет выбранный элемент по двойному клику"""
        selected = self.tree.selection()
        if selected:
            item_id = selected[0]
            self.remove_item_recursive(item_id)
            self.update_buttons_state()
            
    def remove_item_recursive(self, item_id):
        """Рекурсивно удаляет элемент и всех его потомков"""
        # Сначала удаляем всех детей
        children = self.tree.get_children(item_id)
        for child_id in children:
            self.remove_item_recursive(child_id)
            
        # Затем удаляем сам элемент
        if item_id in self.selected_items:
            del self.selected_items[item_id]
        self.tree.delete(item_id)
        
    def clear_all(self):
        """Очищает весь список"""
        for item_id in self.tree.get_children():
            self.remove_item_recursive(item_id)
        self.update_buttons_state()
        
    def update_buttons_state(self):
        """Обновляет состояние кнопок в зависимости от наличия элементов"""
        has_items = len(self.selected_items) > 0
        self.btn_convert.config(state=tk.NORMAL if has_items else tk.DISABLED)
        self.btn_clear_all.config(state=tk.NORMAL if has_items else tk.DISABLED)
        
    def log(self, message):
        self.text_log.insert(tk.END, message + "\n")
        self.text_log.see(tk.END)
        self.root.update_idletasks()
        
    def get_all_png_files(self):
        """Получает все PNG файлы из выбранных элементов"""
        png_files = []
        for item_id, item_data in self.selected_items.items():
            if item_data['type'] == 'file':
                png_files.append(item_data['path'])
            elif item_data['type'] == 'folder':
                # Для папок рекурсивно ищем все PNG файлы
                png_files.extend(self.find_png_files(item_data['path']))
        return png_files
        
    def find_png_files(self, folder):
        """Рекурсивно ищет все PNG файлы в папке"""
        png_files = []
        try:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.png'):
                        png_files.append(os.path.join(root, file))
        except PermissionError:
            self.log(f"Ошибка доступа при поиске в папке: {folder}")
        return png_files
        
    def convert_to_bw(self, file_path):
        try:
            from PIL import Image
            
            # Открываем изображение
            with Image.open(file_path) as img:
                # Сохраняем исходные размеры
                original_size = img.size
                original_mode = img.mode
                
                self.log(f"  Размер: {original_size}, Режим: {original_mode}")
                
                # Если изображение уже в оттенках серого, просто сохраняем как есть
                if original_mode == 'L':
                    self.log(f"  Уже в оттенках серого, пропускаем")
                    return True
                
                # Конвертируем в RGBA чтобы работать с прозрачностью
                if original_mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Создаем новое изображение с теми же размерами и прозрачностью
                bw_img = Image.new('RGBA', original_size, (0, 0, 0, 0))
                
                # Проходим по всем пикселям
                for x in range(original_size[0]):
                    for y in range(original_size[1]):
                        r, g, b, a = img.getpixel((x, y))
                        
                        # Если пиксель прозрачный, оставляем его прозрачным
                        if a == 0:
                            bw_img.putpixel((x, y), (0, 0, 0, 0))
                        else:
                            # Конвертируем цветные пиксели в оттенки серого
                            # Используем стандартную формулу для преобразования RGB в grayscale
                            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                            bw_img.putpixel((x, y), (gray, gray, gray, a))
                
                # Сохраняем с теми же параметрами что и исходное изображение
                bw_img.save(file_path, 'PNG')
                
                # Проверяем что размер не изменился
                with Image.open(file_path) as check_img:
                    if check_img.size != original_size:
                        self.log(f"  ПРЕДУПРЕЖДЕНИЕ: Размер изменился! Было: {original_size}, Стало: {check_img.size}")
                
            return True
            
        except Exception as e:
            self.log(f"Ошибка при обработке {file_path}: {str(e)}")
            return False
            
    def start_conversion(self):
        if not self.selected_items:
            messagebox.showerror("Ошибка", "Сначала выберите папки или файлы!")
            return
            
        # Запускаем в отдельном потоке чтобы не блокировать GUI
        thread = threading.Thread(target=self.convert_files)
        thread.daemon = True
        thread.start()
        
    def convert_files(self):
        self.btn_select.config(state=tk.DISABLED)
        self.btn_convert.config(state=tk.DISABLED)
        self.btn_clear_all.config(state=tk.DISABLED)
        
        try:
            self.log("Поиск PNG файлов...")
            png_files = self.get_all_png_files()
            
            if not png_files:
                self.log("PNG файлы не найдены!")
                return
                
            self.log(f"Найдено {len(png_files)} PNG файлов")
            self.progress['maximum'] = len(png_files)
            
            successful = 0
            for i, file_path in enumerate(png_files):
                self.log(f"Обработка: {os.path.basename(file_path)}")
                if self.convert_to_bw(file_path):
                    successful += 1
                self.progress['value'] = i + 1
                self.root.update_idletasks()
                
            self.log(f"Готово! Успешно обработано: {successful}/{len(png_files)} файлов")
            messagebox.showinfo("Готово", f"Обработано {successful}/{len(png_files)} файлов")
            
        except Exception as e:
            self.log(f"Критическая ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
        finally:
            self.btn_select.config(state=tk.NORMAL)
            self.update_buttons_state()
            self.progress['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = PNGToBWConverter(root)
    root.mainloop()