// 获取全局 App 实例，用于读取 baseUrl 配置。
const app = getApp();

Page({
  // data 是页面响应式状态，setData 后会自动刷新视图。
  data: {
    snippets: [],
    categories: ["全部"],
    selectedCategory: "全部",
    loading: false,
    errorMsg: ""
  },

  // onLoad 在页面首次加载时执行。
  onLoad() {
    // 进入页面后先加载分类，再拉取列表。
    this.initPage();
  },

  // initPage: 初始化页面数据（分类 + 列表）。
  async initPage() {
    this.setData({ loading: true, errorMsg: "" });
    try {
      const categoriesRaw = await this.requestCategories();
      const categories = Array.isArray(categoriesRaw) ? categoriesRaw : [];
      this.setData({ categories: ["全部", ...categories] });
      await this.fetchSnippets();
    } catch (err) {
      this.setData({
        loading: false,
        errorMsg: `初始化失败: ${err.message || err}`
      });
    }
  },

  // fetchSnippets 使用 async/await，写法接近“同步流程”。
  // 对 C++ 同学来说可理解为：逻辑是顺序写的，但网络等待时不会阻塞 UI 线程。
  async fetchSnippets() {
    this.setData({ loading: true, errorMsg: "" });

    try {
      const selectedCategory = this.data.selectedCategory;
      const categoryParam = selectedCategory === "全部" ? "" : selectedCategory;

      // await 会等待 Promise 完成后再往下执行。
      // 我们把 wx.request 包一层 Promise，方便统一用 async/await。
      const dataRaw = await this.requestList(categoryParam);
      const data = Array.isArray(dataRaw) ? dataRaw : [];

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
  requestList(category = "") {
    const query = category ? `?category=${encodeURIComponent(category)}` : "";
    return this.requestJson(`/api/snippets${query}`);
  },

  requestCategories() {
    return this.requestJson("/api/categories");
  },

  requestJson(path) {
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
          url: `${host}${path}`,
          method: "GET",
          success: (res) => {
            if (res.statusCode === 200) {
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
  },

  onCategoryTap(e) {
    const category = e.currentTarget.dataset.category;
    if (!category || category === this.data.selectedCategory) {
      return;
    }
    this.setData({ selectedCategory: category });
    this.fetchSnippets();
  },

  // 点击卡片后跳转详情页。
  goDetail(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/detail/detail?id=${id}`
    });
  }
});
