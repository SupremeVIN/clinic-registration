#!/bin/bash

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}═══════════════════════════════════════════════════════════"
echo "           РЕГИСТРАТУРА ПОЛИКЛИНИКИ - УСТАНОВЩИК"
echo "                    Для Linux"
echo -e "═══════════════════════════════════════════════════════════${NC}"
echo ""

# Проверяем Python
echo -e "${YELLOW}🔍 Проверка Python...${NC}"
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version)
    echo -e "${GREEN}✅ Найден: $PY_VER${NC}"
else
    echo -e "${RED}❌ Python не найден!${NC}"
    echo ""
    echo "Установите Python командой:"
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-tk"
    echo "  Fedora:         sudo dnf install python3 python3-tkinter"
    echo "  Arch:           sudo pacman -S python tk"
    echo "  openSUSE:       sudo zypper install python3 python3-tk"
    echo ""
    exit 1
fi

# Проверяем tkinter
echo -e "${YELLOW}🔍 Проверка tkinter...${NC}"
python3 -c "import tkinter" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ tkinter работает${NC}"
else
    echo -e "${RED}❌ tkinter не найден!${NC}"
    echo ""
    echo "Установите tkinter:"
    echo "  Ubuntu/Debian:  sudo apt install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  Arch:           sudo pacman -S tk"
    echo "  openSUSE:       sudo zypper install python3-tk"
    echo ""
    exit 1
fi

# Создаем папку для программы
echo -e "${YELLOW}📁 Создание папки программы...${NC}"
PROGRAM_DIR="$HOME/.local/share/poliklinika"
mkdir -p "$PROGRAM_DIR"
mkdir -p "$PROGRAM_DIR/backups"
echo -e "${GREEN}✅ Программа будет в: $PROGRAM_DIR${NC}"

# Копируем файлы
echo -e "${YELLOW}📦 Копирование файлов...${NC}"
cp main.py "$PROGRAM_DIR/" 2>/dev/null
cp gui.py "$PROGRAM_DIR/" 2>/dev/null
cp database.py "$PROGRAM_DIR/" 2>/dev/null

# Если есть готовая база данных
if [ -f "clinic.db" ]; then
    cp clinic.db "$PROGRAM_DIR/"
    echo -e "${GREEN}✅ База данных скопирована${NC}"
    
    # Создаем бэкап
    cp clinic.db "$PROGRAM_DIR/backups/clinic_backup_$(date +%Y%m%d_%H%M%S).db"
fi

# Создаем файл аудита
if [ ! -f "$PROGRAM_DIR/audit.log" ]; then
    echo "# Журнал аудита создан $(date)" > "$PROGRAM_DIR/audit.log"
fi

# Создаем скрипт запуска
echo -e "${YELLOW}📝 Создание скрипта запуска...${NC}"
cat > "$PROGRAM_DIR/run.sh" << EOF
#!/bin/bash
cd "$PROGRAM_DIR"
python3 main.py
EOF

chmod +x "$PROGRAM_DIR/run.sh"

# Создаем ярлык на рабочем столе
echo -e "${YELLOW}🔗 Создание ярлыка...${NC}"

# Ищем папку рабочего стола
if [ -d "$HOME/Рабочий стол" ]; then
    DESKTOP="$HOME/Рабочий стол"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP="$HOME/Desktop"
else
    DESKTOP="$HOME"
    echo -e "${YELLOW}⚠️ Папка рабочего стола не найдена, ярлык в домашней папке${NC}"
fi

# Создаем .desktop файл
cat > "$DESKTOP/поликлиника.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Регистратура поликлиники
Comment=Автоматизация работы регистратуры
Exec=$PROGRAM_DIR/run.sh
Icon=applications-education
Terminal=false
Categories=Office;Medical;
StartupNotify=true
EOF

chmod +x "$DESKTOP/поликлиника.desktop"

# Создаем инструкцию
echo -e "${YELLOW}📝 Создание инструкции...${NC}"
cat > "$PROGRAM_DIR/ИНСТРУКЦИЯ.txt" << EOF
================================================
РЕГИСТРАТУРА ПОЛИКЛИНИКИ - ИНСТРУКЦИЯ
================================================

✅ УСТАНОВКА ЗАВЕРШЕНА!

🚀 КАК ЗАПУСТИТЬ:
   1. Дважды щёлкните ярлык "поликлиника.desktop" на рабочем столе
   2. Или выполните: $PROGRAM_DIR/run.sh
   3. Или перейдите в папку и запустите: python3 main.py

📁 ГДЕ ХРАНЯТСЯ ДАННЫЕ:
   • База данных: $PROGRAM_DIR/clinic.db
   • Журнал аудита: $PROGRAM_DIR/audit.log
   • Резервные копии: $PROGRAM_DIR/backups/

🔐 БЕЗОПАСНОСТЬ:
   ✓ Защита от SQL-инъекций
   ✓ Валидация всех данных
   ✓ Логирование действий
   ✓ Автоматические бэкапы

================================================
EOF

# Финальное сообщение
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════"
echo "                  УСТАНОВКА ЗАВЕРШЕНА!"
echo -e "═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ Программа установлена в:${NC}"
echo "   $PROGRAM_DIR"
echo ""
echo -e "${GREEN}✅ Ярлык создан:${NC}"
echo "   $DESKTOP/поликлиника.desktop"
echo ""
echo -e "${GREEN}🚀 Запустить программу:${NC}"
echo "   Дважды щёлкните ярлык на рабочем столе"
echo ""
echo -e "${GREEN}📖 Инструкция:${NC}"
echo "   $PROGRAM_DIR/ИНСТРУКЦИЯ.txt"
echo ""