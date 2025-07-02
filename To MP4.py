
import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import platform
import random
import string
from PIL import Image, ImageDraw, ImageFont

class VideoToASCII:
    def __init__(self):
        # Расширенный набор ASCII символов для более разнообразного вывода
        self.ascii_chars = " .:-=+*#%@"  # Упрощенный набор для лучшей читаемости
        # Добавляем дополнительные символы для лучшего представления
        self.ascii_chars += "█▉▊▋▌▍▎▏▐░▒▓■□▪▫"
        
        # Настройки для создания изображений
        self.font_size = 8
        self.char_width = 6
        self.char_height = 12
        
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
            random_offset = random.randint(-1, 1)
            index = max(0, min(len(self.ascii_chars) - 1, index + random_offset))
            return self.ascii_chars[index]
        else:
            # Традиционный подход
            index = int(pixel_value / 255 * (len(self.ascii_chars) - 1))
            return self.ascii_chars[index]
    
    def get_color_from_pixel(self, bgr_pixel):
        """Определяет цвет на основе BGR значений пикселя"""
        b, g, r = bgr_pixel
        
        # Возвращаем RGB цвет для использования в PIL
        return (r, g, b)
    
    def frame_to_ascii(self, frame, width=120, height=60, use_colors=True, use_random=True):
        """Конвертирует кадр в ASCII"""
        # Изменяем размер кадра
        frame_resized = cv2.resize(frame, (width, height))
        
        # Конвертируем в оттенки серого для определения яркости
        gray_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        ascii_frame = []
        colors_frame = []
        
        for y in range(height):
            row = ""
            color_row = []
            for x in range(width):
                pixel_value = gray_frame[y, x]
                ascii_char = self.pixel_to_ascii(pixel_value, use_random)
                row += ascii_char
                
                if use_colors:
                    color = self.get_color_from_pixel(frame_resized[y, x])
                    color_row.append(color)
                else:
                    color_row.append((255, 255, 255))  # Белый цвет
            
            ascii_frame.append(row)
            colors_frame.append(color_row)
        
        return ascii_frame, colors_frame
    
    def ascii_to_image(self, ascii_frame, colors_frame, output_width=1920, output_height=1080):
        """Конвертирует ASCII кадр в изображение"""
        # Создаем черное изображение
        img = Image.new('RGB', (output_width, output_height), color='black')
        draw = ImageDraw.Draw(img)
        
        # Пытаемся использовать моноширинный шрифт
        try:
            # Для Windows
            font = ImageFont.truetype("consola.ttf", self.font_size)
        except:
            try:
                # Для Linux
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", self.font_size)
            except:
                try:
                    # Для macOS
                    font = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", self.font_size)
                except:
                    # Используем стандартный шрифт
                    font = ImageFont.load_default()
        
        # Вычисляем размеры символов
        char_width = self.char_width
        char_height = self.char_height
        
        # Вычисляем отступы для центрирования
        total_width = len(ascii_frame[0]) * char_width
        total_height = len(ascii_frame) * char_height
        start_x = (output_width - total_width) // 2
        start_y = (output_height - total_height) // 2
        
        # Рисуем ASCII символы
        for y, (line, color_line) in enumerate(zip(ascii_frame, colors_frame)):
            for x, (char, color) in enumerate(zip(line, color_line)):
                if char != ' ':  # Не рисуем пробелы
                    pos_x = start_x + x * char_width
                    pos_y = start_y + y * char_height
                    draw.text((pos_x, pos_y), char, fill=color, font=font)
        
        # Конвертируем PIL изображение в формат OpenCV
        cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return cv_image
    
    def create_ascii_video(self, video_path, ascii_frames, colors_frames, fps=30, output_width=1920, output_height=1080):
        """Создает видео файл из ASCII кадров"""
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(os.path.dirname(video_path), f"{video_name}_ascii")
        
        # Создаем папку для вывода
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = os.path.join(output_dir, f"{video_name}_ascii.mp4")
        
        # Настройки для записи видео
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_filename, fourcc, fps, (output_width, output_height))
        
        print(f"Создание видео файла: {output_filename}")
        
        for i, (ascii_frame, colors_frame) in enumerate(zip(ascii_frames, colors_frames)):
            # Конвертируем ASCII кадр в изображение
            img = self.ascii_to_image(ascii_frame, colors_frame, output_width, output_height)
            
            # Записываем кадр в видео
            out.write(img)
            
            if (i + 1) % 10 == 0:
                print(f"Записано кадров: {i + 1}/{len(ascii_frames)}")
        
        out.release()
        print(f"Видео файл создан: {output_filename}")
        
        return output_filename, output_dir
    
    def process_video(self, video_path, max_frames=300, width=120, height=60, fps=30, output_width=1920, output_height=1080):
        """Обрабатывает видео и конвертирует в ASCII видео"""
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
        
        ascii_frames = []
        colors_frames = []
        frame_count = 0
        processed_frames = 0
        
        while cap.isOpened() and processed_frames < frames_to_process:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_step == 0:
                ascii_frame, colors_frame = self.frame_to_ascii(frame, width, height, use_colors=True, use_random=True)
                ascii_frames.append(ascii_frame)
                colors_frames.append(colors_frame)
                processed_frames += 1
                
                if processed_frames % 10 == 0:
                    print(f"Обработано кадров: {processed_frames}/{frames_to_process}")
            
            frame_count += 1
        
        cap.release()
        print(f"Обработка завершена. Создано {len(ascii_frames)} ASCII кадров")
        
        # Создаем видео файл
        video_file, output_dir = self.create_ascii_video(video_path, ascii_frames, colors_frames, fps, output_width, output_height)
        
        return video_file, output_dir
    
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
    
    print("=== Видео в ASCII конвертер с сохранением в MP4 ===")
    print("Выберите видео файл для конвертации...")
    
    # Выбираем видео файл
    video_path = converter.get_video_file()
    
    if not video_path:
        print("Файл не выбран. Выход из программы.")
        return
    
    try:
        # Настройки конвертации
        print("\nНастройки конвертации:")
        print("- ASCII размер: 120x60 символов")
        print("- Максимум кадров: 300")
        print("- Выходной FPS: 30")
        print("- Разрешение видео: 1920x1080")
        print("- Цвета: Включены")
        print("- Случайные символы: Включены")
        
        # Обрабатываем видео
        video_file, output_dir = converter.process_video(
            video_path, 
            max_frames=300, 
            width=120, 
            height=60, 
            fps=30,
            output_width=1920,
            output_height=1080
        )
        
        print(f"\nКонвертация завершена!")
        print(f"Видео файл создан: {video_file}")
        print(f"Папка с результатами: {output_dir}")
        
        # Показываем сообщение и открываем папку
        root = tk.Tk()
        root.withdraw()
        
        result = messagebox.askyesno(
            "Конвертация завершена", 
            f"Видео успешно конвертировано в ASCII MP4!\n\n"
            f"Видео файл: {os.path.basename(video_file)}\n"
            f"Папка: {output_dir}\n\n"
            f"Открыть папку с результатами?"
        )
        
        if result:
            converter.open_folder(output_dir)
        
        root.destroy()
        
        print("\nВидео готово к просмотру! Откройте созданный MP4 файл в любом видеоплеере.")
        
    except Exception as e:
        print(f"Ошибка при обработке видео: {e}")
        messagebox.showerror("Ошибка", f"Не удалось обработать видео:\n{e}")

if __name__ == "__main__":
    main()
