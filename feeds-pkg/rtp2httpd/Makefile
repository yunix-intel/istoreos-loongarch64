# rtp2httpd (C) for loongarch64 — binary repack, tool (args vary by use)
include $(TOPDIR)/rules.mk

PKG_NAME:=rtp2httpd
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_SOURCE:=rtp2httpd-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/rtp2httpd
  SECTION:=net
  CATEGORY:=Network
  TITLE:=RTP to HTTP proxy (C)
endef

define Package/rtp2httpd/description
  rtp2httpd 龙芯版：无 cmake，按 CMakeLists 手拼 gcc 命令编出，musl 动态链接。
  命令行工具，按需传参（组播源/端口因环境而异，不设守护）。
endef

define Package/rtp2httpd/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BINDIR)/rtp2httpd $(1)/usr/bin/
endef

define Build/Compile
endef

$(eval $(call BuildPackage,rtp2httpd))
