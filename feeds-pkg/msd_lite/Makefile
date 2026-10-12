# msd_lite (C) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=msd_lite
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_SOURCE:=msd_lite-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/msd_lite
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Multicast proxy (C)
endef

define Package/msd_lite/description
  msd_lite 龙芯版：交叉工具链编，musl 动态链接。
endef

define Package/msd_lite/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/msd_lite $(1)/usr/bin/
	$(INSTALL_BIN) ./files/msd_lite.init $(1)/etc/init.d/msd_lite
endef

define Build/Compile
endef

$(eval $(call BuildPackage,msd_lite))
