# block_qq 黑名单拦截插件

一个 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 插件：前置黑名单拦截，阻断所有插件读取黑名单账号消息，减少 Token 消耗。

## 适用场景

- 屏蔽指定 QQ 用户的消息（例如其他机器人），避免刷屏图片、大量消息造成 Token 浪费
- 希望某些用户的消息完全不进入 AstrBot 的处理管道

## 工作原理

- 通过 `@filter.event_message_type(filter.EventMessageType.ALL, priority=999)` 注册高优先级事件监听器，尽可能早地拦截消息（AstrBot 中 `priority` 数值越大越先执行，默认为 `0`）
- 命中黑名单后调用 `event.stop_event()` 终止事件传播，后续所有步骤均不会执行，包括其他插件的 handler 与 LLM 请求
- 因此可以阻止：图片多模态解析、长期记忆插件、LLM 调用等业务插件的处理

> **限制说明**  
>  NapCat 等协议端上报的底层原始日志（core.event_bus）依然会打印消息，这属于协议层行为，插件无法屏蔽，但**不会产生 Token 消耗**。

## 安装与使用

1. **插件市场安装（推荐）**：AstrBot WebUI → 插件 → 插件市场 → 搜索「QQ黑名单前置拦截」安装
2. **手动安装**：将 `astrbot_plugin_block_qq.zip` 压缩包放入 AstrBot 的 `data/plugins/` 目录下解压
3. 在 WebUI 插件配置中填写黑名单 QQ，例如 `111`；多个 QQ 号用英文逗号分隔：`111,222,333`，保存后立即生效，无需重载插件

## 如何确认拦截生效

命中黑名单时控制台会输出：

```text
【前置拦截】黑名单用户 111
```

出现该行日志 = 拦截成功，该消息不会进入后续任何插件和 LLM 处理。

## 环境要求

- AstrBot >= v3.4.21（`priority` 参数自该版本起支持）

## 目录结构

```text
astrbot_plugin_block_qq/
├── main.py            # 插件主逻辑
├── metadata.yaml      # 插件元数据
├── _conf_schema.json  # 插件配置 Schema（WebUI 配置面板）
└── README.md
```
