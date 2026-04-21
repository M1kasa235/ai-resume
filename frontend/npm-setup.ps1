# npm 加速配置脚本
# 将此文件保存为 npm-setup.ps1 并运行

Write-Host "🚀 正在配置 npm 加速..." -ForegroundColor Green

# 设置淘宝镜像源
npm config set registry https://registry.npmmirror.com/
Write-Host "✅ 已设置淘宝镜像源: https://registry.npmmirror.com/" -ForegroundColor Green

# 设置 Electron 镜像源
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
Write-Host "✅ 已设置 Electron 镜像源" -ForegroundColor Green

# 设置 Puppeteer 镜像源
npm config set puppeteer_download_host https://npmmirror.com/mirrors/puppeteer/
Write-Host "✅ 已设置 Puppeteer 镜像源" -ForegroundColor Green

# 设置 chromedriver 镜像源
npm config set chromedriver_cdnurl https://npmmirror.com/mirrors/chromedriver/
Write-Host "✅ 已设置 ChromeDriver 镜像源" -ForegroundColor Green

# 设置 node-sass 镜像源
npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass/
Write-Host "✅ 已设置 Node Sass 镜像源" -ForegroundColor Green

# 设置 phantomjs 镜像源
npm config set phantomjs_cdnurl https://npmmirror.com/mirrors/phantomjs/
Write-Host "✅ 已设置 PhantomJS 镜像源" -ForegroundColor Green

# 设置 fsevents 镜像源
npm config set fsevents_binary_host_mirror https://npmmirror.com/mirrors/fsevents/
Write-Host "✅ 已设置 FSEvents 镜像源" -ForegroundColor Green

# 设置 node-gyp 镜像源
npm config set disturl https://npmmirror.com/mirrors/node/
Write-Host "✅ 已设置 Node-gyp 镜像源" -ForegroundColor Green

# 设置 Python 镜像源（用于 node-gyp）
npm config set python_mirror https://npmmirror.com/mirrors/python/
Write-Host "✅ 已设置 Python 镜像源" -ForegroundColor Green

# 清理缓存
npm cache clean --force
Write-Host "✅ 已清理 npm 缓存" -ForegroundColor Green

Write-Host "`n🎉 npm 加速配置完成！" -ForegroundColor Green
Write-Host "现在可以运行 'npm install' 来安装依赖，速度会快很多！" -ForegroundColor Yellow
Write-Host "`n如果需要恢复默认配置，可以运行以下命令：" -ForegroundColor Cyan
Write-Host "npm config delete registry" -ForegroundColor Cyan
Write-Host "npm config delete electron_mirror" -ForegroundColor Cyan
Write-Host "npm config delete puppeteer_download_host" -ForegroundColor Cyan
Write-Host "npm config delete chromedriver_cdnurl" -ForegroundColor Cyan
Write-Host "npm config delete sass_binary_site" -ForegroundColor Cyan
Write-Host "npm config delete phantomjs_cdnurl" -ForegroundColor Cyan
Write-Host "npm config delete fsevents_binary_host_mirror" -ForegroundColor Cyan
Write-Host "npm config delete disturl" -ForegroundColor Cyan
Write-Host "npm config delete python_mirror" -ForegroundColor Cyan