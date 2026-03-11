# -*- coding: gbk -*-
import os
import time
from pathlib import Path

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 你要监听的本地目录。
# 建议把常用 C++ 模板文件放进这个目录，保存即自动上传。
WATCH_DIR = Path(r"D:\study\projects_trae\weixin\cpp_snippets")

# 后端上传接口地址。
API_URL = os.getenv("CPP_API_URL", "http://127.0.0.1:8000/api/upload")

# 与后端 settings.api_key 保持一致。
API_KEY = os.getenv("CPP_API_KEY", "")

# 默认分类：当文件直接放在根目录时使用。
DEFAULT_CATEGORY = "cpp"

# 分类别名：把常见目录名归一化，避免同义分类重复。
CATEGORY_ALIAS = {
    "c++": "cpp",
    "cplusplus": "cpp",
    "cpp": "cpp",
    "algorithm": "算法",
    "algorithms": "算法",
    "algo": "算法",
    "data-structure": "数据结构",
    "data_structures": "数据结构",
    "ds": "数据结构",
}


def infer_category(file_path: Path) -> str:
    # 规则：
    # 1) 文件在 WATCH_DIR 根目录 -> DEFAULT_CATEGORY
    # 2) 文件在子目录 -> 取第一层子目录名作为分类
    # 3) 目录名会走 CATEGORY_ALIAS 归一化
    try:
        relative_path = file_path.relative_to(WATCH_DIR)
    except ValueError:
        return DEFAULT_CATEGORY

    parts = relative_path.parts
    if len(parts) <= 1:
        return DEFAULT_CATEGORY

    raw = parts[0].strip()
    if not raw:
        return DEFAULT_CATEGORY

    normalized_key = raw.lower()
    return CATEGORY_ALIAS.get(normalized_key, raw)


def upload_file(file_path: Path) -> None:
    # 只处理真实存在的文件，防止临时事件导致读取失败。
    if not file_path.exists():
        return

    # 读取 C++ 文件正文。
    # encoding 使用 utf-8；errors=ignore 可避免少数异常字符直接中断流程。
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    # 如果文件是空内容，就不上传，避免污染数据库。
    if not content.strip():
        return

    # 根据目录自动推断分类。
    category = infer_category(file_path)

    # 使用文件名（不含扩展名）作为 title。
    payload = {
        "title": file_path.stem,
        "category": category,
        "content": content,
    }

    # 在请求头中携带 API key。
    headers = {"X-API-KEY": API_KEY} if API_KEY else {}

    for attempt in range(1, 4):
        try:
            # timeout 防止网络异常时长时间卡住事件线程。
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
            # 非 2xx 响应会抛异常，便于快速发现鉴权或接口错误。
            resp.raise_for_status()
            print(f"[OK] 已上传: {file_path.name} [{category}] -> {resp.json()}")
            return
        except requests.RequestException as exc:
            if attempt == 3:
                # 打印错误，不抛出，让监听循环继续运行。
                print(f"[ERR] 上传失败: {file_path.name}, 原因: {exc}")
                return
            time.sleep(0.5 * attempt)


class CppFileEventHandler(FileSystemEventHandler):
    # 这个字典用来做“防抖”：
    # 某些编辑器一次保存会触发多次 modified 事件，我们用时间窗去重。
    _last_upload_ts: dict[str, float] = {}

    def _handle_cpp_change(self, changed_path: Path) -> None:
        # 统一处理“文件变更”逻辑：
        # - 新建文件（created）
        # - 保存文件（modified）
        # 这样无论是第一次创建 .cpp，还是后续保存，都能触发上传。

        # 只处理 .cpp 文件，其他文件不上传。
        if changed_path.suffix.lower() != ".cpp":
            return

        # 当前时间戳（秒）。
        now = time.time()

        # 获取该文件上次上传时间，默认 0。
        last = self._last_upload_ts.get(str(changed_path), 0)

        # 如果距离上次上传不足 1 秒，则认为是重复事件，直接跳过。
        if now - last < 1:
            return

        # 更新最后上传时间并执行上传。
        self._last_upload_ts[str(changed_path)] = now
        upload_file(changed_path)

    def on_created(self, event) -> None:
        # 新建文件时触发。
        if event.is_directory:
            return
        self._handle_cpp_change(Path(event.src_path))

    def on_modified(self, event) -> None:
        # 目录变化事件直接忽略，我们只关心文件。
        if event.is_directory:
            return

        # 把路径转成 Path 对象，方便做后缀判断与读取。
        changed_path = Path(event.src_path)
        self._handle_cpp_change(changed_path)


def main() -> None:
    # 启动前先确保监听目录存在。
    WATCH_DIR.mkdir(parents=True, exist_ok=True)

    # 创建事件处理器实例。
    event_handler = CppFileEventHandler()
    # 创建观察者（底层会调用系统文件监控能力）。
    observer = Observer()
    # 绑定“目录 + 处理器”，recursive=True 表示子目录也监听。
    observer.schedule(event_handler, str(WATCH_DIR), recursive=True)

    # 启动监听线程。
    observer.start()
    print(f"[INFO] 正在监听目录: {WATCH_DIR}")
    print("[INFO] 按 Ctrl+C 停止监听")

    try:
        # 主线程保持存活，否则程序会直接退出。
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 收到 Ctrl+C 后优雅停止。
        observer.stop()
    finally:
        # 等待监听线程退出，确保资源释放完整。
        observer.join()


if __name__ == "__main__":
    main()
