# -*- coding: gbk -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "miniprogram"


FILES: dict[str, str] = {
    "app.js": """// 小程序全局入口文件。
App({
  // globalData 用于存放全局配置。
  // 注意：真机调试时 localhost 指向手机自身，不是你的电脑。
  // 因此请把 baseUrl 改成你的电脑局域网 IP，例如 http://192.168.1.8:8000
  globalData: {
    baseUrl: "http://127.0.0.1:8000"
  }
});
""",
    "pages/list/list.json": """{
  "navigationBarTitleText": "代码列表"
}
""",
    "pages/list/list.wxml": """<view class="container">
  <view class="header">C++ 代码片段</view>

  <block wx:if="{{loading}}">
    <view class="state">加载中...</view>
  </block>

  <block wx:elif="{{errorMsg}}">
    <view class="state error">{{errorMsg}}</view>
  </block>

  <block wx:elif="{{snippets.length === 0}}">
    <view class="state">暂无数据，请先上传 .cpp 文件</view>
  </block>

  <block wx:else>
    <view
      class="card"
      wx:for="{{snippets}}"
      wx:key="id"
      bindtap="goDetail"
      data-id="{{item.id}}"
      data-title="{{item.title}}"
      data-content="{{item.content}}"
      data-created="{{item.created_at}}"
      data-category="{{item.category}}"
    >
      <view class="title">{{item.title}}</view>
      <view class="meta">{{item.category}} · {{item.created_at}}</view>
    </view>
  </block>
</view>
""",
    "pages/list/list.js": """// 获取全局 App 实例，用于读取 baseUrl 配置。
const app = getApp();

Page({
  // data 是页面响应式状态，setData 后会自动刷新视图。
  data: {
    snippets: [],
    loading: false,
    errorMsg: ""
  },

  // onLoad 在页面首次加载时执行。
  onLoad() {
    // 进入页面后立刻拉取列表。
    this.fetchSnippets();
  },

  // fetchSnippets 使用 async/await，写法接近“同步流程”。
  // 对 C++ 同学来说可理解为：逻辑是顺序写的，但网络等待时不会阻塞 UI 线程。
  async fetchSnippets() {
    this.setData({ loading: true, errorMsg: "" });

    try {
      // await 会等待 Promise 完成后再往下执行。
      // 我们把 wx.request 包一层 Promise，方便统一用 async/await。
      const data = await this.requestList();

      // 成功后更新页面数据。
      this.setData({
        snippets: data,
        loading: false
      });
    } catch (err) {
      // 捕获网络错误或后端错误并显示给用户。
      this.setData({
        loading: false,
        errorMsg: `请求失败: ${err.message || err}`
      });
    }
  },

  // requestList: 把“回调风格”的 wx.request 封装成 Promise。
  requestList() {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${app.globalData.baseUrl}/api/snippets`,
        method: "GET",
        success: (res) => {
          // 后端正常返回数组时 resolve。
          if (res.statusCode === 200 && Array.isArray(res.data)) {
            resolve(res.data);
            return;
          }
          // 非 200 视为失败，交给外层 catch 处理。
          reject(new Error(`HTTP ${res.statusCode}`));
        },
        fail: (err) => {
          // 底层网络失败（断网、地址不可达等）。
          reject(err);
        }
      });
    });
  },

  // 点击卡片后跳转详情页。
  goDetail(e) {
    // dataset 是 WXML data-* 透传参数集合。
    const { id, title, content, created, category } = e.currentTarget.dataset;
    wx.navigateTo({
      // 通过 querystring 把基本信息传给详情页。
      // 注意 content 可能包含特殊字符，因此使用 encodeURIComponent。
      url:
        `/pages/detail/detail?id=${id}` +
        `&title=${encodeURIComponent(title)}` +
        `&content=${encodeURIComponent(content)}` +
        `&created=${encodeURIComponent(created)}` +
        `&category=${encodeURIComponent(category)}`
    });
  }
});
""",
    "pages/detail/detail.json": """{
  "navigationBarTitleText": "代码详情"
}
""",
    "pages/detail/detail.wxml": """<view class="container">
  <view class="title">{{title}}</view>
  <view class="meta">{{category}} · {{createdAt}}</view>

  <view class="section-title">源码</view>

  <block wx:if="{{useTowxml}}">
    <import src="../../towxml/towxml.wxml" />
    <template is="towxml" data="{{...article}}" />
  </block>

  <block wx:else>
    <scroll-view scroll-x="true" class="code-scroll">
      <text class="code-text">{{content}}</text>
    </scroll-view>
  </block>
</view>
""",
    "pages/detail/detail.js": """let towxml = null;

try {
  // 尝试加载 towxml 解析器。
  // 如果项目尚未安装 towxml，这里会抛异常，随后自动走纯文本降级模式。
  towxml = require("../../towxml/index");
} catch (e) {
  towxml = null;
}

Page({
  data: {
    id: "",
    title: "",
    category: "",
    createdAt: "",
    content: "",
    useTowxml: false,
    article: {}
  },

  onLoad(options) {
    // options 是从上一页 navigateTo url querystring 传入的参数。
    const title = decodeURIComponent(options.title || "");
    const category = decodeURIComponent(options.category || "");
    const createdAt = decodeURIComponent(options.created || "");
    const content = decodeURIComponent(options.content || "");

    // 默认先显示基础数据。
    this.setData({
      id: options.id || "",
      title,
      category,
      createdAt,
      content
    });

    // 若 towxml 可用，则把 C++ 代码包装成 markdown 代码块并解析成富文本 AST。
    if (towxml) {
      const markdown = `\\`\\`\\`cpp\\n${content}\\n\\`\\`\\``;
      const article = towxml(markdown, "markdown", {
        theme: "light"
      });
      this.setData({
        article,
        useTowxml: true
      });
    }
  }
});
""",
}


def main() -> None:
    for rel, content in FILES.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"[OK] wrote utf-8: {path}")


if __name__ == "__main__":
    main()
