# Cloudflare R2 图床配置指南

本项目支持将 AI 生成的图片上传到 Cloudflare R2 存储，而不是返回 base64 编码的图片。这可以显著减少响应大小，提高传输效率。

## 功能特点

- ✅ 自动上传生成的图片到 Cloudflare R2
- ✅ 返回公开访问的图片 URL 而不是 base64
- ✅ 支持多种图片格式（PNG, JPEG, GIF, WebP 等）
- ✅ 自动生成唯一文件名（基于内容哈希 + 时间戳）
- ✅ 按年月组织文件结构
- ✅ 可选功能，未配置时自动回退到 base64

## 配置步骤

### 1. 创建 Cloudflare R2 存储桶

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **R2** 服务
3. 点击 **创建存储桶**
4. 输入存储桶名称（例如：`ai-images`）
5. 选择区域（建议选择离用户最近的区域）
6. 点击 **创建存储桶**

### 2. 配置公开访问

1. 进入刚创建的存储桶
2. 点击 **设置** 标签
3. 在 **公开访问** 部分，点击 **允许访问**
4. 记录下公开访问域名（例如：`https://pub-xxxxx.r2.dev`）

或者，你可以绑定自定义域名：
1. 在存储桶设置中，点击 **自定义域**
2. 添加你的域名（例如：`images.yourdomain.com`）
3. 按照提示配置 DNS 记录

### 3. 创建 API 令牌

1. 在 Cloudflare Dashboard 中，进入 **R2** 服务
2. 点击 **管理 R2 API 令牌**
3. 点击 **创建 API 令牌**
4. 选择权限：
   - **对象读取和写入**（Object Read & Write）
5. 选择适用的存储桶（或选择所有存储桶）
6. 点击 **创建 API 令牌**
7. 记录下：
   - **Access Key ID**
   - **Secret Access Key**
   - **Account ID**（在 R2 概览页面可以找到）

### 4. 配置环境变量

在 `.env` 文件中添加以下配置：

```bash
# 启用 R2 图床
R2_ENABLED=true

# R2 账户 ID（在 Cloudflare R2 概览页面查看）
R2_ACCOUNT_ID=your_account_id_here

# R2 API 令牌
R2_ACCESS_KEY_ID=your_access_key_id_here
R2_SECRET_ACCESS_KEY=your_secret_access_key_here

# R2 存储桶名称
R2_BUCKET_NAME=ai-images

# R2 公开访问 URL（使用 R2 提供的域名或自定义域名）
R2_PUBLIC_URL=https://pub-xxxxx.r2.dev
# 或使用自定义域名：
# R2_PUBLIC_URL=https://images.yourdomain.com
```

### 5. 重启服务

配置完成后，重启服务以使配置生效：

```bash
# 如果使用 Docker
docker-compose restart

# 如果直接运行
# 停止当前进程，然后重新启动
python start.py
```

## 使用说明

配置完成后，当 AI 生成图片时：

1. **R2 已启用**：图片会自动上传到 R2，返回的 markdown 格式为：
   ```markdown
   ![Image](https://your-r2-url.com/images/202501/abc123_1234567890.png)
   ```

2. **R2 未启用或上传失败**：自动回退到 base64 格式：
   ```markdown
   ![Image](data:image/png;base64,iVBORw0KG...)
   ```

## 文件组织结构

上传到 R2 的图片按以下结构组织：

```
images/
├── 202501/          # 年月文件夹
│   ├── abc123_1234567890.png
│   ├── def456_1234567891.jpg
│   └── ...
├── 202502/
│   └── ...
└── ...
```

文件名格式：`{内容哈希}_{时间戳}.{扩展名}`

- **内容哈希**：基于图片内容的 MD5 哈希（前16位），相同内容的图片会有相同的哈希
- **时间戳**：毫秒级时间戳，确保文件名唯一性
- **扩展名**：根据 MIME 类型自动确定（png, jpg, gif, webp 等）

## 成本估算

Cloudflare R2 的定价（截至 2024 年）：

- **存储**：$0.015/GB/月
- **Class A 操作**（写入）：$4.50/百万次请求
- **Class B 操作**（读取）：$0.36/百万次请求
- **出站流量**：免费（这是 R2 的主要优势！）

示例：
- 存储 10,000 张图片（每张约 500KB）= 5GB = $0.075/月
- 每月生成 10,000 张图片 = 10,000 次写入 = $0.045
- **总计**：约 $0.12/月

## 故障排查

### 1. 图片仍然返回 base64

**可能原因**：
- R2_ENABLED 未设置为 true
- R2 配置不完整（缺少必需的环境变量）
- R2 API 令牌权限不足

**解决方法**：
- 检查 `.env` 文件中的配置
- 查看服务日志，确认 R2 初始化是否成功
- 验证 API 令牌权限

### 2. 上传失败

**可能原因**：
- API 令牌无效或过期
- 存储桶名称错误
- 网络连接问题

**解决方法**：
- 检查服务日志中的错误信息
- 验证 API 令牌是否有效
- 确认存储桶名称正确
- 检查网络连接

### 3. 图片无法访问

**可能原因**：
- 存储桶未配置公开访问
- R2_PUBLIC_URL 配置错误
- 自定义域名 DNS 未正确配置

**解决方法**：
- 确认存储桶已启用公开访问
- 验证 R2_PUBLIC_URL 是否正确
- 如果使用自定义域名，检查 DNS 配置

## 安全建议

1. **API 令牌权限**：只授予必要的权限（读写对象），不要授予管理权限
2. **存储桶隔离**：为不同的应用使用不同的存储桶
3. **定期审计**：定期检查存储桶中的文件，删除不需要的内容
4. **访问日志**：启用 R2 访问日志，监控异常访问
5. **环境变量保护**：确保 `.env` 文件不被提交到版本控制系统

## 高级配置

### 自定义文件名生成策略

如果需要自定义文件名生成逻辑，可以修改 [`app/r2_uploader.py`](app/r2_uploader.py) 中的 `_generate_filename` 方法。

### 缓存控制

默认缓存策略为 1 年（`max-age=31536000`）。如果需要修改，可以在 [`app/r2_uploader.py`](app/r2_uploader.py) 的 `upload_image` 方法中调整 `CacheControl` 参数。

### 图片压缩

如果需要在上传前压缩图片，可以在 `upload_image` 方法中添加图片处理逻辑（需要安装 Pillow 库）。

## 相关文档

- [Cloudflare R2 官方文档](https://developers.cloudflare.com/r2/)
- [R2 定价](https://developers.cloudflare.com/r2/pricing/)
- [boto3 文档](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)