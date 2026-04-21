@echo off
echo 🚀 正在配置 npm 加速...

:: 设置淘宝镜像源
npm config set registry https://registry.npmmirror.com/
echo ✅ 已设置淘宝镜像源

:: 设置 Electron 镜像源
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
echo ✅ 已设置 Electron 镜像源

:: 设置 Puppeteer 镜像源
npm config set puppeteer_download_host https://npmmirror.com/mirrors/puppeteer/
echo ✅ 已设置 Puppeteer 镜像源

:: 设置 chromedriver 镜像源
npm config set chromedriver_cdnurl https://npmmirror.com/mirrors/chromedriver/
echo ✅ 已设置 ChromeDriver 镜像源

:: 设置 node-sass 镜像源
npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass/
echo ✅ 已设置 Node Sass 镜像源

:: 清理缓存
npm cache clean --force
echo ✅ 已清理 npm 缓存

echo.
echo 🎉 npm 加速配置完成！
echo 现在可以运行 'npm install' 来安装依赖，速度会快很多！
echo.
echo 如果需要恢复默认配置，可以运行以下命令：
echo npm config delete registry
echo npm config delete electron_mirror
echo npm config delete puppeteer_download_host
echo npm config delete chromedriver_cdnurl
echo npm config delete sass_binary_site
echo npm config delete phantomjs_cdnurl
echo npm config delete fsevents_binary_host_mirror
echo npm config delete disturl
echo npm config delete python_mirror
echo.
pause