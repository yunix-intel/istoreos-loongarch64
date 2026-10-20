# quectel-CM-5G (C) for loongarch64 — binary repack, tool (QMI dialer)
include $(TOPDIR)/rules.mk

PKG_NAME:=quectel-CM-5G
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_SOURCE:=quectel-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/quectel-CM-5G
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Quectel QMI dialer (C)
endef

define Package/quectel-CM-5G/description
  quectel-CM 龙芯版：Quectel 5G 模组拨号工具。命令行工具，按模组型号传参。
endef

define Package/quectel-CM-5G/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BINDIR)/quectel-CM $(1)/usr/bin/
endef

define Build/Compile
endef

$(eval $(call BuildPackage,quectel-CM-5G))
