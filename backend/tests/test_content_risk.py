"""内容风险 / 敏感词过滤测试."""

import pytest

from audit.content_risk import DEFAULT_SENSITIVE_WORDS, ContentRiskService
from core.exceptions import ValidationError


def test_default_sensitive_words_not_empty():
    assert len(DEFAULT_SENSITIVE_WORDS) > 0


def test_content_risk_detects_default_word():
    service = ContentRiskService()
    is_safe, matched = service.check("这段文本包含诈骗电话请警惕")
    assert is_safe is False
    assert "诈骗电话" in matched


def test_content_risk_filters_word():
    service = ContentRiskService()
    filtered = service.filter("出现非法赌博内容")
    assert "非法赌博" not in filtered
    assert "*" in filtered


def test_content_risk_require_safe_raises():
    service = ContentRiskService()
    with pytest.raises(ValidationError, match="敏感词"):
        service.require_safe("违禁内容测试")


def test_content_risk_custom_word_list():
    service = ContentRiskService(word_list=["自定义词"])
    is_safe, matched = service.check("命中自定义词")
    assert is_safe is False
    assert matched == ["自定义词"]
