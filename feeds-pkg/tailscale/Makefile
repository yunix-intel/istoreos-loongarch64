# Tailscale mesh VPN (host-Go cross-compile, binary repack for loongarch64)
# 原因：feeds/packages 的 tailscale 在 LA 上 staging 失败（no Go files），
# 改用宿主 Go（GOARCH=loong64）直编。构建机先编好 tarball 放 local-src/。
include $(TOPDIR)/rules.mk

PKG_NAME:=tailscale
PKG_VERSION:=1.80.3
PKG_RELEASE:=1

PKG_SOURCE:=tailscale-la-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
# tar 包内无顶层目录，解压后二进制直接落在 $(BUILD_DIR) 下（同 easytier 的教训）
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/tailscale
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Tailscale mesh VPN (backup link)
  URL:=https://tailscale.com
  DEPENDS:=+kmod-tun +ca-bundle
endef

define Package/tailscale/description
  Tailscale 龙芯版直装包：tailscaled + tailscale CLI。
  首次使用：tailscale up（扫码登录，纯 mesh，别开 exit node 抢默认路由）。
endef

define Package/tailscale/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/var/lib/tailscale
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/tailscaled $(1)/usr/bin/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/tailscale $(1)/usr/bin/
	$(INSTALL_BIN) ./files/tailscaled.init $(1)/etc/init.d/tailscale
endef

# 二进制直装包，无需编译
define Build/Compile
endef

$(eval $(call BuildPackage,tailscale))
