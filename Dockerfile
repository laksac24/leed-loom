FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl unzip gnupg2 wget \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-xetex \
    fonts-liberation \
    libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 \
    xdg-utils libgbm1 libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome (stable)
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
    && apt install -y ./chrome.deb \
    && rm chrome.deb

# Install matching ChromeDriver version (124.x)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
    && curl -sSL https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/124.0.6367.78/linux64/chromedriver-linux64.zip -o chromedriver.zip \
    && unzip chromedriver.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver.zip chromedriver-linux64

ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set workdir and copy app
WORKDIR /app
COPY . .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Run app
CMD ["python", "app.py"]
