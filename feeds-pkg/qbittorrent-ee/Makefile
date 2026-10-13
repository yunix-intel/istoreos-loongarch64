# qBittorrent-EE (upstream loong64 musl static) — repack only
include $(TOPDIR)/rules.mk

PKG_NAME:=qBittorrent-EE
PKG_VERSION:=5.2.4.10
PKG_RELEASE:=1

PKG_SOURCE:=qbittorrent-enhanced-nox_loongarch64-linux-musl_static.zip
PKG_SOURCE_URL:=https://github.com/c0re100/qBittorrent-Enhanced-Edition/releases/download/release-$(PKG_VERSION)/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/qBittorrent-EE
  SECTION:=net
  CATEGORY:=Network
  TITLE:=qBittorrent Enhanced (upstream loong64 static)
  URL:=https://github.com/c0re100/qBittorrent-Enhanced-Edition
endef

define Package/qBittorrent-EE/description
  QBEE 龙芯版：上游官方 musl static 包直装。WebUI 默认 :8080，首次设用户名密码。
endef

define Package/qBittorrent-EE/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/qbittorrent-nox $(1)/usr/bin/ 2>/dev/null || \
		$(INSTALL_BIN) $(PKG_BINDIR)/*nox* $(1)/usr/bin/qbittorrent-nox
	$(INSTALL_BIN) ./files/qbittorrent.init $(1)/etc/init.d/qbittorrent-ee
endef

# zip 包自带顶层目录，残留会导致 unzip 交互式询问而失败：先清后解
define Build/Prepare
	rm -rf $(BUILD_DIR)/qbittorrent-enhanced-nox_loongarch64-linux-musl_static
	$(call Build/Prepare/Default)
endef

define Build/Compile
endef

$(eval $(call BuildPackage,qBittorrent-EE))
