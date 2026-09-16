from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


@register(
    name="astrbot_plugin_block_qq",
    author="MoeDawn",
    version="0.0.1",
    desc="前置黑名单拦截，阻断所有插件读取黑名单账号消息，减少token消耗",
)
class Main(Star):
    """QQ 黑名单前置拦截插件。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        logger.info(f"黑名单加载完成: {self._load_blacklist()}")

    def _load_blacklist(self) -> set:
        """实时读取配置，WebUI 修改黑名单后无需重载插件即可生效。"""
        try:
            raw = str(self.config.get("blacklist_qq", "") or "")
        except Exception as e:
            logger.error(f"读取黑名单配置失败, 本条消息跳过拦截: {e}")
            return set()
        raw = raw.replace("，", ",")
        return {qq.strip() for qq in raw.split(",") if qq.strip()}

    @filter.event_message_type(filter.EventMessageType.ALL, priority=999)
    async def pre_block_user(self, event: AstrMessageEvent):
        """高优先级前置拦截：命中黑名单立即终止事件传播，防止Token消耗。"""
        try:
            block_set = self._load_blacklist()
            if not block_set:
                return
            sender_id = str(event.get_sender_id())
            if sender_id in block_set:
                logger.info(f"【前置拦截】黑名单用户 {sender_id}")
                event.stop_event()
        except Exception:
            # 拦截逻辑异常时放行消息，避免影响正常消息处理
            logger.exception("block_qq 拦截逻辑异常, 已放行该消息")
