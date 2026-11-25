import re
from functools import lru_cache

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

BLACKLIST_KEY = "blacklist_qq"
WHITELIST_KEY = "whitelist_qq"
KEYWORD_REGEX_KEY = "keyword_regex"


def _as_text_list(raw: object) -> list[str]:
    """把配置值归一化为去除空项的字符串列表。

    兼容 WebUI 的真列表、旧版逗号分隔字符串以及误填的单值。
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        items: list[object] = raw.replace("，", ",").replace("\n", ",").split(",")
    elif isinstance(raw, (list, tuple, set)):
        items = list(raw)
    else:
        items = [raw]
    return [text for text in (str(item).strip() for item in items) if text]


@lru_cache(maxsize=32)
def _compile_patterns(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    """按模式列表编译正则，单条非法正则只记录错误并跳过。"""
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as e:
            logger.error(f"正则无效, 已跳过 {pattern!r}: {e}")
    return tuple(compiled)


@register(
    name="astrbot_plugin_block_qq",
    author="MoeDawn",
    version="0.0.1",
    desc="前置黑名单与正则关键词拦截，阻断所有插件读取被屏蔽消息，减少token消耗",
)
class Main(Star):
    """QQ 黑名单 / 正则关键词前置拦截插件。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        logger.info(
            f"拦截规则加载完成: 黑名单 {len(self._load_users(BLACKLIST_KEY))} 人, "
            f"白名单 {len(self._load_users(WHITELIST_KEY))} 人, "
            f"正则 {len(self._load_patterns())} 条"
        )

    def _load_users(self, key: str) -> set[str]:
        """实时读取配置，WebUI 修改名单后无需重载插件即可生效。"""
        try:
            return set(_as_text_list(self.config.get(key, "")))
        except Exception as e:
            logger.error(f"读取 {key} 配置失败, 本条消息跳过该项: {e}")
            return set()

    def _load_patterns(self) -> tuple[str, ...]:
        """实时读取配置，返回去重后的正则源码；编译由 `_compile_patterns` 缓存。"""
        try:
            return tuple(dict.fromkeys(_as_text_list(self.config.get(KEYWORD_REGEX_KEY, ""))))
        except Exception as e:
            logger.error(f"读取 {KEYWORD_REGEX_KEY} 配置失败, 本条消息跳过关键词拦截: {e}")
            return ()

    def _match_keyword(self, text: str) -> re.Pattern[str] | None:
        for pattern in _compile_patterns(self._load_patterns()):
            if pattern.search(text):
                return pattern
        return None

    @filter.event_message_type(filter.EventMessageType.ALL, priority=999)
    async def pre_block_user(self, event: AstrMessageEvent):
        """高优先级前置拦截：黑名单全量屏蔽，正则关键词命中屏蔽，白名单仅豁免关键词。"""
        try:
            sender_id = str(event.get_sender_id())

            if sender_id in self._load_users(BLACKLIST_KEY):
                logger.info(f"【前置拦截】黑名单用户 {sender_id}")
                event.stop_event()
                return

            if sender_id in self._load_users(WHITELIST_KEY):
                return

            text = event.message_str or ""
            if not text:
                return

            matched = self._match_keyword(text)
            if matched is not None:
                logger.info(f"【前置拦截】关键词命中 {matched.pattern!r} 用户 {sender_id}")
                event.stop_event()
        except Exception:
            # 拦截逻辑异常时放行消息，避免影响正常消息处理
            logger.exception("block_qq 拦截逻辑异常, 已放行该消息")
