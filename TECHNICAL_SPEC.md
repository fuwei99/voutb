# voutb 项目技术说明文档

本文档详细阐述了 voutb 项目（OpenAI 格式转 Google Vertex AI 代理）的核心技术实现，特别是针对多模态 Image 生成模型的高级特性支持。

## 1. 核心架构概述

本项目充当中间人代理，接收客户端标准的 OpenAI API 格式请求，将其转换为 Google Vertex AI API 格式，并将响应流式回传给客户端。

*   **入口**: `POST /v1/chat/completions`
*   **核心转换**: `app/message_processing.py` (消息格式转换)
*   **执行层**: `app/api_helpers.py` (API 调用与流式处理)

## 2. Image 模型支持机制

针对 Google Vertex AI 的 Image 生成模型（如 Gemini Pro Vision / Imagen 3 等），本项目实现了特殊的处理逻辑以确保持续连接和上下文连续性。

### 2.1 标准请求构造

当请求 Image 模型时，后端会向 Vertex AI 发送特定的配置参数。

*   **API Endpoint**: `:streamGenerateContent`
*   **关键 Payload 参数**:
    ```json
    {
      "generationConfig": {
        "responseModalities": ["TEXT", "IMAGE"], // 必须显式启用 IMAGE
        "imageConfig": {
          "imageSize": "2k" // 或 "4k"，由模型后缀 -2k/-4k 控制
        }
      }
    }
    ```

### 2.2 长轮询保活 (Keep-Alive)

图片生成通常耗时较长（>10秒），容易导致标准 HTTP 客户端超时。

*   **问题**: Vertex AI 在生成图片期间不返回任何数据，直到图片生成完毕才一次性推送。
*   **解决方案**:
    1.  **异步队列**: 使用 `asyncio.Queue` 将 Vertex AI 的响应流与向客户端的推送流解耦。
    2.  **超时监测**: 消费者循环使用 `asyncio.wait_for` 等待队列数据，超时阈值设为 5 秒。
    3.  **心跳注入**: 若 5 秒内无数据，后端自动构造一个 OpenAI SSE Chunk 发送给客户端。
        *   **内容**: `{"delta": {"reasoning_content": " "}}`
        *   **目的**: 维持 HTTP 连接活跃，防止客户端 Read Timeout。

### 3. 图床与上下文闭环

为了在无状态的 HTTP 交互中支持多轮对话（如“修改这张图”），本项目设计了基于 Cloudflare R2 的闭环机制。

### 3.1 架构流程

1.  **生成阶段 (Model -> Client)**
    *   **拦截**: 后端捕获 Vertex AI 返回的二进制图片数据 (`inline_data`)。
    *   **上传**: 使用 `boto3` 将数据上传至 Cloudflare R2 存储桶。
        *   *文件名策略*: `images/{YYYYMM}/{MD5}_{Timestamp}.png`
        *   *缓存策略*: `Cache-Control: public, max-age=31536000` (1年)
    *   **替换**: 将响应中的二进制数据替换为 Markdown 图片链接 `![Image](https://r2.domain.com/...)`。
    *   **交付**: 客户端收到包含 URL 的文本，历史记录仅存储 URL。

2.  **引用阶段 (Client -> Model)**
    *   **回传**: 用户发起新一轮对话，客户端将包含 R2 URL 的历史记录发回。
    *   **预处理 (`_inject_previous_images_into_user_message`)**:
        *   扫描 Assistant 历史消息，提取 Markdown 图片 URL。
        *   **净化**: 将 Assistant 消息中的图片标记替换为纯文本占位符 `[Generated Image: URL]`，防止触发 Vertex AI 的签名验证错误（`thought_signature`）。
    *   **下载与注入**:
        *   使用 `httpx` 异步下载 URL 指向的图片数据。
        *   将二进制数据封装为新的 `image_url` (转为 `inline_data`)。
        *   **追加**: 将这些图片追加到**当前 User Message** 的末尾，并附带提示 `[System Note: The following images were generated in the previous turn...]`。
    *   **效果**: 模型将这些图视为用户新上传的参考图，从而能够基于上下文进行修改。

## 4. 模型名称解析策略

为了支持灵活的功能组合，项目采用了迭代式后缀解析逻辑。

*   **解析方式**: 从模型名称末尾开始，循环匹配并剥离已知后缀。
*   **支持组合**: 例如 `gemini-3-pro-image-2k-auto`
    1.  剥离 `-auto` -> 启用自动重试/加密回退机制。
    2.  剥离 `-2k` -> 启用 `imageConfig: {imageSize: "2k"}`。
    3.  剩余 `gemini-3-pro-image` -> 触发 Image 模型特有的 Keep-Alive 逻辑。
*   **优势**: 只要后缀位于末尾，顺序不限（推荐机制在外，配置在内），互不冲突。

## 5. 关键代码位置

*   **R2 上传**: `app/r2_uploader.py`
*   **消息预处理/图片注入**: `app/message_processing.py` -> `_inject_previous_images_into_user_message`
*   **保活逻辑**: `app/api_helpers.py` -> `execute_gemini_call`
*   **后缀解析**: `app/routes/chat_api.py`

---
*文档生成时间: 2025-11-23*