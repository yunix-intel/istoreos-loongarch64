# BaiduPCS-Go (Go) for loongarch64 — binary repack, CLI only
include $(TOPDIR)/rules.mk

PKG_NAME:=baidupcs-go
PKG_VERSION:=4.0.2
PKG_RELEASE:=1

PKG_SOURCE:=baidupcs-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/baidupcs-go
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Baidu netdisk CLI (Go)
endef

define Package/baidupcs-go/description
  BaiduPCS-Go 龙芯版：宿主 Go 直编。交互式命令行工具，无守护进程。
endef

define Package/baidupcs-go/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BINDIR)/baidupcs $(1)/usr/bin/
endef

define Build/Compile
endef

$(eval $(call BuildPackage,baidupcs-go))
