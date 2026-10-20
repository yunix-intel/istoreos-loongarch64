# 51ddns-agent (Go) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=51ddns-agent
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_SOURCE:=51ddns-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/51ddns-agent
  SECTION:=net
  CATEGORY:=Network
  TITLE:=51ddns agent (Go)
endef

define Package/51ddns-agent/description
  51ddns-agent 龙芯版：宿主 Go 直编，静态链接。
endef

define Package/51ddns-agent/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/51ddns $(1)/usr/bin/51ddns-agent
	$(INSTALL_BIN) ./files/51ddns.init $(1)/etc/init.d/51ddns-agent
endef

define Build/Compile
endef

$(eval $(call BuildPackage,51ddns-agent))
