# Xray-core (official loong64 release) for loongarch64 — repack only
include $(TOPDIR)/rules.mk

PKG_NAME:=xray-core
PKG_VERSION:=26.3.27
PKG_RELEASE:=1

PKG_SOURCE:=xray-la-$(PKG_VERSION).zip
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/xray-core
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Xray proxy core (upstream loong64)
  URL:=https://github.com/XTLS/Xray-core
endef

define Package/xray-core/description
  Xray 龙芯版：上游官方 Xray-linux-loong64.zip 直装，配 geoip/geosite.dat。
  配置 /etc/xray/config.json，按需填。
endef

define Package/xray-core/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/etc/xray $(1)/usr/share/xray
	$(INSTALL_BIN) $(PKG_BINDIR)/xray $(1)/usr/bin/
	$(INSTALL_DATA) $(PKG_BINDIR)/geoip.dat $(PKG_BINDIR)/geosite.dat $(1)/usr/share/xray/ 2>/dev/null || true
	$(INSTALL_BIN) ./files/xray.init $(1)/etc/init.d/xray
endef

# zip 是平铺包（无顶层目录，共 5 个文件），残留会触发 unzip 交互式询问而失败：
# 只清 BUILD_DIR 根下的解包残留，不动 PKG_BUILD_DIR 本体
#（删 PKG_BUILD_DIR 会导致 Default prepare 建目录失败，已踩）。
define Build/Prepare
	rm -f $(PKG_BINDIR)/xray $(PKG_BINDIR)/geoip.dat $(PKG_BINDIR)/geosite.dat \
		$(PKG_BINDIR)/LICENSE $(PKG_BINDIR)/README.md
	$(call Build/Prepare/Default)
endef

define Build/Compile
endef

$(eval $(call BuildPackage,xray-core))
