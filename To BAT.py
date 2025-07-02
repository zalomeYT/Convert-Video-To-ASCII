import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import platform
import random
import string

class VideoToASCII:
    def __init__(self):
        # Расширенный набор ASCII символов для более разнообразного вывода
        self.ascii_chars = string.printable[:-6]  # Исключаем невидимые символы
        # Добавляем дополнительные символы для лучшего представления
        self.ascii_chars += "█▉▊▋▌▍▎▏▐░▒▓■□▪▫▬▭▮▯"
        
        # ANSI цвета для терминала - только оттенки серого
        self.colors = [
            '\033[30m',  # Черный
            '\033[90m',  # Темно-серый
            '\033[37m',  # Светло-серый
            '\033[97m',  # Белый
        ]
        self.reset_color = '\033[0m'
    
    def get_video_file(self):
        """Открывает диалог выбора видео файла"""
        root = tk.Tk()
        root.withdraw()  # Скрываем главное окно
        
        file_path = filedialog.askopenfilename(
            title="Выберите видео файл",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("Все файлы", "*.*")
            ]
        )
        
        root.destroy()
        return file_path
    
    def pixel_to_ascii(self, pixel_value, use_random=True):
        """Конвертирует значение пикселя в ASCII символ"""
        if use_random:
            # Используем случайный символ с весом, основанным на яркости
            index = min(int(pixel_value / 255 * len(self.ascii_chars)), len(self.ascii_chars) - 1)
            # Добавляем элемент случайности
            random_offset = random.randint(-2, 2)
            index = max(0, min(len(self.ascii_chars) - 1, index + random_offset))
            return self.ascii_chars[index]
        else:
            # Традиционный подход
            index = int(pixel_value / 255 * (len(self.ascii_chars) - 1))
            return self.ascii_chars[index]
    
    def get_color_from_pixel(self, bgr_pixel):
        """Определяет ANSI цвет на основе BGR значений пикселя - только оттенки серого"""
        b, g, r = bgr_pixel

        # Вычисляем яркость пикселя
        brightness = int(0.299 * r + 0.587 * g + 0.114 * b)

        # Выбираем цвет на основе яркости
        if brightness < 64:
            return self.colors[0]  # Черный
        elif brightness < 128:
            return self.colors[1]  # Темно-серый
        elif brightness < 192:
            return self.colors[2]  # Светло-серый
        else:
            return self.colors[3]  # Белый
    
    def frame_to_ascii(self, frame, width=120, height=30, use_colors=True, use_random=True):
        """Конвертирует кадр в ASCII с цветами"""
        # Изменяем размер кадра
        frame_resized = cv2.resize(frame, (width, height))
        
        # Конвертируем в оттенки серого для определения яркости
        gray_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        ascii_frame = []
        for y in range(height):
            row = ""
            for x in range(width):
                pixel_value = gray_frame[y, x]
                ascii_char = self.pixel_to_ascii(pixel_value, use_random)
                
                if use_colors:
                    color = self.get_color_from_pixel(frame_resized[y, x])
                    row += color + ascii_char + self.reset_color
                else:
                    row += ascii_char
            
            ascii_frame.append(row)
        
        return ascii_frame
    
    def create_bat_file(self, video_path, frames_ascii, fps=10):
        """Создает BAT файл для воспроизведения ASCII анимации"""
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(os.path.dirname(video_path), f"{video_name}_ascii")
        
        # Создаем папку для вывода
        os.makedirs(output_dir, exist_ok=True)
        
        bat_filename = os.path.join(output_dir, f"{video_name}_ascii.bat")
        
        with open(bat_filename, 'w', encoding='utf-8') as bat_file:
            # Заголовок BAT файла
            bat_file.write("@echo off\n")
            bat_file.write("chcp 65001 >nul\n")  # Устанавливаем UTF-8 кодировку
            bat_file.write("cls\n")
            bat_file.write("title ASCII Video Player - " + video_name + "\n")
            bat_file.write("mode con cols=150 lines=40\n")  # Устанавливаем размер окна
            
            # Включаем поддержку ANSI цветов в Windows
            bat_file.write("reg add HKCU\\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1\n")
            
            # Основной цикл воспроизведения
            bat_file.write(":loop\n")
            
            delay = max(1, int(1000 / fps))  # Задержка в миллисекундах
            
            for i, frame in enumerate(frames_ascii):
                bat_file.write("cls\n")
                bat_file.write(f"echo Frame {i+1}/{len(frames_ascii)}: {video_name}\n")
                bat_file.write("echo.\n")
                
                for line in frame:
                    # Экранируем специальные символы для BAT
                    escaped_line = line.replace("&", "^&").replace("<", "^<").replace(">", "^>").replace("|", "^|")
                    bat_file.write(f"echo {escaped_line}\n")
                
                bat_file.write("echo.\n")
                bat_file.write("echo Нажмите Ctrl+C для выхода\n")
                
                # Добавляем задержку
                if delay > 0:
                    bat_file.write(f"timeout /t 0 /nobreak >nul\n")
                    bat_file.write(f"ping localhost -n 1 -w {delay} >nul\n")
            
            bat_file.write("goto loop\n")
            bat_file.write("pause\n")
        
        return bat_filename, output_dir
    
    def process_video(self, video_path, max_frames=300, width=120, height=30, fps=10):
        """Обрабатывает видео и конвертирует в ASCII"""
        print(f"Обработка видео: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Не удалось открыть видео файл")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Общее количество кадров: {total_frames}")
        print(f"Оригинальный FPS: {original_fps}")
        
        # Ограничиваем количество кадров для производительности
        frames_to_process = min(max_frames, total_frames)
        frame_step = max(1, total_frames // frames_to_process)
        
        frames_ascii = []
        frame_count = 0
        processed_frames = 0
        
        while cap.isOpened() and processed_frames < frames_to_process:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_step == 0:
                ascii_frame = self.frame_to_ascii(frame, width, height, use_colors=True, use_random=True)
                frames_ascii.append(ascii_frame)
                processed_frames += 1
                
                if processed_frames % 10 == 0:
                    print(f"Обработано кадров: {processed_frames}/{frames_to_process}")
            
            frame_count += 1
        
        cap.release()
        print(f"Обработка завершена. Создано {len(frames_ascii)} ASCII кадров")
        
        # Создаем BAT файл
        bat_file, output_dir = self.create_bat_file(video_path, frames_ascii, fps)
        
        return bat_file, output_dir
    
    def open_folder(self, folder_path):
        """Открывает папку в файловом менеджере"""
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            print(f"Не удалось открыть папку: {e}")

def main():
    converter = VideoToASCII()
    
    print("=== Видео в ASCII конвертер с цветами ===")
    print("Выберите видео файл для конвертации...")
    
    # Выбираем видео файл
    video_path = converter.get_video_file()
    
    if not video_path:
        print("Файл не выбран. Выход из программы.")
        return
    
    try:
        # Настройки конвертации
        print("\nНастройки конвертации:")
        print("- Размер: 120x30 символов")
        print("- Максимум кадров: 300")
        print("- FPS: 10")
        print("- Цвета: Включены")
        print("- Случайные символы: Включены")
        
        # Обрабатываем видео
        bat_file, output_dir = converter.process_video(
            video_path, 
            max_frames=5000, 
            width=180, 
            height=60, 
            fps=30
        )
        
        print(f"\nКонвертация завершена!")
        print(f"BAT файл создан: {bat_file}")
        print(f"Папка с результатами: {output_dir}")
        
        # Показываем сообщение и открываем папку
        root = tk.Tk()
        root.withdraw()
        
        result = messagebox.askyesno(
            "Конвертация завершена", 
            f"Видео успешно конвертировано в ASCII!\n\n"
            f"BAT файл: {os.path.basename(bat_file)}\n"
            f"Папка: {output_dir}\n\n"
            f"Открыть папку с результатами?"
        )
        
        if result:
            converter.open_folder(output_dir)
        
        root.destroy()
        
        print("\nДля запуска ASCII видео выполните созданный BAT файл!")
        print("Примечание: В Windows может потребоваться включить поддержку ANSI цветов в терминале.")
        
    except Exception as e:
        print(f"Ошибка при обработке видео: {e}")
        messagebox.showerror("Ошибка", f"Не удалось обработать видео:\n{e}")

if __name__ == "__main__":
    main()