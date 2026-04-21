# npm 安装加速指南

## 🚀 问题解决方案

npm 安装速度慢通常是因为访问官方 npm 服务器较慢。以下是几种解决方案：

### 方案一：使用淘宝镜像源（推荐）

#### 方法1：手动配置
```bash
# 设置淘宝镜像源
npm config set registry https://registry.npmmirror.com/

# 设置常用依赖的镜像源
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
npm config set puppeteer_download_host https://npmmirror.com/mirrors/puppeteer/
npm config set chromedriver_cdnurl https://npmmirror.com/mirrors/chromedriver/
npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass/
npm config set disturl https://npmmirror.com/mirrors/node/
npm config set python_mirror https://npmmirror.com/mirrors/python/

# 清理缓存
npm cache clean --force
```

#### 方法2：使用脚本
```bash
# Windows 用户
npm-setup.bat

# PowerShell 用户
npm-setup.ps1
```

#### 方法3：使用 nrm（推荐）
```bash
# 安装 nrm
npm install -g nrm

# 切换到淘宝镜像
nrm use taobao

# 验证当前镜像
nrm current
```

### 方案二：使用 yarn 替代 npm

```bash
# 安装 yarn
npm install -g yarn

# 使用 yarn 安装依赖
yarn install
```

### 方案三：使用 pnpm 替代 npm

```bash
# 安装 pnpm
npm install -g pnpm

# 使用 pnpm 安装依赖
pnpm install
```

### 方案四：使用 cnpm

```bash
# 安装 cnpm
npm install -g cnpm

# 使用 cnpm 安装依赖
cnpm install
```

## 📊 性能对比

| 工具 | 下载速度 | 包管理功能 | 内存占用 |
|------|----------|------------|----------|
| npm (官方) | 慢 | 完整 | 中等 |
| npm (淘宝镜像) | 快 | 完整 | 中等 |
| yarn | 快 | 完整 | 较高 |
| pnpm | 最快 | 完整 | 低 |
| cnpm | 快 | 基础 | 中等 |

## 🔧 推荐配置

### 开发环境推荐
```bash
# 推荐使用 pnpm（性能最好）
npm install -g pnpm
pnpm install

# 或者使用 yarn（生态最完善）
npm install -g yarn
yarn install
```

### 生产环境推荐
```bash
# 使用淘宝镜像的 npm
npm config set registry https://registry.npmmirror.com/
npm install
```

## 🛠️ 常用命令

### 查看当前配置
```bash
npm config list
npm config get registry
```

### 恢复默认配置
```bash
npm config delete registry
npm config delete electron_mirror
npm config delete puppeteer_download_host
npm config delete chromedriver_cdnurl
npm config delete sass_binary_site
npm config delete disturl
npm config delete python_mirror
```

### 清理缓存
```bash
npm cache clean --force
```

## 🚨 注意事项

1. **淘宝镜像源更新延迟**：淘宝镜像源通常会有几小时的延迟，如果需要最新版本，建议临时切换回官方源：
   ```bash
   npm config set registry https://registry.npmjs.org/
   ```

2. **私有包安装**：如果项目中有私有包，需要单独配置：
   ```bash
   npm config set @your-scope:registry https://your-private-registry.com/
   ```

3. **CI/CD 环境**：在 CI/CD 环境中，建议在构建脚本中设置镜像源，避免影响其他项目。

## 🎯 最佳实践

1. **项目级配置**：在项目根目录创建 `.npmrc` 文件，避免影响全局配置
   ```ini
   registry=https://registry.npmmirror.com/
   electron_mirror=https://npmmirror.com/mirrors/electron/
   puppeteer_download_host=https://npmmirror.com/mirrors/puppeteer/
   ```

2. **团队协作**：将 `.npmrc` 文件提交到版本控制，确保团队成员使用相同的镜像源

3. **定期更新**：定期更新 npm 和相关工具，获得更好的性能和安全性

## 📝 总结

- **推荐方案**：使用淘宝镜像源 + pnpm
- **简单方案**：使用淘宝镜像源 + npm
- **生态方案**：使用 yarn
- **性能方案**：使用 pnpm

选择最适合您项目需求的方案，享受极速的依赖安装体验！