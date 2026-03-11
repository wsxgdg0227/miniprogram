let towxml = null;
const app = getApp();

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
    codeLines: [],
    useTowxml: false,
    article: {}
  },

  onLoad(options) {
    const id = Number(options.id || 0);
    if (!id) {
      wx.showToast({ title: "参数错误", icon: "none" });
      return;
    }
    this.fetchSnippetDetail(id);
  },

  async fetchSnippetDetail(id) {
    try {
      const detail = await this.requestDetail(id);
      const content = detail.content || "";
      const codeLines = content.split("\n").map((line, index) => ({
        no: index + 1,
        text: line
      }));

      this.setData({
        id: detail.id,
        title: detail.title || "",
        category: detail.category || "",
        createdAt: detail.created_at || "",
        content,
        codeLines
      });

      if (towxml) {
        const markdown = `\`\`\`cpp\n${content}\n\`\`\``;
        const article = towxml(markdown, "markdown", {
          theme: "dark"
        });
        this.setData({
          article,
          useTowxml: true
        });
      }
    } catch (err) {
      wx.showToast({
        title: `加载失败: ${err.message || err}`,
        icon: "none"
      });
    }
  },

  requestDetail(id) {
    const candidates = [
      app.globalData.baseUrl,
      app.globalData.remoteBaseUrl,
      app.globalData.devBaseUrl,
      app.globalData.mobileBaseUrl
    ]
      .filter((v, i, arr) => v && arr.indexOf(v) === i);

    return new Promise((resolve, reject) => {
      const tryNext = (index) => {
        if (index >= candidates.length) {
          wx.showModal({
            title: "网络不可达",
            content:
              "请在电脑上用管理员权限放行 8000 端口入站，或临时关闭 Windows 防火墙后重试。",
            showCancel: false
          });
          reject(new Error("网络不可达：可能被 Windows 防火墙拦截 8000 端口"));
          return;
        }
        const host = candidates[index];
        wx.request({
          url: `${host}/api/snippets/${id}`,
          method: "GET",
          success: (res) => {
            if (res.statusCode === 200 && res.data) {
              app.globalData.baseUrl = host;
              resolve(res.data);
              return;
            }
            tryNext(index + 1);
          },
          fail: () => tryNext(index + 1)
        });
      };
      tryNext(0);
    });
  }
});
