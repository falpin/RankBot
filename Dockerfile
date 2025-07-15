FROM python:3.11-slim-bullseye

# Установка системных зависимостей и Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    # Основные зависимости для Chrome
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libgbm1 \
    libasound2 \
    # Дополнительные зависимости для headless-режима
    xvfb \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    # Очистка кэша
    && apt-get clean autoclean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN apt-get update && apt-get install -y git

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скрипта
COPY . .

# Установка переменных среды для headless-режима
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Уменьшение размера shared memory
ENV SCREEN_WIDTH=1920
ENV SCREEN_HEIGHT=1080
ENV SCREEN_DEPTH=24

# Запуск X virtual framebuffer
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension RANDR &\n\
exec "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Команда для запуска скрипта
CMD ["python", "bot.py"]