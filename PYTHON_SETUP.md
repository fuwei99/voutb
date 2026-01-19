# Python 启动配置指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例配置文件：
```bash
copy .env.example .env
```

编辑 `.env` 文件，配置必需的环境变量。

### 3. 启动服务

```bash
python start.py
```

或者直接使用 uvicorn：
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8050
```

---

## 环境变量详细说明

### 必需配置

#### `API_KEY` (必需)
- **说明**: 用于保护此适配器服务的API密钥
- **示例**: `API_KEY=your_secure_api_key_here`
- **默认值**: `123456` (不安全，仅用于测试)

### 认证配置（三选一）

#### 方式1: Vertex AI Express API Key（推荐，最简单）

```env
VERTEX_EXPRESS_API_KEY=your_vertex_express_key
```

- **说明**: 使用Vertex AI Express API密钥进行认证
- **支持多个密钥**: 用逗号分隔，例如 `key1,key2,key3`
- **优点**: 配置简单，无需服务账号
- **限制**: 仅支持特定的Gemini模型

#### 方式2: Google服务账号JSON内容

```env
GOOGLE_CREDENTIALS_JSON={"type": "service_account", "project_id": "..."}
```

- **说明**: 直接提供服务账号JSON密钥的完整内容
- **支持多个账号**: 用逗号分隔多个JSON对象，例如 `{...},{...}`
- **优点**: 适合云部署（如Hugging Face Spaces）
- **注意**: JSON内容需要是单行字符串

#### 方式3: 服务账号JSON文件目录（默认）

```env
CREDENTIALS_DIR=./credentials
```

- **说明**: 指定包含服务账号JSON文件的目录
- **默认值**: `/app/credentials` (Docker环境)
- **使用方法**:
  1. 创建目录: `mkdir credentials`
  2. 将 `.json` 密钥文件放入该目录
  3. 服务会自动加载所有 `.json` 文件

### 可选配置

#### `ROUNDROBIN`
```env
ROUNDROBIN=true
```
- **说明**: 启用服务账号轮询模式
- **默认值**: `false`
- **适用**: 当有多个服务账号时，轮流使用以分散请求

#### `GCP_PROJECT_ID`
```env
GCP_PROJECT_ID=your-gcp-project-id
```
- **说明**: 显式指定Google Cloud项目ID
- **默认**: 从凭据自动推断

#### `GCP_LOCATION`
```env
GCP_LOCATION=us-central1
```
- **说明**: 显式指定Google Cloud区域
- **默认**: 从凭据自动推断或使用Vertex AI默认值
- **常用区域**: `us-central1`, `asia-northeast1`, `europe-west1`

#### `HOST` 和 `PORT`
```env
HOST=0.0.0.0
PORT=8050
```
- **说明**: 服务监听的主机和端口
- **默认**: `0.0.0.0:8050`

#### `FAKE_STREAMING`
```env
FAKE_STREAMING=true
FAKE_STREAMING_INTERVAL=1.0
```
- **说明**: 调试用，模拟流式输出
- **默认**: `false`

#### `PROXY_URL`
```env
PROXY_URL=http://proxy.example.com:8080
```
- **说明**: HTTP代理服务器地址

#### `SSL_CERT_FILE`
```env
SSL_CERT_FILE=/path/to/cert.pem
```
- **说明**: SSL证书文件路径

#### `SAFETY_SCORE`
```env
SAFETY_SCORE=true
```
- **说明**: 显示安全评分信息
- **默认**: `false`

---

## 配置示例

### 示例1: 使用Express API Key（最简单）

```env
API_KEY=my_secure_password_123
VERTEX_EXPRESS_API_KEY=AIzaSyD...your_key_here
```

### 示例2: 使用单个服务账号JSON

```env
API_KEY=my_secure_password_123
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"my-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...@....iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

### 示例3: 使用多个服务账号文件 + 轮询

```env
API_KEY=my_secure_password_123
CREDENTIALS_DIR=./credentials
ROUNDROBIN=true
GCP_PROJECT_ID=my-gcp-project
GCP_LOCATION=us-central1
```

目录结构：
```
credentials/
├── account1.json
├── account2.json
└── account3.json
```

---

## Windows 环境变量设置

### 方法1: 使用 `.env` 文件（推荐）

1. 创建 `.env` 文件
2. 添加配置（参考上面的示例）
3. 运行 `python start.py`

### 方法2: 临时设置（当前命令行会话）

```cmd
set API_KEY=your_api_key
set VERTEX_EXPRESS_API_KEY=your_vertex_key
python start.py
```

### 方法3: PowerShell临时设置

```powershell
$env:API_KEY="your_api_key"
$env:VERTEX_EXPRESS_API_KEY="your_vertex_key"
python start.py
```

### 方法4: 系统环境变量（永久）

1. 右键"此电脑" → "属性"
2. "高级系统设置" → "环境变量"
3. 在"用户变量"或"系统变量"中添加
4. 重启命令行窗口

---

## 验证配置

启动服务后，访问以下端点验证：

### 健康检查
```bash
curl http://localhost:8050/
```

### 查看可用模型
```bash
curl http://localhost:8050/v1/models ^
  -H "Authorization: Bearer your_api_key"
```

### 测试聊天接口
```bash
curl -X POST http://localhost:8050/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer your_api_key" ^
  -d "{\"model\":\"gemini-1.5-flash-latest\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}"
```

---

## 常见问题

### Q: 启动时提示"未配置任何认证方式"？
**A**: 请确保至少配置了以下之一：
- `VERTEX_EXPRESS_API_KEY`
- `GOOGLE_CREDENTIALS_JSON`
- `credentials/` 目录中有 `.json` 文件

### Q: 如何获取Vertex AI Express API Key？
**A**: 访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 创建API密钥

### Q: 如何创建服务账号？
**A**: 
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 进入"IAM和管理" → "服务账号"
3. 创建服务账号并授予"Vertex AI用户"角色
4. 创建JSON密钥并下载

### Q: 支持哪些模型？
**A**: 访问 `/v1/models` 端点查看当前可用的所有Gemini模型

### Q: 如何在生产环境部署？
**A**: 建议使用Docker部署，参考项目根目录的 `README.md` 文件

---

## 开发模式

启用自动重载（代码修改后自动重启）：

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8050 --reload
```

---

## 日志和调试

查看详细日志：
```bash
python start.py
```

启动脚本会显示：
- ✓ 配置的环境变量
- ✓ 认证方式
- ✓ 加载的凭据数量
- ⚠️ 配置警告
- ❌ 配置错误

---

## 安全建议

1. **不要**将 `.env` 文件提交到版本控制
2. **不要**在代码中硬编码API密钥
3. **使用强密码**作为 `API_KEY`
4. **定期轮换**服务账号密钥
5. **限制服务账号权限**，仅授予必要的Vertex AI访问权限