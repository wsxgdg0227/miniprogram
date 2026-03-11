App({
  onLaunch() {
    let platform = "";
    try {
      platform = wx.getSystemInfoSync().platform || "";
    } catch (e) {
      platform = "";
    }
    const remote = (this.globalData.remoteBaseUrl || "").trim();
    if (platform === "devtools") {
      this.globalData.baseUrl = this.globalData.devBaseUrl;
      return;
    }
    this.globalData.baseUrl = remote || this.globalData.mobileBaseUrl;
  },
  globalData: {
    baseUrl: "",
    devBaseUrl: "http://127.0.0.1:8000",
    mobileBaseUrl: "http://172.17.60.69:8000",
    remoteBaseUrl: ""
  }
});
