import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
import cmd

VERSION = "1.0.0"

def check_dependencies():
    """Проверяет наличие необходимых зависимостей."""
    print("[+] Проверка зависимостей...")
    
    try:
        import PyInstaller
        print("[+] PyInstaller найден.")
    except ImportError:
        print("[-] PyInstaller не найден. Установка...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=5.6.2"])
    
    try:
        from cryptography.fernet import Fernet
        print("[+] Cryptography найден.")
    except ImportError:
        print("[-] Cryptography не найден. Установка...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography>=38.0.0"])
    
    print("[+] Все зависимости установлены.")

def create_launcher():
    """Создает простой лаунчер для ExeCryptor."""
    
    # Проверим, существует ли файл exe_cryptor.py, и загрузим его содержимое
    cryptor_code = ""
    if os.path.exists("exe_cryptor.py"):
        try:
            with open("exe_cryptor.py", "r", encoding="utf-8") as f:
                cryptor_code = f.read()
            print("[+] Загружено содержимое exe_cryptor.py")
        except Exception as e:
            print(f"[-] Ошибка при чтении exe_cryptor.py: {e}")
            cryptor_code = ""
    else:
        print("[-] Файл exe_cryptor.py не найден, лаунчер будет работать с внешним файлом")
    
    # Используем raw строку (r) и двойные фигурные скобки для экранирования
    launcher_code = r"""import os
import sys
import argparse
import subprocess
import tempfile
import shutil
import cmd
import inspect

# Встроенный код exe_cryptor.py (будет заполнен при сборке)
EMBEDDED_CRYPTOR_CODE = '''
{}
'''

class ExeCryptorShell(cmd.Cmd):
    intro = '\nВведите команду или help для справки. Для выхода введите exit или quit.'
    prompt = 'ExeCryptor> '
    
    def __init__(self, cryptor_module=None):
        super().__init__()
        self.cryptor_module = cryptor_module
        
    def do_encrypt(self, arg):
        '''Шифрует EXE файл: encrypt input.exe output.py [--hide-console] [--password PASS]'''
        if not arg:
            print("Ошибка: Не указаны параметры.")
            print("Использование: encrypt input.exe output.py [--hide-console] [--password PASS]")
            return
            
        args = arg.split()
        if len(args) < 2:
            print("Ошибка: Недостаточно параметров.")
            print("Использование: encrypt input.exe output.py [--hide-console] [--password PASS]")
            return
        
        input_file = args[0]
        output_file = args[1]
        
        # Парсим дополнительные аргументы
        hide_console = "--hide-console" in args
        password = None
        for i, arg in enumerate(args):
            if arg == "--password" and i + 1 < len(args):
                password = args[i + 1]
        
        # Проверяем, что входной файл существует
        if not os.path.exists(input_file):
            print(f"[-] Ошибка: Входной файл '{{input_file}}' не существует.")
            return
        
        try:
            # Если у нас есть встроенный модуль криптора
            if self.cryptor_module:
                print(f"[+] Шифрование файла {{input_file}}...")
                success = self.cryptor_module.encrypt_file(input_file, output_file, password, hide_console)
                if success:
                    print("[+] Операция завершена успешно.")
                else:
                    print("[-] Операция завершена с ошибкой.")
            else:
                # Если нужно запустить внешний файл
                cryptor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exe_cryptor.py")
                if not os.path.exists(cryptor_path):
                    print("[-] Ошибка: Файл exe_cryptor.py не найден.")
                    return
                
                cmd_args = [sys.executable, cryptor_path, input_file, output_file]
                if hide_console:
                    cmd_args.append("--hide-console")
                if password:
                    cmd_args.extend(["--password", password])
                
                process = subprocess.Popen(cmd_args)
                process.wait()
                
                if process.returncode == 0:
                    print("[+] Операция завершена успешно.")
                else:
                    print(f"[-] Операция завершена с ошибкой (код: {{process.returncode}}).")
        except Exception as e:
            print(f"[-] Ошибка при выполнении: {{e}}")
    
    def do_compile(self, arg):
        '''Компилирует зашифрованный файл в EXE: compile file.py [--noconsole]'''
        if not arg:
            print("Ошибка: Не указан файл.")
            print("Использование: compile file.py [--noconsole]")
            return
            
        args = arg.split()
        file_path = args[0]
        noconsole = "--noconsole" in args
        
        if not os.path.exists(file_path):
            print(f"[-] Ошибка: Файл '{{file_path}}' не существует.")
            return
        
        cmd = [sys.executable, "-m", "PyInstaller", "--onefile"]
        if noconsole:
            cmd.append("--noconsole")
        cmd.append(file_path)
        
        try:
            print(f"[+] Компиляция файла {{file_path}}...")
            process = subprocess.Popen(cmd)
            process.wait()
            if process.returncode == 0:
                print("[+] Компиляция завершена успешно.")
                print(f"[+] Исполняемый файл создан в папке dist/")
            else:
                print(f"[-] Компиляция завершена с ошибкой (код: {{process.returncode}}).")
        except Exception as e:
            print(f"[-] Ошибка при компиляции: {{e}}")
    
    def do_help(self, arg):
        '''Показывает справку о командах'''
        if arg:
            # Показать помощь по конкретной команде
            super().do_help(arg)
        else:
            print("\nДоступные команды:")
            print("  encrypt input.exe output.py [--hide-console] [--password PASS]")
            print("    - Шифрует исполняемый файл")
            print("  compile file.py [--noconsole]")
            print("    - Компилирует зашифрованный файл в EXE")
            print("  exit или quit")
            print("    - Выход из программы")
            print("  help [команда]")
            print("    - Показать эту справку или справку по конкретной команде\n")
    
    def do_exit(self, arg):
        '''Выход из программы'''
        print("Выход из программы...")
        return True
        
    def do_quit(self, arg):
        '''Выход из программы'''
        return self.do_exit(arg)
    
    def emptyline(self):
        '''Не делать ничего при пустой строке'''
        pass
        
    def default(self, line):
        '''Обработка неизвестных команд'''
        print(f"Неизвестная команда: {{line}}")
        print("Введите help для просмотра доступных команд.")

def show_banner():
    banner = r'''
    ______           _____                  _             
   |  ____|         / ____|                | |            
   | |__  __  _____|  |     _ __ _   _ _ __ | |_ ___  _ __ 
   |  __| \ \/ / _ \  |    | '__| | | | '_ \| __/ _ \| '__|
   | |____ >  <  __/  |____| |  | |_| | |_) | || (_) | |   
   |______/_/\_\___|\_______|_|   \__, | .__/ \__\___/|_|   
                                  __/ | |                  
                                 |___/|_|                  
    v1.0.0 - Защита исполняемых файлов      
    '''
    print(banner)
    print("    GitHub: https://github.com/yearningss/execryptor")
    print("    Telegram: https://t.me/yearningss")
    print("    " + "-" * 50)
    print()

def show_help():
    print("Использование:")
    print("  ExeCryptor.exe [путь_к_исходному_exe] [путь_к_выходному_py] [опции]")
    print()
    print("Опции:")
    print("  --password PASSWORD    Пользовательский пароль для шифрования")
    print("  --hide-console         Скрывать окно консоли при запуске защищенного файла")
    print()
    print("Примеры:")
    print("  ExeCryptor.exe MyApp.exe protected.py")
    print("  ExeCryptor.exe MyApp.exe protected.py --hide-console")
    print("  ExeCryptor.exe MyApp.exe protected.py --password mypassword")
    print()
    print("После шифрования используйте PyInstaller для создания EXE:")
    print("  python -m PyInstaller --onefile protected.py")
    print("  python -m PyInstaller --onefile --noconsole protected.py")

def main():
    show_banner()
    
    # Загружаем встроенный модуль криптора, если возможно
    cryptor_module = None
    if EMBEDDED_CRYPTOR_CODE.strip():
        try:
            # Создаем временный модуль из встроенного кода
            import types
            from io import StringIO
            
            # Создаем пространство имен для выполнения кода
            namespace = {{}}
            exec(EMBEDDED_CRYPTOR_CODE, namespace)
            
            # Создаем модуль с функциями из namespace
            cryptor_module = types.SimpleNamespace()
            for name, func in namespace.items():
                if callable(func) and not name.startswith('__'):
                    setattr(cryptor_module, name, func)
                    
            print("[+] Встроенный модуль криптора успешно загружен")
        except Exception as e:
            print(f"[-] Ошибка при загрузке встроенного модуля: {{e}}")
            cryptor_module = None
    
    # Проверяем, переданы ли аргументы
    if len(sys.argv) > 1:
        # Режим прямого выполнения команды
        args = sys.argv[1:]
        
        if len(args) >= 2 and os.path.exists(args[0]):
            # Предполагаем, что первые два аргумента - входной и выходной файлы
            input_file = args[0]
            output_file = args[1]
            hide_console = "--hide-console" in args
            
            # Ищем пароль, если он указан
            password = None
            for i, arg in enumerate(args):
                if arg == "--password" and i + 1 < len(args):
                    password = args[i + 1]
            
            # Выполняем шифрование
            try:
                if cryptor_module:
                    print(f"[+] Шифрование файла {{input_file}}...")
                    success = cryptor_module.encrypt_file(input_file, output_file, password, hide_console)
                    if success:
                        print("[+] Операция завершена успешно.")
                    else:
                        print("[-] Операция завершена с ошибкой.")
                else:
                    # Если встроенный модуль недоступен, ищем внешний файл
                    cryptor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exe_cryptor.py")
                    if not os.path.exists(cryptor_path):
                        print("[-] Ошибка: Файл exe_cryptor.py не найден.")
                    else:
                        cmd_args = [sys.executable, cryptor_path] + args
                        process = subprocess.Popen(cmd_args)
                        process.wait()
                        
                        if process.returncode == 0:
                            print("\n[+] Операция завершена успешно.")
                        else:
                            print(f"\n[-] Операция завершена с ошибкой (код: {{process.returncode}}).")
            except Exception as e:
                print(f"\n[-] Ошибка при выполнении: {{e}}")
        else:
            print("[-] Ошибка: неверные аргументы или файл не найден.")
            show_help()
        
        # После выполнения команды переходим в интерактивный режим
        print("\n[+] Переход в интерактивный режим.")
        shell = ExeCryptorShell(cryptor_module)
        shell.cmdloop()
    else:
        # Показываем справку и переходим в интерактивный режим
        show_help()
        shell = ExeCryptorShell(cryptor_module)
        shell.cmdloop()

if __name__ == "__main__":
    main()
""".format(cryptor_code)
    
    with open("launcher.py", "w", encoding="utf-8") as f:
        f.write(launcher_code)
    
    print("[+] Файл лаунчера создан.")
    return "launcher.py"

def ensure_file_exists(file_path, default_content=""):
    """Проверяет существование файла и создает его с дефолтным содержимым, если он отсутствует."""
    if not os.path.exists(file_path):
        print(f"[-] Файл не найден: {file_path}, создаю...")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(default_content)
            print(f"[+] Файл создан: {file_path}")
            return True
        except Exception as e:
            print(f"[-] Ошибка при создании файла {file_path}: {e}")
            return False
    return True

def create_default_files():
    """Создает необходимые файлы с дефолтным содержимым, если они отсутствуют."""
    print("[+] Проверка наличия необходимых файлов...")
    
    # README.md
    readme_content = """# ExeCryptor

Продвинутый инструмент для защиты исполняемых файлов с использованием сильного шифрования.

## Особенности

- 🔒 Сильное шифрование (AES-256)
- 💻 Поддержка Windows
- 🚫 Возможность скрыть консольное окно
- 🔑 Генерация случайных паролей
- ⚡ Быстрое выполнение
- 🧩 Самораспаковывающийся механизм

## Связь

- GitHub: [@yearningss](https://github.com/yearningss)
- Telegram: [@yearningss](https://t.me/yearningss)

## Лицензия

MIT
"""
    ensure_file_exists("README.md", readme_content)
    
    # LICENSE
    license_content = """MIT License

Copyright (c) 2024 yearningss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    ensure_file_exists("LICENSE", license_content)
    
    # requirements.txt
    requirements_content = """cryptography>=38.0.0
pyinstaller>=5.6.2
"""
    ensure_file_exists("requirements.txt", requirements_content)
    
    # RELEASE.md
    release_content = """# ExeCryptor v1.0.0

## Релиз

Первый официальный релиз ExeCryptor - продвинутого инструмента для защиты исполняемых файлов с использованием сильного шифрования AES-256.
"""
    ensure_file_exists("RELEASE.md", release_content)

def build_executable(launcher_path):
    """Создает исполняемый файл с помощью PyInstaller."""
    print("[+] Сборка исполняемого файла...")
    
    # Создаем временную директорию для сборки
    build_dir = tempfile.mkdtemp()
    try:
        # Копируем необходимые файлы во временную директорию
        shutil.copy("exe_cryptor.py", build_dir)
        shutil.copy(launcher_path, build_dir)
        shutil.copy("requirements.txt", build_dir)
        
        # Путь к иконке, если есть
        icon_path = ""
        if os.path.exists("icon.ico"):
            icon_path = os.path.abspath("icon.ico")
            shutil.copy("icon.ico", build_dir)
        
        # Переходим во временную директорию
        original_dir = os.getcwd()
        os.chdir(build_dir)
        
        # Запускаем PyInstaller
        pyinstaller_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--clean",
            "--name", f"ExeCryptor-{VERSION}",
        ]
        
        if icon_path:
            pyinstaller_cmd.extend(["--icon", icon_path])
            
        pyinstaller_cmd.append(launcher_path)
        
        try:
            subprocess.check_call(pyinstaller_cmd)
        except subprocess.CalledProcessError as e:
            print(f"[-] Ошибка при сборке: {e}")
            # Проверим содержимое файла
            print("[+] Проверка содержимого лаунчера...")
            with open(launcher_path, "rb") as f:
                content = f.read()
                try:
                    content.decode("utf-8")
                    print("[+] Файл в кодировке UTF-8")
                except UnicodeDecodeError:
                    print("[-] Проблема с кодировкой файла. Пересоздание файла...")
                    # Пробуем пересоздать файл с явным указанием кодировки
                    with open(launcher_path, "w", encoding="utf-8") as f:
                        f.write(launcher_code)
                    # Повторная попытка сборки
                    try:
                        subprocess.check_call(pyinstaller_cmd)
                    except subprocess.CalledProcessError as e:
                        print(f"[-] Повторная ошибка при сборке: {e}")
                        return None
        
        # Возвращаемся в исходную директорию
        os.chdir(original_dir)
        
        # Копируем собранный исполняемый файл
        dist_dir = os.path.join(build_dir, "dist")
        exe_name = f"ExeCryptor-{VERSION}.exe"
        exe_path = os.path.join(dist_dir, exe_name)
        
        if not os.path.exists(exe_path):
            print(f"[-] Ошибка: Исполняемый файл не создан: {exe_path}")
            return None
        
        if not os.path.exists("dist"):
            os.makedirs("dist")
        
        shutil.copy(exe_path, os.path.join("dist", exe_name))
        print(f"[+] Исполняемый файл создан: dist/{exe_name}")
        
        return os.path.join("dist", exe_name)
    
    except Exception as e:
        print(f"[-] Ошибка при сборке: {e}")
        return None
    
    finally:
        # Удаляем временную директорию
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
        except Exception as e:
            print(f"[-] Ошибка при удалении временной директории: {e}")

def create_release_zip(exe_path):
    """Создает ZIP-архив с релизом."""
    print("[+] Создание архива релиза...")
    
    # Проверяем существование exe_path
    if not os.path.exists(exe_path):
        print(f"[-] Ошибка: Исполняемый файл не найден: {exe_path}")
        return None
    
    release_dir = "release"
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)
    
    zip_filename = f"ExeCryptor-{VERSION}-release.zip"
    zip_path = os.path.join(release_dir, zip_filename)
    
    print("[+] Файлы для добавления в архив:")
    
    # Список файлов для добавления в архив
    files_to_add = [
        (exe_path, os.path.basename(exe_path)),
        ("exe_cryptor.py", "exe_cryptor.py"),
        ("requirements.txt", "requirements.txt"),
        ("README.md", "README.md"),
        ("LICENSE", "LICENSE"),
    ]
    
    if os.path.exists("RELEASE.md"):
        files_to_add.append(("RELEASE.md", "RELEASE.md"))
    
    # Проверяем существование всех файлов
    missing_files = []
    for file_path, _ in files_to_add:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"[-] Файл не найден: {file_path}")
        else:
            print(f"[+] Файл найден: {file_path}")
    
    if missing_files:
        print("\n[-] Обнаружены отсутствующие файлы.")
        print("[-] Создаем только файлы, которые существуют.")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path, arc_name in files_to_add:
            if os.path.exists(file_path):
                zipf.write(file_path, arc_name)
                print(f"[+] Добавлен в архив: {file_path} -> {arc_name}")
    
    print(f"[+] Архив релиза создан: {zip_path}")
    return zip_path

def main():
    """Основная функция сборки релиза."""
    print("=" * 60)
    print(f"  Сборка релиза ExeCryptor v{VERSION}")
    print("=" * 60)
    
    # Проверяем зависимости
    check_dependencies()
    
    # Создаем необходимые файлы, если они отсутствуют
    create_default_files()
    
    # Создаем лаунчер
    launcher_path = create_launcher()
    
    # Строим исполняемый файл
    exe_path = build_executable(launcher_path)
    
    # Создаем архив релиза (если exe файл был успешно создан)
    if exe_path and os.path.exists(exe_path):
        zip_path = create_release_zip(exe_path)
        
        if zip_path and os.path.exists(zip_path):
            print("\n" + "=" * 60)
            print(f"  Релиз ExeCryptor v{VERSION} успешно создан")
            print("=" * 60)
            print(f"- Исполняемый файл: {exe_path}")
            print(f"- ZIP-архив: {zip_path}")
        else:
            print("\n" + "=" * 60)
            print(f"  Релиз ExeCryptor v{VERSION} создан частично")
            print("=" * 60)
            print(f"- Исполняемый файл: {exe_path}")
            print(f"- ZIP-архив: НЕ СОЗДАН")
    else:
        print("\n" + "=" * 60)
        print(f"  Ошибка при создании релиза ExeCryptor v{VERSION}")
        print("=" * 60)
        
    print("\nГотово!")

if __name__ == "__main__":
    main() 