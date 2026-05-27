"""共享测试 fixtures。"""

import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def tmp_dir():
    """创建临时目录，测试结束后自动清理。"""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_text():
    """示例文本，包含多种内容类型。"""
    return """# 技术文档示例

这是一个测试文档，用于验证分块和检索功能。

## 代码示例

```python
def hello():
    print("Hello, World!")
```

## 数据表格

| 名称 | 类型 | 说明 |
|------|------|------|
| config | dict | 配置对象 |
| logger | Logger | 日志实例 |

## 总结

以上是文档的主要内容。
"""
